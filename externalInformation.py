from flask import abort
import models
from flask import Response
from sqlalchemy.sql import text
import sqlalchemy as sa
import os


def getAutocomplete(searchString):
    """
    Funtion to retrieve the autocomplete possibilities for the webside
    :param searchString: String (ensg_number, gene_symbol, hs_number or mimat_number)
    :return: list of all genes/mirnas having search string as a prefic
    """
    # Note: this function does not check for the database version because this would take too long

    if searchString.startswith("ENSG") or searchString.startswith("ensg"):
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.ensg_number.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data)
        else:
            abort(404, "No ensg number found for the given String")
    elif searchString.startswith("HSA") or searchString.startswith("hsa"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.hs_nr.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data)
        else:
            abort(404, "No hsa number found for the given String")
    elif searchString.startswith("MIMAT") or searchString.startswith("mimat"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.mir_ID.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data)
        else:
            abort(404, "No mimat number found for the given String")
    else:
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.gene_symbol.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data)
        else:
            abort(404, "No gene symbol found for the given String")


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
            return models.GeneSchema(many=True).dump(data)
        else:
            abort(404, "No gene(s) found with: " + ''.join(ensg_number))

    elif gene_symbol is not None:
        data = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data)
        else:
            abort(404, "No gene found with: " + ''.join(gene_symbol))


def getTranscriptInformation(enst_number):
    """
    :param enst_number:
    :return: Available information for given transcript identifier
    """

    # test if the identification is given
    if enst_number is None:
        abort(404, "At least one transcript identification number is needed!")

    data = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(data) > 0:
        return models.TranscriptSchema(many=True).dump(data)
    else:
        abort(404, "No transcript found with: " + enst_number)


def getOverallCount(sponge_db_version: int = LATEST):
    """
    Function return current statistic about database - amount of shared miRNA, significant and insignificant
     interactions per dataset
    :param sponge_db_version: Version of the database
    :return: Current statistic about database
    """

    # count = db.session.execute(text(
    #         "select * "
    #         " from (select sum(count_all)/2 as count_interactions, sum(count_sign)/2 as count_interactions_sign, sponge_run_ID "
    #             "from gene_counts group by sponge_run_ID) as t1 "
    #         "left join "
    #         "(select sum(occurences) as count_shared_miRNAs, sponge_run_ID from occurences_mirna_gene group by sponge_run_ID) as t2 "
    #         "using(sponge_run_ID) "
    #         "join "
    #         "(SELECT dataset.disease_name, sponge_run.sponge_run_ID from dataset join sponge_run on dataset.dataset_ID = sponge_run.dataset_ID) "
    #         "WHERE dataset.version = 2 AND sponge_run.version = 2 as t3 "
    #         "using(sponge_run_ID);")).fetchall()

    # Aliases for tables
    t1 = (
        select(
            (func.sum(models.GeneCount.count_all) / 2).label("count_interactions"),
            (func.sum(models.GeneCount.count_sign) / 2).label("count_interactions_sign"),
            models.GeneCount.sponge_run_ID
        )
        .group_by(models.GeneCount.sponge_run_ID)
        .subquery("t1")
    )

    t2 = (
        select(
            (func.sum(models.OccurencesMiRNA.occurences)).label("count_shared_mirnas_gene"),
            models.OccurencesMiRNA.sponge_run_ID
        )
        .group_by(models.OccurencesMiRNA.sponge_run_ID)
        .subquery("t2")
    )

    t3 = (
        select(
            models.Dataset.disease_name,
            models.SpongeRun.sponge_run_ID
        )
        .select_from(
            join(models.Dataset, models.SpongeRun, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID)
        )
        .where(
            models.Dataset.sponge_db_version == sponge_db_version,
            models.SpongeRun.sponge_db_version == sponge_db_version
        )
        .subquery("t3")
    )

    # Main query
    query = (
        select(
            t1.c.count_interactions,
            t1.c.count_interactions_sign,
            t1.c.sponge_run_ID,
            t2.c.count_shared_mirnas_gene,
            t3.c.disease_name
        )
        .select_from(
            t1.outerjoin(t2, t1.c.sponge_run_ID == t2.c.sponge_run_ID)
            .join(t3, t1.c.sponge_run_ID == t3.c.sponge_run_ID)
        )
    )

    count = db.session.execute(query).fetchall()

    schema = models.OverallCountSchema(many=True)
    return schema.dump(count)


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
        return models.GeneOntologySchema(many=True).dump(interaction_result)
    else:
        return Response("{"
                        "\"detail\": \"No GO terms with given parameters found!\","
                        "\"status\": 202,"
                        "\"title\": \"Accepted\","
                        "\"type\": \"about:blank\"}",
                        status=202)


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
        return models.HallmarksSchema(many=True).dump(interaction_result)   
    else:
        return Response("{"
                        "\"detail\": \"No hallmark associated for gene(s) of interest!\","
                        "\"status\": 202,"
                        "\"title\": \"Accepted\","
                        "\"type\": \"about:blank\"}",
                        status=202)

def getWikipathway(gene_symbol):
    """
    :param gene_symbol: Gene symbol of the genes of interest
    :return: Returns all associated wikipathway keys for the gene(s) of interest.
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

    interaction_result = models.wikipathways.query \
        .filter(models.wikipathways.gene_ID.in_(gene_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.WikipathwaySchema(many=True).dump(interaction_result)
    else:
        return Response("{"
                        "\"detail\": \"No wikipathway key associated for gene(s) of interest!\","
                        "\"status\": 202,"
                        "\"title\": \"Accepted\","
                        "\"type\": \"about:blank\"}",
                        status=202)


def getTranscriptGene(enst_number):
    """
    :param enst_number:
    :return: Returns all associated gene id(s) for the transcript(s) of interest.
    """

    # test if the identification is given
    if enst_number is None:
        abort(404, "At least one transcript identification number is needed!")

    query = select(models.Gene.ensg_number).select_from(
        join(models.Gene, models.Transcript, models.Gene.gene_ID == models.Transcript.gene_ID)
    ).where(models.Transcript.enst_number.in_(enst_number))

    result = db.session.execute(query).fetchall()

    if len(result) > 0:
        # return models.GeneSchemaShort(many=True).dump(result)
        return [r[0] for r in result]
    else:
        return Response("{"
                        "\"detail\": \"No gene(s) associated for transcript(s) of interest!\","
                        "\"status\": 202,"
                        "\"title\": \"Accepted\","
                        "\"type\": \"about:blank\"}",
                        status=202)


def getGeneTranscripts(ensg_number):
    """
    :param ensg_number:
    :return: Returns all associated transcript id(s) for the gene(s) of interest.
    """

    # test if the identification is given
    if ensg_number is None:
        abort(404, "At least one gene identification number is needed!")

    query = select(models.Transcript.enst_number).select_from(
        join(models.Gene, models.Transcript, models.Gene.gene_ID == models.Transcript.gene_ID)
    ).where(models.Gene.ensg_number.in_(ensg_number))

    result = db.session.execute(query).fetchall()

    if len(result) > 0:
        # return models.TranscriptSchemaShort(many=True).dump(result)
        return [r[0] for r in result]
    else:
        return Response("{"
                        "\"detail\": \"No transcript(s) associated for gene(s) of interest!\","
                        "\"status\": 202,"
                        "\"title\": \"Accepted\","
                        "\"type\": \"about:blank\"}",
                        status=202)