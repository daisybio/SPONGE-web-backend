from flask import jsonify
from sqlalchemy import and_
import app.models as models
from app.config import LATEST, db
from typing import List


def _dataset_query(query = None, sponge_db_version = LATEST, **kwargs):
    
    if query is None: 
        query = db.select(models.Dataset)
    for key, value in kwargs.items():
        # special cases: 
        if value is None or value == 'any':
            continue
        elif key == 'disease_subtype' and value == 'unspecific':
            query = query.where(getattr(models.Dataset, key).is_(None))
        # filter standart cases
        elif type(value) == str:
            query = query.where(getattr(models.Dataset, key).like("%" + value + "%"))
        elif type(value) == int:
            query = query.where(getattr(models.Dataset, key) == value)
        elif type(value) == list:
            query = query.where(getattr(models.Dataset, key).in_(value))

        else:
            return jsonify({
                "detail": "Unknown input type",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    if not sponge_db_version == 'any':
        query = query.where(models.Dataset.sponge_db_version == sponge_db_version)
    data = db.session.execute(query).scalars().all()

    if len(data) == 0:
        return jsonify({
            "detail": "No transcript(s) found for the given enst_number(s)!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
        
    return data


def get_diseases(disease_ID: int = None, disease_name: str = None, disease_subtype: str = None, versions: List[int] = None):
    """
    This function responds to a request for /sponge/diseases
    with the complete lists of diseases passing the filter parameters

    :param disease_ID: ID of the disease to find.
    :param disease_name: Name of the disease to find.
    :param disease_subtype: Subtype of the disease to find.
    :param versions: List of sponge_db_versions in which the disease need to be present.
    :return: All diseases that match the filter.
    """

    query = db.select(models.Disease)

    if disease_ID is not None: 
        query = query.where(models.Disease.disease_ID == disease_ID)
    if disease_name is not None:
        query = query.where(models.Disease.disease_name.like("%" + disease_name + "%"))
    if disease_subtype is not None:
        query = query.where(models.Disease.disease_subtype.like("%" + disease_subtype + "%"))
    if versions is not None:
        conditions = [models.Disease.versions.like(f"%{version}%") for version in versions]
        query = query.where(and_(*conditions))
        
    diseases = db.session.execute(query).scalars().all()

    if len(diseases) > 0:
        for disease in diseases:
            dataset_query = db.select(models.Dataset.dataset_ID).where(models.Dataset.disease_ID == disease.disease_ID)
            dataset_IDs = db.session.execute(dataset_query).scalars().all()
            disease.dataset_IDs = dataset_IDs

        return models.DiseaseSchema(many=True).dump(diseases)
    else:
        return jsonify({
            "detail": 'No data found for name: {disease_name}'.format(disease_name=disease_name),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_datasets(dataset_ID: int = None, disease_name: str = None, disease_subtype: str = None, data_origin=None, sponge_db_version: int = LATEST):
    """
        This function responds to a request for /sponge/datasets?data_origin={data_origin}&sponge_db_version={version}
        with one matching entry to the specified data_origin

        :param dataset_id:   ID of the dataset to find
        :param disease_name:   name of the dataset to find
        :param data_origin:   name of the data source
        :param sponge_db_version:       version of the database
        :return:            all datasets that match the source (e.g. TCGA)
    """
    # Query dataset table
    query = db.select(models.Dataset)

    data = _dataset_query(query, sponge_db_version, dataset_ID=dataset_ID, disease_name=disease_name, disease_subtype=disease_subtype, data_origin=data_origin)

    # Did we find a source?
    if len(data) > 0:
        # Serialize the data for the response
        return models.DatasetSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": 'No data found for name: {data_origin}'.format(data_origin=data_origin),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

# def read(disease_name=None, sponge_db_version: int = LATEST):
#     """
#        This function responds to a request for /sponge/dataset/?disease_name={disease_name}&version={version}
#        with one matching entry to the specified disease_name

#        :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
#        :param sponge_db_version:       version of the database
#        :return:            dataset matching ID
#        """

#     if disease_name is None:
#         # Create the list of people from our data
#         query = models.Dataset.query 
#     else:
#         # Get the dataset requested
#         query = models.Dataset.query \
#             .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))
    
#     # filter for db version
#     data = query.filter(models.Dataset.sponge_db_version == sponge_db_version) \
#             .all()

#     # Did we find a dataset?
#     if len(data) > 0:
#         # Serialize the data for the response
#         return models.DatasetSchema(many=True).dump(data)
#     else:
#         abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))


def read_spongeRunInformation(dataset_ID: int = None, disease_name: str = None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /sponge/dataset/spongeRunInformation/?disease_name={disease_name}&sponge_db_version={sponge_db_version}
    with a matching entry to the specifed diesease_name

    :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
    :param sponge_db_version:       sponge_db_version of the database
    :return: all available runs + information for disease of interest
    """

    query = db.select(models.SpongeRun).join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID)
 
    data = _dataset_query(query, sponge_db_version, dataset_ID=dataset_ID, disease_name=disease_name)

    if len(data) > 0:
        # Serialize the data for the response
        return models.SpongeRunSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": 'No data found for name: {disease_name}'.format(disease_name=disease_name),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
