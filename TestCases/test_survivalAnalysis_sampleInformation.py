from app.config import app, db, LATEST
from werkzeug.exceptions import HTTPException
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import survivalAnalysis
from flask import jsonify
from app.controllers.dataset import _dataset_query


def mock_get_patient_information(dataset_ID=None, disease_name=None, disease_subtype=None, sample_ID=None):
    """
      :param disease_name: disease_name of interest
      :param sample_ID: sample ID of the patient of interest
      :return: all patient information for the samples of interest
    """
    query = db.select(models.PatientInformation)

    dataset = _dataset_query(disease_name=disease_name, disease_subtype=disease_subtype,
                             dataset_ID=dataset_ID, sponge_db_version=1)

    if len(dataset) > 0 and getattr(dataset[0], 'dataset_ID', None) is not None:
        dataset_IDs = [i.dataset_ID for i in dataset]
        query = query.where(models.PatientInformation.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if sample_ID is not None:
        query = query.where(models.PatientInformation.sample_ID.in_(sample_ID))

    result = db.session.execute(query).scalars().all()

    if len(result) > 0:
        return models.PatientInformationSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


########################################################################################################################
"""Test Cases for Endpoint /survivalAnalysis/sampleInformation"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = survivalAnalysis.get_patient_information(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_sample_ID(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        # Without disease_name, _dataset_query still returns datasets (v1); invalid sample yields empty 200
        result = survivalAnalysis.get_patient_information(sample_ID=["foobar"])
        self.assertEqual(result[1], 200)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = survivalAnalysis.get_patient_information(
            disease_name="bladder urothelial carcinoma", sample_ID=["foobar"])
        self.assertEqual(result[1], 200)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_patient_information(
            disease_name='bladder urothelial carcinoma', sample_ID=['TCGA-BT-A20T'])
        api_response = survivalAnalysis.get_patient_information(
            disease_name='bladder urothelial carcinoma', sample_ID=['TCGA-BT-A20T'])
        assert_payloads_equal(self, mock_response, api_response)
