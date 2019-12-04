from config import *
from werkzeug.exceptions import HTTPException
import models, externalInformation, unittest
from flask import abort

def test_getAutocomplete(searchString):
    """
    Funtion to retrieve the autocomplete possibilities for the webside
    :param searchString: String (ensg_number, gene_symbol, hs_number or mimat_number)
    :return: list of all genes/mirnas having search string as a prefic
    """

    if searchString.startswith("ENSG") or searchString.startswith("ensg"):
        data = models.Gene.query.with_entities(models.Gene.ensg_number) \
            .filter(models.Gene.ensg_number.ilike(searchString + "%")) \
            .all()
        print(data)
        if len(data) > 0:
            return models.GeneSchemaENSG(many=True).dump(data).data
        else:
            abort(404, "No ensg number found for the given String")
    elif searchString.startswith("HSA") or searchString.startswith("hsa"):
        data = models.miRNA.query.with_entities(models.miRNA.hs_nr) \
            .filter(models.miRNA.hs_nr.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaHS(many=True).dump(data).data
        else:
            abort(404, "No hsa number found for the given String")
    elif searchString.startswith("MIMAT") or searchString.startswith("mimat"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID) \
            .filter(models.miRNA.mir_ID.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaMimat(many=True).dump(data).data
        else:
            abort(404, "No mimat number found for the given String")
    else:
        data = models.Gene.query.with_entities(models.Gene.gene_symbol) \
            .filter(models.Gene.gene_symbol.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaSymbol(many=True).dump(data).data
        else:
            abort(404, "No gene symbol found for the given String")

########################################################################################################################
"""Test Cases for Endpoint ​/stringSearch"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def test_abort_error_no_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(externalInformation.getAutocomplete(searchString="ENSGforrbar"), 404)

    def test_abort_error_no_hs(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(externalInformation.getAutocomplete(searchString="HSAforbaar"), 404)

    def test_abort_error_no_mimat(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(externalInformation.getAutocomplete(searchString="MIMATfoobar"), 404)

    def test_abort_error_no_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(externalInformation.getAutocomplete(searchString="helloWorld"), 404)