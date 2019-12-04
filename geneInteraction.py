import sqlalchemy as sa
from flask import abort
from sqlalchemy import desc
import models


def read_all_genes(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None, pValue=None,
                   pValueDirection="<", mscor=None, mscorDirection="<", correlation=None, correlationDirection="<",
                   sorting=None, descending=True, limit=15000, offset=0, information=True):
    """
    This function responds to a request for /sponge/ceRNAInteraction/findAll
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
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
    :return: all interactions given gene is involved
    """
    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")
    # test if just one of the possible identifiers is given
    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol or gene type)")

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
    queries = []
    if ensg_number is not None or gene_symbol is not None or gene_type is not None:
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(
                sa.or_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs)))
        else:
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queries.append(models.GeneInteraction.p_value < pValue)
        else:
            queries.append(models.GeneInteraction.p_value > pValue)
    if mscor is not None:
        if mscorDirection == "<":
            queries.append(models.GeneInteraction.mscor < mscor)
        else:
            queries.append(models.GeneInteraction.mscor > mscor)
    if correlation is not None:
        if correlationDirection == "<":
            queries.append(models.GeneInteraction.correlation < correlation)
        else:
            queries.append(models.GeneInteraction.correlation > correlation)

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

    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.GeneInteractionDatasetLongSchema(many=True)
        else:
            # Serialize the data for the response depending on parameter all
            schema = models.GeneInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")


def read_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, limit=15000, offset=0):
    """
      This function responds to a request for /sponge/ceRNAInteraction/findSpecific
      and returns all interactions between the given identifications (ensg_number or gene_symbol)
      :param disease_name: disease_name of interest
      :param ensg_number: esng number of the genes of interest
      :param gene_symbol: gene symbol of the genes of interest
      :param limit: number of results that shouls be shown
      :param offset: startpoint from where results should be shown
      :return: all interactions between given genes
      """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

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
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # save all needed queries to get correct results
    queries = [sa.and_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs))]

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneInteractionDatasetShortSchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")


def read_all_gene_network_analysis(disease_name=None, gene_type=None, betweenness=None, degree=None, eigenvector=None,
                                   sorting=None, descending=True, limit=15000, offset=0):
    """
    This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findAll/networkAnalysis
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
    :param disease_name: isease_name of interest
    :param betweenness: betweenness cutoff (>)
    :param degree: degree cutoff (>)
    :param eigenvector: eigenvector cutoff (>)
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # save all needed queries to get correct results
    queries = []

    # if specific disease_name is given (should be because for this endpoint is it required):
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.networkAnalysis.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    # filter further depending on given statistics cutoffs
    if betweenness is not None:
        queries.append(models.networkAnalysis.betweeness > betweenness)
    if degree is not None:
        queries.append(models.networkAnalysis.node_degree > degree)
    if eigenvector is not None:
        queries.append(models.networkAnalysis.eigenvector > eigenvector)
    if gene_type is not None:
        queries.append(models.Gene.gene_type == gene_type)

    # add all sorting if given:
    sort = [models.networkAnalysis.run_ID]
    if sorting is not None:
        if sorting == "betweenness":
            if descending:
                sort.append(models.networkAnalysis.betweeness.desc())
            else:
                sort.append(models.networkAnalysis.betweeness.asc())
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
        return schema.dump(result).data
    else:
        abort(404, "Not data found that satisfies the given filters")


def read_all_to_one_mirna(disease_name=None, mimat_number=None, hs_number=None, limit=15000, offset=0,
                          information=True):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions the given miRNA is involved in
    """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    if mimat_number is None and hs_number is None:
        abort(404, "Mimat_ID or hs_number of mirna(s) of interest are needed!!")
    if mimat_number is not None and hs_number is not None:
        abort(404, "More than one miRNA identifier is given. Please choose one.")

    # get mir_ID from given mimat_number or hs number
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
    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
        queries.append(models.miRNAInteraction.miRNA_ID.in_(mirna_IDs))
    else:
        abort(404, "With given mimat_ID or hs_number no miRNA could be found")

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    interaction_result = models.miRNAInteraction.query \
        .join(models.GeneInteraction,
              models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.miRNAInteractionLongSchema(many=True)
        else:
            # Serialize the data for the response depending on parameter all
            schema = models.miRNAInteractionShortSchema(many=True)
        return schema.dump(interaction_result).data
    else:
        abort(404, "No data found with input parameter")


def read_all_mirna(disease_name=None, mimat_number=None, hs_number=None, occurences=None, sorting=None, descending=None,
                   limit=15000, offset=0):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param occurences: how often a miRNA should contribute to a ceRNA interaction to be returned
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :return: all mirna involved in disease of interest (searchs not for a specific miRNA, but search for all miRNA satisfying filter functions)
    """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    if mimat_number is not None and hs_number is not None:
        abort(404, "More than one miRNA identifier is given. Please choose one.")

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
    else:
        abort(404, "No miRNA identifier is given. Please provide one.")

    # save queries
    queries = []
    if mimat_number is not None or hs_number is not None:
        if len(mirna) > 0:
            mirna_IDs = [i.miRNA_ID for i in mirna]
            queries.append(models.OccurencesMiRNA.miRNA_ID.in_(mirna_IDs))
        else:
            abort(404, "With given mimat_ID or hs_number no mirna could be found")

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()
        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.OccurencesMiRNA.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

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
        return models.occurencesMiRNASchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")

def read_mirna_for_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNA
    and returns all miRNAs thar contribute to all interactions between the given identifications (ensg_number or gene_symbol)
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param gene_type: defines the type of gene of interest

    :return: all miRNAs contributing to the interactions between genes of interest
    """
    # test if just one of the possible identifiers is given
    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol or gene type)")

    queries = []
    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

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

    interaction_IDs = []
    # get requires interaction_ID from database
    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
        queries.append(
            sa.and_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs)))
        interactions = models.GeneInteraction.query \
            .filter(*queries) \
            .all()
        if len(interactions) > 0:
            interaction_IDs = [i.interactions_genegene_ID for i in interactions]
        else:
            abort(404, "No gene interaction found for given ensg_number(s) or gene_symbol(s).")
    else:
        abort(404, "No gene found for given identifiers.")


    # get all wished mirnas
    if len(interaction_IDs) > 0:
        interaction_result = models.miRNAInteraction.query \
            .filter(models.miRNAInteraction.interactions_genegene_ID.in_(interaction_IDs)) \
            .all()

        if len(interaction_result) > 0:
            # Serialize the data for the response depending on parameter all
            return models.miRNAInteractionShortSchema(many=True).dump(interaction_result).data
        else:
            abort(404, "No data found with input parameter")
