from flask import abort
import models

def get_comparison(disease_name=None, disease_subtype=None):
    """
    :param disease_name: disease name of one part of the comparison (e.g. Sarcoma)
    :param disease_subtype: subtype of the same part of the comparison, overtype if none is provided (e.g. LMS) 
    :return: all comparisons which contain the given disease name and subtype combination
    """

    # if specific disease_name is given:
    dataset = models.Dataset.query

    if disease_name is not None:
        dataset = dataset.filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
            
        if disease_subtype is None:
            dataset = dataset.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset = dataset.filter(models.Dataset.disease_subtype.like("%" + disease_subtype + "%"))

    dataset = dataset.all()

    dataset = [x.dataset_ID for x in dataset]

    if len(dataset) == 0:
        abort(404, "No dataset with given disease_name found")

    result = models.Comparison.query \
        .filter(models.Comparison.dataset_ID_1.in_(dataset) | models.Comparison.dataset_ID_2.in_(dataset)) \
        .all()
                                
    if len(result) > 0:
        return models.ComparisonSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")
