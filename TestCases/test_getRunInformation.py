from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import dataset
from app.controllers.dataset import _dataset_query
from flask import jsonify


def mock_read_runInformation(dataset_ID=None, disease_name=None, sponge_db_version=LATEST):
    """
    This function responds to a request for /sponge/runInformation/?disease_name={disease_name}
    with a matching entry to the specifed diesease_name

    :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
    :return: all available runs + information for disease of interest
    """
    query = db.select(models.SpongeRun).join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID)
    data = _dataset_query(query, sponge_db_version, dataset_ID=dataset_ID, disease_name=disease_name)

    if len(data) > 0:
        return models.SpongeRunSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": 'No data found for name: {disease_name}'.format(disease_name=disease_name),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

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

        mock_response = mock_read_runInformation(disease_name="breast invasive carcinoma")
        api_response = dataset.read_spongeRunInformation(disease_name="breast invasive carcinoma")
        assert_payloads_equal(self, mock_response, api_response)

    def test_get_dataset_infomration_404(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        result = dataset.read_spongeRunInformation(disease_name="foobar")
        self.assertEqual(result[1], 200)
