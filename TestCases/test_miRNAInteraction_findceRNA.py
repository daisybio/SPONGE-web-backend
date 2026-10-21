from app.config import app, db, LATEST
import app.models as models, unittest
from compare import assert_payloads_equal
with app.app_context():
    import geneInteraction
from flask import jsonify


def mock_read_mirna_for_specific_interaction(dataset_ID=None, disease_name=None, ensg_number=None,
                                            gene_symbol=None, between=False, sponge_db_version=LATEST):
    """
    This function responds to a request for /sponge/miRNAInteraction/findceRNA
    and returns all miRNAs thar contribute to all interactions between the given identifications
    """
    disease_query = db.select(models.Dataset.dataset_ID).where(
        models.Dataset.sponge_db_version == sponge_db_version)
    if disease_name is not None:
        disease_query = disease_query.where(models.Dataset.disease_name.like("%" + disease_name + "%"))
    if dataset_ID is not None:
        disease_query = disease_query.where(models.Dataset.dataset_ID == dataset_ID)

    run_query = db.select(models.SpongeRun.sponge_run_ID).where(
        models.SpongeRun.dataset_ID.in_(disease_query))

    gene_query = db.select(models.Gene.gene_ID)
    if ensg_number is not None:
        gene_query = gene_query.where(models.Gene.ensg_number.in_(ensg_number))
    if gene_symbol is not None:
        gene_query = gene_query.where(models.Gene.gene_symbol.in_(gene_symbol))

    base_interaction_query = db.select(models.miRNAInteraction).where(
        models.miRNAInteraction.gene_ID.in_(gene_query),
        models.miRNAInteraction.sponge_run_ID.in_(run_query),
    )

    if between:
        distinct_gene_count_subquery = (
            db.select(db.func.count(db.func.distinct(gene_query.c.gene_ID))).scalar_subquery()
        )
        mirna_query = db.select(models.miRNAInteraction.miRNA_ID) \
            .where(models.miRNAInteraction.gene_ID.in_(gene_query)) \
            .where(models.miRNAInteraction.sponge_run_ID.in_(run_query)) \
            .group_by(models.miRNAInteraction.miRNA_ID) \
            .having(db.func.count(models.miRNAInteraction.gene_ID) == distinct_gene_count_subquery)
        interaction_query = base_interaction_query.where(
            models.miRNAInteraction.miRNA_ID.in_(mirna_query)
        )
    else:
        interaction_query = base_interaction_query

    interaction_result = db.session.execute(interaction_query).scalars().all()

    if len(interaction_result) > 0:
        return models.miRNAInteractionSchema(many=True).dump(interaction_result)
    else:
        return jsonify({
            "detail": "No data found using the given input parameters",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


########################################################################################################################
"""Test Cases for Endpoint ​/miRNAInteraction​/findceRNA"""
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
        result = geneInteraction.read_mirna_for_specific_interaction(
            disease_name="foobar", between=True)
        self.assertEqual(result[1], 200)

    def test_abort_error_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_mirna_for_specific_interaction(
            ensg_number=["ENSGfoobar"], between=True)
        self.assertEqual(result[1], 200)

    def test_abort_error_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        result = geneInteraction.read_mirna_for_specific_interaction(
            gene_symbol=["foobar"], between=True)
        self.assertEqual(result[1], 200)

    def test_abort_error_ensg_and_gene_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        # Both filters applied; no matching genes → empty 200
        result = geneInteraction.read_mirna_for_specific_interaction(
            ensg_number=["ENSGfoobar"], gene_symbol=["foobar"], between=True)
        self.assertEqual(result[1], 200)

    def test_miRNAInteraction_findceRNA_disease_and_ensg(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_mirna_for_specific_interaction(
            disease_name='head & neck squamous cell carcinoma',
            ensg_number=['ENSG00000001626', 'ENSG00000002726'], between=True)
        api_response = geneInteraction.read_mirna_for_specific_interaction(
            disease_name='head & neck squamous cell carcinoma',
            ensg_number=['ENSG00000001626', 'ENSG00000002726'], between=True)
        assert_payloads_equal(self, mock_response, api_response)

    def test_miRNAInteraction_findceRNA_disease_and_symbol(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        mock_response = mock_read_mirna_for_specific_interaction(
            disease_name='head & neck squamous cell carcinoma',
            gene_symbol=['CFTR', 'AOC1'], between=True)
        api_response = geneInteraction.read_mirna_for_specific_interaction(
            disease_name='head & neck squamous cell carcinoma',
            gene_symbol=['CFTR', 'AOC1'], between=True)
        assert_payloads_equal(self, mock_response, api_response)
