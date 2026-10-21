from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import geneInteraction
from flask import jsonify


def mock_read_all_genes(dataset_ID=None, disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None,
                        pValue=0.05, pValueDirection="<", mscor=None, mscorDirection="<", correlation=None,
                        correlationDirection="<", sorting=None, descending=True, limit=100, offset=0,
                        information=True, sponge_db_version=LATEST):
    """
    This function responds to a request for /sponge/ceRNAInteraction/findAll
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
    """
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        return jsonify({
            "detail": "More than one identification paramter is given. Please choose one out of (ensg number, gene symbol or gene type)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries_1 = []
    queries_2 = []

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
        queries_1.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
        queries_2.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name / dataset_ID found",
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
    elif gene_type is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_type == gene_type) \
            .all()

    if ensg_number is not None or gene_symbol is not None or gene_type is not None:
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries_1.append(models.GeneInteraction.gene_ID1.in_(gene_IDs))
            queries_2.append(models.GeneInteraction.gene_ID2.in_(gene_IDs))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    if pValue is not None:
        if pValueDirection == "<":
            queries_1.append(models.GeneInteraction.p_value <= pValue)
            queries_2.append(models.GeneInteraction.p_value <= pValue)
        else:
            queries_1.append(models.GeneInteraction.p_value >= pValue)
            queries_2.append(models.GeneInteraction.p_value >= pValue)
    if mscor is not None:
        if mscorDirection == "<":
            queries_1.append(models.GeneInteraction.mscor <= mscor)
            queries_2.append(models.GeneInteraction.mscor <= mscor)
        else:
            queries_1.append(models.GeneInteraction.mscor >= mscor)
            queries_2.append(models.GeneInteraction.mscor >= mscor)
    if correlation is not None:
        if correlationDirection == "<":
            queries_1.append(models.GeneInteraction.correlation <= correlation)
            queries_2.append(models.GeneInteraction.correlation <= correlation)
        else:
            queries_1.append(models.GeneInteraction.correlation >= correlation)
            queries_2.append(models.GeneInteraction.correlation >= correlation)

    sort = []
    if sorting is not None:
        if sorting == "pValue":
            if descending:
                sort.append(models.GeneInteraction.p_value.desc())
            else:
                sort.append(models.GeneInteraction.p_value.asc())
        if sorting == "mscor":
            if descending:
                sort.append(models.GeneInteraction.mscor.desc())
            else:
                sort.append(models.GeneInteraction.mscor.asc())
        if sorting == "correlation":
            if descending:
                sort.append(models.GeneInteraction.correlation.desc())
            else:
                sort.append(models.GeneInteraction.correlation.asc())

    sort.extend([
        models.GeneInteraction.sponge_run_ID.asc(),
        models.GeneInteraction.gene_ID1.asc(),
        models.GeneInteraction.gene_ID2.asc(),
    ])

    interaction_result = models.GeneInteraction.query \
        .filter(*queries_1) \
        .union(models.GeneInteraction.query
               .filter(*queries_2)) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        if information:
            schema = models.GeneInteractionDatasetLongSchema(many=True)
        else:
            schema = models.GeneInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_result)
    else:
        return jsonify({
            "detail": "No information with given parameters found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

########################################################################################################################
"""Test Cases for Endpoint /ceRNAInteraction/findAll"""
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
        result = geneInteraction.read_all_genes(disease_name="foobar", pValue=None)
        self.assertEqual(result[1], 400)

    def test_abort_error_limit(self):
        result = geneInteraction.read_all_genes(disease_name="foobar", limit=20000, pValue=None)
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg(self):
        result = geneInteraction.read_all_genes(ensg_number=["ENSGfoobar"], pValue=None)
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_symbol(self):
        result = geneInteraction.read_all_genes(gene_symbol=["foobar"], pValue=None)
        self.assertEqual(result[1], 400)

    def test_abort_error_ensg_and_gene_symbol(self):
        result = geneInteraction.read_all_genes(
            ensg_number=["ENSGfoobar"], gene_symbol=["foobar"], pValue=None)
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_type(self):
        result = geneInteraction.read_all_genes(gene_type="foobar", pValue=None)
        self.assertEqual(result[1], 400)

    def test_abort_error_no_data(self):
        result = geneInteraction.read_all_genes(
            disease_name="bladder urothelial carcinoma",
            ensg_number=['ENSG00000023041'], pValue=None)
        self.assertEqual(result[1], 200)

    def test_findAll_disease_and_ensg(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_ensg_pValue_smaller(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            pValue=0.5, pValueDirection="<", sorting="pValue")
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            pValue=0.5, pValueDirection="<", sorting="pValue")
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_ensg_pValue_greater(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            pValue=0.5, pValueDirection=">", sorting="pValue")
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            pValue=0.5, pValueDirection=">", sorting="pValue")
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_pValue_smaller(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            pValue=0.5, pValueDirection="<", sorting="pValue")
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            pValue=0.5, pValueDirection="<", sorting="pValue")
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_pValue_greater(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            pValue=0.5, pValueDirection=">", sorting="pValue")
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            pValue=0.5, pValueDirection=">", sorting="pValue")
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_ensg_correlation_smaller(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            correlation=0.2, correlationDirection="<", sorting="correlation", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            correlation=0.2, correlationDirection="<", sorting="correlation", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_ensg_correlation_greater(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            correlation=0.1, correlationDirection=">", sorting="correlation", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            correlation=0.1, correlationDirection=">", sorting="correlation", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_correlation_smaller(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            correlation=0.2, correlationDirection="<", sorting="correlation", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            correlation=0.2, correlationDirection="<", sorting="correlation", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_correlation_greater(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            correlation=0.1, correlationDirection=">", sorting="correlation", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            correlation=0.1, correlationDirection=">", sorting="correlation", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_ensg_mscor_smaller(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            mscor=0.02, mscorDirection="<", sorting="mscor", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            mscor=0.02, mscorDirection="<", sorting="mscor", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_ensg_mscor_greater(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            mscor=0.01, mscorDirection=">", sorting="mscor", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50,
            mscor=0.01, mscorDirection=">", sorting="mscor", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_mscor_smaller(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            mscor=0.02, mscorDirection="<", sorting="mscor", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            mscor=0.02, mscorDirection="<", sorting="mscor", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_mscor_greater(self):
        mock_response = mock_read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            mscor=0.01, mscorDirection=">", sorting="mscor", pValue=None)
        api_response = geneInteraction.read_all_genes(
            disease_name='bladder urothelial carcinoma',
            gene_symbol=['CALB2', 'TIGAR'], limit=50,
            mscor=0.01, mscorDirection=">", sorting="mscor", pValue=None)
        assert_payloads_equal(self, mock_response, api_response)
