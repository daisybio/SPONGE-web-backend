import sqlalchemy as sa
import os
from flask import abort
from sqlalchemy import desc
import models


def read_all_genes(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None, pValue=0.05,
                   pValueDirection="<", mscor=None, mscorDirection="<", correlation=None, correlationDirection="<",
                   sorting=None, descending=True, limit=100, offset=0, information=True):
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
    if limit > 1000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # test if just one of the possible identifiers is given
    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol or gene type)")

    queries_1 = []
    queries_2 = []
    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries_1.append(models.GeneInteraction.run_ID.in_(run_IDs))
            queries_2.append(models.GeneInteraction.run_ID.in_(run_IDs))
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

    # save all needed queries to get correct results
    if ensg_number is not None or gene_symbol is not None or gene_type is not None:
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries_1.append(models.GeneInteraction.gene_ID1.in_(gene_IDs))
            queries_2.append(models.GeneInteraction.gene_ID2.in_(gene_IDs))
        else:
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

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
        return schema.dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")


def read_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, pValue=0.05,
                              pValueDirection="<", limit=100, offset=0):
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
    if limit > 1000:
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
        return models.GeneInteractionDatasetShortSchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")


def read_all_gene_network_analysis(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None,
                                   minBetweenness=None, minNodeDegree=None, minEigenvector=None,
                                   sorting=None, descending=True, limit=100, offset=0):
    """
    This function responds to a request for /sponge/findceRNA
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
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
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    """

    # test limit
    if limit > 1000:
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

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

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
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

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
    sort = [models.networkAnalysis.run_ID]
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
        return schema.dump(result).data
    else:
        abort(404, "Not data found that satisfies the given filters")


def testGeneInteraction(ensg_number=None, gene_symbol=None):
    """
    :param ensg_number: ensg number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :return: lists of all cancer types gene of interest has at least one interaction in the corresponding ceRNA II network
    """
    # an Engine, which the Session will use for connection resources
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"))

    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)

    # create a Session
    session = Session()

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    # test if not both identification possibilites are given
    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

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
        abort(404, "No gene found for given ensg_number(s) or gene_symbol(s)")

    # test for each dataset if the gene(s) of interest are included in the ceRNA network
    run = session.execute("SELECT * from dataset join run where dataset.dataset_ID = run.dataset_ID").fetchall()

    result = []
    for r in run:
        tmp = session.execute("SELECT EXISTS(SELECT * FROM interactions_genegene where run_ID = " + str(r.run_ID) +
                              " and gene_ID1 = " + str(gene_ID[0]) + " limit 1) as include;").fetchone()

        if (tmp[0] == 1):
            check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "run_ID": r.run_ID,
                     "include": tmp[0]}
        else:
            tmp2 = session.execute("SELECT EXISTS(SELECT * FROM interactions_genegene where run_ID = " + str(r.run_ID) +
                                   " and gene_ID2 = " + str(gene_ID[0]) + " limit 1) as include;").fetchone()
            if (tmp2[0] == 1):
                check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "run_ID": r.run_ID,
                         "include": 1}
            else:
                check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "run_ID": r.run_ID,
                         "include": 0}

        result.append(check)

    session.close()

    schema = models.checkGeneInteractionProCancer(many=True)
    return schema.dump(result).data


def read_all_to_one_mirna(disease_name=None, mimat_number=None, hs_number=None, pValue=0.05,
                   pValueDirection="<", mscor=None, mscorDirection="<", correlation=None, correlationDirection="<",
                   limit=100, offset=0):
    """
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
    :return: all interactions the given miRNA is involved in
    """

    # test limit
    if limit > 1000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    if mimat_number is None and hs_number is None:
        abort(404, "Mimat_ID or hs_number of mirna of interest are needed!")
    if mimat_number is not None and hs_number is not None:
        abort(404, "More than one miRNA identifier is given. Please choose one.")

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
        abort(404, "With given mimat_ID or hs_number no miRNA could be found")

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queriesmirnaInteraction.append(models.miRNAInteraction.run_ID.in_(run_IDs))
            queriesGeneInteraction.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    # get all possible gene interaction partner for specific miRNA
    gene_interaction = models.miRNAInteraction.query \
        .filter(*queriesmirnaInteraction) \
        .all()

    geneInteractionIDs = []
    if len(gene_interaction) > 0:
        geneInteractionIDs = [i.gene_ID for i in gene_interaction]
    else:
        abort(404, "No gene is associated with the given miRNA.")

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
        return schema.dump(interaction_result).data
    else:
        abort(404, "No data found with input parameter")


def read_all_mirna(disease_name=None, mimat_number=None, hs_number=None, occurences=None, sorting=None, descending=None,
                   limit=100, offset=0):
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
    if limit > 1000:
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


def read_mirna_for_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, between=False):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNA
    and returns all miRNAs thar contribute to all interactions between the given identifications (ensg_number or gene_symbol)
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param gene_type: defines the type of gene of interest
    :param between: If false, all interactions where one of the interaction partners fits the given genes of interest
                    will be considered.
                    If true, just interactions between the genes of interest will be considered.

    :return: all miRNAs contributing to the interactions between genes of interest
    """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    queries = []
    run_IDs = []
    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.miRNAInteraction.run_ID.in_(run_IDs))
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

    gene_IDs = []
    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
        queries.append(models.miRNAInteraction.gene_ID.in_(gene_IDs))
    else:
        abort(404, "No gene found for given identifiers.")

    interaction_result = []
    if between:
        # an Engine, which the Session will use for connection resources
        some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)

        # create a configured "Session" class
        Session = sa.orm.sessionmaker(bind=some_engine)

        # create a Session
        session = Session()
        # test for each dataset if the gene(s) of interest are included in the ceRNA network

        mirna_filter = session.execute("select mirna_ID from interacting_miRNAs where run_ID IN ( "
                                       + ','.join(str(e) for e in run_IDs) + ") and gene_ID IN ( "
                                       + ','.join(str(e) for e in gene_IDs)
                                       + ") group by mirna_ID HAVING count(mirna_ID) >= 2;").fetchall()

        session.close()
        some_engine.dispose()

        if len(mirna_filter) == 0:
            abort(404, "No shared miRNA between genes found.")

        flat_mirna_filter = [item for sublist in mirna_filter for item in sublist]
        queries.append(models.miRNAInteraction.miRNA_ID.in_(flat_mirna_filter))

        interaction_result = models.miRNAInteraction.query \
            .filter(*queries) \
            .all()
    else:
        interaction_result = models.miRNAInteraction.query \
            .filter(*queries) \
            .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.miRNAInteractionSchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No data found with input parameter")


def getGeneCounts(disease_name=None, ensg_number=None, gene_symbol=None, minCountAll=None, minCountSign=None):
    """
    This function responds to a request for /geneCounts
    and returns gene(s) of interest with respective counts in disease of interest.
    :param disease_name: disease_name of interest
    :param ensg_number: ensg number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param minCountAll: defines the minimal number of times a gene has to be involved in the complete network
    :param minCountSign: defines the minimal number of times a gene has to be involved in significant (p.adj < 0.05) interactionss

    :return: all genes with counts.
    """

    # test if any of the two identification possibilities is given or disease_name is specified
    if ensg_number is None and gene_symbol is None and disease_name is None:
        abort(404,
              "One of the two possible identification numbers must be provided or the disease_name must be specified.")

    # test if not both identification possibilites are given
    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one gene identifier is given. Please choose one out of (ensg number, gene symbol)")

    queries = []
    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.GeneCount.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

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
            abort(404, "No gene found for given ensg_number(s) or gene_symbol(s)")
    # if gene_symbol is given to specify gene(s), get the intern gene_ID(primary_key) for requested gene_symbol(gene_ID)
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

        if len(gene) > 0:
            gene_ID = [i.gene_ID for i in gene]
            queries.append(models.GeneCount.gene_ID.in_(gene_ID))
        else:
            abort(404, "No gene found for given ensg_number(s) or gene_symbol(s)")

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
        return models.GeneCountSchema(many=True).dump(result).data
    else:
        abort(404, "No data found with input parameter")

def get_distinc_ceRNA_sets(disease_name):
    """
    Function returns list of distinct gene_IDs (ensg_nr) contributing to a significant interaction (adjusted pVal <= 0.05) in one specific cancer
    :param disease_name: mandatory, cancer type of interest
    :return: List of distinct gene_IDs (ensg_nr)
    """

    # if specific disease_name is given:
    run_IDs = []
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
        else:
            abort(404, "No dataset with given disease_name found")


    ensg_nr = []
    if len(run_IDs) > 0:
        # an Engine, which the Session will use for connection resources
        some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)

        # create a configured "Session" class
        Session = sa.orm.sessionmaker(bind=some_engine)

        # create a Session
        session = Session()
        # test for each dataset if the gene(s) of interest are included in the ceRNA network



        id1 = session.execute("SELECT DISTINCT gene_ID1 FROM interactions_genegene where run_ID IN (" +
                                  ','.join(str(e) for e in run_IDs) + ") AND p_value <= 0.05")

        print("first ids ready")
        #id2 = session.execute("SELECT DISTINCT gene_ID2 FROM interactions_genegene where run_ID IN (" +
        #                          ','.join(str(e) for e in run_IDs) + ") AND p_value <= 0.05").fetchall()


        #for gene in results:
        #    tmp = session.execute("SELECT ensg_number FROM gene where gene_ID = " + str(gene.gene_ID)).fetchall()
        #    #print(tmp[0].ensg_number)
        #    ensg_nr.append({"gene_ID": tmp[0].ensg_number})

        session.close()
        some_engine.dispose()

    #if len(ensg_nr) > 0:
        # Serialize the data for the response depending on parameter all
        #return models.DistinctGeneSetSchema(many=True).dump(results).data
    #else:
        #abort(404, "No data found with input parameter")
    return print("Null")

get_distinc_ceRNA_sets(disease_name="kidney clear")