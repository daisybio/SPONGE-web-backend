from app.config import *
import app.models as models, unittest
with app.app_context(): 
    import geneInteraction
from flask import abort
from werkzeug.exceptions import HTTPException

def test_read_all_gene_network_analysis(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None,
                                   minBetweenness=None, minNodeDegree=None, minEigenvector=None,
                                   sorting=None, descending=True, limit=100, offset=0, db_version=2):
    """
    This function responds to a request for /sponge/findceRNA
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
    :param disease_name: isease_name of interest
    :param gene_type: defines the type of gene of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param minBetweenness: betweenness cutoff (>)
    :param minNodeDegree: degree cutoff (>)
    :param minEigenvector: eigenvector cutoff (>)
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    :db_version: database version
    """

    # test limit
    if limit > 1000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # save all needed queries to get correct results
    queries = []

    # if specific disease_name is given (should be because for this endpoint is it required):
    if disease_name is not None:
        run = models.SpongeRun.query.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.sponge_run_ID for i in run]
            queries.append(models.networkAnalysis.sponge_run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    gene = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries.append(models.networkAnalysis.gene_ID.in_(gene_IDs))
        else:
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # filter further depending on given statistics cutoffs
    if minBetweenness is not None:
        queries.append(models.networkAnalysis.betweenness > minBetweenness)
    if minNodeDegree is not None:
        queries.append(models.networkAnalysis.node_degree > minNodeDegree)
    if minEigenvector is not None:
        queries.append(models.networkAnalysis.eigenvector > minEigenvector)
    if gene_type is not None:
        queries.append(models.Gene.gene_type == gene_type)
    if db_version is not None: 
        queries.append(models.Dataset.sponge_db_version == db_version)

    # add all sorting if given:
    sort = [models.networkAnalysis.sponge_run_ID]
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
        abort(404, "Not data found that satisfies the given filters")

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

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_gene_network_analysis(disease_name="foobar"), 404)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_gene_network_analysis(disease_name="foobar", limit = 20000), 404)

    def test_abort_error_gene_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_gene_network_analysis(gene_type="foobar"), 404)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_gene_network_analysis(disease_name="bladder urothelial carcinoma", gene_type='lincRNA'), 404)

    def test_findceRNA_disease_and_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', limit=50, db_version=1)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma',
                                                                      gene_type='protein_coding', limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_betweenness_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minBetweenness=5000, sorting="betweenness", descending=True, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minBetweenness=5000, sorting="betweenness", descending=True, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_betweenness_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minBetweenness=5000, sorting="betweenness", descending=False, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minBetweenness=5000, sorting="betweenness", descending=False, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_eigenvector_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minEigenvector=0.5, sorting="eigenvector", descending=True, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minEigenvector=0.5, sorting="eigenvector", descending=True, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_eigenvector_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minEigenvector=0.5, sorting="eigenvector", descending=False, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minEigenvector=0.5, sorting="eigenvector", descending=False, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_degree_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minNodeDegree=2500, sorting="degree", descending=True, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minNodeDegree=2500, sorting="degree", descending=True, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_degree_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minNodeDegree=2500, sorting="degree", descending=False, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', minNodeDegree=2500, sorting="degree", descending=False, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)
