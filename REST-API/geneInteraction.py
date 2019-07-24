from flask import abort
import models
import sqlalchemy as sa

def read_all_to_one_gene(disease_name=None, ensg_number = None, gene_symbol = None, pValue = None, pValueDirection = "<",
                         mscore = None, mscoreDirection = "<", correlation = None, correlationDirection ="<",information=True):
    """
    This function responds to a request for /sponge/ceRNANetwork/ceRNAInteraction/findAll?ensg_number={ensg_number}&gene_symbol={gene_symbol}&information={true|false}
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved
    :param disease_name: disease_name of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param pValue: pValue cutoff
    :param pValueDirection: < or >
    :param mscore mscore cutofff
    :param mscoreDirection: < or >
    :param correlation: correlation cutoff
    :param correlationDirection: < or >
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions given gene is involved
    """

    #test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    # if ensg_numer is given for specify gene, get the intern gene_ID(primary_key) for requested ensg_nr(gene_ID)
    if ensg_number is not None:
        gene = models.Gene.query \
            .filter(models.Gene.ensg_number == ensg_number) \
            .one_or_none()
    elif gene_symbol is not None:
        gene = models.Gene.query \
            .filter(models.Gene.gene_symbol == gene_symbol) \
            .one_or_none()

    #save all needed queries to get correct results
    queries = [sa.or_(models.GeneInteraction.gene_ID1 == gene.gene_ID,
        models.GeneInteraction.gene_ID2 == gene.gene_ID)]

    #if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name == disease_name) \
            .one_or_none()
        if run is not None:
            queries.append(models.GeneInteraction.run_ID == run.run_ID)
        else:
            abort(404, "No dataset with given disease_name found")

    # filter further depending on given statistics cutoffs
    if pValue is not None:
        if pValueDirection == "<":
            queries.append(models.GeneInteraction.p_value < pValue)
        else:
            queries.append(models.GeneInteraction.p_value > pValue)
    if mscore is not None:
        if mscoreDirection == "<":
            queries.append(models.GeneInteraction.mscore < mscore)
            print(models.GeneInteraction.mscore < mscore)
        else:
            queries.append(models.GeneInteraction.mscore > mscore)
    if correlation is not None:
        if correlationDirection == "<":
            queries.append(models.GeneInteraction.correlation < correlation)
        else:
            queries.append(models.GeneInteraction.correlation > correlation)

    interaction_result = models.GeneInteraction.query \
        .filter(*queries)\
        .limit(250)\
        .all()

    if interaction_result is not None:
        if disease_name is not None:
            if information:
                # Serialize the data for the response depending on parameter all
                schema = models.GeneInteractionLongSchema(many=True)
            else:
                # Serialize the data for the response depending on parameter all
                schema = models.GeneInteractionShortSchema(many=True)
        else:
            if information:
                # Serialize the data for the response depending on parameter all
                schema = models.GeneInteractionDatasetLongSchema(many=True)
            else:
                # Serialize the data for the response depending on parameter all
                schema = models.GeneInteractionDatasetShortSchema(many=True)
        return schema.dump(interaction_result).data
    else:
        abort(404, "No information with given parameters found")

def read_all_to_one_mirna(disease_name=None, mimat_number=None, information=True):
    """
    This function responds to a request for /sponge/ceRNANetwork/miRNAInteraction?disease_name={disease_name}&mimat_number={mimat_number}&information={true|false}
    and returns all interactions the given identification (ensg_number or gene_symbol) in all available datasets is in involved

    :param disease_name: disease_name: disease_name of interest
    :param mimat_number: Mimat number of miRNA of interest
    :param information: defines if each gene should contain all available information or not (default: True, if False: just ensg_nr will be shown)
    :return: all interactions the given miRNA is involved in
    """


    #get mir_ID from given mimat_number
    mirna = models.miRNA.query\
        .filter(models.miRNA.mir_ID == mimat_number)\
        .one_or_none()

    # save all needed queries to get correct results
    queries = [models.miRNAInteraction.miRNA_ID == mirna.miRNA_ID]

    # if specific disease_name is given:
    if disease_name is not None:
        run = models.Run.query.join(models.Dataset, models.Dataset.dataset_ID == models.Run.dataset_ID) \
            .filter(models.Dataset.disease_name == disease_name) \
            .one_or_none()
        if run is not None:
            queries.append(models.GeneInteraction.run_ID == run.run_ID)
        else:
            abort(404, "No dataset with given disease_name found")

    interaction_result = models.miRNAInteraction.query\
        .join(models.GeneInteraction, models.miRNAInteraction.interactions_genegene_ID == models.GeneInteraction.interactions_genegene_ID)\
        .filter(*queries)\
        .limit(50)\
        .all()

    if len(interaction_result) >= 1:
        if information:
            # Serialize the data for the response depending on parameter all
            schema = models.miRNAInteractionLongSchema(many=True)
            return schema.dump(interaction_result).data
        else:
            # Serialize the data for the response depending on parameter all
            schema = models.miRNAInteractionShortSchema(many=True)
            return schema.dump(interaction_result).data
    else:
        abort(404, "No data found with input paramter")





