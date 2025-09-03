from flask import jsonify
from sqlalchemy import or_
from app.controllers.dataset import _dataset_query
import app.models as models
from flask import Response
from app.config import db, LATEST, cache


@cache.cached(query_string=True)
def get_transcript_events(enst_number):
    """
    :param enst_number: Enst number of the transcript of interest
    :return: all event type names for the transcript of interest
    """

    # test if the identification is given
    if enst_number is None:
        return jsonify({
            "detail": "At least one transcript identification number is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    transcript = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(transcript) > 0:
        transcript_IDs = [i.transcript_ID for i in transcript]
    else:
        return jsonify({
            "detail": "No transcript(s) found for the given enst_number(s)!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

    interaction_result = models.AlternativeSplicingEventTranscripts.query \
        .filter(models.AlternativeSplicingEventTranscripts.transcript_ID.in_(transcript_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.AlternativeSplicingEventsTranscriptsSchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No event types with given parameters found!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


@cache.cached(query_string=True)
def get_event_positions(enst_number, event_type):
    """
    :param enst_number: Enst number of the transcript of interst
    :param event_type: Name of the event type
    :return: start and end position(s) of the transcript with event type of interst
    """

    # test if any of the two identification possibilities is given
    if enst_number is None:
        return jsonify({
            "detail": "At least one transcript identification number is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if event_type is None:
        return jsonify({
            "detail": "At least one event type is needed!",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    transcript = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(transcript) > 0:
        transcript_IDs = [i.transcript_ID for i in transcript]
    else:
        return jsonify({
            "detail": "No transcript found for given enst_number(s)!",
            "status": 200,
            "title": "Bad Request",
            "type": "about:blank"
        }), 200

    event = models.AlternativeSplicingEventTranscripts.query \
        .filter(models.AlternativeSplicingEventTranscripts.event_type.in_(event_type)) \
        .all()

    if len(event) > 0:
        event_types = [e.event_type for e in event]
    else:
        return jsonify({
            "detail": "No possible event type name",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


@cache.cached(query_string=True)
def get_exons_for_position(start_pos: int, end_pos: int):
    """
    This function response for the request: /alternativeSplicing/getExonsForPosition/
    with genomic start and end positions
    :param start_pos: genomic start position
    :param end_pos: genomic end position
    :return: exons matching the exact genomic positions
    """
    # get matching transcript_element_positions
    transcript_element_positions_ids = models.TranscriptElementPositions.query \
        .filter(models.TranscriptElementPositions.start_pos == start_pos) \
        .filter(models.TranscriptElementPositions.end_pos == end_pos) \
        .all()
    result = models.TranscriptElement.query \
        .filter(models.TranscriptElement.transcript_element_positions_ID.in_(transcript_element_positions_ids)) \
        .all()
    if len(result) > 0:
        schema = models.TranscriptElementSchema(many=True)
        return schema.dump(result)
    else:
        return jsonify({
            "detail": "No data found that satisfies the given filters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank"
        }), 400


@cache.cached(query_string=True)
def get_psi_values(dataset_ID: str = None, disease_name: str = None, data_origin: str = None, transcript_ID: str = None, enst_number: str =None, psivec_ID: int = None, alternative_splicing_event_transcripts_ID: str = None, sample_ID: str = None, limit=100, sponge_db_version: int = LATEST):
    """
    This function response for the request: /alternativeSplicing/getPsiValue/
    with the possibility to filter by psivec_ID, alternative
    splicing event transcripts ID and sample ID
    :param disease_name: name of the disease
    :param dataset_ID: ID of the dataset
    :param psivec_ID: ID of the psivec
    :param alternative_splicing_event_transcripts_ID: ID of the alternative splicing event transcripts
    :param sample_ID: ID of the sample
    :return: psi value for the given parameters, ordered by psi value
    """

    # Get the dataset
    if dataset_ID or disease_name or data_origin:
        data = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID, disease_name=disease_name, data_origin=data_origin)
        data = [d.disease_name for d in data]
    else: 
        data = None

    # Build the transcript query
    transcript_query = db.select(models.Transcript.transcript_ID)
    if transcript_ID:
        transcript_query = transcript_query.where(models.Transcript.transcript_ID == transcript_ID)
    if enst_number:
        transcript_query = transcript_query.where(models.Transcript.enst_number == enst_number)

    # Build the alternative splicing events query
    as_query = db.select(models.AlternativeSplicingEventTranscripts.alternative_splicing_event_transcripts_ID).where(
        models.AlternativeSplicingEventTranscripts.transcript_ID.in_(transcript_query)
    )
    if alternative_splicing_event_transcripts_ID:
        as_query = as_query.where(
            models.AlternativeSplicingEventTranscripts.alternative_splicing_event_transcripts_ID == alternative_splicing_event_transcripts_ID
        )

    # Build the psi values query
    psi_query = db.select(models.PsiVec).where(
        models.PsiVec.alternative_splicing_event_transcripts_ID.in_(as_query)
    )
    if psivec_ID:
        psi_query = psi_query.where(models.PsiVec.psivec_ID == psivec_ID)
    if sample_ID:
        psi_query = psi_query.where(models.PsiVec.sample_ID == sample_ID)
    if data:
        psi_query = psi_query.where(or_(*[models.PsiVec.sample_ID.like(d.replace(" ", "_") + "%") for d in data]))

    # Apply limit and sort results
    psi_query = psi_query.order_by(models.PsiVec.psi_value.desc()).limit(limit)

    psi_values = db.session.execute(psi_query).scalars().all()

    if psi_values:
        schema = models.PsiVecSchema(many=True)
        return schema.dump(psi_values)
    else:
        return jsonify({
            "detail": "No data found that satisfies the given filters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

