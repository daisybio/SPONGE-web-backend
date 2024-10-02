from flask import abort
import models
import gseapy as gp
from gseapy.plot import GSEAPlot
import base64
import io 
import matplotlib.pyplot as plt

plt.switch_backend('agg')

def gsea_sets(disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None):
    """
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :return: gene sets with significant terms for the selected comparison
    """

    queries = []

    if disease_name_1 is not None:
        dataset_1 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_1 + "%")) \
            .filter(models.Dataset.version == 2)

        if disease_subtype_1 is None:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_1 + "%"))

        dataset_1 = dataset_1.all()

        dataset_1 = [x.dataset_ID for x in dataset_1]

        if len(dataset_1) == 0:
            abort(404, f"No dataset with disease_name_1 {disease_name_1} and disease_subtype_1 {disease_subtype_1} found")
    else:
        abort(404, "No disease_name_1 given")

    if disease_name_2 is not None:
        dataset_2 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_2 + "%")) \
            .filter(models.Dataset.version == 2)

        if disease_subtype_2 is None:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_2 + "%"))

        dataset_2 = dataset_2.all()

        dataset_2 = [x.dataset_ID for x in dataset_2]

        if len(dataset_2) == 0:
            abort(404, f"No dataset with disease_name_2 {disease_name_2} and disease_subtype_2 {disease_subtype_2} found")
    else:
        abort(404, "No disease_name_2 found")

    if condition_1 is not None and condition_2 is not None:
        comparison = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1.in_(dataset_1)) \
            .filter(models.Comparison.dataset_ID_2.in_(dataset_2)) \
            .filter(models.Comparison.condition_1 == condition_1) \
            .filter(models.Comparison.condition_2 == condition_2) \
            .filter(models.Comparison.gene_transcript == "gene") \
            .all()

        if len(comparison) == 0:
            comparison = models.Comparison.query \
                .filter(models.Comparison.dataset_ID_1.in_(dataset_2)) \
                .filter(models.Comparison.dataset_ID_2.in_(dataset_1)) \
                .filter(models.Comparison.condition_1 == condition_2) \
                .filter(models.Comparison.condition_2 == condition_1) \
                .filter(models.Comparison.gene_transcript == "gene") \
                .all()
            if len(comparison) == 0:
                abort(404, "No comparison found for given inputs")
    else:
        abort(404, "Condition missing")

    comparison_ID = comparison[0].comparison_ID

    result = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .all()
                            
    if len(result) > 0:
        return [dict(s) for s in set(frozenset(d.items()) for d in models.GseaSetSchema(many=True).dump(result))] 
    else:
        abort(404, "No data found.")



def gsea_terms(disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, gene_set=None):
    """
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param gene_set: gene set which should include the terms that are returned
    :return: names of the significantly enriched terms present in the gene set for the selected comparison
    """


    if disease_name_1 is not None:
        dataset_1 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_1 + "%")) \
            .filter(models.Dataset.version == 2) 

        if disease_subtype_1 is None:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_1 + "%"))

        dataset_1 = dataset_1.all()

        dataset_1 = [x.dataset_ID for x in dataset_1]

        if len(dataset_1) == 0:
            abort(404, f"No dataset with disease_name_1 {disease_name_1} and disease_subtype_1 {disease_subtype_1} found")
    else:
        abort(404, "No disease_name_1 given")

    if disease_name_2 is not None:
        dataset_2 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_2 + "%")) \
            .filter(models.Dataset.version == 2)

        if disease_subtype_2 is None:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_2 + "%"))

        dataset_2 = dataset_2.all()

        dataset_2 = [x.dataset_ID for x in dataset_2]

        if len(dataset_2) == 0:
            abort(404, f"No dataset with disease_name_2 {disease_name_2} and disease_subtype_2 {disease_subtype_2} found")
    else:
        abort(404, "No disease_name_2 found")

    if condition_1 is not None and condition_2 is not None:
        comparison = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1.in_(dataset_1)) \
            .filter(models.Comparison.dataset_ID_2.in_(dataset_2)) \
            .filter(models.Comparison.condition_1 == condition_1) \
            .filter(models.Comparison.condition_2 == condition_2) \
            .filter(models.Comparison.gene_transcript == "gene") \
            .all()

        if len(comparison) == 0:
            comparison = models.Comparison.query \
                .filter(models.Comparison.dataset_ID_1.in_(dataset_2)) \
                .filter(models.Comparison.dataset_ID_2.in_(dataset_1)) \
                .filter(models.Comparison.condition_1 == condition_2) \
                .filter(models.Comparison.condition_2 == condition_1) \
                .filter(models.Comparison.gene_transcript == "gene") \
                .all()
            if len(comparison) == 0:
                abort(404, "No comparison found for given inputs")
    else:
        abort(404, "Condition missing")

    comparison_ID = comparison[0].comparison_ID

    result = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .filter(models.Gsea.gene_set == gene_set) \
        .all() # TODO: maybe replace with _in(term)
                            
    if len(result) > 0:
        return [dict(s) for s in set(frozenset(d.items()) for d in models.GseaTermsSchema(many=True).dump(result))] 
    else:
        abort(404, "No data found.")


def gsea_results(disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, gene_set=None, term=None):
    """
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param gene_set: gene set which should include the selected term
    :param term: term for which to return the gene set enrichment results
    :return: Gene set enrichment results for the term and comparison
    """
    if disease_name_1 is not None:
        dataset_1 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_1 + "%")) \
            .filter(models.Dataset.version == 2)

        if disease_subtype_1 is None:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_1 + "%"))

        dataset_1 = dataset_1.all()

        dataset_1 = [x.dataset_ID for x in dataset_1]

        if len(dataset_1) == 0:
            abort(404, f"No dataset with disease_name_1 {disease_name_1} and disease_subtype_1 {disease_subtype_1} found")
    else:
        abort(404, "No disease_name_1 given")

    if disease_name_2 is not None:
        dataset_2 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_2 + "%")) \
            .filter(models.Dataset.version == 2) 

        if disease_subtype_2 is None:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_2 + "%"))

        dataset_2 = dataset_2.all()

        dataset_2 = [x.dataset_ID for x in dataset_2]

        if len(dataset_2) == 0:
            abort(404, f"No dataset with disease_name_2 {disease_name_2} and disease_subtype_2 {disease_subtype_2} found")
    else:
        abort(404, "No disease_name_2 found")
        
    reverse = False
    if condition_1 is not None and condition_2 is not None:
        comparison = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1.in_(dataset_1)) \
            .filter(models.Comparison.dataset_ID_2.in_(dataset_2)) \
            .filter(models.Comparison.condition_1 == condition_1) \
            .filter(models.Comparison.condition_2 == condition_2) \
            .filter(models.Comparison.gene_transcript == "gene") \
            .all()

        if len(comparison) == 0:
            comparison = models.Comparison.query \
                .filter(models.Comparison.dataset_ID_1.in_(dataset_2)) \
                .filter(models.Comparison.dataset_ID_2.in_(dataset_1)) \
                .filter(models.Comparison.condition_1 == condition_2) \
                .filter(models.Comparison.condition_2 == condition_1) \
                .filter(models.Comparison.gene_transcript == "gene") \
                .all()
            reverse = True
            if len(comparison) == 0:
                abort(404, "No comparison found for given inputs")
    else:
        abort(404, "Condition missing")

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
        abort(404, "No data found.")

def gsea_plot(disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, condition_2=None, term=None, gene_set=None):
    """
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param gene_set: gene set which should include the selected term
    :param term: term for which to return the gene set enrichment results
    :return: Gene set enrichment plot for the term and comparison
    """

    if disease_name_1 is not None:
        dataset_1 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_1 + "%")) \
            .filter(models.Dataset.version == 2)

        if disease_subtype_1 is None:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_1 = dataset_1.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_1 + "%"))

        dataset_1 = dataset_1.all()

        dataset_1 = [x.dataset_ID for x in dataset_1]

        if len(dataset_1) == 0:
            abort(404, f"No dataset with disease_name_1 {disease_name_1} and disease_subtype_1 {disease_subtype_1} found")
    else:
        abort(404, "No disease_name_1 given")

    if disease_name_2 is not None:
        dataset_2 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_2 + "%")) \
            .filter(models.Dataset.version == 2)

        if disease_subtype_2 is None:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_2 + "%"))

        dataset_2 = dataset_2.all()

        dataset_2 = [x.dataset_ID for x in dataset_2]

        if len(dataset_2) == 0:
            abort(404, f"No dataset with disease_name_2 {disease_name_2} and disease_subtype_2 {disease_subtype_2} found")
    else:
        abort(404, "No disease_name_2 found")
        
    reverse = False
    if condition_1 is not None and condition_2 is not None:
        comparison = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1.in_(dataset_1)) \
            .filter(models.Comparison.dataset_ID_2.in_(dataset_2)) \
            .filter(models.Comparison.condition_1 == condition_1) \
            .filter(models.Comparison.condition_2 == condition_2) \
            .filter(models.Comparison.gene_transcript == "gene") \
            .all()

        if len(comparison) == 0:
            comparison = models.Comparison.query \
                .filter(models.Comparison.dataset_ID_1.in_(dataset_2)) \
                .filter(models.Comparison.dataset_ID_2.in_(dataset_1)) \
                .filter(models.Comparison.condition_1 == condition_2) \
                .filter(models.Comparison.condition_2 == condition_1) \
                .filter(models.Comparison.gene_transcript == "gene") \
                .all()
            reverse = True
            if len(comparison) == 0:
                abort(404, "No comparison found for given inputs")
    else:
        abort(404, "Condition missing")

    comparison_ID = comparison[0].comparison_ID

    gsea = models.Gsea.query \
        .filter(models.Gsea.comparison_ID == comparison_ID) \
        .filter(models.Gsea.term.like("%" + term + "%")) \
        .filter(models.Gsea.gene_set == gene_set) \
        .all()


    if len(gsea) > 0:
        gsea = models.GseaSchemaPlot(many=True).dump(gsea)

        gene_map = models.Gene.query \
            .filter(models.Gene.gene_ID.in_([x["gene_ID"] for x in gsea[0]["gsea_ranking_genes"]])) \
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
                tag=[ranking_ids.index(x["gene_ID"]) for x in gsea[0]["matched_genes"]],
                rank_metric=[-x["log2FoldChange"] for x in ranking],
                runes=[-y["score"] for y in sorted(gsea[0]["res"], key= lambda x: -x["res_ID"])],
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
                tag=[ranking_ids.index(x["gene_ID"]) for x in gsea[0]["matched_genes"]],
                rank_metric=[x["log2FoldChange"] for x in ranking],
                runes=[y["score"] for y in sorted(gsea[0]["res"], key= lambda x: x["res_ID"])],
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
        abort(404, "No data found.")

