from flask import jsonify
import app.models as models
from app.config import LATEST, db
from app.controllers.dataset import _dataset_query


def _comparison_query(dataset_1, dataset_2, condition_1=None, condition_2=None, gene_transcript="gene"):

    # old:
    # reverse = False
    # if condition_1 is not None and condition_2 is not None:
    #     comparison = models.Comparison.query \
    #         .filter(models.Comparison.dataset_ID_1.in_(dataset_1)) \
    #         .filter(models.Comparison.dataset_ID_2.in_(dataset_2)) \
    #         .filter(models.Comparison.condition_1 == condition_1) \
    #         .filter(models.Comparison.condition_2 == condition_2) \
    #         .filter(models.Comparison.gene_transcript == "gene") \
    #         .all()

    #     if len(comparison) == 0:
    #         comparison = models.Comparison.query \
    #             .filter(models.Comparison.dataset_ID_1.in_(dataset_2)) \
    #             .filter(models.Comparison.dataset_ID_2.in_(dataset_1)) \
    #             .filter(models.Comparison.condition_1 == condition_2) \
    #             .filter(models.Comparison.condition_2 == condition_1) \
    #             .filter(models.Comparison.gene_transcript == "gene") \
    #             .all()
    #         reverse = True
    #         if len(comparison) == 0:
    #             abort(404, "No comparison found for given inputs")
    # else:
    #     abort(404, "Condition missing")

    # new: 
    reverse = False
    comparison = models.Comparison.query \
    .filter(models.Comparison.dataset_ID_1.in_(dataset_1)) \
    .filter(models.Comparison.dataset_ID_2.in_(dataset_2)) \
    .filter(models.Comparison.gene_transcript == gene_transcript) 

    # filter conditions
    if condition_1 is not None:
        comparison = comparison.filter(models.Comparison.condition_1 == condition_1)
    if condition_2 is not None:
        comparison = comparison.filter(models.Comparison.condition_2 == condition_2)
    
    comparisons = comparison.all()

    # check if comparison is named differently 
    if len(comparisons) == 0:
        reverse = True
        comparison = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1.in_(dataset_2)) \
            .filter(models.Comparison.dataset_ID_2.in_(dataset_1)) \
            .filter(models.Comparison.gene_transcript == gene_transcript) 

        comparisons = comparison.all()    
    
    # error if no comparison found
    if len(comparisons) == 0:
        return jsonify({
            "detail": "No comparison found for given inputs",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

    if len(comparisons) > 1:
        return jsonify({
            "detail": "Multiple comparisons found for given inputs",
            "status": 200,
            "title": "Wrong Content",
            "type": "about:blank",
            "data": []
        }), 200

    return comparisons, reverse
    

def get_comparison(dataset_ID: str = None, disease_name: str = None, disease_subtype=None, sponge_db_version: int = LATEST):
    """
    :param dataset_ID: ID of the dataset to find
    :param disease_name: disease name of one part of the comparison (e.g. Sarcoma)
    :param disease_subtype: subtype of the same part of the comparison, overtype if none is provided (e.g. LMS) 
    :param sponge_db_version: version of the database
    :return: all comparisons which contain the given disease name and subtype combination
    """

    # get dataset table
    data = _dataset_query(sponge_db_version=sponge_db_version, disease_name=disease_name, disease_subtype=disease_subtype, dataset_ID=dataset_ID)
    dataset = [i.dataset_ID for i in data]

    comparison_query = db.select(models.Comparison).where(models.Comparison.dataset_ID_1.in_(dataset) | models.Comparison.dataset_ID_2.in_(dataset))

    result = db.session.execute(comparison_query).scalars().all()
                                
    if len(result) > 0:
        return models.ComparisonSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No transcript(s) found for the given enst_number(s)!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
