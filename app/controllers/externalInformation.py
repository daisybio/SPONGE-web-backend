from flask import jsonify
from app.controllers import dataset
import app.models as models
from flask import Response
from sqlalchemy.sql import text
from sqlalchemy import case, func, select, join
from sqlalchemy.orm import aliased
from app.config import LATEST, db
from app.controllers.dataset import _dataset_query


def getAutocomplete(searchString):
    """
    Funtion to retrieve the autocomplete possibilities for the webside (API route /stringSearch)
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
            return jsonify({
                "detail": "No ensg number found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200

    elif searchString.startswith("HSA") or searchString.startswith("hsa"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.hs_nr.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No hsa number found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200

    elif searchString.startswith("MIMAT") or searchString.startswith("mimat"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.mir_ID.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No mimat number found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200

    else:
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.gene_symbol.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No gene symbol found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200
        
def getAutocompleteTranscripts(searchString):
        
    """
    Funtion to retrieve the autocomplete possibilities for the webside (API route /stringSearchTranscript)
    :param searchString: String (ensg_number, gene_symbol, hs_number or mimat_number)
    :return: list of all genes/mirnas having search string as a prefic
    """
    # Note: this function does not check for the database version because this would take too long

    if searchString.startswith("ENST") or searchString.startswith("enst"):
        query = db.select(models.Transcript) \
                .where(models.Transcript.enst_number.ilike(searchString + "%"))
        data = db.session.execute(query).scalars().all()

    elif searchString.startswith("ENSG") or searchString.startswith("ensg"):
        query = db.select(models.Transcript) \
                .join(models.Gene, models.Transcript.gene_ID == models.Gene.gene_ID) \
                .where(models.Gene.ensg_number.ilike(searchString + "%"))
        data = db.session.execute(query).scalars().all()

    else: 
        query = db.select(models.Transcript) \
                .join(models.Gene, models.Transcript.gene_ID == models.Gene.gene_ID) \
                .where(models.Gene.gene_symbol.ilike(searchString + "%"))
        data = db.session.execute(query).scalars().all()    

    if len(data) > 0:
        return models.TranscriptSchemaShort(many=True).dump(data)
    else:
        return jsonify({
            "detail": "No gene symbol found for the given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def getGeneInformation(ensg_number=None, gene_symbol=None):
    """
    :param ensg_number:
    :param gene_symbol:
    :return: Available information for given gene identifier
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
            "detail": "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None:
        data = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No gene(s) found with: " + ''.join(ensg_number),
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200

    elif gene_symbol is not None:
        data = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No gene(s) found with: " + ''.join(gene_symbol),
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200


def getTranscriptInformation(enst_number):
    """
    :param enst_number:
    :return: Available information for given transcript identifier
    """

    # test if the identification is given
    if enst_number is None:
        return jsonify({
            "detail": "At least one transcript identification number is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    data = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(data) > 0:
        return models.TranscriptSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": "No transcript found for given enst: " + enst_number,
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def getOverallCount(sponge_db_version: int = LATEST, level: str = "gene"):
    """
    Function return current statistic about database - amount of shared miRNA, significant and insignificant
     interactions per dataset. Handles the route /getOverallCounts/?sponge_db_version={sponge_db_version}
    :param sponge_db_version: Version of the database
    :param level: Level of the statistic to be returned, either "gene" or "transcript"
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

    # Note: the info in the gene_counts table is e.g. 
    # count_interactions_sign: SELECT * FROM interactions_genegene WHERE sponge_run_ID = 57 and p_value < 0.01;

    # datasets
    dataset_query = _dataset_query(sponge_db_version=sponge_db_version)
    dataset_ids = [dataset.dataset_ID for dataset in dataset_query]

    # Aliases for tables
    if level == "gene":
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
                (func.sum(models.OccurencesMiRNA.occurences)).label("count_shared_mirnas"),
                models.OccurencesMiRNA.sponge_run_ID
            )
            .group_by(models.OccurencesMiRNA.sponge_run_ID)
            .subquery("t2")
        )
    elif level == "transcript":
        t1 = (
            select(
                (func.sum(models.TranscriptCounts.count_all) / 2).label("count_interactions"),
                (func.sum(models.TranscriptCounts.count_sign) / 2).label("count_interactions_sign"),
                models.TranscriptCounts.sponge_run_ID
            )
            .group_by(models.TranscriptCounts.sponge_run_ID)
            .subquery("t1")
        )

        t2 = (
            select(
                (func.sum(models.OccurencesMiRNATranscript.occurences)).label("count_shared_mirnas"),
                models.OccurencesMiRNATranscript.sponge_run_ID
            )
            .group_by(models.OccurencesMiRNATranscript.sponge_run_ID)
            .subquery("t2")
        )

    t3 = (
        select(
            models.Dataset.disease_name,
            models.Dataset.disease_subtype,
            models.SpongeRun.sponge_run_ID
        )
        .select_from(
            join(models.Dataset, models.SpongeRun, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID)
        )
        .where(
            models.Dataset.sponge_db_version == sponge_db_version,
            models.SpongeRun.sponge_db_version == sponge_db_version,
            models.Dataset.dataset_ID.in_(dataset_ids),
        )
        .subquery("t3")
    )

    # Main query
    query = (
        select(
            t1.c.count_interactions,
            t1.c.count_interactions_sign,
            t1.c.sponge_run_ID,
            t2.c.count_shared_mirnas,
            t3.c.disease_name,
            t3.c.disease_subtype
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
        return jsonify({
            "detail": "At least one gene symbol is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = models.Gene.query \
        .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
        .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        return jsonify({
            "detail": "No gene(s) found for given gene_symbol(s)!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    interaction_result = models.GeneOntology.query \
        .filter(models.GeneOntology.gene_ID.in_(gene_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneOntologySchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No GO terms with given parameters found!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def getHallmark(gene_symbol):
    """
    :param gene_symbol: Gene symbol of the genes of interest
    :return: Returns all associated cancer hallmarks for the gene(s) of interest.
    """

    # test if any of the two identification possibilites is given
    if gene_symbol is None:
        return jsonify({
            "detail": "At least one gene symbol is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400
    gene = models.Gene.query \
        .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
        .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        return jsonify({
            "detail": "No gene(s) found for given gene_symbol(s)!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    interaction_result = models.hallmarks.query \
        .filter(models.hallmarks.gene_ID.in_(gene_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.HallmarksSchema(many=True).dump(interaction_result)   
    else:
        return jsonify({
            "detail": "No hallmark associated for gene(s) of interest!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

def getWikipathway(gene_symbol):
    """
    :param gene_symbol: Gene symbol of the genes of interest
    :return: Returns all associated wikipathway keys for the gene(s) of interest.
    """

    # test if any of the two identification possibilites is given
    if gene_symbol is None:
        return jsonify({
            "detail": "At least one gene symbol is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = models.Gene.query \
        .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
        .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
    else:
        return jsonify({
            "detail": "No gene(s) found for given gene_symbol(s)!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    interaction_result = models.wikipathways.query \
        .filter(models.wikipathways.gene_ID.in_(gene_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.WikipathwaySchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No wikipathway key associated for gene(s) of interest!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def getTranscriptGene(enst_number):
    """
    This function handles the route /getTranscriptGene and returns the gene id(s) for the given transcript id(s).
    :param enst_number: List of transcript identification numbers
    :return: Returns all associated gene id(s) for the transcript(s) of interest.
    """

    # test if the identification is given
    if enst_number is None:
        return jsonify({
            "detail": "At least one transcript identification number is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # Create a CASE statement to preserve the order of enst_number
    case_statement = case(
        *[(models.Transcript.enst_number == enst, index) for index, enst in enumerate(enst_number)]
    )

    query = select(models.Gene.ensg_number).select_from(
            join(models.Gene, models.Transcript, models.Gene.gene_ID == models.Transcript.gene_ID)
        ).where(models.Transcript.enst_number.in_(enst_number)) \
        .order_by(case_statement)
    

    result = db.session.execute(query).fetchall()

    if len(result) > 0:
        # return models.GeneSchemaShort(many=True).dump(result)
        return [r[0] for r in result]
    else:
        return jsonify({
            "detail": "No gene(s) associated for transcript(s) of interest!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def getGeneTranscripts(ensg_number):
    """
    This function handles the route /getGeneTranscripts and returns the transcript id(s) for the given gene id(s).
    :param ensg_number: List of gene identification numbers
    :return: Returns all associated transcript id(s) for the gene(s) of interest (list of lists).
    """

    # test if the identification is given
    if ensg_number is None:
        return jsonify({
            "detail": "At least one gene identification number is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    case_statement = case(
        *[(models.Gene.ensg_number == ensg, index) for index, ensg in enumerate(ensg_number)]
    )

    query = select(models.Gene.ensg_number, models.Transcript.enst_number).select_from(
        join(models.Gene, models.Transcript, models.Gene.gene_ID == models.Transcript.gene_ID)
    ).where(models.Gene.ensg_number.in_(ensg_number)) \
        .order_by(case_statement)

    result = db.session.execute(query).fetchall()

    if len(result) > 0:
        # return models.TranscriptSchemaShort(many=True).dump(result)
        # return [r[0] for r in result]
        gene_transcripts = {ensg: [] for ensg in ensg_number}
        for gene_id, transcript_id in result:
            gene_transcripts[gene_id].append(transcript_id)
        return [gene_transcripts[ensg] for ensg in ensg_number]
    else:
        return jsonify({
            "detail": "No transcript(s) associated for gene(s) of interest!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
    

def get_genes(gene_ID: int = None, ensg_number: str = None, gene_symbol: str = None, execute=True):
    """
    Function to retrieve all genes with the given parameters
    :param gene_ID: int
    :param ensg_number: str
    :param gene_symbol: str
    :return: list of all genes with the given parameters
    """
    
    gene_query = db.select(models.Gene) 
    if ensg_number is not None:
        gene_query = gene_query.where(models.Gene.ensg_number == ensg_number)
    if gene_symbol is not None:
        gene_query = gene_query.where(models.Gene.gene_symbol == gene_symbol)
    if gene_ID is not None:
        gene_query = gene_query.where(models.Gene.gene_ID == gene_ID)

    if execute: 
        gene_data = db.session.execute(gene_query).scalars().all()
        return gene_data
    else: 
        return gene_query


def get_transcripts(gene_ID: int = None, ensg_number: str = None, gene_symbol: str = None, transcript_ID: int = None, enst_number: str = None, execute=True):
    """
    Function to retrieve all transcripts with the given parameters
    :param transcript_ID: int
    :param enst_number: str
    :return: list of all transcripts with the given parameters
    """

    gene_data = get_genes(gene_ID=gene_ID, ensg_number=ensg_number, gene_symbol=gene_symbol)
    gene_IDs = [gene.gene_ID for gene in gene_data]
    
    transcript_query = db.select(models.Transcript).where(models.Transcript.gene_ID.in_(gene_IDs))
    if enst_number is not None:
        transcript_query = transcript_query.where(models.Transcript.enst_number == enst_number)
    if transcript_ID is not None:
        transcript_query = transcript_query.where(models.Transcript.transcript_ID == transcript_ID)
    
    transcript_data = db.session.execute(transcript_query).scalars().all()

    return transcript_data
