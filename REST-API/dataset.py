from multiprocessing import Process

from flask import abort

import models


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


def read_runInformation(disease_name=None):
    """
    This function responds to a request for /sponge/runInformation/?disease_name={disease_name}
    with a matching entry to the specifed diesease_name

    :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
    :return: all available runs + information for disease of interest
    """

    data = models.Run.query \
        .join(models.Dataset, models.Run.dataset_ID == models.Dataset.dataset_ID) \
        .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
        .all()

    print(data)

    if len(data) > 0:
        # Serialize the data for the response
        # dataset_schema = models.AllRunInformationSchema(many=True)
        # return dataset_schema.dump([{'run': x[0], 'target_databases': x[1], "selected_genes": x[2]} for x in data]).data
        return models.RunSchema(many=True).dump(data).data
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))
