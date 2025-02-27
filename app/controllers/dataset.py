from flask import jsonify
import app.models as models
from app.config import LATEST, db, logger


def _dataset_query(query = None, sponge_db_version = LATEST, **kwargs):
    
    if query is None: 
        query = db.select(models.Dataset)
    for key, value in kwargs.items():
        if type(value) == str:
            query = query.where(getattr(models.Dataset, key).like("%" + value + "%"))
        elif type(value) == int:
            query = query.where(getattr(models.Dataset, key) == value)
        elif type(value) == list:
            query = query.where(getattr(models.Dataset, key).in_(value))
        elif value is None:
            if key == 'disease_subtype':
                query = query.where(models.Dataset.disease_subtype.is_(None))
            else: 
                continue
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


def get_datasets(dataset_ID: int = None, disease_name: str = None, data_origin=None, sponge_db_version: int = LATEST):
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

    data = _dataset_query(query, sponge_db_version, dataset_ID=dataset_ID, disease_name=disease_name, data_origin=data_origin)

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
