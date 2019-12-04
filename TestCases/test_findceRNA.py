from config import *
import models, geneInteraction, unittest
from flask import abort
from werkzeug.exceptions import HTTPException

def test_read_all_gene_network_analysis(disease_name=None, gene_type=None, betweenness=None, degree=None, eigenvector=None,
                                   sorting=None, descending=True, limit=15000, offset=0):
    """
    This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findAll/networkAnalysis
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved and satisfies the given filters
    :param disease_name: isease_name of interest
    :param betweenness: betweenness cutoff (>)
    :param degree: degree cutoff (>)
    :param eigenvector: eigenvector cutoff (>)
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :return: all ceRNAInteractions in the dataset of interest that satisfy the given filters
    """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # save all needed queries to get correct results
    queries = []

    # if specific disease_name is given (should be because for this endpoint is it required):
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.networkAnalysis.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    # filter further depending on given statistics cutoffs
    if betweenness is not None:
        queries.append(models.networkAnalysis.betweeness > betweenness)
    if degree is not None:
        queries.append(models.networkAnalysis.node_degree > degree)
    if eigenvector is not None:
        queries.append(models.networkAnalysis.eigenvector > eigenvector)
    if gene_type is not None:
        queries.append(models.Gene.gene_type == gene_type)

    # add all sorting if given:
    sort = [models.networkAnalysis.run_ID]
    if sorting is not None:
        if sorting == "betweenness":
            if descending:
                sort.append(models.networkAnalysis.betweeness.desc())
            else:
                sort.append(models.networkAnalysis.betweeness.asc())
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
        return schema.dump(result).data
    else:
        abort(404, "Not data found that satisfies the given filters")

########################################################################################################################
"""Test Cases for Endpoint /findceRNA"""
########################################################################################################################

class TestDataset(unittest.TestCase):
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
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma',
                                                                      gene_type='protein_coding', limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_betweeness_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', betweenness=5000, sorting="betweenness", descending=True, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', betweenness=5000, sorting="betweenness", descending=True, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_betweeness_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', betweenness=5000, sorting="betweenness", descending=False, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', betweenness=5000, sorting="betweenness", descending=False, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_eigenvector_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', eigenvector=0.5, sorting="eigenvector", descending=True, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', eigenvector=0.5, sorting="eigenvector", descending=True, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_eigenvector_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', eigenvector=0.5, sorting="eigenvector", descending=False, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', eigenvector=0.5, sorting="eigenvector", descending=False, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_degree_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', degree=2500, sorting="degree", descending=True, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', degree=2500, sorting="degree", descending=True, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findceRNA_disease_and_type_and_degree_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', degree=2500, sorting="degree", descending=False, limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_gene_network_analysis(disease_name='bladder urothelial carcinoma', gene_type='protein_coding', degree=2500, sorting="degree", descending=False, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)
