from flask import jsonify
import app.models as models
from gseapy.plot import GSEAPlot
import base64
import io 
import matplotlib.pyplot as plt
from app.config import LATEST
from app.controllers.dataset import _dataset_query
from app.controllers.comparison import _comparison_query

plt.switch_backend('agg')    

def gsea_sets(dataset_ID_1: int = None, disease_name_1=None, dataset_ID_2: int = None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /gseaSets
    and returns all gene sets for which GSEA results are available for the given type, subtype and condition combination.
    :param dataset_ID_1: dataset ID of the first part of comparison (alternatively, disease_name_1 can be used)
    :param dataset_ID_2: dataset ID of the second part of comparison (alternatively, disease_name_2 can be used)
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param db_version: version of the sponge database
    :return: gene sets with significant terms for the selected comparison
    """

    # check inputs
    if dataset_ID_1 is None and disease_name_1 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if dataset_ID_2 is None and disease_name_2 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter datasets
    dataset_1 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_1, disease_name=disease_name_1, disease_subtype=disease_subtype_1)
    dataset_2 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_2, disease_name=disease_name_2, disease_subtype=disease_subtype_2)

    # extract ids
    dataset_1 = [x.dataset_ID for x in dataset_1]
    dataset_2 = [x.dataset_ID for x in dataset_2]

    # get comparisons
    comparison, _ = _comparison_query(dataset_1, dataset_2, condition_1, condition_2)
    comparison_ID = comparison[0].comparison_ID

    result = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .all()    
                            
    if len(result) > 0:
        return [dict(s) for s in set(frozenset(d.items()) for d in models.GseaSetSchema(many=True).dump(result))] 
    else:
        return jsonify({
            "detail": "No results for given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200




def gsea_terms(dataset_ID_1: int = None, dataset_ID_2: int = None, disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, gene_set=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /gseaTerms
    and returns all terms for which GSEA results are available for the given gene set, type/subtype, and condition combination.
    :param dataset_ID_1: dataset ID of the first part of comparison (alternatively, disease_name_1 can be used)
    :param dataset_ID_2: dataset ID of the second part of comparison (alternatively, disease_name_2 can be used)
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param gene_set: gene set which should include the terms that are returned
    :param sponge_db_version: version of the sponge database
    :return: names of the significantly enriched terms present in the gene set for the selected comparison
    """

    # check inputs
    if dataset_ID_1 is None and disease_name_1 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400
    if dataset_ID_2 is None and disease_name_2 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter datasets
    dataset_1 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_1, disease_name=disease_name_1, disease_subtype=disease_subtype_1)
    dataset_2 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_2, disease_name=disease_name_2, disease_subtype=disease_subtype_2)

    # extract ids
    dataset_1 = [x.dataset_ID for x in dataset_1]
    dataset_2 = [x.dataset_ID for x in dataset_2]

    # get comparisons
    comparison, _ = _comparison_query(dataset_1, dataset_2, condition_1, condition_2)
    comparison_ID = comparison[0].comparison_ID

    result = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .filter(models.Gsea.gene_set == gene_set) \
        .all() # TODO: maybe replace with _in(term)
                            
    if len(result) > 0:
        return [dict(s) for s in set(frozenset(d.items()) for d in models.GseaTermsSchema(many=True).dump(result))] 
    else:
        return jsonify({
            "detail": "No results for given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def gsea_results(dataset_ID_1: int = None, dataset_ID_2: int = None, disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, gene_set=None, term=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /gseaResults
    and returns GSEA results for the given gene set, type, subtype, and condition combination.
    :param dataset_ID_1: dataset ID of the first part of comparison (alternatively, disease_name_1 can be used)
    :param dataset_ID_2: dataset ID of the second part of comparison (alternatively, disease_name_2 can be used)
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param gene_set: gene set which should include the selected term
    :param term: term for which to return the gene set enrichment results
    :param sponge_db_version: version of the sponge database
    :return: Gene set enrichment results for the term and comparison
    """

    # check inputs
    if dataset_ID_1 is None and disease_name_1 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400
    if dataset_ID_2 is None and disease_name_2 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter datasets
    dataset_1 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_1, disease_name=disease_name_1, disease_subtype=disease_subtype_1)
    dataset_2 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_2, disease_name=disease_name_2, disease_subtype=disease_subtype_2)

    # extract ids
    dataset_1 = [x.dataset_ID for x in dataset_1]
    dataset_2 = [x.dataset_ID for x in dataset_2]

    # get comparisons
    comparison, reverse = _comparison_query(dataset_1, dataset_2, condition_1, condition_2)
    comparison_ID = comparison[0].comparison_ID

    result = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .filter(models.Gsea.gene_set == gene_set) \

    if term is not None:
        result = result.filter(models.Gsea.term.like("%" + term + "%"))

    result = result.all()
                            
    if len(result) > 0:
        result = models.GseaSchema(many=True).dump(result)
        for r in result:
            r.update({"tag_percent": f"{len(r['lead_genes'])}/{len(r['matched_genes'])}"})

        if reverse:
            for i in range(len(result)):
                result[i]["es"] = -result[i]["es"]
                result[i]["nes"] = -result[i]["nes"]
                result[i]["matched_genes"] = result[i]["matched_genes"][::-1]

        return result
    else:
        return jsonify({
            "detail": "No results for given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def gsea_plot(dataset_ID_1: int = None, dataset_ID_2: int = None, disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, term=None, gene_set=None, sponge_db_version: int = LATEST):
    """
    This function responds to a request for /gseaPlot
    and returns a GSEA plot for the given gene set, type, subtype, and condition combination.
    :param dataset_ID_1: dataset ID of the first part of comparison (alternatively, disease_name_1 can be used)
    :param dataset_ID_2: dataset ID of the second part of comparison (alternatively, disease_name_2 can be used)
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param gene_set: gene set which should include the selected term
    :param term: term for which to return the gene set enrichment results
    :param sponge_db_version: version of the sponge database
    :return: Gene set enrichment plot for the term and comparison
    """

    # check inputs
    if dataset_ID_1 is None and disease_name_1 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400
    if dataset_ID_2 is None and disease_name_2 is None:
        return jsonify({
            "detail": "Missing dataset id or disease id",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter datasets
    dataset_1 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_1, disease_name=disease_name_1, disease_subtype=disease_subtype_1)
    dataset_2 = _dataset_query(sponge_db_version=sponge_db_version, dataset_ID=dataset_ID_2, disease_name=disease_name_2, disease_subtype=disease_subtype_2)

    # extract ids
    dataset_1 = [x.dataset_ID for x in dataset_1]
    dataset_2 = [x.dataset_ID for x in dataset_2]

    # get comparisons
    comparison, reverse = _comparison_query(dataset_1, dataset_2, condition_1, condition_2)
    comparison_ID = comparison[0].comparison_ID

    gsea = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .filter(models.Gsea.term.like("%" + term + "%")) \
        .filter(models.Gsea.gene_set == gene_set) \
    
    # get res and ranging genes 
    gsea = gsea.join(models.GseaRes, models.Gsea.gsea_ID == models.GseaRes.gsea_ID) \
        .join(models.GseaRankingGenes, models.Gsea.gsea_ID == models.GseaRankingGenes.gsea_ID) \
        .all()


    if len(gsea) > 0:
        gsea = models.GseaSchemaPlot(many=True).dump(gsea)

        gene_map = models.Gene.query \
            .filter(models.Gene.gene_ID.in_([x.gene_ID for x in gsea[0]["gsea_ranking_genes"]])) \
            .all()                                                               # There are some gene symbols with multiple entries in the gene table
        ranking_gene_ids = {x.gene_symbol: x.gene_ID for x in gene_map}.values() # both ids are present with identical values in the diff expr. table, but only one is needed

        de = models.DifferentialExpression.query \
            .filter(models.DifferentialExpression.comparison_ID == comparison_ID) \
            .filter(models.DifferentialExpression.gene_ID.in_(ranking_gene_ids)) \
            .all()

        de = models.DESchemaShort(many=True).dump(de)

        ranking = [y for y in sorted(de, key= lambda x: x["log2FoldChange"], reverse=not reverse)]
        ranking_ids = [x["gene_ID"] for x in ranking]
        
        if reverse:
            g = GSEAPlot(
                term=term,
                tag=[ranking_ids.index(x.gene_ID) for x in gsea[0]["matched_genes"]],
                rank_metric=[-x["log2FoldChange"] for x in ranking],
                runes=[-y.score for y in sorted(gsea[0]["res"], key= lambda x: -x.res_ID)],
                nes=-gsea[0]["nes"],
                pval=gsea[0]["pvalue"],
                fdr=gsea[0]["fdr"],
                ofname=None,
                pheno_pos='Pos',
                pheno_neg='Neg',
                color=None,
                figsize=(9,5.5)
            )
        else:
            g = GSEAPlot(
                term=term,
                tag=[ranking_ids.index(x.gene_ID) for x in gsea[0]["matched_genes"]],
                rank_metric=[x["log2FoldChange"] for x in ranking],
                runes=[y["score"] for y in sorted(gsea[0]["res"], key= lambda x: x.res_ID)],
                nes=gsea[0]["nes"],
                pval=gsea[0]["pvalue"],
                fdr=gsea[0]["fdr"],
                ofname=None,
                pheno_pos='Pos',
                pheno_neg='Neg',
                color=None,
                figsize=(9,5.5)
            )

        g.add_axes()

        pic_IObytes = io.BytesIO()
        g.fig.savefig(pic_IObytes,  format='png')
        pic_IObytes.seek(0)
        pic_hash = base64.b64encode(pic_IObytes.read())
        
        return pic_hash.decode()
    else:
        return jsonify({
            "detail": "No results for given input",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

