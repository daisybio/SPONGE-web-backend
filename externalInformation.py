from flask import abort
import models

def getAutocomplete(searchString):
    """
    Funtion to retrieve the autocomplete possibilities for the webside
    :param searchString: String (ensg_number, gene_symbol, hs_number or mimat_number)
    :return: list of all genes/mirnas having search string as a prefic
    """

    if searchString.startswith("ENSG") or searchString.startswith("ensg"):
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.ensg_number.ilike(searchString + "%")) \
            .all()
        print(data)
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data).data
        else:
            abort(404, "No ensg number found for the given String")
    elif searchString.startswith("HSA") or searchString.startswith("hsa"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.hs_nr.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data).data
        else:
            abort(404, "No hsa number found for the given String")
    elif searchString.startswith("MIMAT") or searchString.startswith("mimat"):
        data = models.miRNA.query.with_entities(models.miRNA.mir_ID, models.miRNA.hs_nr) \
            .filter(models.miRNA.mir_ID.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.miRNASchemaShort(many=True).dump(data).data
        else:
            abort(404, "No mimat number found for the given String")
    else:
        data = models.Gene.query.with_entities(models.Gene.ensg_number, models.Gene.gene_symbol) \
            .filter(models.Gene.gene_symbol.ilike(searchString + "%")) \
            .all()
        if len(data) > 0:
            return models.GeneSchemaShort(many=True).dump(data).data
        else:
            abort(404, "No gene symbol found for the given String")


def getGeneInformation(ensg_number = None, gene_symbol = None):
    """
    :param ensg_number:
    :param gene_symbol:
    :return: Available information for given gene identifier
    """

    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    # test if not both identification possibilites are given
    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    if ensg_number is not None:
        data = models.Gene.query \
            .filter(models.Gene.ensg_number.in_(ensg_number)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data).data
        else:
            abort(404, "No gene found with: " + ensg_number)

    elif gene_symbol is not None:
        data = models.Gene.query \
            .filter(models.Gene.gene_symbol.in_(gene_symbol)) \
            .all()

        if len(data) > 0:
            return models.GeneSchema(many=True).dump(data).data
        else:
            abort(404, "No gene found with: " + gene_symbol)





