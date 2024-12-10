from flask import abort
import models
from config import LATEST, db

def get_comparison(dataset_ID: str = None, disease_name: str = None, disease_subtype=None, sponge_db_version: int = LATEST):
    """
    :param dataset_ID: ID of the dataset to find
    :param disease_name: disease name of one part of the comparison (e.g. Sarcoma)
    :param disease_subtype: subtype of the same part of the comparison, overtype if none is provided (e.g. LMS) 
    :param sponge_db_version: version of the database
    :return: all comparisons which contain the given disease name and subtype combination
    """

    # get dataset table
    query = db.select(models.Dataset)

    # do filtering
    if dataset_ID is not None:
        query = query.where(models.Dataset.dataset_ID == dataset_ID)
    if disease_name is not None:
        query = query.where(models.Dataset.disease_name.like("%" + disease_name + "%"))
    if disease_subtype is None:
        query = query.where(models.Dataset.disease_subtype.is_(None))
    else:
        query = query.where(models.Dataset.disease_subtype.like("%" + disease_subtype + "%"))

    data = db.session.execute(query).scalars().all()

    dataset = [i.dataset_ID for i in data]

    if len(dataset) == 0:
        abort(404, "No dataset with given disease_name found")

    comparison_query = db.select(models.Comparison).where(models.Comparison.dataset_ID_1.in_(dataset) | models.Comparison.dataset_ID_2.in_(dataset))

    result = db.session.execute(comparison_query).scalars().all()
                                
    if len(result) > 0:
        return models.ComparisonSchema(many=True).dump(result)
    else:
        abort(404, "No data found.")
