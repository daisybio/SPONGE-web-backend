from flask import (
    abort,
)

from models import (
    Dataset,
    DatasetSchema,
)


def read(disease_name = None):
    """
       This function responds to a request for /sponge/?dataset={disease_name}
       with one matching entry to the specifed diesease_name

       :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
       :return:            dataset matching ID
       """

    if disease_name is None:
        # Create the list of people from our data
        data = Dataset.query \
            .all()
    else:
        # Get the dataset requested
        data = Dataset.query \
            .filter(Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        print(data)

    # Did we find a dataset?
    if data is not None:
        # Serialize the data for the response
        dataset_schema = DatasetSchema(many=True)
        return dataset_schema.dump(data).data
    # Otherwise, nope, didn't find that person
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))
