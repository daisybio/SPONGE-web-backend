import sqlalchemy as sa
import os
from flask import jsonify
from sqlalchemy import desc, engine_from_config, literal_column, or_, and_
from sqlalchemy.sql import text
from app.controllers.dataset import _dataset_query
import app.models as models
from app.config import LATEST, db


def read_all_genes(dataset_ID: int = None, disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None, pValue=0.05,
                   pValueDirection="<", mscor=None, mscorDirection="<", correlation=None, correlationDirection="<",
                   sorting=None, descending=True, limit=100, offset=0, information=True, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /ceRNAInteraction/findAll
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param gene_type: defines the type of gene of interest
    :param pValue: pValue cutoff
    :param pValueDirection: < or >
    :param mscor mscor cutofff
    :param mscorDirection: < or >
    :param correlation: correlation cutoff
    :param correlationDirection: < or >
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :param sponge_db_version: version of the sponge database
    :return: all interactions given gene is involved
    """
    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # test if just one of the possible identifiers is given
    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        return jsonify({
            "detail": "More than one identification paramter is given. Please choose one out of (ensg number, gene symbol or gene type)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


    queries_1 = []
    queries_2 = []

    # filter for database version 
    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    # if specific disease_name is given:
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
    
    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)
    
    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries_1.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
        queries_2.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name / dataset_ID found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


    gene = []
    # if ensg_numer is given to specify gene(s), get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
    # if gene_symbol is given to specify gene(s), get the intern gene_ID(primary_key) for requested gene_symbol(gene_ID)
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()
    elif gene_type is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_type == gene_type) \
            .all()

    # save all needed queries to get correct results
    if ensg_number is not None or gene_symbol is not None or gene_type is not None:
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries_1.append(models.GeneInteraction.gene_ID1.in_(gene_IDs))
            queries_2.append(models.GeneInteraction.gene_ID2.in_(gene_IDs))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queries_1.append(models.GeneInteraction.p_value <= pValue)
            queries_2.append(models.GeneInteraction.p_value <= pValue)
        else:
            queries_1.append(models.GeneInteraction.p_value >= pValue)
            queries_2.append(models.GeneInteraction.p_value >= pValue)
    if mscor is not None:
        if mscorDirection == "<":
            queries_1.append(models.GeneInteraction.mscor <= mscor)
            queries_2.append(models.GeneInteraction.mscor <= mscor)
        else:
            queries_1.append(models.GeneInteraction.mscor >= mscor)
            queries_2.append(models.GeneInteraction.mscor >= mscor)
    if correlation is not None:
        if correlationDirection == "<":
            queries_1.append(models.GeneInteraction.correlation <= correlation)
            queries_2.append(models.GeneInteraction.correlation <= correlation)
        else:
            queries_1.append(models.GeneInteraction.correlation >= correlation)
            queries_2.append(models.GeneInteraction.correlation >= correlation)

    # add all sorting if given:
    sort = []
    if sorting is not None:
        if sorting == "pValue":
            if descending:
                sort.append(models.GeneInteraction.p_value.desc())
            else:
                sort.append(models.GeneInteraction.p_value.asc())
        if sorting == "mscor":
            if descending:
                sort.append(models.GeneInteraction.mscor.desc())
            else:
                sort.append(models.GeneInteraction.mscor.asc())
        if sorting == "correlation":
            if descending:
                sort.append(models.GeneInteraction.correlation.desc())
            else:
                sort.append(models.GeneInteraction.correlation.asc())

    # interaction_result = []

    interaction_result = models.GeneInteraction.query \
        .filter(*queries_1) \
        .order_by(*sort) \
        .union(models.GeneInteraction.query
               .filter(*queries_2)
               .order_by(*sort)) \
        .slice(offset, offset + limit) \
        .all()

    # if len(tmp) > 0:
    #    interaction_result.append(tmp)
    # else:
    #    abort(404, "No information with given parameters found")

    # interaction_result = [val for sublist in interaction_result for val in sublist]

    if len(interaction_result) > 0:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.GeneInteractionDatasetLongSchema(many=True)
        else:
            # Serialize the data for the response depending on parameter all
            schema = models.GeneInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_result)
    else:
        return jsonify({
            "detail": "No information with given parameters found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def read_specific_interaction(dataset_ID: int = None, disease_name=None, ensg_number=None, gene_symbol=None, 
                              pValue=0.05, pValueDirection="<", 
                            #   minBetweenness: float = 0, minNodeDegree: int = 0, minEigenvector: float = 0,
                              sorting: str = "betweenness", descending: bool = True,
                              limit: int=100, offset=0, sponge_db_version: int = LATEST):
    """
        This function responds to a request for /ceRNAInteraction/findSpecific
        and returns all interactions between the given identifications (ensg_number or gene_symbol)
        :param dataset_ID: dataset_ID of interest
        :param disease_name: disease_name of interest
        :param ensg_number: esng number of the genes of interest
        :param gene_symbol: gene symbol of the genes of interest
        :param minBetweenness: betweenness cutoff (>)
        :param minNodeDegree: degree cutoff (>)
        :param minEigenvector: eigenvector cutoff (>)
        :param sorting: how the results of the db query should be sorted
        :param descending: should the results be sorted in descending or ascending order
        :param limit: number of results that shouls be shown
        :param offset: startpoint from where results should be shown
        :param sponge_db_version: version of the sponge database    
        :return: all interactions between given genes
      """
    
    SORT_KEYS = {
        "betweenness": models.networkAnalysis.betweenness,
        "degree": models.networkAnalysis.node_degree,
        "eigenvector": models.networkAnalysis.eigenvector
    }
    if not sorting in SORT_KEYS:
        abort(404, "Invalid sorting key. Choose one of 'betweenness', 'degree', 'eigenvector'")

    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification parameter is given. Please choose one.",
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
            "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


    # save all needed queries to get correct results
    queries = [sa.and_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs))]

    # filter for database version 
    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    # if specific disease_name is given:
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
    
    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)
            
    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queries.append(models.GeneInteraction.p_value < pValue)
        else:
            queries.append(models.GeneInteraction.p_value > pValue)

    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneInteractionDatasetShortSchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No information with given parameters found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def read_all_gene_network_analysis(dataset_ID: int = None, disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None,
                                   minBetweenness=None, minNodeDegree=None, minEigenvector=None,
                                   sorting=None, descending=True, limit=100, offset=0, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /findceRNA
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
    :param dataset_ID: dataset_ID of interest
    :param disease_name: isease_name of interest
    :param gene_type: defines the type of gene of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param minBetweenness: betweenness cutoff (>)
    :param minNodeDegree: degree cutoff (>)
    :param minEigenvector: eigenvector cutoff (>)
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :param sponge_db_version: version of the sponge database
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    """

    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # save all needed queries to get correct results
    queries = []

    # select runs for database version 
    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    # if specific disease_name is given (should be because for this endpoint is it required):
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            
    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)
        
    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.networkAnalysis.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification paramter is given. Please choose one.",
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
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # filter further depending on given statistics cutoffs
    if minBetweenness is not None:
        queries.append(models.networkAnalysis.betweenness > minBetweenness)
    if minNodeDegree is not None:
        queries.append(models.networkAnalysis.node_degree > minNodeDegree)
    if minEigenvector is not None:
        queries.append(models.networkAnalysis.eigenvector > minEigenvector)
    if gene_type is not None:
        queries.append(models.Gene.gene_type == gene_type)

    # add all sorting if given:
    sort = [models.networkAnalysis.sponge_run_ID]
    if sorting is not None:
        if sorting == "betweenness":
            if descending:
                sort.append(models.networkAnalysis.betweenness.desc())
            else:
                sort.append(models.networkAnalysis.betweenness.asc())
        if sorting == "degree":
            if descending:
                sort.append(models.networkAnalysis.node_degree.desc())
            else:
                sort.append(models.networkAnalysis.node_degree.asc())
        if sorting == "eigenvector":
            if descending:
                sort.append(models.networkAnalysis.eigenvector.desc())
            else:
                sort.append(models.networkAnalysis.eigenvector.asc())

    result = models.networkAnalysis.query \
        .join(models.Gene, models.Gene.gene_ID == models.networkAnalysis.gene_ID) \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()
    
    if len(result) > 0:
        schema = models.networkAnalysisSchema(many=True)
        return schema.dump(result)
    else:
        return jsonify({
            "detail": "No data found that satisfies the given filters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200



def testGeneInteraction(dataset_ID: int = None, ensg_number=None, gene_symbol=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /ceRNAInteraction/checkGeneInteraction
    :param dataset_ID: dataset_ID of interest
    :param ensg_number: ensg number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :return: lists of all cancer types gene of interest has at least one interaction in the corresponding ceRNA II network
    """

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # test if not both identification possibilites are given
    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification paramter is given. Please choose one.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number == ensg_number) \
            .all()
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol == gene_symbol) \
            .all()

    if len(gene) > 0:
        gene_ID = [i.gene_ID for i in gene]
    else:
        return jsonify({
            "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # test for each dataset if the gene(s) of interest are included in the ceRNA network
    run = db.session.execute(text(f"SELECT * from dataset join sponge_run on dataset.dataset_ID = sponge_run.dataset_ID where dataset.sponge_db_version = {sponge_db_version}"))

    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)

    result = []
    for r in run:
        tmp = db.session.execute(text("SELECT EXISTS(SELECT * FROM interactions_genegene where sponge_run_ID = " + str(r.sponge_run_ID) +
                              " and gene_ID1 = " + str(gene_ID[0]) + " limit 1) as include;")).fetchone()

        if (tmp[0] == 1):
            check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "disease_subtype": r.disease_subtype, "sponge_run_ID": r.sponge_run_ID,
                     "include": tmp[0]}
        else:
            tmp2 = db.session.execute(text("SELECT EXISTS(SELECT * FROM interactions_genegene where sponge_run_ID = " + str(r.sponge_run_ID) +
                                   " and gene_ID2 = " + str(gene_ID[0]) + " limit 1) as include;")).fetchone()
            if (tmp2[0] == 1):
                check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "disease_subtype": r.disease_subtype, "sponge_run_ID": r.sponge_run_ID,
                         "include": 1}
            else:
                check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "disease_subtype": r.disease_subtype, "sponge_run_ID": r.sponge_run_ID,
                         "include": 0}

        result.append(check)

    schema = models.checkGeneInteractionProCancer(many=True)
    return schema.dump(result)


def read_all_to_one_mirna(dataset_ID: int = None, disease_name=None, mimat_number=None, hs_number=None, pValue=0.05,
                   pValueDirection="<", mscor=None, mscorDirection="<", correlation=None, correlationDirection="<",
                   limit=100, offset=0, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /miRNAInteraction/findSpecific
    and returns all interactions the given miRNA is involved in
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param mimat_number: mimat_id( of miRNA of interest
    :param: hs_nr: hs_number of miRNA of interest
    :param pValue: pValue cutoff
    :param pValueDirection: < or >
    :param mscor mscor cutofff
    :param mscorDirection: < or >
    :param correlation: correlation cutoff
    :param correlationDirection: < or >
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :param sponge_db_version: version of the sponge database
    :return: all interactions the given miRNA is involved in
    """

    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if mimat_number is None and hs_number is None:
        return jsonify({
            "detail": "Mimat_ID or hs_number of mirna of interest are needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if mimat_number is not None and hs_number is not None:
        return jsonify({
            "detail": "More than one miRNA identifier is given. Please choose one.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # get mir_ID from given mimat_number or hs number
    mirna = []
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.like("%" + mimat_number + "%")) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.like("%" + hs_number + "%")) \
            .all()

    # save queries
    queriesGeneInteraction = []
    queriesmirnaInteraction = []
    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
        queriesmirnaInteraction.append(models.miRNAInteraction.miRNA_ID.in_(mirna_IDs))
    else:
        return jsonify({
            "detail": "No miRNA was found using given identifier",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter for database version 
    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version) 

    # if specific disease_name is given:
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
        
    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)
    
    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queriesmirnaInteraction.append(models.miRNAInteraction.sponge_run_ID.in_(run_IDs))
        queriesGeneInteraction.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # get all possible gene interaction partner for specific miRNA
    gene_interaction = models.miRNAInteraction.query \
        .filter(*queriesmirnaInteraction) \
        .all()

    geneInteractionIDs = []
    if len(gene_interaction) > 0:
        geneInteractionIDs = [i.gene_ID for i in gene_interaction]
    else:
        return jsonify({
            "detail": "No gene is associated with the given miRNA.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # save all needed queries to get correct results
    queriesGeneInteraction.append(sa.and_(models.GeneInteraction.gene_ID1.in_(geneInteractionIDs),
                                          models.GeneInteraction.gene_ID2.in_(geneInteractionIDs)))

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queriesGeneInteraction.append(models.GeneInteraction.p_value <= pValue)
        else:
            queriesGeneInteraction.append(models.GeneInteraction.p_value >= pValue)
    if mscor is not None:
        if mscorDirection == "<":
            queriesGeneInteraction.append(models.GeneInteraction.mscor <= mscor)
        else:
            queriesGeneInteraction.append(models.GeneInteraction.mscor >= mscor)
    if correlation is not None:
        if correlationDirection == "<":
            queriesGeneInteraction.append(models.GeneInteraction.correlation <= correlation)
        else:
            queriesGeneInteraction.append(models.GeneInteraction.correlation >= correlation)

    interaction_result = models.GeneInteraction.query \
        .filter(*queriesGeneInteraction) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        schema = models.GeneInteractionDatasetLongSchema(many=True)
        return schema.dump(interaction_result)
    else:
        return jsonify({
            "detail": "No data found using the given input parameters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

def read_all_mirna(dataset_ID: int = None, disease_name=None, mimat_number=None, hs_number=None, occurences=None, sorting=None, descending=None,
                   limit=100, offset=0, sponge_db_version: int = LATEST):
    """
    Handles API request for /miRNAInteraction/getOccurence
    and returns all miRNA that are involved in the disease of interest
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param occurences: how often a miRNA should contribute to a ceRNA interaction to be returned
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :param sponge_db_version: version of the sponge database
    :return: all mirna involved in disease of interest (searchs not for a specific miRNA, but search for all miRNA satisfying filter functions)
    """

    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if mimat_number is not None and hs_number is not None:
        return jsonify({
            "detail": "More than one miRNA identifier is given. Please choose one.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


    # get mir_ID from given mimat_number
    mirna = []
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()

    # save queries
    queries = []
    if mimat_number is not None or hs_number is not None:
        if len(mirna) > 0:
            mirna_IDs = [i.miRNA_ID for i in mirna]
            queries.append(models.OccurencesMiRNA.miRNA_ID.in_(mirna_IDs))
        else:
            return jsonify({
                "detail": "No miRNA was found using given identifier",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # filter for database version
    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    # if specific disease_name is given:
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
        
    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)
        
    run = run.all()
        
    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.OccurencesMiRNA.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if occurences is not None:
        queries.append(models.OccurencesMiRNA.occurences > occurences)

    # add sorting
    sort = []
    if sorting == "occurences":
        if descending:
            sort.append(desc(models.OccurencesMiRNA.occurences))
        else:
            sort.append(models.OccurencesMiRNA.occurences)

    interaction_result = models.OccurencesMiRNA.query \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.occurencesMiRNASchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No information with given parameters found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def read_mirna_for_specific_interaction(dataset_ID: int = None, disease_name=None, ensg_number=None, gene_symbol=None, between=False, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNA
    and returns all miRNAs thar contribute to all interactions between the given identifications (ensg_number or gene_symbol)
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param gene_type: defines the type of gene of interest
    :param between: If false, all interactions where one of the interaction partners fits the given genes of interest
                    will be considered.
                    If true, just interactions between the genes of interest will be considered.
    :param sponge_db_version: version of the sponge database
    :return: all miRNAs contributing to the interactions between genes of interest
    """

    # get diseases 
    disease_query = db.select(models.Dataset.dataset_ID).where(models.Dataset.sponge_db_version == sponge_db_version)
    if disease_name is not None:
        disease_query = disease_query.where(models.Dataset.disease_name.like("%" + disease_name + "%"))
    if dataset_ID is not None:
        disease_query = disease_query.where(models.Dataset.dataset_ID == dataset_ID)

    # filter runs for diseases
    run_query = db.select(models.SpongeRun.sponge_run_ID).where(models.SpongeRun.dataset_ID.in_(disease_query))

    # get gene IDs 
    gene_query = db.select(models.Gene.gene_ID)
    if ensg_number is not None:
        gene_query = gene_query.where(models.Gene.ensg_number.in_(ensg_number))
    if gene_symbol is not None:
        gene_query = gene_query.where(models.Gene.gene_symbol.in_(gene_symbol))

    # Get all interactions for the given genes and runs
    base_interaction_query = db.select(models.miRNAInteraction).where(
        models.miRNAInteraction.gene_ID.in_(gene_query),
        models.miRNAInteraction.sponge_run_ID.in_(run_query),
    )

    if between:
        # Subquery to count distinct genes
        distinct_gene_count_subquery = (
            db.select(db.func.count(db.func.distinct(gene_query.c.gene_ID))).scalar_subquery()
        )
        print(distinct_gene_count_subquery)

        # Subquery to get miRNA IDs that meet the 'between' condition
        mirna_query = db.select(models.miRNAInteraction.miRNA_ID) \
            .where(models.miRNAInteraction.gene_ID.in_(gene_query)) \
            .where(models.miRNAInteraction.sponge_run_ID.in_(run_query)) \
            .group_by(models.miRNAInteraction.miRNA_ID) \
            .having(db.func.count(models.miRNAInteraction.gene_ID) == distinct_gene_count_subquery)

        # Filter interactions by the miRNA IDs from the previous subquery
        interaction_query = base_interaction_query.where(
            models.miRNAInteraction.miRNA_ID.in_(mirna_query)
        )
    else:
        interaction_query = base_interaction_query

    interaction_result = db.session.execute(interaction_query).scalars().all()


    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.miRNAInteractionSchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No data found using the given input parameters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def getGeneCounts(dataset_ID: int = None, disease_name=None, ensg_number=None, gene_symbol=None, minCountAll=None, minCountSign=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /getGeneCount
    and returns gene(s) of interest with respective counts in disease of interest.
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param ensg_number: ensg number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param minCountAll: defines the minimal number of times a gene has to be involved in the complete network
    :param minCountSign: defines the minimal number of times a gene has to be involved in significant (p.adj < 0.05) interactionss
    :param sponge_db_version: version of the sponge database
    :return: all genes with counts.
    """

    # test if any of the two identification possibilities is given or disease_name is specified
    if ensg_number is None and gene_symbol is None and disease_name is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided or the disease_name must be specified.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # test if not both identification possibilites are given
    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one gene identifier is given. Please choose one.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries = []

    # get all sponge_runs for the given sponge_db_version
    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.SpongeRun.query.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
        
    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)
    
    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.GeneCount.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = []
    # if ensg_numer is given to specify gene(s), get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()

        if len(gene) > 0:
            gene_ID = [i.gene_ID for i in gene]
            queries.append(models.GeneCount.gene_ID.in_(gene_ID))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # if gene_symbol is given to specify gene(s), get the intern gene_ID(primary_key) for requested gene_symbol(gene_ID)
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

        if len(gene) > 0:
            gene_ID = [i.gene_ID for i in gene]
            queries.append(models.GeneCount.gene_ID.in_(gene_ID))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # add count filter if provided
    if minCountAll is not None:
        queries.append(models.GeneCount.count_all >= minCountAll)
    if minCountSign is not None:
        queries.append(models.GeneCount.count_sign >= minCountSign)

    # get results
    result = models.GeneCount.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneCountSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No data found using the given input parameters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_gene_network(dataset_ID: int = None, disease_name=None,
                      minBetweenness:float = None, minNodeDegree:float = None, minEigenvector:float = None,
                      maxPValue=0.05, minMscor=None, minCorrelation=None,
                      edgeSorting: str = None, nodeSorting: list[str] = None,
                      maxNodes: int = 100, maxEdges: int = 100, 
                      offsetNodes: int = None, offsetEdges: int = None, 
                      sponge_db_version: int = LATEST):
    """
    Optimized function for fetching ceRNA network nodes and edges with applied filters and sorting. Handles route /ceRNAInteraction/getGeneNetwork
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param minBetweenness: betweenness cutoff (>)
    :param minNodeDegree: degree cutoff (>)
    :param minEigenvector: eigenvector cutoff (>)
    :param maxPValue: p-value cutoff (<)
    :param minMscor: mscor cutoff (>)
    :param minCorrelation: correlation cutoff (>)
    :param edgeSorting: sorting key for edges
    :param nodeSorting: sorting key(s) for nodes (options are 'betweenness', 'degree', 'eigenvector')
    :param maxNodes: maximum number of nodes
    :param maxEdges: maximum number of edges
    :param offsetNodes: offset for node pagination
    :param offsetEdges: offset for edge pagination
    :param sponge_db_version: version of the sponge database
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters

    """
    # Step 1: Filter for SpongeRun IDs
    run_query = db.select(models.SpongeRun.sponge_run_ID).filter(
        models.SpongeRun.sponge_db_version == sponge_db_version
    )
    if disease_name:
        run_query = run_query.join(models.Dataset).filter(
            models.Dataset.disease_name.like(f"%{disease_name}%")
        )
    if dataset_ID:
        run_query = run_query.filter(
            models.SpongeRun.dataset_ID == dataset_ID
        )

    # Step 2: Prefilter edges by SpongeRun ID and p-value
    edge_query = db.select(models.GeneInteraction).filter(
        models.GeneInteraction.sponge_run_ID.in_(run_query)
    )
    if maxPValue:
        edge_query = edge_query.filter(
            models.GeneInteraction.p_value <= maxPValue
        )

    # Get prefiltered edges
    edges = db.session.execute(edge_query).scalars().all()
    gene_ids_in_edges = set([edge.gene_ID1 for edge in edges] + [edge.gene_ID2 for edge in edges])

    # Filter nodes by edges that pass the p-value filter & sponge run
    node_query = db.select(models.networkAnalysis).filter(
        models.networkAnalysis.sponge_run_ID.in_(run_query),
        models.networkAnalysis.gene_ID.in_(gene_ids_in_edges)    )

    # Apply node-specific filters
    if minBetweenness:
        node_query = node_query.filter(models.networkAnalysis.betweenness >= minBetweenness)
    if minNodeDegree:
        node_query = node_query.filter(models.networkAnalysis.node_degree >= minNodeDegree)
    if minEigenvector:
        node_query = node_query.filter(models.networkAnalysis.eigenvector >= minEigenvector)

    # Sorting nodes: if more than one sorting key, rank by each key individually and sort by the mean of the ranks
    if nodeSorting:
        if any([key not in ['betweenness', 'node_degree', 'eigenvector'] for key in nodeSorting]):
            raise ValueError("Invalid node sorting key. Choose from 'betweenness', 'node_degree', 'eigenvector'")
        rank_columns = [db.func.rank().over(order_by=getattr(models.networkAnalysis, col).desc()).label(f"{col}_rank") for col in nodeSorting]
        mean_rank = sum(rank_columns) / len(rank_columns)
        node_query = node_query.order_by(mean_rank)

    # node pagination
    node_query = node_query.offset(offsetNodes).limit(maxNodes)

    # filter edges based on filtered nodes
    nodes = db.session.execute(node_query).scalars().all()
    node_gene_ids = set([node.gene_ID for node in nodes])
    edge_query = edge_query.filter(
        and_(
            models.GeneInteraction.gene_ID1.in_(node_gene_ids),
            models.GeneInteraction.gene_ID2.in_(node_gene_ids)
        )
    )

    # Apply edge-specific filters
    if minMscor:
        edge_query = edge_query.filter(models.GeneInteraction.mscor >= minMscor)
    if minCorrelation:
        edge_query = edge_query.filter(models.GeneInteraction.correlation >= minCorrelation)

    # Sorting edges
    if edgeSorting == "pValue":
        edge_query = edge_query.order_by(models.GeneInteraction.p_value.asc())
    elif edgeSorting == "mscor":
        edge_query = edge_query.order_by(models.GeneInteraction.mscor.desc())
    elif edgeSorting == "correlation":
        edge_query = edge_query.order_by(models.GeneInteraction.correlation.desc())
    else: 
        raise ValueError("Invalid edge sorting key. Choose one of 'pValue', 'mscor', 'correlation'")
    
    # edge pagination 
    edge_query = edge_query.offset(offsetEdges).limit(maxEdges)

    # Execute queries
    node_results = db.session.execute(node_query).scalars().all()
    edge_results = db.session.execute(edge_query).scalars().all()

    # Return results
    return jsonify({
        "edges": models.GeneInteractionDatasetLongSchema(many=True).dump(edge_results),
        "nodes": models.networkAnalysisSchema(many=True).dump(node_results),
    })