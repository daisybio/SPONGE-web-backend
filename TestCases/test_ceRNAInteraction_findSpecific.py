from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import geneInteraction
from flask import jsonify
import sqlalchemy as sa


def mock_read_specific_interaction(dataset_ID=None, disease_name=None, ensg_number=None, gene_symbol=None,
                                   pValue=0.05, pValueDirection="<", limit=100, offset=0,
                                   sponge_db_version=LATEST):
    """
      This function responds to a request for /sponge/ceRNAInteraction/findSpecific
      and returns all interactions between the given identifications (ensg_number or gene_symbol)
      """
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification parameter is given. Please choose one.",
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
            "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries = [sa.and_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs))]

    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.filter(models.SpongeRun.dataset_ID == dataset_ID)

    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if pValue is not None:
        if pValueDirection == "<":
            queries.append(models.GeneInteraction.p_value < pValue)
        else:
            queries.append(models.GeneInteraction.p_value > pValue)

    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        return models.GeneInteractionDatasetShortSchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No information with given parameters found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


########################################################################################################################
"""Test Cases for Endpoint /ceRNAInteraction/findSpecific"""
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
        result = geneInteraction.read_specific_interaction(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_specific_interaction(disease_name="foobar", limit=20000)
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_specific_interaction(ensg_number=["ENSGfoobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_specific_interaction(gene_symbol=["foobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_specific_interaction(
            ensg_number=["ENSGfoobar"], gene_symbol=["foobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_specific_interaction(
            disease_name="bladder urothelial carcinoma", ensg_number=['ENSG00000023041'])
        self.assertEqual(result[1], 200)

    def test_findSpecific_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_specific_interaction(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=1)
        api_response = geneInteraction.read_specific_interaction(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=1)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findSpecific_disease_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_specific_interaction(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=1)
        api_response = geneInteraction.read_specific_interaction(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=1)
        assert_payloads_equal(self, mock_response, api_response)
