from config import *
import models, geneInteraction, unittest
from flask import abort
import sqlalchemy as sa
from werkzeug.exceptions import HTTPException

def test_read_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, limit=15000, offset=0):
    """
      This function responds to a request for /sponge/ceRNAInteraction/findSpecific
      and returns all interactions between the given identifications (ensg_number or gene_symbol)
      :param disease_name: disease_name of interest
      :param ensg_number: esng number of the genes of interest
      :param gene_symbol: gene symbol of the genes of interest
      :param limit: number of results that shouls be shown
      :param offset: startpoint from where results should be shown
      :return: all interactions between given genes
      """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    gene = []
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
    else:
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # save all needed queries to get correct results
    queries = [sa.and_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs))]

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    interaction_result = models.GeneInteraction.query \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.GeneInteractionDatasetShortSchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")

########################################################################################################################
"""Test Cases for Endpoint /ceRNAInteraction/findSpecific"""
########################################################################################################################

class TestDataset(unittest.TestCase):
    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_specific_interaction(disease_name="foobar"), 404)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_specific_interaction(disease_name="foobar", limit = 20000), 404)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_specific_interaction(ensg_number=["ENSGfoobar"]), 404)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_specific_interaction(gene_symbol=["foobar"]), 404)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_specific_interaction(ensg_number=["ENSGfoobar"],gene_symbol=["foobar"]), 404)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_specific_interaction(disease_name="bladder urothelial carcinoma", ensg_number=['ENSG00000023041']), 404)

    def test_findSpecific_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_specific_interaction(disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000172137','ENSG00000078237'], limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_specific_interaction(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findSpecific_disease_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_specific_interaction(disease_name='bladder urothelial carcinoma', gene_symbol=['CALB2','TIGAR'], limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_specific_interaction(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)