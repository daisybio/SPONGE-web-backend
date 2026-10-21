from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
import json
with app.app_context():
    import expressionValues
from flask import jsonify, Response
from app.controllers.dataset import _dataset_query


def mock_get_gene_expr(dataset_ID=None, disease_name=None, disease_subtype=None, ensg_number=None,
                       gene_symbol=None, sponge_db_version=LATEST):
    """
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param sponge_db_version: database version
    :return: all expression values for the genes of interest
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
            "detail": "More than one identification parameter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    gene = []
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
    else:
        return jsonify({
            "detail": "No gene(s) found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries = [models.GeneExpressionValues.gene_ID.in_(gene_IDs)]

    dataset = _dataset_query(dataset_ID=dataset_ID, disease_name=disease_name,
                             disease_subtype=disease_subtype, sponge_db_version=sponge_db_version)

    if len(dataset) > 0:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.GeneExpressionValues.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": f"No dataset with given disease_name for the database version {sponge_db_version} found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.GeneExpressionValues.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.geneExpressionSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def _normalize_gene_expr_response(api_response):
    """Controller streams JSON on success; mock returns a dumped list."""
    if isinstance(api_response, Response):
        return json.loads(api_response.get_data(as_text=True))
    return api_response

########################################################################################################################
"""Test Cases for Endpoint /exprValue/getceRNA"""
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
        result = expressionValues.get_gene_expr(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_gene_expr(ensg_number=["ENSGfobar", "ENSGbarfoo"])
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_gene_expr(gene_symbol=["foobar", "barfoo"])
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_symbol_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_gene_expr(
            ensg_number=["ENSGfobar", "ENSGbarfoo"], gene_symbol=["foobar", "barfoo"])
        self.assertEqual(result[1], 400)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_gene_expr(
            disease_name="foobar", ensg_number=["ENSGfobar", "ENSGbarfoo"])
        self.assertEqual(result[1], 400)

    def test_get_expr_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_gene_expr(
            disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000078237'])
        api_response = _normalize_gene_expr_response(
            expressionValues.get_gene_expr(
                disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000078237']))
        assert_payloads_equal(self, mock_response, api_response)

    def test_get_expr_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_gene_expr(
            disease_name='bladder urothelial carcinoma', gene_symbol=['TIGAR'])
        api_response = _normalize_gene_expr_response(
            expressionValues.get_gene_expr(
                disease_name='bladder urothelial carcinoma', gene_symbol=['TIGAR']))
        assert_payloads_equal(self, mock_response, api_response)
