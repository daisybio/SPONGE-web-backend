from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import expressionValues
from flask import jsonify


def mock_get_mirna_expr(dataset_ID=None, disease_name=None, mimat_number=None, hs_number=None,
                        sponge_db_version=LATEST):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :return: all expression values for the mimats of interest
    """
    if mimat_number is None and hs_number is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if mimat_number is not None and hs_number is not None:
        return jsonify({
            "detail": "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    mirna = []
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
        return jsonify({
            "detail": "No miRNA(s) found for given mimat_number(s) or hs_number(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries = [models.MiRNAExpressionValues.miRNA_ID.in_(mirna_IDs)]

    dataset_query = models.Dataset.query.filter(models.Dataset.sponge_db_version == sponge_db_version)

    if disease_name is not None:
        dataset_query = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        dataset_query = dataset_query \
            .filter(models.Dataset.dataset_ID == dataset_ID)

    dataset = dataset_query.all()

    if len(dataset) > 0:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.MiRNAExpressionValues.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": f"No dataset with given disease_name for the database version {sponge_db_version} found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.MiRNAExpressionValues.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.miRNAExpressionSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results.",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

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
        result = expressionValues.get_mirna_expr(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_mimat(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_mirna_expr(mimat_number=["mirfobar", "mirbarfoo"])
        self.assertEqual(result[1], 400)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_mirna_expr(hs_number=["hs-foobar", "hs-barfoo"])
        self.assertEqual(result[1], 400)

    def test_abort_error_mimat_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_mirna_expr(
            mimat_number=["mirfobar", "mirbarfoo"], hs_number=["hs-foobar", "hs-barfoo"])
        self.assertEqual(result[1], 400)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = expressionValues.get_mirna_expr(
            disease_name="foobar", mimat_number=["mirfobar", "mirbarfoo"])
        self.assertEqual(result[1], 400)

    def test_get_expr_mimat(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_mirna_expr(
            disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000062'])
        api_response = expressionValues.get_mirna_expr(
            disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000062'])
        assert_payloads_equal(self, mock_response, api_response)

    def test_get_expr_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_get_mirna_expr(
            disease_name='bladder urothelial carcinoma', hs_number=['hsa-let-7a-5p'])
        api_response = expressionValues.get_mirna_expr(
            disease_name='bladder urothelial carcinoma', hs_number=['hsa-let-7a-5p'])
        assert_payloads_equal(self, mock_response, api_response)
