from flask import jsonify
import app.models as models
from app.config import LATEST, db
from app.controllers.dataset import _dataset_query

def get_patient_information(dataset_ID: int = None, disease_name=None, disease_subtype=None, sample_ID: list=None):
    """
    API call /survivalAnalysis/sampleInformation
    to get all available clinical information for patients/samples
    :param dataset_ID: dataset_ID of the dataset of interest
    :param disease_name: disease_name of interest
    :param disease_subtype: disease_subtype of interest
    :param sample_ID: sample ID of the patient of interest
    :param sponge_db_version: version of the database
    :return: all patient information for the samples of interest
      """

    query = db.select(models.PatientInformation)

    if dataset_ID is not None:
        dataset = _dataset_query(sponge_db_version='any', dataset_ID=dataset_ID)
        if type(dataset) == list and len(dataset) > 0:
            dataset_IDs = [i.dataset_ID for i in dataset]
            query = query.where(models.PatientInformation.dataset_ID.in_(dataset_IDs))
        else:
            return jsonify({
                "detail": "No dataset with given disease_name found",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400
        
    if disease_name is not None or disease_subtype is not None:
        disease = db.select(models.Disease)
        if disease_name is not None:
            disease = disease.where(models.Disease.disease_name == disease_name)
        if disease_subtype is not None:
            disease = disease.where(models.Disease.disease_subtype == disease_subtype)
        diseases = db.session.execute(disease).scalars().all()
        disease_IDs = [i.disease_ID for i in diseases]
        query = query.where(models.PatientInformation.disease_ID.in_(disease_IDs))

    if (sample_ID is not None):
        query = query.where(models.PatientInformation.sample_ID.in_(sample_ID))

    result = db.session.execute(query).scalars().all()

    if len(result) > 0:
        return models.PatientInformationSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_survival_rate(dataset_ID: int = None, disease_name: str = None, disease_subtype: str = None, ensg_number = None, gene_symbol = None, sample_ID = None):
    """
    API call /survivalAnalysis/getRates
    Get all raw data for kaplan meier plots
    :param dataset_ID: dataset_ID of the dataset of interest
    :param disease_name: disease_name of interest
    :param disease_subtype: disease_subtype of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param sample_ID: sample_Id of patient/sample of interest
    :param sponge_db_version: version of the database
    :return: all "raw data" for genes of interest for plotting kaplan meier plots
       """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

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
        return jsonify({
            "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


    patient = []
    # if sample_ID is given for specify patient, get the intern patient_ID(primary_key)
    if (sample_ID is not None):
        patient = models.PatientInformation.query \
            .filter(models.PatientInformation.sample_ID.in_(sample_ID)) \
            .all()

        if (len(patient) > 0):
            sample_IDs = [i.patient_information_ID for i in patient]
            # save all needed queries to get correct results
            queries.append(models.SurvivalRate.patient_information_ID.in_(sample_IDs))
        else:
            return jsonify({
                "detail": "No samples found for given IDs",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

    # filter for database version
    dataset = _dataset_query(sponge_db_version=1, disease_name=disease_name, disease_subtype=disease_subtype, dataset_ID=dataset_ID)
    
    if len(dataset) > 0:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.SurvivalRate.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.SurvivalRate.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.SurvivalRateSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_survival_pValue(dataset_ID: int = None, disease_name: str = None, disease_subtype: str = None, ensg_number = None, gene_symbol = None):
    """
    API call /survivalAnalysis/getPValues
    Retrieve pValues from log rank test based on raw survival analysis data
    :param disease_name: disease_name of interest
    :param disease_subtype: disease_subtype of interest
    :param ensg_number: esng number of the gene of interest
    :param gene_symbol: gene symbol of the gene of interest
    :param sponge_db_version: version of the database
    :return: all pValues for genes of interest for plotting kaplan meier plots
    """
    # test if any of the two identification possibilites is given
    if ensg_number is None and gene_symbol is None:
        return jsonify({
            "detail": "One of the two possible identification numbers must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if ensg_number is not None and gene_symbol is not None:
        return jsonify({
            "detail": "More than one identifikation paramter is given. Please choose one out of (ensg number, gene symbol)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

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
        return jsonify({
            "detail": "No gene found for given ensg_number(s) or gene_symbol(s)",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # filter for database version
    dataset = _dataset_query(disease_name=disease_name, disease_subtype=disease_subtype, dataset_ID=dataset_ID)

    if len(dataset) > 0 and getattr(dataset[0], 'dataset_ID', None) is not None:
        dataset_IDs = [i.dataset_ID for i in dataset]
        queries.append(models.SurvivalPValue.dataset_ID.in_(dataset_IDs))
    else:
        return jsonify({
            "detail": "No dataset with given disease_name found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    result = models.SurvivalPValue.query \
        .filter(*queries) \
        .all()

    if len(result) > 0:
        return models.SurvivalPValueSchema(many=True).dump(result)
    else:
        return jsonify({
            "detail": "No results!",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


