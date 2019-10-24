from flask import abort

import models


def get_gene_expr(disease_name=None, ensg_number=None, gene_symbol=None):
    """
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :return: all expression values for the genes of interest
    """

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
    queries = [models.GeneExpressionValues.gene_ID.in_(gene_IDs)]

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

    if len(run) > 0:
        run_IDs = [i.run_ID for i in run]
        queries.append(models.GeneExpressionValues.run_ID.in_(run_IDs))
    else:
        abort(404, "No dataset with given disease_name found")

    result = models.GeneExpressionValues.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.geneExpressionSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")


def get_mirna_expr(disease_name=None, mimat_number=None, hs_number=None):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :return: all expression values for the mimats of interest
    """

    # test if any of the two identification possibilites is given
    if mimat_number is None and hs_number is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if mimat_number is not None and hs_number is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

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
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # save all needed queries to get correct results
    queries = [models.MiRNAExpressionValues.miRNA_ID.in_(mirna_IDs)]

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

    if len(run) > 0:
        run_IDs = [i.run_ID for i in run]
        queries.append(models.MiRNAExpressionValues.run_ID.in_(run_IDs))
    else:
        abort(404, "No dataset with given disease_name found")

    result = models.MiRNAExpressionValues.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.miRNAExpressionSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")
