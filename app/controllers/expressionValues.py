from flask import Response, jsonify, stream_with_context
from scipy.cluster.hierarchy import linkage, dendrogram
import pandas as pd
import app.models as models
from app.config import LATEST, db

def get_gene_expr(dataset_ID: int = None, disease_name=None, ensg_number=None, gene_symbol=None, cluster: bool = False, limit: int = None, offset: int = None, sponge_db_version: int = LATEST):
    """
    Handles API call /exprValue/getceRNA to get gene expression values
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param sponge_db_version: version of the database
    :param cluster: whether to cluster the gene expression (rows and columns)
    :param limit: limit the number of results
    :return: all expression values for the genes of interest
    """
    # test if any of the two identification possibilities is given
    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification parameter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        return jsonify({
            "detail": "No gene(s) found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # save all needed queries to get correct results
    queries = [models.GeneExpressionValues.gene_ID.in_(gene_IDs)]

    # filter datasets by database version 
    dataset_query = models.Dataset.query.filter(models.Dataset.sponge_db_version == sponge_db_version)

    # if specific disease_name is given:
    if disease_name is not None:
        dataset_query = dataset_query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
        
    if dataset_ID is not None:
        dataset_query = dataset_query \
            .filter(models.Dataset.dataset_ID == dataset_ID)
    
    dataset = dataset_query.all()

    if len(dataset) > 0:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.GeneExpressionValues.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": f"No dataset with given disease_name for the database version {sponge_db_version} found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.GeneExpressionValues.query \
        .filter(*queries) \
        .all()
    
    if len(result) > 0:
        # perform hierarchical clustering on rows and columns
        if cluster:
            # Convert result to a DataFrame for clustering
            data = pd.DataFrame([{
                "gene_ID": r.gene.gene_symbol if r.gene.gene_symbol else r.gene.ensg_number,
                "sample_ID": r.sample_ID + "___" + (
                    str(r.dataset.disease_name) if disease_name == "pancancer" else
                    str(r.dataset.disease_subtype)
                    ),
                "expression_value": r.expr_value,
            } for r in result])

            # Pivot the data to create a matrix for clustering
            expression_matrix = data.pivot(index="gene_ID", columns="sample_ID", values="expression_value").fillna(0)

            # Perform hierarchical clustering on rows (genes) and columns (datasets)
            try:
                row_linkage = linkage(expression_matrix, method='ward', optimal_ordering=False)
                col_linkage = linkage(expression_matrix.T, method='ward', optimal_ordering=False)
            except ValueError as e:
                # Handle the case where the data is not suitable for clustering
                return jsonify({
                    "detail": str(e),
                    "status": 400,
                    "title": "Bad Request",
                    "type": "about:blank"
                }), 400

            # Add clustering results to the response
            row_order = dendrogram(row_linkage, labels=expression_matrix.index, no_plot=True).get('leaves')
            col_order = dendrogram(col_linkage, labels=expression_matrix.columns, no_plot=True).get('leaves')
            expression_matrix = expression_matrix.iloc[row_order, col_order]

            result = expression_matrix.reset_index().melt(id_vars='gene_ID', var_name='sample_ID', value_name='expression_value')
            result = [models.GeneExpressionValues(gene={"gene_symbol": row['gene_ID'], "ensg_number": None}, 
                                                    expr_value=row['expression_value'],
                                                    sample_ID=row['sample_ID'], #.split('___')[0],
                                                    # note that this is 'pancancer' if the disease is 'pancancer'
                                                    dataset={"disease_subtype": row['sample_ID'].split('___')[1]},
                                                    )
                for _, row in result.iterrows()]
            

        # Limit the number of results if specified
        if offset is not None:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]

        def generate():
            yield "["
            first = True
            for r in result:
                if not first:
                    yield ","
                yield models.geneExpressionSchema().dumps(r)
                first = False
            yield "]"
            
            
        return Response(stream_with_context(generate()), content_type='application/json')
        
        # return models.geneExpressionSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
        
    



def get_transcript_expression(dataset_ID: int = None, disease_name: str = None, enst_number: str = None, ensg_number: str = None, cluster: bool = False, gene_symbol: str = None, limit: int = None, sponge_db_version: int = LATEST):
    """
    Handles API call /exprValue/getTranscriptExpr to return transcript expressions
    :param dataset_ID: dataset_ID of interest
    :param disease_name: Name of the disease
    :param enst_number: Ensembl transcript ID
    :param ensg_number: Ensembl gene ID
    :param gene_symbol: gene symbol
    :param limit: limit the number of results
    :param cluster: whether to cluster the gene expression (rows and columns)
    :param sponge_db_version: version of the database
    :return: expression values for given search parameters
    """
    if ensg_number is None and gene_symbol is None and enst_number is None:
        return jsonify({
            "detail": "Please supply one of 'enst_number' ensg_number', or 'gene_symbol",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    elif enst_number is not None:
        # query by enst_numbers only
        transcript = models.Transcript.query \
            .filter(models.Transcript.enst_number.in_(enst_number)) \
            .all()
    elif ensg_number is not None or gene_symbol is not None:
        if ensg_number is not None:
            # query all transcripts with matching ensg_number
            gene = models.Gene.query \
                .filter(models.Gene.ensg_number.in_(enst_number)) \
                .all()
        else:
            # query all transcripts with matching gene symbol
            gene = models.Gene.query \
                .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
                .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
        else:
            return jsonify({
                "detail": "No gene(s) found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

        # get associated transcripts
        transcript = models.Transcript.query \
            .filter(models.Transcript.gene_ID.in_(gene_IDs)) \
            .all()
    else:
        return jsonify({
            "detail": "Multiple filters supplied, please give one of 'enst_number' ensg_number', or 'gene_symbol",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # collect transcript IDs
    transcript_IDs = [i.transcript_ID for i in transcript]
    # build filters
    filters = [models.ExpressionDataTranscript.transcript_ID.in_(transcript_IDs)]
    
    # filter datasets by database version 
    dataset_query = models.Dataset.query.filter(models.Dataset.sponge_db_version == sponge_db_version)

    # search for disease and add dataset_ID to filters if found
    if disease_name is not None:
        dataset_query = dataset_query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
    
    if dataset_ID is not None:
        dataset_query = dataset_query \
            .filter(models.Dataset.dataset_ID == dataset_ID)
    
    dataset = dataset_query.all()

    if len(dataset) > 0:
        dataset_IDs = [i.dataset_ID for i in dataset]
        filters.append(models.ExpressionDataTranscript.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": f"No dataset with given disease_name for the database version {sponge_db_version} found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400
    
    # apply all filters
    query = db.select(models.ExpressionDataTranscript).filter(*filters)
    result = db.session.execute(query).scalars().all()

    if len(result) > 0:
                # perform hierarchical clustering on rows and columns
        if cluster:
            # Convert result to a DataFrame for clustering
            data = pd.DataFrame([{
                "ensembl_ID": r.transcript.enst_number + "___" + (r.transcript.gene.gene_symbol if r.transcript.gene.gene_symbol else r.transcript.gene.ensg_number),
                "sample_ID": r.sample_ID + "___" + str(r.dataset.disease_subtype),
                "expression_value": r.expr_value,
            } for r in result])

            # Pivot the data to create a matrix for clustering
            expression_matrix = data.pivot(index="ensembl_ID", columns="sample_ID", values="expression_value").fillna(0)

            # Perform hierarchical clustering on rows (genes) and columns (datasets)
            row_linkage = linkage(expression_matrix, method='ward')
            col_linkage = linkage(expression_matrix.T, method='ward')

            # Add clustering results to the response
            row_order = dendrogram(row_linkage, labels=expression_matrix.index, no_plot=True).get('leaves')
            col_order = dendrogram(col_linkage, labels=expression_matrix.columns, no_plot=True).get('leaves')
            expression_matrix = expression_matrix.iloc[row_order, col_order]

            result = expression_matrix.reset_index().melt(id_vars='ensembl_ID', var_name='sample_ID', value_name='expression_value')
            result = [models.ExpressionDataTranscript(
                transcript={"enst_number": row['ensembl_ID'].split("___")[0], "gene": {"gene_symbol": row['ensembl_ID'].split('___')[1]}}, 
                expr_value=row['expression_value'],
                sample_ID=row['sample_ID'].split('___')[0],
                dataset={"disease_subtype": row['sample_ID'].split('___')[1]},
            )for _, row in result.iterrows()]
        return models.ExpressionDataTranscriptSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No transcript expression data found for the given filters.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_mirna_expr(dataset_ID: int = None, disease_name=None, mimat_number=None, hs_number=None, sponge_db_version: int = LATEST):
    """
    Handles API call /exprValue/getmiRNA to get miRNA expression values
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param sponge_db_version: version of the database
    :return: all expression values for the mimats of interest
    """

    # test if any of the two identification possibilites is given
    if mimat_number is None and hs_number is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if mimat_number is not None and hs_number is not None:
        return jsonify({
            "detail": "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    mirna = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()

    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
    else:
        return jsonify({
            "detail": "No miRNA(s) found for given mimat_number(s) or hs_number(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # save all needed queries to get correct results
    queries = [models.MiRNAExpressionValues.miRNA_ID.in_(mirna_IDs)]

    # filter datasets by database version
    dataset_query = models.Dataset.query.filter(models.Dataset.sponge_db_version == sponge_db_version)

    # if specific disease_name is given:
    if disease_name is not None:
        dataset_query = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) 
        
    if dataset_ID is not None:
        dataset_query = dataset_query \
            .filter(models.Dataset.dataset_ID == dataset_ID)
    
    dataset = dataset_query.all()

    if len(dataset) > 0:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.MiRNAExpressionValues.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": f"No dataset with given disease_name for the database version {sponge_db_version} found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.MiRNAExpressionValues.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.miRNAExpressionSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
