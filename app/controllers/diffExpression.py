from flask import jsonify
import app.models as models
from app.config import LATEST
from app.controllers.dataset import _dataset_query
from app.controllers.comparison import _comparison_query

def get_diff_expr(dataset_ID_1: str = None, dataset_ID_2: int = None, 
                  condition_1=None, condition_2=None, 
                  ensg_number=None, gene_symbol=None, sponge_db_version: int = LATEST, 
                  limit: int = None, offset: int = None):
    """
    API call /differentialExpression,
    get differential expression results between genes
    :param dataset_ID_1: dataset_ID of the first dataset of interest
    :param dataset_ID_2: dataset_ID of the second dataset of interest
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param ensg_number: esng number of the gene(s) of interest
    :param gene_symbol: gene symbol of the gene(s) of interest
    :param sponge_db_version: version of the database
    :return: differential expression information for the genes of interest and the selected comparison
    """

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification parameter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

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

    dataset_1 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_1)
    dataset_1 = [x.dataset_ID for x in dataset_1]

    dataset_2 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_2)
    dataset_2 = [x.dataset_ID for x in dataset_2]

    comparisons, reverse = _comparison_query(dataset_1, dataset_2, condition_1, condition_2, "gene")

    if type(comparisons) is not list: 
        return comparisons

    comparison_ID = comparisons[0].comparison_ID

    result = models.DifferentialExpression.query \
        .filter(models.DifferentialExpression.comparison_ID == comparison_ID)

    if len(gene) > 0:
        result = result.filter(models.DifferentialExpression.gene_ID.in_(gene_IDs))

    if limit is not None:
        result = result.limit(limit)
    if offset is not None:
        result = result.offset(offset)
    result = result.all()

    if len(result) > 0:
        out = models.DESchema(many=True).dump(result)
        if reverse:
            for i in range(len(out)):
                out[i]["log2FoldChange"] = -out[i]["log2FoldChange"]
                out[i]["stat"] = -out[i]["stat"]

        return out
    else:
        return jsonify({
            "detail": "No data found.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_diff_expr_transcript(dataset_ID_1: int = None, dataset_ID_2: int = None, 
                             condition_1=None, condition_2=None, 
                             enst_number=None, sponge_db_version: int = LATEST,
                             limit: int = None, offset: int = None):
    """
    API call /differentialExpressionTranscript,
    get differential expression results between transcripts.
    :param dataset_ID_1: dataset_ID of the first dataset of interest
    :param dataset_ID_2: dataset_ID of the second dataset of interest
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param enst_number: esng number of the transcript(s) of interest
    :param sponge_db_version: version of the database
    :return: differential expression information for the transcript of interest and the selected comparison
    """

    transcript = []

    if enst_number is not None:
        transcript = models.Transcript.query \
            .filter(models.Transcript.enst_number.in_(enst_number)) \
            .all()

    if len(transcript) > 0:
        transcript_IDs = [i.transcript_ID for i in transcript]

    dataset_1 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_1)
    dataset_1 = [x.dataset_ID for x in dataset_1]

    dataset_2 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_2)
    dataset_2 = [x.dataset_ID for x in dataset_2]

    comparisons, reverse = _comparison_query(dataset_1, dataset_2, condition_1, condition_2, "transcript")
    comparison_ID = comparisons[0].comparison_ID

    result = models.DifferentialExpression.query \
        .filter(models.DifferentialExpression.comparison_ID == comparison_ID)

    if len(transcript) > 0:
        result = result.filter(models.DifferentialExpression.transcript_ID.in_(transcript_IDs))

    if limit is not None:
        result = result.limit(limit)
    if offset is not None:  
        result = result.offset(offset)

    result = result.all()

    if len(result) > 0:
        out = models.DETranscriptSchema(many=True).dump(result)
        if reverse:
            for i in range(len(out)):
                out[i]["log2FoldChange"] = -out[i]["log2FoldChange"]
                out[i]["stat"] = -out[i]["stat"]

        return out
    else:
        return jsonify({
            "detail": "No data found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


