from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import geneInteraction
from flask import jsonify
from sqlalchemy import desc

# Disease name in DuckDB uses '&' (pre-existing test drift vs MySQL-era spelling).
_HEAD_NECK = 'head & neck squamous cell carcinoma'


def mock_read_all_mirna(dataset_ID=None, disease_name=None, mimat_number=None, hs_number=None,
                        occurences=None, sorting=None, descending=None, limit=100, offset=0,
                        sponge_db_version=LATEST):
    """
    :param disease_name: disease_name of interest
    :param mimat_number: comma-separated list of mimat_id(s) of miRNA of interest
    :param: hs_nr: comma-separated list of hs_number(s) of miRNA of interest
    :param occurences: how often a miRNA should contribute to a ceRNA interaction to be returned
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that should be shown
    :param offset: startpoint from where results should be shown
    :return: all mirna involved in disease of interest
    """
    if limit > 1000:
        return jsonify({
            "detail": "Limit is to high. For a high number of needed interactions please use the download section.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if mimat_number is not None and hs_number is not None:
        return jsonify({
            "detail": "More than one miRNA identifier is given. Please choose one.",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    mirna = []
    if mimat_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.mir_ID.in_(mimat_number)) \
            .all()
    elif hs_number is not None:
        mirna = models.miRNA.query \
            .filter(models.miRNA.hs_nr.in_(hs_number)) \
            .all()

    queries = []
    if mimat_number is not None or hs_number is not None:
        if len(mirna) > 0:
            mirna_IDs = [i.miRNA_ID for i in mirna]
            queries.append(models.OccurencesMiRNA.miRNA_ID.in_(mirna_IDs))
        else:
            return jsonify({
                "detail": "No miRNA was found using given identifier",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    run = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version)

    if disease_name is not None:
        run = run.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%"))

    if dataset_ID is not None:
        run = run.filter(models.SpongeRun.dataset_ID == dataset_ID)

    run = run.all()

    if len(run) > 0:
        run_IDs = [i.sponge_run_ID for i in run]
        queries.append(models.OccurencesMiRNA.sponge_run_ID.in_(run_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if occurences is not None:
        queries.append(models.OccurencesMiRNA.occurences > occurences)

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
        return models.occurencesMiRNASchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No information with given parameters found",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

########################################################################################################################
"""Test Cases for Endpoint ​/miRNAInteraction​/getOccurences"""
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
        result = geneInteraction.read_all_mirna(disease_name="foobar")
        self.assertEqual(result[1], 400)

    def test_abort_error_limit(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_mirna(disease_name="foobar", limit=20000)
        self.assertEqual(result[1], 400)

    def test_abort_error_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_mirna(mimat_number=["MIMATfoobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_mirna(hs_number=["hs-foobar"])
        self.assertEqual(result[1], 400)

    def test_abort_error_mimat_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0000062'], hs_number=['hsa-let-7a-5p'])
        self.assertEqual(result[1], 400)

    def test_abort_error_no_data(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0037307'], sponge_db_version=1)
        self.assertEqual(result[1], 200)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0026472', 'MIMAT0004486'],
            occurences=10, sorting="occurences", limit=50)
        api_response = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0026472', 'MIMAT0004486'],
            occurences=10, sorting="occurences", limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0026472', 'MIMAT0004486'],
            occurences=10, limit=50, sorting="occurences", descending=False)
        api_response = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0026472', 'MIMAT0004486'],
            occurences=10, limit=50, sorting="occurences", descending=False)
        assert_payloads_equal(self, mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_mimat_number_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0026472', 'MIMAT0004486'],
            occurences=10, limit=50, sorting="occurences", descending=True)
        api_response = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, mimat_number=['MIMAT0026472', 'MIMAT0004486'],
            occurences=10, sorting="occurences", limit=50, descending=True)
        assert_payloads_equal(self, mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_hs_number(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_mirna(
            disease_name=_HEAD_NECK, hs_number=['hsa-let-7c-3p', 'hsa-let-7f-1-3p'],
            occurences=10, limit=50)
        api_response = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, hs_number=['hsa-let-7c-3p', 'hsa-let-7f-1-3p'],
            occurences=10, limit=50)
        assert_payloads_equal(self, mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_hs_number_sorting_asc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_mirna(
            disease_name=_HEAD_NECK, hs_number=['hsa-let-7c-3p', 'hsa-let-7f-1-3p'],
            occurences=10, limit=50, sorting="occurences", descending=False)
        api_response = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, hs_number=['hsa-let-7c-3p', 'hsa-let-7f-1-3p'],
            occurences=10, limit=50, sorting="occurences", descending=False)
        assert_payloads_equal(self, mock_response, api_response)

    def test_miRNA_Interaction_getOccurences_disease_and_hs_number_sorting_desc(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_all_mirna(
            disease_name=_HEAD_NECK, hs_number=['hsa-let-7c-3p', 'hsa-let-7f-1-3p'],
            occurences=10, limit=50, sorting="occurences", descending=True)
        api_response = geneInteraction.read_all_mirna(
            disease_name=_HEAD_NECK, hs_number=['hsa-let-7c-3p', 'hsa-let-7f-1-3p'],
            occurences=10, limit=50, sorting="occurences", descending=True)
        assert_payloads_equal(self, mock_response, api_response)
