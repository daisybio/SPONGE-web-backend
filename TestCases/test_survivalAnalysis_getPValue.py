from config import *
from werkzeug.exceptions import HTTPException
import models, survivalAnalysis, unittest
from flask import abort

def test_get_survival_pValue(disease_name, ensg_number = None, gene_symbol = None):
    """
          :param disease_name: disease_name of interest
          :param ensg_number: esng number of the gene of interest
          :param gene_symbol: gene symbol of the gene of interest
          :return: all pValues for genes of interest for plotting kaplan meier plots
          """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    gene = []
    queries = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
        # save all needed queries to get correct results
        queries.append(models.SurvivalPValue.gene_ID.in_(gene_IDs))
    else:
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # if specific disease_name is given:
    if disease_name is not None:
        dataset = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            queries.append(models.SurvivalPValue.dataset_ID.in_(dataset_IDs))
        else:
             abort(404, "No dataset with given disease_name found")

    result = models.SurvivalPValue.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.SurvivalPValueSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")

########################################################################################################################
"""Test Cases for Endpoint /survivalAnalysis/getPValue"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_survival_pValue(disease_name="foobar"), 404)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_survival_pValue(disease_name="bladder urothelial carcinoma", ensg_number=["ENSGfoobar"]), 404)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_survival_pValue(disease_name="bladder urothelial carcinoma", gene_symbol=["foobar"]), 404)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_survival_pValue(disease_name="bladder urothelial carcinoma", ensg_number=["ENSGfoobar"],gene_symbol=["foobar"]), 404)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(survivalAnalysis.get_survival_pValue(disease_name="bladder urothelial carcinoma", ensg_number=['ENSG00000023041']), 404)

    def test_surivalAnalysis_getPValue_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_get_survival_pValue(disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000242268','ENSG00000078237'])

        # retrieve current API response to request
        api_response = survivalAnalysis.get_survival_pValue(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000242268', 'ENSG00000078237'])
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_surivalAnalysis_getPValue_disease_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_get_survival_pValue(disease_name='bladder urothelial carcinoma', gene_symbol=['LINC02082','TIGAR'])

        # retrieve current API response to request
        api_response = survivalAnalysis.get_survival_pValue(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['LINC02082', 'TIGAR'])
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)