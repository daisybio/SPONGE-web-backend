from config import *
from werkzeug.exceptions import HTTPException
import models, survivalAnalysis, unittest
from flask import abort

def test_get_patient_information(disease_name=None, sample_ID=None):
    """
      :param disease_name: disease_name of interest
      :param sample_ID: sample ID of the patient of interest
      :return: all patient information for the samples of interest
    """

    # if specific disease_name is given:
    if disease_name is not None:
        dataset = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            queries = [models.PatientInformation.dataset_ID.in_(dataset_IDs)]
        else:
            abort(404, "No dataset with given disease_name found")

    if (sample_ID is not None):
        queries = [models.PatientInformation.sample_ID.in_(sample_ID)]

    result = models.PatientInformation.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.PatientInformationSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")


########################################################################################################################
"""Test Cases for Endpoint /survivalAnalysis/sampleInformation"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_patient_information(disease_name="foobar"), 404)

    def test_abort_error_sample_ID(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_patient_information(sample_ID="foobar"), 404)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_patient_information(disease_name = "bladder urothelial carcinoma", sample_ID="foobar"), 404)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_get_patient_information(disease_name='bladder urothelial carcinoma', sample_ID=['TCGA-BT-A20T'])

        # retrieve current API response to request
        api_response = survivalAnalysis.get_patient_information(disease_name='bladder urothelial carcinoma', sample_ID=['TCGA-BT-A20T'])
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)