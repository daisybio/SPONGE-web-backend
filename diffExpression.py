from flask import abort
import models
from config import LATEST

def get_diff_expr(disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, condition_1=None, 
                  condition_2=None, ensg_number=None, gene_symbol=None, sponge_db_version: int = LATEST):
    """
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param ensg_number: esng number of the gene(s) of interest
    :param gene_symbol: gene symbol of the gene(s) of interest
    :param sponge_db_version: version of the database
    :return: differential expression information for the genes of interest and the selected comparison
    """

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identification parameter is given. Please choose one out of (ensg number, gene symbol)")

    gene = []
    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

    if len(gene) > 0:
        gene_IDs = [i.gene_ID for i in gene]

    queries = []

    expression_dataset_gene_IDs = []

    if disease_name_1 is not None:
        dataset_1 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_1 + "%")) \
            .filter(models.Dataset.sponge_db_version == sponge_db_version)

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
            .filter(models.Dataset.sponge_db_version == sponge_db_version) 

        if disease_subtype_2 is None:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_2 + "%"))

        dataset_2 = dataset_2.all()

        dataset_2 = [x.dataset_ID for x in dataset_2]

        if len(dataset_2) == 0:
            abort(404, f"No dataset with disease_name_2 {disease_name_2} and disease_subtype_2 {disease_subtype_2} found")
    else:
        abort(404, "No disease_name_2 given")


    reverse = False
    comparisons = models.Comparison.query \
        .filter(models.Comparison.dataset_ID_1 == dataset_1) \
        .filter(models.Comparison.dataset_ID_2 == dataset_2) \
        .filter(models.Comparison.condition_1 == condition_1) \
        .filter(models.Comparison.condition_2 == condition_2) \
        .filter(models.Comparison.gene_transcript == "gene") \
        .all()

    if len(comparisons) != 1:
        comparisons = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1 == dataset_2) \
            .filter(models.Comparison.dataset_ID_2 == dataset_1) \
            .filter(models.Comparison.condition_1 == condition_2) \
            .filter(models.Comparison.condition_2 == condition_1) \
            .filter(models.Comparison.gene_transcript == "gene") \
            .all()
        reverse = True
    
    if len(comparisons) != 1:
        abort(404, "No (unique) comparison found for the requested inputs")

    comparison_ID = comparisons[0].comparison_ID

    result = models.DifferentialExpression.query \
        .filter(models.DifferentialExpression.comparison_ID == comparison_ID)

    if len(gene) > 0:
        result = result.filter(models.DifferentialExpression.gene_ID.in_(gene_IDs))

    result = result.all()

    if len(result) > 0:
        out = models.DESchema(many=True).dump(result)
        if reverse:
            for i in range(len(out)):
                out[i]["log2FoldChange"] = -out[i]["log2FoldChange"]
                out[i]["stat"] = -out[i]["stat"]

        return out
    else:
        abort(404, "No data found.")


def get_diff_expr_transcript(disease_name_1=None, disease_name_2=None, disease_subtype_1=None, disease_subtype_2=None, 
                             condition_1=None, condition_2=None, enst_number=None, sponge_db_version: int = LATEST):
    """
    :param disease_name_1: disease name of the first part of comparison (e.g. Sarcoma)
    :param disease_name_2: disease name of the second part of comparison (e.g. Sarcoma)
    :param disease_subtype_1: subtype of first part of comparison, overtype if none is provided (e.g. LMS) 
    :param disease_subtype_2: subtype of second part of comparison, overtype if none is provided (e.g. LMS) 
    :param condition_1: condition of first part of comparison (e.g. disease, normal)
    :param condition_2: condition of second part of comparison (e.g. disease, normal)
    :param enst_number: esng number of the transcript(s) of interest
    :param sponge_db_version: version of the database
    :return: differential expression information for the transcript of interest and the selected comparison
    """

    transcript = []

    if enst_number is not None:
        transcript = models.Transcript.query \
            .filter(models.Transcript.enst_number.in_(enst_number)) \
            .all()

    if len(transcript) > 0:
        transcript_IDs = [i.transcript_ID for i in transcript]

    queries = []

    expression_dataset_transcript_IDs = []

    if disease_name_1 is not None:
        dataset_1 = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name_1 + "%")) \
            .filter(models.Dataset.sponge_db_version == sponge_db_version)

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
            .filter(models.Dataset.sponge_db_version == sponge_db_version) 

        if disease_subtype_2 is None:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.is_(None))
        else:
            dataset_2 = dataset_2.filter(models.Dataset.disease_subtype.like("%" + disease_subtype_2 + "%"))

        dataset_2 = dataset_2.all()

        dataset_2 = [x.dataset_ID for x in dataset_2]

        if len(dataset_2) == 0:
            abort(404, f"No dataset with disease_name_2 {disease_name_2} and disease_subtype_2 {disease_subtype_2} found")
    else:
        abort(404, "No disease_name_2 given")


    reverse = False
    comparisons = models.Comparison.query \
        .filter(models.Comparison.dataset_ID_1 == dataset_1) \
        .filter(models.Comparison.dataset_ID_2 == dataset_2) \
        .filter(models.Comparison.condition_1 == condition_1) \
        .filter(models.Comparison.condition_2 == condition_2) \
        .filter(models.Comparison.gene_transcript == "transcript") \
        .all()

    if len(comparisons) != 1:
        comparisons = models.Comparison.query \
            .filter(models.Comparison.dataset_ID_1 == dataset_2) \
            .filter(models.Comparison.dataset_ID_2 == dataset_1) \
            .filter(models.Comparison.condition_1 == condition_2) \
            .filter(models.Comparison.condition_2 == condition_1) \
            .filter(models.Comparison.gene_transcript == "transcript") \
            .all()
        reverse = True
    
    if len(comparisons) != 1:
        abort(404, "No (unique) comparison found for the requested inputs")

    comparison_ID = comparisons[0].comparison_ID

    result = models.DifferentialExpression.query \
        .filter(models.DifferentialExpression.comparison_ID == comparison_ID)

    if len(transcript) > 0:
        result = result.filter(models.DifferentialExpression.transcript_ID.in_(transcript_IDs))

    result = result.all()

    if len(result) > 0:
        out = models.DETranscriptSchema(many=True).dump(result)
        if reverse:
            for i in range(len(out)):
                out[i]["log2FoldChange"] = -out[i]["log2FoldChange"]
                out[i]["stat"] = -out[i]["stat"]

        return out
    else:
        abort(404, "No data found.")


