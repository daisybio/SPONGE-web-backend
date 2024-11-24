from flask import abort
import models
from flask import Response

def get_transcript_events(enst_number):
    """
    :param enst_number: Enst number of the transcript of interest
    :return: all event type names for the transcript of interest
    """

    # test if the identification is given
    if enst_number is None:
        abort(404, "At least one transcript identification number is needed!")

    transcript = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(transcript) > 0:
        transcript_IDs = [i.transcript_ID for i in transcript]
    else:
        abort(404, "No transcript(s) found for given enst_number(s)!")

    interaction_result = models.AlternativeSplicingEventTranscripts.query \
        .filter(models.AlternativeSplicingEventTranscripts.transcript_ID.in_(transcript_IDs)) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.AlternativeSplicingEventTranscripts(many=True).dump(interaction_result)
    else:
        return Response("{"
                        "\"detail\": \"No event types with given parameters found!\","
                        "\"status\": 202,"
                        "\"title\": \"Accepted\","
                        "\"type\": \"about:blank\"}",
                        status=202)

def get_event_positions(enst_number, event_type):
    """
    :param enst_number: Enst number of the transcript of interst
    :param event_type: Name of the event type
    :return: start and end position(s) of the transcript with event type of interst
    """

    # test if any of the two identification possibilities is given
    if enst_number is None:
        abort(404, "At least one transcript identification number is needed!")

    if event_type is None:
        abort(404, "At least one event type is needed!")

    transcript = models.Transcript.query \
        .filter(models.Transcript.enst_number.in_(enst_number)) \
        .all()

    if len(transcript) > 0:
        transcript_IDs = [i.transcript_ID for i in transcript]
    else:
        abort(404, "No transcript found for given enst_number(s)!")

    event = models.AlternativeSplicingEventTranscripts.query \
        .filter(models.AlternativeSplicingEventTranscripts.event_type.in_(event_type)) \
        .all()

    if len(event) > 0:
        event_types = [e.event_type for e in event]
    else:
        abort(404, "No possible event type name")


def get_exons_for_position(start_pos: int, end_pos: int):
    """
    This function response for the request: /sponge//alternativeSplicing/getExonsForPosition/
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
        schema = models.networkAnalysisSchema(many=True)
        return schema.dump(result)
    else:
        abort(404, "No data found that satisfies the given filters")

