from flask import abort
import models


def getAutocomplete(searchString):
    """
    Funtion to retrieve the autocomplete possibilities for the webside
    :param searchString: String (ensg_number, gene_symbol, hs_number or mimat_number)
    :return: list of all genes/mirnas having search string as a prefic
    """

    if searchString.startswith("ENSG") or searchString.startswith("ensg"):
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.ensg_number.ilike(searchString + "%")) \
            .all()
        print(data)
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data).data
        else:
            abort(404, "No ensg number found for the given String")
    elif searchString.startswith("HSA") or searchString.startswith("hsa"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.hs_nr.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data).data
        else:
            abort(404, "No hsa number found for the given String")
    elif searchString.startswith("MIMAT") or searchString.startswith("mimat"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.mir_ID.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data).data
        else:
            abort(404, "No mimat number found for the given String")
    else:
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.gene_symbol.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data).data
        else:
            abort(404, "No gene symbol found for the given String")

import sqlalchemy as sa
import os

def getGeneInformation(ensg_number=None, gene_symbol=None):
    """
    :param ensg_number:
    :param gene_symbol:
    :return: Available information for given gene identifier
    """

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    # test if not both identification possibilites are given
    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    if ensg_number is not None:
        data = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data).data
        else:
            abort(404, "No gene(s) found with: " + ''.join(ensg_number))

    elif gene_symbol is not None:
        data = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data).data
        else:
            abort(404, "No gene found with: " + ''.join(gene_symbol))


def getOverallCount():
    """
    Function return current statistic about database - amount of shared miRNA, significant and insignificant
     interactions per dataset
    :return: Current statistic about database
    """

    # an Engine, which the Session will use for connection resources
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)

    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)

    # create a Session
    session = Session()
    # test for each dataset if the gene(s) of interest are included in the ceRNA network

    count = session.execute(
            "select * "
            " from (select sum(count_all)/2 as count_interactions, sum(count_sign)/2 as count_interactions_sign, run_ID "
                "from gene_counts group by run_ID) as t1 "
            "left join "
            "(select sum(occurences) as count_shared_miRNAs, run_ID from occurences_miRNA group by run_ID) as t2 "
            "using(run_ID) "
            "join "
            "(SELECT dataset.disease_name, run.run_ID from dataset join run where dataset.dataset_ID = run.dataset_ID) as t3 "
            "using(run_ID);").fetchall()

    session.close()
    some_engine.dispose()

    schema = models.OverallCountSchema(many=True)
    return schema.dump(count).data

def getGeneOntology(gene_symbol):
    """
    :param gene_symbol: Gene symbol of the genes of interest
    :return: Returns all associated ontologies using QuickGO - a fast web-based browser of the Gene Ontology and Gene Ontology annotation data - for the gene(s) of interest.
    """

    # test if any of the two identification possibilites is given
    if gene_symbol is None:
        abort(404, "At least one gene symbol is needed!")

    gene = models.Gene.query \
        .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
        .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        abort(404, "Not gene(s) found for given gene_symbol(s)!")

    interaction_result = models.GeneOntology.query \
        .filter(models.GeneOntology.gene_ID.in_(gene_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneOntologySchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No GO terms with given parameters found!")

from flask import Response

def getHallmark(gene_symbol):
    """
    :param gene_symbol: Gene symbol of the genes of interest
    :return: Returns all associated cancer hallmarks for the gene(s) of interest.
    """

    # test if any of the two identification possibilites is given
    if gene_symbol is None:
        abort(404, "At least one gene symbol is needed!")

    gene = models.Gene.query \
        .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
        .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        abort(404, "No gene(s) found for given gene_symbol(s)!")

    interaction_result = models.hallmarks.query \
        .filter(models.hallmarks.gene_ID.in_(gene_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.HallmarksSchema(many=True).dump(interaction_result).data
    else:

        return Response("{"
                        "'detail': 'No hallmark associated for gene(s) of interest!',"
                        "'status': 202,"
                        "'title': 'Accepted',"
                        "'type': 'about:blank'}",
                        status=202)
