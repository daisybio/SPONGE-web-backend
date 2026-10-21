from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import dataset
from app.controllers.dataset import _dataset_query
from flask import jsonify


def mock_get_datasets(dataset_ID=None, disease_name=None, disease_subtype=None, data_origin=None,
                      sponge_db_version=LATEST):
    """
       This function responds to a request for /sponge/dataset/?disease_name={disease_name}
       with one matching entry to the specifed diesease_name

       :param disease_name:   name of the dataset to find (if not given, all available datasets will be shown)
       :return:            dataset matching ID
       """
    query = db.select(models.Dataset)
    data = _dataset_query(
        query, sponge_db_version,
        dataset_ID=dataset_ID, disease_name=disease_name,
        disease_subtype=disease_subtype, data_origin=data_origin,
    )

    if len(data) > 0:
        return models.DatasetSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": 'No data found for name: {data_origin}'.format(data_origin=data_origin),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

########################################################################################################################
"""Test Cases for Endpoint /dataset"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_get_dataset_information_all(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_datasets()
        api_response = dataset.get_datasets()
        assert_payloads_equal(self, mock_response, api_response)

    def test_get_dataset_information_specific(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_datasets(disease_name="breast invasive carcinoma")
        api_response = dataset.get_datasets(disease_name="breast invasive carcinoma")
        assert_payloads_equal(self, mock_response, api_response)

    def test_get_dataset_infomration_404(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        result = dataset.get_datasets(disease_name="foobar")
        self.assertEqual(result[1], 200)
