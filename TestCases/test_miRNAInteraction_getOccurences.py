from config import *
import models, geneInteraction, unittest
from flask import abort
from sqlalchemy import desc
from werkzeug.exceptions import HTTPException

def test_read_all_mirna(disease_name=None, mimat_number=None, hs_number=None, occurences=None, sorting=None, descending=None,
                   limit=15000, offset=0):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param occurences: how often a miRNA should contribute to a ceRNA interaction to be returned
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :return: all mirna involved in disease of interest (searchs not for a specific miRNA, but search for all miRNA satisfying filter functions)
    """

    # test limit
    if limit > 15000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    if mimat_number is not None and hs_number is not None:
        abort(404, "More than one miRNA identifier is given. Please choose one.")

    # get mir_ID from given mimat_number
    mirna = []
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()
    else:
        abort(404, "No miRNA identifier is given. Please provide one.")

    # save queries
    queries = []
    if mimat_number is not None or hs_number is not None:
        if len(mirna) > 0:
            mirna_IDs = [i.miRNA_ID for i in mirna]
            queries.append(models.OccurencesMiRNA.miRNA_ID.in_(mirna_IDs))
        else:
            abort(404, "With given mimat_ID or hs_number no mirna could be found")

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()
        if len(run) > 0:
            run_IDs = [i.run_ID for i in run]
            queries.append(models.OccurencesMiRNA.run_ID.in_(run_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    if occurences is not None:
        queries.append(models.OccurencesMiRNA.occurences > occurences)

    # add sorting
    sort = []
    if sorting == "occurences":
        if descending:
            sort.append(desc(models.OccurencesMiRNA.occurences))
        else:
            sort.append(models.OccurencesMiRNA.occurences)

    interaction_result = models.OccurencesMiRNA.query \
        .filter(*queries) \
        .order_by(*sort) \
        .slice(offset, offset + limit) \
        .all()

    if len(interaction_result) > 0:
        # Serialize the data for the response depending on parameter all
        return models.occurencesMiRNASchema(many=True).dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")

########################################################################################################################
"""Test Cases for Endpoint ​/miRNAInteraction​/getOccurences"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_disease(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_mirna(disease_name="foobar"), 404)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_mirna(disease_name="foobar", limit = 20000), 404)

    def test_abort_error_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_mirna(mimat_number=["MIMATfoobar"]), 404)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_mirna(hs_number=["hs-foobar"]), 404)

    def test_abort_error_mimat_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_mirna(disease_name="bladder urothelial carcinoma", mimat_number=['MIMAT0000062'], hs_number=['hsa-let-7a-5p']), 404)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_mirna(disease_name="bladder urothelial carcinoma", mimat_number=['MIMAT0004482']), 404)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_mirna(disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000080', 'MIMAT0000095'], occurences=500, sorting="occurences", limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_mirna(disease_name='bladder urothelial carcinoma', mimat_number= ['MIMAT0000080', 'MIMAT0000095'],  occurences=500,  sorting="occurences", limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_mirna(disease_name='bladder urothelial carcinoma', mimat_number=['MIMAT0000080', 'MIMAT0000095'], occurences=500, limit=50,  sorting="occurences", descending=False)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_mirna(disease_name='bladder urothelial carcinoma',
                                                                 mimat_number= ['MIMAT0000080', 'MIMAT0000095'],  occurences=500, limit=50,  sorting="occurences", descending=False)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_mirna(disease_name='bladder urothelial carcinoma',
                                            mimat_number=['MIMAT0000080', 'MIMAT0000095'], occurences=500, limit=50,  sorting="occurences",
                                            descending=True)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_mirna(disease_name='bladder urothelial carcinoma',
                                                      mimat_number=['MIMAT0000080', 'MIMAT0000095'], occurences=500,  sorting="occurences",
                                                      limit=50, descending=True)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_mirna(disease_name='bladder urothelial carcinoma', hs_number=['hsa-miR-24-3p', 'hsa-miR-96-5p'], occurences=500,limit=50)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_mirna(disease_name='bladder urothelial carcinoma',
                                                                 hs_number= ['hsa-miR-24-3p', 'hsa-miR-96-5p'],  occurences=500, limit=50)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_hs_number_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_mirna(disease_name='bladder urothelial carcinoma', hs_number=['hsa-miR-24-3p', 'hsa-miR-96-5p'], occurences=500, limit=50,  sorting="occurences", descending=False)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_mirna(disease_name='bladder urothelial carcinoma',
                                                                 hs_number= ['hsa-miR-24-3p', 'hsa-miR-96-5p'],  occurences=500, limit=50,  sorting="occurences", descending=False)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_hs_number_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        # retrieve correct database response to request
        mock_response = test_read_all_mirna(disease_name='bladder urothelial carcinoma',
                                            hs_number=['hsa-miR-24-3p', 'hsa-miR-96-5p'], occurences=500, limit=50,
                                            sorting="occurences", descending=True)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_mirna(disease_name='bladder urothelial carcinoma',
                                                      hs_number=['hsa-miR-24-3p', 'hsa-miR-96-5p'], occurences=500,
                                                      limit=50,  sorting="occurences", descending=True)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

