from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import geneInteraction
from flask import jsonify


def mock_read_all_gene_network_analysis(dataset_ID=None, disease_name=None, ensg_number=None, gene_symbol=None,
                                       gene_type=None, minBetweenness=None, minNodeDegree=None, minEigenvector=None,
                                       sorting=None, descending=True, limit=100, offset=0,
                                       sponge_db_version=LATEST):
    """
    This function responds to a request for /sponge/findceRNA
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
    """
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    queries = []

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
        queries.append(models.networkAnalysis.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identification paramter is given. Please choose one.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            return jsonify({
                "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    if minBetweenness is not None:
        queries.append(models.networkAnalysis.betweenness > minBetweenness)
    if minNodeDegree is not None:
        queries.append(models.networkAnalysis.node_degree > minNodeDegree)
    if minEigenvector is not None:
        queries.append(models.networkAnalysis.eigenvector > minEigenvector)
    if gene_type is not None:
        queries.append(models.Gene.gene_type == gene_type)

    sort = [models.networkAnalysis.sponge_run_ID, models.networkAnalysis.gene_ID]
    if sorting is not None:
        if sorting == "betweenness":
            if descending:
                sort.append(models.networkAnalysis.betweenness.desc())
            else:
                sort.append(models.networkAnalysis.betweenness.asc())
        if sorting == "degree":
            if descending:
                sort.append(models.networkAnalysis.node_degree.desc())
            else:
                sort.append(models.networkAnalysis.node_degree.asc())
        if sorting == "eigenvector":
            if descending:
                sort.append(models.networkAnalysis.eigenvector.desc())
            else:
                sort.append(models.networkAnalysis.eigenvector.asc())

    result = models.networkAnalysis.query \
        .join(models.Gene, models.Gene.gene_ID == models.networkAnalysis.gene_ID) \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(result) > 0:
        schema = models.networkAnalysisSchema(many=True)
        return schema.dump(result)
    else:
        return jsonify({
            "detail": "No data found that satisfies the given filters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

########################################################################################################################
"""Test Cases for Endpoint /findceRNA"""
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
        result = geneInteraction.read_all_gene_network_analysis(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_gene_network_analysis(disease_name="foobar", limit=20000)
        self.assertEqual(result[1], 400)

    def test_abort_error_gene_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        # No disease filter: runs for LATEST version exist; bogus gene_type yields empty 200
        result = geneInteraction.read_all_gene_network_analysis(gene_type="foobar")
        self.assertEqual(result[1], 200)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_gene_network_analysis(
            disease_name="bladder urothelial carcinoma", gene_type='vaultRNA')
        self.assertEqual(result[1], 200)

    def test_findceRNA_disease_and_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding', limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding', limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findceRNA_disease_and_type_and_betweenness_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minBetweenness=5000, sorting="betweenness", descending=True, limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minBetweenness=5000, sorting="betweenness", descending=True, limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findceRNA_disease_and_type_and_betweenness_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minBetweenness=5000, sorting="betweenness", descending=False, limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minBetweenness=5000, sorting="betweenness", descending=False, limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findceRNA_disease_and_type_and_eigenvector_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minEigenvector=0.5, sorting="eigenvector", descending=True, limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minEigenvector=0.5, sorting="eigenvector", descending=True, limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findceRNA_disease_and_type_and_eigenvector_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minEigenvector=0.5, sorting="eigenvector", descending=False, limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minEigenvector=0.5, sorting="eigenvector", descending=False, limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findceRNA_disease_and_type_and_degree_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minNodeDegree=2500, sorting="degree", descending=True, limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minNodeDegree=2500, sorting="degree", descending=True, limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_findceRNA_disease_and_type_and_degree_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minNodeDegree=2500, sorting="degree", descending=False, limit=50)
        api_response = geneInteraction.read_all_gene_network_analysis(
            disease_name='bladder urothelial carcinoma', gene_type='protein_coding',
            minNodeDegree=2500, sorting="degree", descending=False, limit=50)
        assert_payloads_equal(self, mock_response, api_response)
