from config import *
import models, dataset, unittest
from flask import abort
from werkzeug.exceptions import HTTPException

def test_read(disease_name=None):
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

########################################################################################################################
"""Test Cases for Endpoint /dataset"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_get_dataset_information_all(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read()

        # retrieve current API response to request
        api_response = dataset.read()

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_get_dataset_information_specific(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read(disease_name= "breast invasive carcinoma")

        # retrieve current API response to request
        api_response = dataset.read(disease_name= "breast invasive carcinoma")

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    # Ensure that an invalid accept header type will return a 406
    def test_get_dataset_infomration_404(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(dataset.read(disease_name="foobar"), 404)








