from config import *
import models, geneInteraction, unittest
from flask import abort
import sqlalchemy as sa
from werkzeug.exceptions import HTTPException

def test_read_mirna_for_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNA
    and returns all miRNAs thar contribute to all interactions between the given identifications (ensg_number or gene_symbol)
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param gene_type: defines the type of gene of interest

    :return: all miRNAs contributing to the interactions between genes of interest
    """
    # test if just one of the possible identifiers is given
    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol or gene type)")

    queries = []
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

    gene = []
    # if ensg_numer is given to specify gene(s), get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
    # if gene_symbol is given to specify gene(s), get the intern gene_ID(primary_key) for requested gene_symbol(gene_ID)
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()
    elif gene_type is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_type == gene_type) \
            .all()

    interaction_IDs = []
    # get requires interaction_ID from database
    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
        queries.append(
            sa.and_(models.GeneInteraction.gene_ID1.in_(gene_IDs), models.GeneInteraction.gene_ID2.in_(gene_IDs)))
        interactions = models.GeneInteraction.query \
            .filter(*queries) \
            .all()
        if len(interactions) > 0:
            interaction_IDs = [i.interactions_genegene_ID for i in interactions]
        else:
            abort(404, "No gene interaction found for given ensg_number(s) or gene_symbol(s).")
    else:
        abort(404, "No gene found for given identifiers.")


    # get all wished mirnas
    if len(interaction_IDs) > 0:
        interaction_result = models.miRNAInteraction.query \
            .filter(models.miRNAInteraction.interactions_genegene_ID.in_(interaction_IDs)) \
            .all()

        if len(interaction_result) > 0:
            # Serialize the data for the response depending on parameter all
            return models.miRNAInteractionShortSchema(many=True).dump(interaction_result).data
        else:
            abort(404, "No data found with input parameter")

########################################################################################################################
"""Test Cases for Endpoint ​/miRNAInteraction​/findceRNA"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(disease_name="foobar"), 404)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(ensg_number=["ENSGfoobar"]), 404)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(gene_symbol=["foobar"]), 404)

    def test_abort_error_gene_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(gene_type="foobar"), 404)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(ensg_number=["ENSGfoobar"], gene_symbol=["foobar"]), 404)

    def test_abort_error_ensg_and_gene_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(ensg_number=["ENSGfoobar"], gene_type="foobar"), 404)

    def test_abort_error_symbol_and_gene_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(gene_symbol=["foobar"], gene_type="foobar"), 404)

    def test_abort_error_symbol_and_gene_type_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(ensg_number=["ENSGfoobar"], gene_symbol=["foobar"], gene_type="foobar"), 404)

    def test_abort_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(disease_name="bladder urothelial carcinoma", gene_type='lincRNA'), 404)

    def test_miRNAInteraction_findceRNA_disease_and_type(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_mirna_for_specific_interaction(disease_name='bladder urothelial carcinoma', gene_type='protein_coding')

        # retrieve current API response to request
        api_response = geneInteraction.read_mirna_for_specific_interaction(disease_name='bladder urothelial carcinoma',
                                                                      gene_type='protein_coding')
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNAInteraction_findceRNA_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_mirna_for_specific_interaction(disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000007312','ENSG00000113657'])

        # retrieve current API response to request
        api_response = geneInteraction.read_mirna_for_specific_interaction(disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000007312','ENSG00000113657'])

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNAInteraction_findceRNA_disease_and_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_mirna_for_specific_interaction(disease_name='bladder urothelial carcinoma', gene_symbol=['CD79B', 'DPYSL3'])

        # retrieve current API response to request
        api_response = geneInteraction.read_mirna_for_specific_interaction(disease_name='bladder urothelial carcinoma', gene_symbol=['CD79B', 'DPYSL3'])

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)
