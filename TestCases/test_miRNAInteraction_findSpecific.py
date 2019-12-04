from config import *
import models, geneInteraction, unittest
from flask import abort
from werkzeug.exceptions import HTTPException

def test_read_all_to_one_mirna(disease_name=None, mimat_number=None, hs_number=None, limit=15000, offset=0,
                          information=True):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions the given miRNA is involved in
    """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    if mimat_number is None and hs_number is None:
        abort(404, "Mimat_ID or hs_number of mirna(s) of interest are needed!!")
    if mimat_number is not None and hs_number is not None:
        abort(404, "More than one miRNA identifier is given. Please choose one.")

    # get mir_ID from given mimat_number or hs number
    mirna = []
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()

    # save queries
    queries = []
    if len(mirna) > 0:
        mirna_IDs = [i.miRNA_ID for i in mirna]
        queries.append(models.miRNAInteraction.miRNA_ID.in_(mirna_IDs))
    else:
        abort(404, "With given mimat_ID or hs_number no miRNA could be found")

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

    interaction_result = models.miRNAInteraction.query \
        .join(models.GeneInteraction,
              models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID) \
        .filter(*queries) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.miRNAInteractionLongSchema(many=True)
        else:
            # Serialize the data for the response depending on parameter all
            schema = models.miRNAInteractionShortSchema(many=True)
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
            self.assertEqual(geneInteraction.read_all_to_one_mirna(mimat_number=["MIMATfoobar"]), 404)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(hs_number=["hs-foobar"]), 404)

    def test_abort_error_mimat_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(disease_name="bladder urothelial carcinoma", mimat_number=['MIMAT0000062'], hs_number=['hsa-let-7a-5p']), 404)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_to_one_mirna(disease_name="bladder urothelial carcinoma", mimat_number=['MIMAT0000062']), 404)

    def test_miRNA_Interaction_findSpecific_disease_and_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_to_one_mirna(disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000080', 'MIMAT0000095'], limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_to_one_mirna(disease_name='bladder urothelial carcinoma',
                                                                 mimat_number= ['MIMAT0000080', 'MIMAT0000095'], limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_findSpecific_disease_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_to_one_mirna(disease_name='bladder urothelial carcinoma', hs_number=['hsa-miR-24-3p', 'hsa-miR-96-5p'], limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_to_one_mirna(disease_name='bladder urothelial carcinoma',
                                                                 hs_number= ['hsa-miR-24-3p', 'hsa-miR-96-5p'], limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)


