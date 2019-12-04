from flask import abort
import models

def get_patient_information(disease_name=None, sample_ID=None):
    """
      :param disease_name: disease_name of interest
      :param sample_ID: sample ID of the patient of interest
      :return: all patient information for the samples of interest
      """

    #patient = []
    ## if sample_ID is given for specify patient, get the intern patient_ID(primary_key)
    #if (sample_ID is not None):
    #    patient = models.PatientInformation.query \
    #        .filter(models.PatientInformation.sample_ID.in_(sample_ID)) \
    #        .all()

    #if (len(patient) > 0):
    #    sample_IDs = [i.sample_ID for i in patient]
    #else:
    #    abort(404, "No samples found for given IDs)")

    ## save all needed queries to get correct results
    #queries = [models.PatientInformation.sample_ID.in_(sample_IDs)]

    # if specific disease_name is given:
    if disease_name is not None:
        dataset = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            queries = [models.PatientInformation.dataset_ID.in_(dataset_IDs)]
        else:
            abort(404, "No dataset with given disease_name found")

    if (sample_ID is not None):
        queries = [models.PatientInformation.sample_ID.in_(sample_ID)]

    result = models.PatientInformation.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.PatientInformationSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")

def get_survival_rate(disease_name, ensg_number = None, gene_symbol = None, sample_ID = None):
    """
       :param disease_name: disease_name of interest
       :param ensg_number: esng number of the gene of interest
       :param gene_symbol: gene symbol of the gene of interest
       :param sample_ID: sample_Id of patient/sample of interest
       :return: all "raw data" for genes of interest for plotting kaplan meier plots
       """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    gene = []
    queries = []
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
        # save all needed queries to get correct results
        queries.append(models.SurvivalRate.gene_ID.in_(gene_IDs))
    else:
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    patient = []
    # if sample_ID is given for specify patient, get the intern patient_ID(primary_key)
    if (sample_ID is not None):
        patient = models.PatientInformation.query \
            .filter(models.PatientInformation.sample_ID.in_(sample_ID)) \
            .all()

        if (len(patient) > 0):
            sample_IDs = [i.patient_information_ID for i in patient]
            print(sample_IDs)
            # save all needed queries to get correct results
            queries.append(models.SurvivalRate.patient_information_ID.in_(sample_IDs))
        else:
            abort(404, "No samples found for given IDs)")

    # if specific disease_name is given:
    if disease_name is not None:
        dataset = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            queries.append(models.SurvivalRate.dataset_ID.in_(dataset_IDs))
        else:
            abort(404, "No dataset with given disease_name found")

    result = models.SurvivalRate.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.SurvivalRateSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")

def get_survival_pValue(disease_name, ensg_number = None, gene_symbol = None):
    """
          :param disease_name: disease_name of interest
          :param ensg_number: esng number of the gene of interest
          :param gene_symbol: gene symbol of the gene of interest
          :return: all pValues for genes of interest for plotting kaplan meier plots
          """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)")

    gene = []
    queries = []
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
        # save all needed queries to get correct results
        queries.append(models.SurvivalPValue.gene_ID.in_(gene_IDs))
    else:
        abort(404, "Not gene found for given ensg_number(s) or gene_symbol(s)")

    # if specific disease_name is given:
    if disease_name is not None:
        dataset = models.Dataset.query \
            .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
            .all()

        if len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            queries.append(models.SurvivalPValue.dataset_ID.in_(dataset_IDs))
        else:
             abort(404, "No dataset with given disease_name found")

    result = models.SurvivalPValue.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.SurvivalPValueSchema(many=True).dump(result).data
    else:
        abort(404, "No data found.")


