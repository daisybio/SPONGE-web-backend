from app.config import app, db, LATEST
from werkzeug.exceptions import HTTPException
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import survivalAnalysis
from flask import jsonify
from app.controllers.dataset import _dataset_query


def mock_get_survival_pValue(dataset_ID=None, disease_name=None, disease_subtype=None,
                             ensg_number=None, gene_symbol=None):
    """
          :param disease_name: disease_name of interest
          :param ensg_number: esng number of the gene of interest
          :param gene_symbol: gene symbol of the gene of interest
          :return: all pValues for genes of interest for plotting kaplan meier plots
          """
    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = []
    queries = []
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
        queries.append(models.SurvivalPValue.gene_ID.in_(gene_IDs))
    else:
        return jsonify({
            "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    dataset = _dataset_query(disease_name=disease_name, disease_subtype=disease_subtype,
                             dataset_ID=dataset_ID, sponge_db_version=1)

    if len(dataset) > 0 and getattr(dataset[0], 'dataset_ID', None) is not None:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.SurvivalPValue.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.SurvivalPValue.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.SurvivalPValueSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

########################################################################################################################
"""Test Cases for Endpoint /survivalAnalysis/getPValue"""
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
        result = survivalAnalysis.get_survival_pValue(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = survivalAnalysis.get_survival_pValue(
            disease_name="bladder urothelial carcinoma", ensg_number=["ENSGfoobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = survivalAnalysis.get_survival_pValue(
            disease_name="bladder urothelial carcinoma", gene_symbol=["foobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = survivalAnalysis.get_survival_pValue(
            disease_name="bladder urothelial carcinoma",
            ensg_number=["ENSGfoobar"], gene_symbol=["foobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = survivalAnalysis.get_survival_pValue(
            disease_name="bladder urothelial carcinoma", ensg_number=['ENSG00000214976'])
        self.assertEqual(result[1], 200)

    def test_surivalAnalysis_getPValue_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_survival_pValue(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000242268', 'ENSG00000078237'])
        api_response = survivalAnalysis.get_survival_pValue(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000242268', 'ENSG00000078237'])
        assert_payloads_equal(self, mock_response, api_response)

    def test_surivalAnalysis_getPValue_disease_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_survival_pValue(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['LINC02082', 'TIGAR'])
        api_response = survivalAnalysis.get_survival_pValue(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['LINC02082', 'TIGAR'])
        assert_payloads_equal(self, mock_response, api_response)
