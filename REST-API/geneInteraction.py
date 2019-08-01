import sqlalchemy as sa
from flask import abort
from sqlalchemy import desc
from sqlalchemy import func

import models


def read_all_to_one_gene(disease_name=None, ensg_number=None, gene_symbol=None, pValue=None, pValueDirection="<",
                         mscore=None, mscoreDirection="<", correlation=None, correlationDirection="<", sorting=None,
                         descending=True, top=None,
                         information=True):
    """
    This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findSpecific
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param pValue: pValue cutoff
    :param pValueDirection: < or >
    :param mscore mscore cutofff
    :param mscoreDirection: < or >
    :param correlation: correlation cutoff
    :param correlationDirection: < or >
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param top: show just the top x elements of the query
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions given gene is involved
    """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
        # .one_or_none()
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # save all needed queries to get correct results
    queries = [sa.or_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs))]

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
    if mscore is not None:
        if mscoreDirection == "<":
            queries.append(models.GeneInteraction.mscore < mscore)
            print(models.GeneInteraction.mscore < mscore)
        else:
            queries.append(models.GeneInteraction.mscore > mscore)
    if correlation is not None:
        if correlationDirection == "<":
            queries.append(models.GeneInteraction.correlation < correlation)
        else:
            queries.append(models.GeneInteraction.correlation > correlation)

    # add all sorting if given:
    sort = [models.GeneInteraction.run_ID]
    if sorting is not None:
        if sorting == "pValue":
            if descending:
                sort.append(models.GeneInteraction.p_value.desc())
            else:
                sort.append(models.GeneInteraction.p_value.asc())
        if sorting == "mscore":
            if descending:
                sort.append(models.GeneInteraction.mscore.desc())
            else:
                sort.append(models.GeneInteraction.mscore.asc())
        if sorting == "correlation":
            if descending:
                sort.append(models.GeneInteraction.correlation.desc())
            else:
                sort.append(models.GeneInteraction.correlation.asc())


    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .order_by(*sort) \
        .limit(top) \
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

def read_all_gene(disease_name=None, pValue=None, pValueDirection="<",
                  mscore=None, mscoreDirection="<", correlation=None, correlationDirection="<", sorting=None,
                  descending=True, top=None,
                  information=True):
    """
    This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findAll
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
    :param disease_name: disease_name of interest
    :param pValue: pValue cutoff
    :param pValueDirection: < or >
    :param mscore mscore cutofff
    :param mscoreDirection: < or >
    :param correlation: correlation cutoff
    :param correlationDirection: < or >
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param top: show just the top x elements of the query
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    """
    # save all needed queries to get correct results
    queries = []

    # if specific disease_name is given (should be because for this endpoint is it required):
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
    if mscore is not None:
        if mscoreDirection == "<":
            queries.append(models.GeneInteraction.mscore < mscore)
            print(models.GeneInteraction.mscore < mscore)
        else:
            queries.append(models.GeneInteraction.mscore > mscore)
    if correlation is not None:
        if correlationDirection == "<":
            queries.append(models.GeneInteraction.correlation < correlation)
        else:
            queries.append(models.GeneInteraction.correlation > correlation)

    # add all sorting if given:
    sort = [models.GeneInteraction.run_ID]
    if sorting is not None:
        if sorting == "pValue":
            if descending:
                sort.append(models.GeneInteraction.p_value.desc())
            else:
                sort.append(models.GeneInteraction.p_value.asc())
        if sorting == "mscore":
            if descending:
                sort.append(models.GeneInteraction.mscore.desc())
            else:
                sort.append(models.GeneInteraction.mscore.asc())
        if sorting == "correlation":
            if descending:
                sort.append(models.GeneInteraction.correlation.desc())
            else:
                sort.append(models.GeneInteraction.correlation.asc())

    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .order_by(*sort) \
        .limit(top) \
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


def read_all_gene_network_analysis(disease_name=None, betweenness=None, degree=None, eigenvector=None, sorting=None,
                                   descending=True, top=None):
    """
    This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findAll/networkAnalysis
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
    :param disease_name: isease_name of interest
    :param betweenness: betweenness cutoff (>)
    :param degree: degree cutoff (>)
    :param eigenvector: eigenvector cutoff (>)
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param top: show just the top x elements of the query
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    """

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
        .filter(*queries) \
        .order_by(*sort) \
        .limit(top) \
        .all()

    if len(result) > 0:
        schema = models.networkAnalysisSchema(many=True)
        return schema.dump(result).data
    else:
        abort(404, "Not data found that satisfies the given filters")


def read_all_to_one_mirna(disease_name=None, mimat_number=None, hs_number=None, top=None, information=True):
    """
    This function responds to a request for /sponge/ceRNANetwork/miRNAInteraction?disease_name={disease_name}&mimat_number={mimat_number}&information={true|false}
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved

    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param top: show just the top x elements of the query
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions the given miRNA is involved in
    """

    if mimat_number is None and hs_number is None:
        abort(404, "Mimat_ID or hs_number of mirna(s) of interest are needed!!")

    # get mir_ID from given mimat_number
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNAInteraction.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()

    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
    else:
        abort(404, "With given mimat_ID or hs_number no mirna could be found")

    # save all needed queries to get correct results
    queries = [models.miRNAInteraction.miRNA_ID.in_(mirna_IDs)]

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
        .limit(top) \
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


def read_all_mirna(disease_name=None, occurences=None, sorting=None, descending=None, top=None, information=True):
    """
    :param disease_name: disease_name of interest
    :param count: how often a miRNA should contribute to a ceRNA interaction to be returned
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param top: show just the top x elements of the query
    :return: all mirna involved in disease of interest (searchs not for a specific miRNA, but search for all miRNA satisfying filter functions)
    """

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()
        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries = [models.GeneInteraction.run_ID.in_(run_IDs)]
        else:
            abort(404, "No dataset with given disease_name found")

    # add sorting
    sort = []
    if sorting == "occurences":
        if descending:
            sort.append(desc("count"))
        else:
            sort.append("count")

    if occurences is not None:
        if information:
            interaction_result = models.miRNAInteraction. \
                query.with_entities(models.miRNA.mir_ID,
                                    models.miRNA.hs_nr,
                                    models.miRNA.id_type,
                                    models.miRNA.seq,
                                    func.count(
                                        models.miRNAInteraction.interacting_miRNAs_ID).label(
                                        "count"),
                                    models.Run.run_ID,
                                    models.Dataset.disease_name) \
                .join(models.GeneInteraction,
                      models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
                .join(models.miRNA, models.miRNAInteraction.miRNA_ID == models.miRNA.miRNA_ID) \
                .join(models.Run, models.Run.run_ID == models.GeneInteraction.run_ID) \
                .join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
                .filter(*queries) \
                .group_by(models.miRNAInteraction.miRNA_ID, models.Run.run_ID, models.Dataset.disease_name) \
                .having(func.count(models.miRNAInteraction.interacting_miRNAs_ID).label("count") > occurences) \
                .order_by(*sort) \
                .limit(top) \
                .all()
        else:
            interaction_result = models.miRNAInteraction. \
                query.with_entities(models.miRNA.mir_ID,
                                    models.miRNA.hs_nr,
                                    func.count(
                                        models.miRNAInteraction.interacting_miRNAs_ID).label(
                                        "count"),
                                    models.Run.run_ID,
                                    models.Dataset.disease_name) \
                .join(models.GeneInteraction,
                      models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
                .join(models.miRNA, models.miRNAInteraction.miRNA_ID == models.miRNA.miRNA_ID) \
                .join(models.Run, models.Run.run_ID == models.GeneInteraction.run_ID) \
                .join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
                .filter(*queries) \
                .group_by(models.miRNAInteraction.miRNA_ID, models.Run.run_ID, models.Dataset.disease_name) \
                .having(func.count(models.miRNAInteraction.interacting_miRNAs_ID).label("count") > occurences) \
                .order_by(*sort) \
                .limit(top) \
                .all()
    else:
        if information:
            interaction_result = models.miRNAInteraction. \
                query.with_entities(models.miRNA.mir_ID,
                                    models.miRNA.hs_nr,
                                    models.miRNA.id_type,
                                    models.miRNA.seq,
                                    func.count(
                                        models.miRNAInteraction.interacting_miRNAs_ID).label(
                                        "count"),
                                    models.Run.run_ID,
                                    models.Dataset.disease_name) \
                .join(models.GeneInteraction,
                      models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
                .join(models.miRNA, models.miRNAInteraction.miRNA_ID == models.miRNA.miRNA_ID) \
                .join(models.Run, models.Run.run_ID == models.GeneInteraction.run_ID) \
                .join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
                .filter(*queries) \
                .group_by(models.miRNAInteraction.miRNA_ID, models.Run.run_ID, models.Dataset.disease_name) \
                .order_by(*sort) \
                .limit(top) \
                .all()
        else:
            interaction_result = models.miRNAInteraction. \
                query.with_entities(models.miRNA.mir_ID,
                                    models.miRNA.hs_nr,
                                    func.count(
                                        models.miRNAInteraction.interacting_miRNAs_ID).label(
                                        "count"),
                                    models.Run.run_ID,
                                    models.Dataset.disease_name) \
                .join(models.GeneInteraction,
                      models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
                .join(models.miRNA, models.miRNAInteraction.miRNA_ID == models.miRNA.miRNA_ID) \
                .join(models.Run, models.Run.run_ID == models.GeneInteraction.run_ID) \
                .join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
                .filter(*queries) \
                .group_by(models.miRNAInteraction.miRNA_ID, models.Run.run_ID, models.Dataset.disease_name) \
                .order_by(*sort) \
                .limit(top) \
                .all()

    if information:
        schema = models.miRNAInteractionAllSeachLongSchema(many=True)
    else:
        schema = models.miRNAInteractionAllSeachShortSchema(many=True)
    return schema.dump(interaction_result).data


def read_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None):
    """
      This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findSpecificInteraction
      and returns all interactions between the given identifications (ensg_number or gene_symbol)
      :param disease_name: disease_name of interest
      :param ensg_number: esng number of the genes of interest
      :param gene_symbol: gene symbol of the genes of interest
      :return: all interactions between given genes
      """

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

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
        .order_by(models.GeneInteraction.run_ID) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneInteractionDatasetShortSchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")


def read_mirna_for_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None):
    """
    This function responds to a request for /sponge/ceRNANetwork/miRNAInteraction/findSpecificForceRNAInteraction
    and returns all miRNAs thar contribute to all interactions between the given identifications (ensg_number or gene_symbol)
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :return: all miRNAs contributing to the interactions between genes of interest
    """

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

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

    # get all wished mirnas
    interaction_result = models.miRNAInteraction.query \
        .join(models.GeneInteraction,
              models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
        .filter(*queries) \
        .order_by(models.GeneInteraction.run_ID, models.miRNAInteraction.miRNA_ID) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.miRNAInteractionShortSchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No data found with input parameter")
