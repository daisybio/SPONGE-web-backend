from config import *
import models, expressionValues, unittest
from flask import abort
from werkzeug.exceptions import HTTPException

def test_get_mirna_expr(disease_name=None, mimat_number=None, hs_number=None):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :return: all expression values for the mimats of interest
    """

    # test if any of the two identification possibilites is given
    if mimat_number is None and hs_number is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if mimat_number is not None and hs_number is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    mirna = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()

    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
    else:
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # save all needed queries to get correct results
    queries = [models.MiRNAExpressionValues.miRNA_ID.in_(mirna_IDs)]

    # if specific disease_name is given:
    if disease_name is not None:
        dataset = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            queries.append(models.MiRNAExpressionValues.dataset_ID.in_(dataset_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    result = models.MiRNAExpressionValues.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.miRNAExpressionSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")

########################################################################################################################
"""Test Cases for Endpoint /exprValue/getceRNA"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(expressionValues.get_mirna_expr(disease_name="foobar"), 404)

    def test_abort_error_mimat(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(expressionValues.get_mirna_expr(mimat_number=["mirfobar", "mirbarfoo"]), 404)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(expressionValues.get_mirna_expr(hs_number=["hs-foobar", "hs-barfoo"]), 404)

    def test_abort_error_mimat_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(expressionValues.get_mirna_expr(mimat_number=["mirfobar", "mirbarfoo"], hs_number=["hs-foobar", "hs-barfoo"]), 404)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(expressionValues.get_mirna_expr(disease_name="foobar",mimat_number=["mirfobar", "mirbarfoo"]), 404)

    def test_get_expr_mimat(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_get_mirna_expr(disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000062'])

        # retrieve current API response to request
        api_response = expressionValues.get_mirna_expr(disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000062'])

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_get_expr_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_get_mirna_expr(disease_name='bladder urothelial carcinoma', hs_number=['hsa-let-7a-5p'])

        # retrieve current API response to request
        api_response = expressionValues.get_mirna_expr(disease_name='bladder urothelial carcinoma', hs_number=['hsa-let-7a-5p'])

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)