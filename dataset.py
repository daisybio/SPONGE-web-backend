from flask import abort
import models
from config import LATEST, db


def get_datasets(dataset_id: str = None, disease_name: str = None, data_origin=None, sponge_db_version: int = LATEST):
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

    # Filter if provided
    if dataset_id is not None:
        query = query.where(models.Dataset.dataset_ID == dataset_id)
    if disease_name is not None:
        query = query.where(models.Dataset.disease_name.like("%" + disease_name + "%"))
    if data_origin is not None:
        query = query.where(models.Dataset.data_origin.like("%" + data_origin + "%"))

    # filter for db version 
    query = query.where(models.Dataset.sponge_db_version == sponge_db_version)

    data = db.session.execute(query).scalars().all()

    # Did we find a source?
    if len(data) > 0:
        # Serialize the data for the response
        return models.DatasetSchema(many=True).dump(data)
    else:
        abort(404, 'No data found for \
              name: {data_origin}'.format(data_origin=data_origin))

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


def read_spongeRunInformation(disease_name=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /sponge/spongeRunInformation/?disease_name={disease_name}&version={version}
    with a matching entry to the specifed diesease_name

    :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
    :param sponge_db_version:       sponge_db_version of the database
    :return: all available runs + information for disease of interest
    """

    data = models.SpongeRun.query \
        .join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID) \
        .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
        .filter(models.Dataset.sponge_db_version == sponge_db_version) \
        .all()

    if len(data) > 0:
        # Serialize the data for the response
        return models.SpongeRunSchema(many=True).dump(data)
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))
