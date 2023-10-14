from flask import abort
import models


def get_datasets(data_origin=None):
    """
       This function responds to a request for /sponge/datasets?data_origin={data_origin}
       with one matching entry to the specified data_origin

       :param data_origin:   name of the data source
       :return:            all datasets that match the source (e.g. TCGA)
    """
    # version is hardcoded since version 1 does not have spongEffects scores for transcripts
    sponge_db_version: int = 2
    if data_origin is None:
        # Create the list of people from our data
        data = models.Dataset.query \
            .all()
    else:
        # Get the dataset requested
        data = models.SpongeRun.query \
            .join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.data_origin.like("%" + data_origin + "%")) \
            .filter(models.SpongeRun.sponge_db_version == sponge_db_version) \
            .all()

    # Did we find a source?
    if len(data) > 0:
        # Serialize the data for the response
        return models.DatasetDetailedSchema(many=True).dump(data).data
    else:
        abort(404, 'No data found for name: {data_origin}'.format(data_origin=data_origin))

def read(disease_name=None):
    """
       This function responds to a request for /sponge/dataset/?disease_name={disease_name}
       with one matching entry to the specifed diesease_name

       :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
       :return:            dataset matching ID
       """

    if disease_name is None:
        # Create the list of people from our data
        data = models.Dataset.query \
            .all()
    else:
        # Get the dataset requested
        data = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

    # Did we find a dataset?
    if len(data) > 0:
        # Serialize the data for the response
        return models.DatasetSchema(many=True).dump(data).data
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))


def read_spongeRunInformation(disease_name=None):
    """
    This function responds to a request for /sponge/spongeRunInformation/?disease_name={disease_name}
    with a matching entry to the specifed diesease_name

    :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
    :return: all available runs + information for disease of interest
    """

    data = models.SpongeRun.query \
        .join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID) \
        .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
        .all()

    if len(data) > 0:
        # Serialize the data for the response
        return models.SpongeRunSchema(many=True).dump(data).data
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))