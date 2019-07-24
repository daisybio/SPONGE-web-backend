from flask import (
    make_response,
    abort,
)
from config import db
from models import (
    Dataset,
    DatasetSchema,
)

def read_all():
    """
        This function responds to a request for /sponge/dataset
        with the complete lists of people

        :return:        json string of list of people
        """
    # Create the list of people from our data
    dataset = Dataset.query \
        .all()

    # Serialize the data for the response
    dataset_schema = DatasetSchema(many=True)
    return dataset_schema.dump(dataset).data

def read_one(disease_name):
    """
    This function responds to a request for /sponge/dataset/{disease_name}
    with one matching person from people

    :param disease_name:   name of the dataset to find
    :return:            dataset matching ID
    """
    # Get the person requested
    data = Dataset.query \
        .filter(Dataset.disease_name == disease_name) \
        .one_or_none()

    # Did we find a dataset?
    if data is not None:
        # Serialize the data for the response
        dataset_schema = DatasetSchema()
        return dataset_schema.dump(data).data

    # Otherwise, nope, didn't find that person
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))

def read(disease_name = None):
    """
       This function responds to a request for /sponge/?dataset={disease_name}
       with one matching entry to the specifed diesease_name

       :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
       :return:            dataset matching ID
       """

    if disease_name is None:
        # Create the list of people from our data
        dataset = Dataset.query \
            .all()

        # Serialize the data for the response
        dataset_schema = DatasetSchema(many=True)
        return dataset_schema.dump(dataset).data
    else:
        # Get the person requested
        data = Dataset.query \
            .filter(Dataset.disease_name == disease_name) \
            .one_or_none()

        # Did we find a dataset?
        if data is not None:
            # Serialize the data for the response
            dataset_schema = DatasetSchema()
            return dataset_schema.dump(data).data

        # Otherwise, nope, didn't find that person
        else:
            abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))



