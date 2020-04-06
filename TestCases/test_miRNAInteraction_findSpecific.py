from config import *
import models, geneInteraction, unittest, sqlalchemy as sa
from flask import abort
from werkzeug.exceptions import HTTPException

def test_read_all_to_one_mirna(disease_name=None, mimat_number=None, hs_number=None, limit=100, offset=0):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: mimat_id( of miRNA of interest
    :param: hs_nr: hs_number of miRNA of interest
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :return: all interactions the given miRNA is involved in
    """

    # test limit
    if limit > 1000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    if mimat_number is None and hs_number is None:
        abort(404, "Mimat_ID or hs_number of mirna of interest are needed!")
    if mimat_number is not None and hs_number is not None:
        abort(404, "More than one miRNA identifier is given. Please choose one.")

    # get mir_ID from given mimat_number or hs number
    mirna = []
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.like("%" + mimat_number + "%")) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.like("%" + hs_number + "%")) \
            .all()

    # save queries
    queriesGeneInteraction = []
    queriesmirnaInteraction = []
    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
        queriesmirnaInteraction.append(models.miRNAInteraction.miRNA_ID.in_(mirna_IDs))
    else:
        abort(404, "With given mimat_ID or hs_number no miRNA could be found")

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queriesmirnaInteraction.append(models.miRNAInteraction.run_ID.in_(run_IDs))
            queriesGeneInteraction.append(models.GeneInteraction.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    # get all possible gene interaction partner for specific miRNA
    gene_interaction = models.miRNAInteraction.query \
        .filter(*queriesmirnaInteraction) \
        .all()

    geneInteractionIDs = []
    if len(gene_interaction) > 0:
        geneInteractionIDs = [i.gene_ID for i in gene_interaction]
    else:
        abort(404, "No gene is associated with the given miRNA.")
    print(len(gene_interaction))

    # save all needed queries to get correct results
    queriesGeneInteraction.append(sa.and_(models.GeneInteraction.gene_ID1.in_(geneInteractionIDs),
                                          models.GeneInteraction.gene_ID2.in_(geneInteractionIDs)))

    interaction_result = models.GeneInteraction.query \
        .filter(*queriesGeneInteraction) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        schema = models.GeneInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_result).data
    else:
        abort(404, "No data found with input parameter")

########################################################################################################################
"""Test Cases for Endpoint ​/miRNAInteraction​/findSpecific"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(disease_name="foobar"), 404)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(limit = 20000), 404)

    def test_abort_error_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(mimat_number="MIMATfoobar"), 404)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(hs_number="hs-foobar"), 404)

    def test_abort_error_mimat_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(disease_name="head & neck squamous cell carcinoma", mimat_number='MIMAT0000062', hs_number='hsa-let-7a-5p'), 404)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(disease_name="head & neck squamous cell carcinoma", mimat_number='MIMAT0000062'), 404)

    def test_miRNA_Interaction_findSpecific_disease_and_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_to_one_mirna(disease_name='head & neck squamous cell carcinoma', mimat_number='MIMAT0000069', limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_to_one_mirna(disease_name='head & neck squamous cell carcinoma',
                                                                 mimat_number= 'MIMAT0000069', limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_findSpecific_disease_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_to_one_mirna(disease_name='head & neck squamous cell carcinoma', hs_number='hsa-miR-16-5p', limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_to_one_mirna(disease_name='head & neck squamous cell carcinoma',
                                                                 hs_number= 'hsa-miR-16-5p', limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)


