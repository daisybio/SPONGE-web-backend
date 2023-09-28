from config import *
import models, geneInteraction, unittest
from flask import abort
import sqlalchemy as sa
from werkzeug.exceptions import HTTPException

def test_read_mirna_for_specific_interaction(disease_name=None, ensg_number=None, gene_symbol=None, between=False):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNA
    and returns all miRNAs thar contribute to all interactions between the given identifications (ensg_number or gene_symbol)
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the genes of interest
    :param gene_symbol: gene symbol of the genes of interest
    :param gene_type: defines the type of gene of interest
    :param between: If false, all interactions where one of the interaction partners fits the given genes of interest
                    will be considered.
                    If true, just interactions between the genes of interest will be considered.

    :return: all miRNAs contributing to the interactions between genes of interest
    """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    queries = []
    run_IDs = []
    # if specific disease_name is given:
    if disease_name is not None:
        run = models.SpongeRun.query.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.sponge_run_ID for i in run]
            queries.append(models.miRNAInteraction.sponge_run_ID.in_(run_IDs))
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

    gene_IDs = []
    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]
        queries.append(models.miRNAInteraction.gene_ID.in_(gene_IDs))
    else:
        abort(404, "No gene found for given identifiers.")

    interaction_result = []
    if between:
        # an Engine, which the Session will use for connection resources
        some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)

        # create a configured "Session" class
        Session = sa.orm.sessionmaker(bind=some_engine)

        # create a Session
        session = Session()
        # test for each dataset if the gene(s) of interest are included in the ceRNA network

        print()

        mirna_filter = session.execute("select mirna_ID from interacting_miRNAs where run_ID IN ( "
                                       + ','.join(str(e) for e in run_IDs) + ") and gene_ID IN ( "
                                       + ','.join(str(e) for e in gene_IDs)
                                       + ") group by mirna_ID HAVING count(mirna_ID) >= 2;").fetchall()

        session.close()
        some_engine.dispose()

        if len(mirna_filter) == 0:
            abort(404, "No shared miRNA between genes found.")

        flat_mirna_filter = [item for sublist in mirna_filter for item in sublist]
        queries.append(models.miRNAInteraction.miRNA_ID.in_(flat_mirna_filter))

        interaction_result = models.miRNAInteraction.query \
            .filter(*queries) \
            .all()
    else:
        interaction_result = models.miRNAInteraction.query \
            .filter(*queries) \
            .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.miRNAInteractionSchema(many=True).dump(interaction_result).data
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
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(disease_name="foobar", between=True), 404)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(ensg_number=["ENSGfoobar"], between=True), 404)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(gene_symbol=["foobar"], between=True), 404)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_mirna_for_specific_interaction(ensg_number=["ENSGfoobar"], gene_symbol=["foobar"], between=True), 404)

    def test_miRNAInteraction_findceRNA_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_mirna_for_specific_interaction(disease_name='head and neck squamous cell carcinoma', ensg_number=['ENSG00000001626','ENSG00000002726'], between=True)

        # retrieve current API response to request
        api_response = geneInteraction.read_mirna_for_specific_interaction(disease_name='head and neck squamous cell carcinoma', ensg_number=['ENSG00000001626','ENSG00000002726'], between=True)

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNAInteraction_findceRNA_disease_and_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_mirna_for_specific_interaction(disease_name='head and neck squamous cell carcinoma', gene_symbol=['CFTR', 'AOC1'], between=True)

        # retrieve current API response to request
        api_response = geneInteraction.read_mirna_for_specific_interaction(disease_name='head and neck squamous cell carcinoma', gene_symbol=['CFTR', 'AOC1'], between=True)

        # assert that the two output the same
        self.assertEqual(mock_response, api_response)
