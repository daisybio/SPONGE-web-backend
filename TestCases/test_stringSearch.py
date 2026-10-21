from app.config import app, db, LATEST
from werkzeug.exceptions import HTTPException
import app.models as models, unittest
with app.app_context():
    import externalInformation
from flask import jsonify


def mock_getAutocomplete(searchString):
    """
    Funtion to retrieve the autocomplete possibilities for the webside
    :param searchString: String (ensg_number, gene_symbol, hs_number or mimat_number)
    :return: list of all genes/mirnas having search string as a prefic
    """

    if searchString.startswith("ENSG") or searchString.startswith("ensg"):
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.ensg_number.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No ensg number found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200
    elif searchString.startswith("HSA") or searchString.startswith("hsa"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.hs_nr.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No hsa number found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200
    elif searchString.startswith("MIMAT") or searchString.startswith("mimat"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.mir_ID.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No mimat number found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200
    else:
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.gene_symbol.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data)
        else:
            return jsonify({
                "detail": "No gene symbol found for the given input",
                "status": 200,
                "title": "No Content",
                "type": "about:blank",
                "data": []
            }), 200

########################################################################################################################
"""Test Cases for Endpoint ​/stringSearch"""
########################################################################################################################

class TestDataset(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_abort_error_no_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = externalInformation.getAutocomplete(searchString="ENSGforrbar")
        self.assertEqual(result[1], 200)

    def test_abort_error_no_hs(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = externalInformation.getAutocomplete(searchString="HSAforbaar")
        self.assertEqual(result[1], 200)

    def test_abort_error_no_mimat(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = externalInformation.getAutocomplete(searchString="MIMATfoobar")
        self.assertEqual(result[1], 200)

    def test_abort_error_no_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = externalInformation.getAutocomplete(searchString="helloWorld")
        self.assertEqual(result[1], 200)
