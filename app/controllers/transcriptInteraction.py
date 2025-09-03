import sqlalchemy as sa
import os
from flask import jsonify
from sqlalchemy import desc, and_
from sqlalchemy.sql import text
from app.controllers.dataset import _dataset_query
import app.models as models
from app.config import LATEST, db, cache


@cache.cached(query_string=True)
def read_all_transcripts(dataset_ID: int = None, disease_name=None, enst_number=None, transcript_type=None, pValue=0.05,
                         pValueDirection="<",
                         mscor=None,
                         mscorDirection="<", correlation=None, correlationDirection="<", sorting=None,
                         descending=True, limit=100, offset=0, information=True, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /ceRNAInteraction/findAllTranscripts
    and returns all interactions the given identification (enst_number) in all available datasets is in involved
    :param dataset_ID: dataset_ID of the dataset of interest
    :param sponge_db_version:
    :param disease_name: disease_name of interest
    :param enst_number: esnt number of the transcript of interest
    :param transcript_type: defines the type of transcript of interest
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
    :param information: defines if each transcript should contain all available information or not (default: True, if False: just enst_nr will be shown)
    :return: all interactions given transcript is involved
    """

    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
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
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.filter(models.SpongeRun.dataset_ID == dataset_ID)

    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries_1.append(models.TranscriptInteraction.sponge_run_ID.in_(run_IDs))
        queries_2.append(models.TranscriptInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    transcript = []
    if enst_number is not None:
        transcript = models.Transcript.query \
            .filter(models.Transcript.enst_number.in_(enst_number)) \
            .all()
    elif transcript_type is not None:
        transcript = models.Transcript.query \
            .filter(models.Transcript.transcript_type == transcript_type) \
            .all()

    if enst_number is not None or transcript_type is not None:
        if len(transcript) > 0:
            transcript_IDs = [t.transcript_ID for t in transcript]
            queries_1.append(models.TranscriptInteraction.transcript_ID_1.in_(transcript_IDs))
            queries_2.append(models.TranscriptInteraction.transcript_ID_2.in_(transcript_IDs))

        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # filter depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queries_1.append(models.TranscriptInteraction.p_value <= pValue)
            queries_2.append(models.TranscriptInteraction.p_value <= pValue)
        else:
            queries_1.append(models.TranscriptInteraction.p_value >= pValue)
            queries_2.append(models.TranscriptInteraction.p_value >= pValue)

    if mscor is not None:
        if mscorDirection == "<":
            queries_1.append(models.TranscriptInteraction.mscor <= mscor)
            queries_2.append(models.TranscriptInteraction.mscor <= mscor)
        else:
            queries_1.append(models.TranscriptInteraction.mscor >= mscor)
            queries_2.append(models.TranscriptInteraction.mscor >= mscor)

    if correlation is not None:
        if correlationDirection == "<":
            queries_1.append(models.TranscriptInteraction.correlation <= correlation)
            queries_2.append(models.TranscriptInteraction.correlation <= correlation)
        else:
            queries_1.append(models.TranscriptInteraction.correlation >= correlation)
            queries_2.append(models.TranscriptInteraction.correlation >= correlation)

    # add all sorting if given:
    sort = []
    if sorting is not None:
        if sorting == "pValue":
            if descending:
                sort.append(models.TranscriptInteraction.p_value.desc())
            else:
                sort.append(models.TranscriptInteraction.p_value.asc())
        if sorting == "mscor":
            if descending:
                sort.append(models.TranscriptInteraction.mscor.desc())
            else:
                sort.append(models.TranscriptInteraction.mscor.asc())
        if sorting == "correlation":
            if descending:
                sort.append(models.TranscriptInteraction.correlation.desc())
            else:
                sort.append(models.TranscriptInteraction.correlation.asc())

    interaction_results = models.TranscriptInteraction.query \
        .filter(*queries_1) \
        .order_by(*sort) \
        .union(models.TranscriptInteraction.query
               .filter(*queries_2)
               .order_by(*sort)) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_results) > 0:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.TranscriptInteractionDatasetLongSchema(many=True)
        else:
            schema = models.TranscriptInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_results)

    else:
        return jsonify({
            "detail": "No results",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def read_specific_interaction(dataset_ID: int = None, disease_name=None, enst_number=None, pValue=0.05,
                              pValueDirection="<", limit=100,
                              offset=0):
    """
    This function responds to a request for /ceRNAInteraction/findSpecificTranscripts
    and returns all interactions between the given identifications (enst_number)
    :param dataset_ID: dataset_ID of the dataset of interest
    :param disease_name: disease_name of interest
    :param enst_number: esnt number of the transcript of interest
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :return: all interactions between given genes
    """
    # test limit
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    transcript_query = db.select(models.Transcript)

    if enst_number is not None:
            transcript_query = transcript_query.where(models.Transcript.enst_number.in_(enst_number))

    transcript = db.session.execute(transcript_query).scalars().all()

    if len(transcript) > 0:
        transcript_IDs = [t.transcript_ID for t in transcript]
    else:
        return jsonify({
            "detail": "No transcript found for given enst_number(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # save all needed queries to get correct results
    queries = [sa.and_(models.TranscriptInteraction.transcript_ID_1.in_(transcript_IDs),
                       models.TranscriptInteraction.transcript_ID_2.in_(transcript_IDs))]

    run = db.select(models.SpongeRun)

    # if specific disease_name is given
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .where(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.where(models.SpongeRun.dataset_ID == dataset_ID)

    run = db.session.execute(run).scalars().all()

    if len(run) > 0:
        run_Ids = [i.sponge_run_ID for i in run]
        queries.append(models.TranscriptInteraction.sponge_run_ID.in_(run_Ids))
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
            queries.append(models.TranscriptInteraction.p_value < pValue)
        else:
            queries.append(models.TranscriptInteraction.p_value > pValue)

    interaction_result = models.TranscriptInteraction.query \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        return models.TranscriptInteractionDatasetLongSchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No results",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def read_all_transcript_network_analysis(dataset_ID: int = None, disease_name=None, enst_number=None,
                                         transcript_type=None,
                                         minBetweenness=None, minNodeDegree=None, minEigenvector=None,
                                         sorting=None, descending=None, limit=100, offset=0,
                                         sponge_db_version: int = LATEST):
    """
        This function responds to a request for /sponge/findceRNATranscripts
        and returns all interactions the given identification (enst_number) in all available datasets is in involved and satisfies the given filters
        :param dataset_ID: dataset_ID of the dataset of interest
        :param sponge_db_version:
        :param disease_name: isease_name of interest
        :param transcript_type: defines the type of transcript of interest
        :param enst_number: enst number of the transcript of interest
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
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries = []

    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    if disease_name is not None:
        run = models.SpongeRun.query.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.filter(models.SpongeRun.dataset_ID == dataset_ID)

    run = run.all()
    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.networkAnalysisTranscript.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if enst_number is not None:
        transcript = models.Transcript.query \
            .filter(models.Transcript.enst_number.in_(enst_number)) \
            .all()

        if len(transcript) > 0:
            transcript_IDs = [t.transcript_ID for t in transcript]
            queries.append(models.networkAnalysisTranscript.transcript_ID.in_(transcript_IDs))
        else:
            return jsonify({
                "detail": "No transcript found for given enst_number(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400


    # filter further depending on given statistics cutoffs
    if minBetweenness is not None:
        queries.append(models.networkAnalysisTranscript.betweenness > minBetweenness)
    if minNodeDegree is not None:
        queries.append(models.networkAnalysisTranscript.node_degree > minNodeDegree)
    if minEigenvector is not None:
        queries.append(models.networkAnalysisTranscript.eigenvector > minEigenvector)
    if transcript_type is not None:
        queries.append(models.Transcript.transcript_type == transcript_type)

    # add all sorting if given:
    sort = [models.networkAnalysisTranscript.sponge_run_ID]
    if sorting is not None:
        if sorting == "betweenness":
            if descending:
                sort.append(models.networkAnalysisTranscript.betweenness.desc())
            else:
                sort.append(models.networkAnalysisTranscript.betweenness.asc())
        if sorting == "degree":
            if descending:
                sort.append(models.networkAnalysisTranscript.node_degree.desc())
            else:
                sort.append(models.networkAnalysisTranscript.node_degree.asc())
        if sorting == "eigenvector":
            if descending:
                sort.append(models.networkAnalysisTranscript.eigenvector.desc())
            else:
                sort.append(models.networkAnalysisTranscript.eigenvector.asc())

    result = models.networkAnalysisTranscript.query \
        .join(models.Transcript, models.Transcript.transcript_ID == models.networkAnalysisTranscript.transcript_ID) \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(result) > 0:
        schema = models.networkAnalysisSchemaTranscript(many=True)
        return schema.dump(result)
    else:
        return jsonify({
            "detail": "No data found that satisfies the given filters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def read_all_to_one_mirna(dataset_ID: int = None, disease_name=None, mimat_number=None, hs_number=None, pValue=0.05,
                          pValueDirection="<", mscor=None, mscorDirection="<", correlation=None,
                          correlationDirection="<",
                          limit=100, offset=0):
    """
    :param dataset_ID: dataset_ID of the dataset of interest
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
    queriesTranscriptInteraction = []
    queriesmirnaInteraction = []

    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
        queriesmirnaInteraction.append(models.miRNAInteractionTranscript.miRNA_ID.in_(mirna_IDs))
    else:
        return jsonify({
            "detail": "With given mimat_ID or hs_number no miRNA could be found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    run = db.select(models.SpongeRun)

    # if specific disease_name is given
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .where(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.where(models.SpongeRun.dataset_ID == dataset_ID)

    run = db.session.execute(run).scalars().all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queriesmirnaInteraction.append(models.miRNAInteractionTranscript.sponge_run_ID.in_(run_IDs))
        queriesTranscriptInteraction.append(models.TranscriptInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # get all possible transcript interaction partners for specific miRNA
    transcript_interaction = models.miRNAInteractionTranscript.query \
        .filter(*queriesmirnaInteraction) \
        .all()

    transcriptInteractionIDs = []
    if len(transcript_interaction) > 0:
        transcriptInteractionIDs = [t.transcript_ID for t in transcript_interaction]
    else:
        return jsonify({
            "detail": "No transcript is associated with the given miRNA.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # save all needed queries to get correct results
    queriesTranscriptInteraction.append(
        sa.and_(models.TranscriptInteraction.transcript_ID_1.in_(transcriptInteractionIDs),
                models.TranscriptInteraction.transcript_ID_2.in_(transcriptInteractionIDs)))

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queriesTranscriptInteraction.append(models.TranscriptInteraction.p_value <= pValue)
        else:
            queriesTranscriptInteraction.append(models.TranscriptInteraction.p_value >= pValue)
    if mscor is not None:
        if mscorDirection == "<":
            queriesTranscriptInteraction.append(models.TranscriptInteraction.mscor <= mscor)
        else:
            queriesTranscriptInteraction.append(models.TranscriptInteraction.mscor >= mscor)
    if correlation is not None:
        if correlationDirection == "<":
            queriesTranscriptInteraction.append(models.TranscriptInteraction.correlation <= correlation)
        else:
            queriesTranscriptInteraction.append(models.TranscriptInteraction.correlation >= correlation)

    interaction_result = models.TranscriptInteraction.query \
        .filter(*queriesTranscriptInteraction) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        schema = models.TranscriptInteractionLongSchema(many=True)
        return schema.dump(interaction_result)
    else:
        return jsonify({
            "detail": "No data found that satisfies the given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def read_all_mirna(dataset_ID: int = None, disease_name=None, mimat_number=None, hs_number=None, occurences=None,
                   sorting=None, descending=None,
                   limit=100, offset=0):
    """
    :param dataset_ID: dataset_ID of the dataset of interest
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
            queries.append(models.OccurencesMiRNATranscript.miRNA_ID.in_(mirna_IDs))
        else:
            return jsonify({
                "detail": "With given mimat_ID or hs_number no mirna could be found",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    run = db.select(models.SpongeRun)

    # if specific disease_name is given
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .where(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.where(models.SpongeRun.dataset_ID == dataset_ID)

    run = db.session.execute(run).scalars().all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.OccurencesMiRNATranscript.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if occurences is not None:
        queries.append(models.OccurencesMiRNATranscript.occurences > occurences)

    # add sorting
    sort = []
    if sorting == "occurences":
        if descending:
            sort.append(desc(models.OccurencesMiRNATranscript.occurences))
        else:
            sort.append(models.OccurencesMiRNATranscript.occurences)

    interaction_result = models.OccurencesMiRNATranscript.query \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.occurencesMiRNASchemaTranscript(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No results",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def test_transcript_interaction(dataset_ID: int = None, enst_number=None, sponge_db_version: int = LATEST):
    """
        :param enst_number: ensg number of the gene of interest
        :return: lists of all cancer types transcript of interest has at least one interaction in the corresponding ceRNA II network
    """
    transcripts = models.Transcript.query \
        .filter(models.Transcript.enst_number == enst_number) \
        .all()

    if len(transcripts) > 0:
        transcript_ID = [t.transcript_ID for t in transcripts]
    else:
        return jsonify({
            "detail": "No transcripts found for given enst_number(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    run = db.session.execute(text(
        f"SELECT * from dataset join sponge_run on dataset.dataset_ID = sponge_run.dataset_ID where dataset.sponge_db_version = {sponge_db_version}"))

    if dataset_ID is not None:
        run = run.filter(models.Dataset.dataset_ID == dataset_ID)

    result = []
    for r in run:
        tmp = db.session.execute(
            text("SELECT EXISTS(SELECT * FROM interactions_transcripttranscript where sponge_run_ID = " + str(r.sponge_run_ID) +
                 " and transcript_ID_1 = " + str(transcript_ID[0]) + " limit 1) as include;")).fetchone()

        if (tmp[0] == 1):
            check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "disease_subtype": r.disease_subtype,
                     "sponge_run_ID": r.sponge_run_ID, "include": tmp[0]}
        else:
            tmp2 = db.session.execute(
                text("SELECT EXISTS(SELECT * FROM interactions_transcripttranscript where sponge_run_ID = " + str(
                    r.sponge_run_ID) +
                     " and transcript_ID_2 = " + str(transcript_ID[0]) + " limit 1) as include;")).fetchone()

            if (tmp2[0] == 1):
                check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "disease_subtype": r.disease_subtype, "sponge_run_ID": r.sponge_run_ID,
                         "include": 1}
            else:
                check = {"data_origin": r.data_origin, "disease_name": r.disease_name, "disease_subtype": r.disease_subtype, "sponge_run_ID": r.sponge_run_ID,
                         "include": 0}

        result.append(check)

    schema = models.checkTranscriptInteractionProCancer(many=True)
    return schema.dump(result)


@cache.cached(query_string=True)
def read_mirna_for_specific_interaction(dataset_ID: int = None, disease_name=None, enst_number=None, between=False):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNATranscripts
    and returns all miRNAs that contribute to all interactions between the given identifications (enst_number)
    :param dataset_ID: dataset_ID of the dataset of interest
    :param disease_name: disease_name of interest
    :param enst_number: enst number of the transcripts of interest
    :param between: If false, all interactions where one of the interaction partners fits the given transcripts of interest
                    will be considered.
                    If true, just interactions between the transcripts of interest will be considered.

    :return: all miRNAs contributing to the interactions between transcripts of interest
    """

    # get datasets 
    disease_query = _dataset_query(disease_name=disease_name, dataset_ID=dataset_ID)
    diseases = [d.dataset_ID for d in disease_query]  

    # get runs
    run_query = db.select(models.SpongeRun.sponge_run_ID).where(models.SpongeRun.dataset_ID.in_(diseases))

    # get transcripts 
    transcript_query = db.select(models.Transcript.transcript_ID).where(models.Transcript.enst_number.in_(enst_number))
    
    # get interactions for given transcripts and runs
    base_interaction_query = db.select(models.miRNAInteractionTranscript).where(
        models.miRNAInteractionTranscript.transcript_ID.in_(transcript_query),
        models.miRNAInteractionTranscript.sponge_run_ID.in_(run_query)
    )

    base_interaction = db.session.execute(base_interaction_query).scalars().all()
    print(base_interaction)

    if between:
        # subquery to count distinct transcripts
        distinct_query = db.select(db.func.count(db.distinct(models.miRNAInteractionTranscript.transcript_ID))) \
            .where(models.miRNAInteractionTranscript.transcript_ID.in_(transcript_query)) \
            .where(models.miRNAInteractionTranscript.sponge_run_ID.in_(run_query))
        

        # subquery to get miRNA IDs that are shared between transcripts
        mirna_query = db.select(models.miRNAInteractionTranscript.miRNA_ID) \
            .where(models.miRNAInteractionTranscript.transcript_ID.in_(transcript_query)) \
            .where(models.miRNAInteractionTranscript.sponge_run_ID.in_(run_query)) \
            .group_by(models.miRNAInteractionTranscript.miRNA_ID) \
            .having(db.func.count(models.miRNAInteractionTranscript.transcript_ID) == distinct_query)
        
        mirnas = db.session.execute(mirna_query).scalars().all()
        print(mirnas)

        # filter interactions by the miRNA IDs from the previous subquery
        interaction_query = base_interaction_query.where(models.miRNAInteractionTranscript.miRNA_ID.in_(mirna_query))

    else:
        interaction_query = base_interaction_query

    interaction_result = db.session.execute(interaction_query).scalars().all()

    if len(interaction_result) > 0:
        return models.miRNAInteractionSchemaTranscript(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No shared miRNA between transcripts found.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def getTranscriptCounts(dataset_ID: int = None, disease_name=None, enst_number=None, minCountAll=None,
                        minCountSign=None):
    """
    This function responds to a request for /transcriptCounts
    and returns transcript(s) of interest with respective counts in disease of interest.
    :param dataset_ID: dataset_ID of the dataset of interest
    :param disease_name: disease_name of interest
    :param enst_number: enst number of the genes of interest
    :param minCountAll: defines the minimal number of times a gene has to be involved in the complete network
    :param minCountSign: defines the minimal number of times a gene has to be involved in significant (p.adj < 0.05) interactionss

    :return: all transcripts with counts.
    """

    queries = []

    run = db.select(models.SpongeRun)

    # if specific disease_name is given
    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .where(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.where(models.SpongeRun.dataset_ID == dataset_ID)

    run = db.session.execute(run).scalars().all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.TranscriptCounts.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    transcript = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(transcript) > 0:
        transcript_ID = [t.transcript_ID for t in transcript]
        queries.append(models.TranscriptCounts.transcript_ID.in_(transcript_ID))

    else:
        return jsonify({
            "detail": "No transcript found for given enst_number(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # add count filter if provided
    if minCountAll is not None:
        queries.append(models.TranscriptCounts.count_all >= minCountAll)
    if minCountSign is not None:
        queries.append(models.TranscriptCounts.count_sign >= minCountSign)

    results = models.TranscriptCounts.query \
        .filter(*queries) \
        .all()

    if len(results) > 0:
        return models.TranscriptCountSchema(many=True).dump(results)

    else:
        return jsonify({
            "detail": "No data found that satisfies the given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def get_transcript_network(dataset_ID: int = None, disease_name=None,
                            minBetweenness:float = None, minNodeDegree:float = None, minEigenvector:float = None,
                            maxPValue=0.05, minMscor=None, minCorrelation=None,
                            edgeSorting: str = None, nodeSorting: list[str] = None,
                            maxNodes: int = 100, maxEdges: int = 100, 
                            offsetNodes: int = None, offsetEdges: int = None,
                            sponge_db_version: int = LATEST):
    """
    Optimized function for fetching ceRNA network nodes and edges with applied filters and sorting. Handles route /ceRNAInteraction/getTranscriptNetwork
    :param dataset_ID: dataset_ID of interest
    :param disease_name: disease_name of interest
    :param minBetweenness: betweenness cutoff (>)
    :param minNodeDegree: degree cutoff (>)
    :param minEigenvector: eigenvector cutoff (>)
    :param maxPValue: p-value cutoff (<)
    :param minMscor: mscor cutoff (>)
    :param minCorrelation: correlation cutoff (>)
    :param edgeSorting: sorting key for edges
    :param nodeSorting: sorting key(s) for nodes (options are 'betweenness', 'node_degree', 'eigenvector')
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
    edge_query = db.select(models.TranscriptInteraction).filter(
        models.TranscriptInteraction.sponge_run_ID.in_(run_query),
    )
    if maxPValue: 
        edge_query = edge_query.filter(
            models.TranscriptInteraction.p_value <= maxPValue
        )
    
    # Get prefiltered edges 
    edges = db.session.execute(edge_query).scalars().all()
    tr_ids_in_edges = set([edge.transcript_ID_1 for edge in edges] + [edge.transcript_ID_2 for edge in edges])

    # Filter nodes by edges that pass the p-value filter
    node_query = db.select(models.networkAnalysisTranscript).filter(
        models.networkAnalysisTranscript.sponge_run_ID.in_(run_query),
        models.networkAnalysisTranscript.transcript_ID.in_(tr_ids_in_edges)
    )

    # Apply node-specific filters
    if minBetweenness:
        node_query = node_query.filter(models.networkAnalysisTranscript.betweenness >= minBetweenness)
    if minNodeDegree:
        node_query = node_query.filter(models.networkAnalysisTranscript.node_degree >= minNodeDegree)
    if minEigenvector:
        node_query = node_query.filter(models.networkAnalysisTranscript.eigenvector >= minEigenvector)

    # Sorting nodes: if more than one sorting key, rank by each key individually and sort by the mean of the ranks
    if nodeSorting:
        if any([key not in ['betweenness', 'node_degree', 'eigenvector'] for key in nodeSorting]):
            raise ValueError("Invalid node sorting key. Choose from 'betweenness', 'node_degree', 'eigenvector'")
        rank_columns = [db.func.rank().over(order_by=getattr(models.networkAnalysisTranscript, col).desc()).label(f"{col}_rank") for col in nodeSorting]
        mean_rank = sum(rank_columns) / len(rank_columns)
        node_query = node_query.order_by(mean_rank)

    # node pagination
    node_query = node_query.offset(offsetNodes).limit(maxNodes)    
    
    # filter edges based on filtered nodes
    nodes = db.session.execute(node_query).scalars().all()
    node_tr_ids = set([node.transcript_ID for node in nodes])
    edge_query = edge_query.filter(
        and_(
            models.TranscriptInteraction.transcript_ID_1.in_(node_tr_ids),
            models.TranscriptInteraction.transcript_ID_2.in_(node_tr_ids)
        )
    )

    # Apply edge-specific filters
    if minMscor:
        edge_query = edge_query.filter(models.TranscriptInteraction.mscor >= minMscor)
    if minCorrelation:
        edge_query = edge_query.filter(models.TranscriptInteraction.correlation >= minCorrelation)

    # Sort edges
    if edgeSorting == "pValue":
        edge_query = edge_query.order_by(models.TranscriptInteraction.p_value.asc())
    elif edgeSorting == "mscor":
        edge_query = edge_query.order_by(models.TranscriptInteraction.mscor.desc())
    elif edgeSorting == "correlation":
        edge_query = edge_query.order_by(models.TranscriptInteraction.correlation.desc())
    else:
        raise ValueError("Invalid edge sorting key. Choose one of 'pValue', 'mscor', 'correlation'")    

    # edge pagination
    edge_query = edge_query.offset(offsetEdges).limit(maxEdges)

    # Execute queries
    node_results = db.session.execute(node_query).scalars().all()
    edge_results = db.session.execute(edge_query).scalars().all()

    # Return results 
    return jsonify({
        "edges": models.TranscriptInteractionDatasetLongSchema(many=True).dump(edge_results),
        "nodes": models.networkAnalysisSchemaTranscript(many=True).dump(node_results)
    })

