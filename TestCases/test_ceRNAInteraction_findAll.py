from app.config import *
import app.models as models, unittest
with app.app_context(): 
    import geneInteraction
from flask import abort
import sqlalchemy as sa
from werkzeug.exceptions import HTTPException

def test_read_all_genes(disease_name=None, ensg_number=None, gene_symbol=None, gene_type=None, pValue=0.05,
                   pValueDirection="<", mscor=None, mscorDirection="<", correlation=None, correlationDirection="<",
                   sorting=None, descending=True, limit=100, offset=0, information=True):
    """
    This function responds to a request for /sponge/ceRNAInteraction/findAll
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param gene_type: defines the type of gene of interest
    :param pValue: pValue cutoff
    :param pValueDirection: < or >
    :param mscor mscor cutofff
    :param mscorDirection: < or >
    :param correlation: correlation cutoff
    :param correlationDirection: < or >
    :param sorting: how the results of the db query should be sorted
    :param descending: should the results be sorted in descending or ascending order
    :param limit: number of results that shouls be shown
    :param offset: startpoint from where results should be shown
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions given gene is involved
    """
    # test limit
    if limit > 1000:
        abort(404, "Limit is to high. For a high number of needed interactions please use the download section.")

    # test if just one of the possible identifiers is given
    if ensg_number is not None and (gene_symbol is not None or gene_type is not None) or (
            gene_symbol is not None and gene_type is not None):
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol or gene type)")

    queries_1 = []
    queries_2 = []
    # if specific disease_name is given:
    if disease_name is not None:
        with app.app_context():
            run = models.SpongeRun.query.join(models.Dataset, models.Dataset.dataset_ID == models.SpongeRun.dataset_ID) \
                .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
                .all()

        if len(run) > 0:
            run_IDs = [i.sponge_run_ID for i in run]
            queries_1.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
            queries_2.append(models.GeneInteraction.sponge_run_ID.in_(run_IDs))
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

    # save all needed queries to get correct results
    if ensg_number is not None or gene_symbol is not None or gene_type is not None:
        if len(gene) > 0:
            gene_IDs = [i.gene_ID for i in gene]
            queries_1.append(models.GeneInteraction.gene_ID1.in_(gene_IDs))
            queries_2.append(models.GeneInteraction.gene_ID2.in_(gene_IDs))
        else:
            abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queries_1.append(models.GeneInteraction.p_value <= pValue)
            queries_2.append(models.GeneInteraction.p_value <= pValue)
        else:
            queries_1.append(models.GeneInteraction.p_value >= pValue)
            queries_2.append(models.GeneInteraction.p_value >= pValue)
    if mscor is not None:
        if mscorDirection == "<":
            queries_1.append(models.GeneInteraction.mscor <= mscor)
            queries_2.append(models.GeneInteraction.mscor <= mscor)
        else:
            queries_1.append(models.GeneInteraction.mscor >= mscor)
            queries_2.append(models.GeneInteraction.mscor >= mscor)
    if correlation is not None:
        if correlationDirection == "<":
            queries_1.append(models.GeneInteraction.correlation <= correlation)
            queries_2.append(models.GeneInteraction.correlation <= correlation)
        else:
            queries_1.append(models.GeneInteraction.correlation >= correlation)
            queries_2.append(models.GeneInteraction.correlation >= correlation)

    # add all sorting if given:
    sort = []
    if sorting is not None:
        if sorting == "pValue":
            if descending:
                sort.append(models.GeneInteraction.p_value.desc())
            else:
                sort.append(models.GeneInteraction.p_value.asc())
        if sorting == "mscor":
            if descending:
                sort.append(models.GeneInteraction.mscor.desc())
            else:
                sort.append(models.GeneInteraction.mscor.asc())
        if sorting == "correlation":
            if descending:
                sort.append(models.GeneInteraction.correlation.desc())
            else:
                sort.append(models.GeneInteraction.correlation.asc())

    #interaction_result = []
    interaction_result = models.GeneInteraction.query \
        .filter(*queries_1) \
        .order_by(*sort) \
        .union(models.GeneInteraction.query
               .filter(*queries_2)
               .order_by(*sort)) \
        .slice(offset, offset + limit) \
        .all()

    #if len(tmp) > 0:
    #    interaction_result.append(tmp)
    #else:
    #    abort(404, "No information with given parameters found")

    #interaction_result = [val for sublist in interaction_result for val in sublist]

    if len(interaction_result) > 0:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.GeneInteractionDatasetLongSchema(many=True)
        else:
            # Serialize the data for the response depending on parameter all
            schema = models.GeneInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_result)
    else:
        abort(404, "No information with given parameters found")

########################################################################################################################
"""Test Cases for Endpoint /ceRNAInteraction/findAll"""
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
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(disease_name="foobar", pValue = None), 404)

    def test_abort_error_limit(self):
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(disease_name="foobar", limit = 20000, pValue = None), 404)

    def test_abort_error_ensg(self):
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(ensg_number=["ENSGfoobar"], pValue = None), 404)

    def test_abort_error_gene_symbol(self):
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(gene_symbol=["foobar"], pValue = None), 404)

    def test_abort_error_ensg_and_gene_symbol(self):
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(ensg_number=["ENSGfoobar"],gene_symbol=["foobar"], pValue = None), 404)

    def test_abort_error_gene_type(self):
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(gene_type="foobar", pValue = None), 404)

    def test_abort_error_no_data(self):
        with self.assertRaises(HTTPException) as http_error:
            # retrieve current API response to request
            self.assertEqual(geneInteraction.read_all_genes(disease_name="bladder urothelial carcinoma", ensg_number=['ENSG00000023041'], pValue = None), 404)

    def test_findAll_disease_and_ensg(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma', ensg_number=['ENSG00000172137','ENSG00000078237'], limit=50, pValue = None)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma', gene_symbol=['CALB2','TIGAR'], limit=50, pValue = None)

        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_ensg_pValue_smaller(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=0.5, pValueDirection="<", sorting="pValue")


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=0.5, pValueDirection="<", sorting="pValue")
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_ensg_pValue_greater(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=0.5, pValueDirection=">", sorting="pValue")


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, pValue=0.5, pValueDirection=">", sorting="pValue")
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_pValue_smaller(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=0.5, pValueDirection="<", sorting="pValue")


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=0.5, pValueDirection="<", sorting="pValue")
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_pValue_greater(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=0.5, pValueDirection=">", sorting="pValue")


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, pValue=0.5, pValueDirection=">", sorting="pValue")
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)


    def test_findAll_disease_and_ensg_correlation_smaller(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, correlation=0.2, correlationDirection="<", sorting="correlation", pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, correlation=0.2, correlationDirection="<", sorting="correlation", pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_ensg_correlation_greater(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, correlation=0.1, correlationDirection=">", sorting="correlation", pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, correlation=0.1, correlationDirection=">", sorting="correlation", pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_correlation_smaller(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            gene_symbol=['CALB2', 'TIGAR'], limit=50, correlation=0.2, correlationDirection="<", sorting="correlation",pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, correlation=0.2, correlationDirection="<", sorting="correlation",pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_correlation_greater(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            gene_symbol=['CALB2', 'TIGAR'], limit=50, correlation=0.1, correlationDirection=">", sorting="correlation",pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, correlation=0.1, correlationDirection=">", sorting="correlation",pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)


    def test_findAll_disease_and_ensg_mscor_smaller(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, mscor=0.02, mscorDirection="<", sorting="mscor",pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, mscor=0.02, mscorDirection="<", sorting="mscor", pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_ensg_mscor_greater(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, mscor=0.01, mscorDirection=">", sorting="mscor", pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      ensg_number=['ENSG00000172137', 'ENSG00000078237'], limit=50, mscor=0.01, mscorDirection=">", sorting="mscor", pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_mscor_smaller(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            gene_symbol=['CALB2', 'TIGAR'], limit=50, mscor=0.02, mscorDirection="<", sorting="mscor", pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, mscor=0.02, mscorDirection="<", sorting="mscor", pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)

    def test_findAll_disease_and_gene_symbol_mscor_greater(self):
        # retrieve correct database response to request
        mock_response = test_read_all_genes(disease_name='bladder urothelial carcinoma',
                                            gene_symbol=['CALB2', 'TIGAR'], limit=50, mscor=0.01, mscorDirection=">", sorting="mscor", pValue = None)


        # retrieve current API response to request
        api_response = geneInteraction.read_all_genes(disease_name='bladder urothelial carcinoma',
                                                      gene_symbol=['CALB2', 'TIGAR'], limit=50, mscor=0.01, mscorDirection=">", sorting="mscor", pValue = None)
        # assert that the two output the same
        self.assertEqual(mock_response, api_response)
