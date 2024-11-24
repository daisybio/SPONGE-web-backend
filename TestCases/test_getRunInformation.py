from config import *
import models, unittest
with app.app_context(): 
    import dataset
from flask import abort
from werkzeug.exceptions import HTTPException

def test_read_runInformation(disease_name=None):
    """
    This function responds to a request for /sponge/runInformation/?disease_name={disease_name}
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
        return models.SpongeRunSchema(many=True).dump(data)
    else:
        abort(404, 'No data found for name: {disease_name}'.format(disease_name=disease_name))

########################################################################################################################
"""Test Cases for Endpoint /dataset​/runInformation"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_get_dataset_information(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_runInformation(disease_name="breast invasive carcinoma")

        # retrieve current API response to request
        api_response = dataset.read_spongeRunInformation(disease_name="breast invasive carcinoma")

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    # Ensure that an invalid accept header type will return a 406
    def test_get_dataset_infomration_404(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(dataset.read_spongeRunInformation(disease_name="foobar"), 404)