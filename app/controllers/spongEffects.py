import json
import os
import random
import string
import subprocess
import tempfile
from flask import request, jsonify, abort
import app.config as config
import app.models as models
from app.config import LATEST, db


def get_spongEffects_run_ID(dataset_ID: int = None, disease_name: str = None, level: str = "gene", sponge_db_version: int = LATEST):
    """

    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: spongEffects_run_ID for given disease name and level
    """
     # old
    # query = db.session.execute(
    #     "SELECT sEr.spongEffects_run_ID from spongEffects_run_performance"
    #     " JOIN spongEffects_run sEr on spongEffects_run_performance.spongEffects_run_ID = sEr.spongEffects_run_ID"
    #     " JOIN sponge_run sr on sEr.sponge_run_ID = sr.sponge_run_ID"
    #     " JOIN dataset d on sr.dataset_ID = d.dataset_ID"
    #     f" WHERE d.disease_name LIKE '%{disease_name}%'"
    #     f" AND d.sponge_db_version = {sponge_db_version}"
    #     f" AND level = '{level}'"
    #     " AND split_type = 'train'"
    #     " ORDER BY accuracy_upper DESC"
    #     " LIMIT 1;"
    # ).fetchall()

    # Build the query
    query = db.select(models.SpongeRun.sponge_run_ID)

    # join with dataset if necessary 
    if dataset_ID is not None or disease_name is not None:
        query = query.join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID)

    # filter for sponge_db_version
    query = query.where(models.Dataset.sponge_db_version == sponge_db_version)

    if dataset_ID is not None:
        query = query.where(models.SpongeRun.dataset_ID == dataset_ID)
    if disease_name is not None:
        query = query.where(models.Dataset.disease_name.like(f"%{disease_name}%"))

    # Execute the query and fetch the sponge_run_ID
    sponge_run_IDs = db.session.execute(query).scalars().all()

    if len(sponge_run_IDs) == 0:
        abort(404, f"No sponge run found for disease_name: {disease_name} and dataset_ID: {dataset_ID}")

    # Build the query to get spong_effects_run_ID
    query = db.select(models.SpongEffectsRun.spongEffects_run_ID).where(models.SpongEffectsRun.sponge_run_ID.in_(sponge_run_IDs))

    # filter for level 
    if level is not None:
        query = query.where(models.SpongEffectsRun.level == level)

    # Execute the query and fetch the result
    spong_effects_run_IDs = db.session.execute(query).scalars().all()

    if len(spong_effects_run_IDs) == 0:
        abort(404, f"No spongEffects run found for sponge_run_ID: {sponge_run_IDs}")

    else:
        return spong_effects_run_IDs


def get_run_performance(dataset_ID: int = None, disease_name: str = None, level: str = 'gene', sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getRunPerformance
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: Best spongEffects model performances for given disease and level
    """
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, level, sponge_db_version)
    query = models.SpongEffectsRunPerformance.query \
        .join(models.SpongEffectsRun, models.SpongEffectsRun.spongEffects_run_ID == models.SpongEffectsRunPerformance.spongEffects_run_ID) \
        .filter(models.SpongEffectsRun.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .all()

    if len(query) > 0:
        return models.SpongEffectsRunPerformanceSchema(many=True).dump(query)
    else:
        abort(404, 'No spongEffects model performance found for name: {disease_name}'.format(disease_name=disease_name))


def get_run_class_performance(dataset_ID: int = None, disease_name: str = None, level: str = 'gene', sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getRunClassPerformance
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: Best spongEffects model class performances for given disease and level
    """
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, level, sponge_db_version)
    query = models.SpongEffectsRunClassPerformance.query \
        .join(models.SpongEffectsRunPerformance,
              models.SpongEffectsRunPerformance.spongEffects_run_performance_ID == models.SpongEffectsRunClassPerformance.spongEffects_run_performance_ID) \
        .filter(models.SpongEffectsRunPerformance.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .all()
    if len(query) > 0:
        return models.SpongEffectsRunClassPerformanceSchema(many=True).dump(query)
    else:
        abort(404, f'No spongEffects run class performance found for name: {disease_name}')


def get_enrichment_score_class_distributions(dataset_ID: int = None, disease_name: str = None, level: str = 'gene', sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/enrichmentScoreDistributions?disease_name={disease_name}
    Get spongEffects enrichment score distributions for a given disease_name
    :param dataset_ID: Dataset ID as string
    :param disease_name: Name of the disease to filter for
    :param level: one of gene/transcript
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: enrichment score class distribution for all available subtypes of given disease
    """
    level = level.lower()
    if level not in ['gene', 'transcript']:
        abort(404, 'Provided level not recognised, please use one of gene/transcript')
    # extract spongEffects_run_ID
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, level, sponge_db_version)
    # extract density data for spongEffects run
    query = models.SpongEffectsEnrichmentClassDensity.query \
        .filter(models.SpongEffectsEnrichmentClassDensity.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .all()
    if len(query) > 0:
        return models.SpongEffectsEnrichmentClassDensitySchema(many=True).dump(query)
    else:
        abort(404, 'No spongEffects class enrichment score distribution data found for given parameters')


def get_gene_modules(dataset_ID: int = None, disease_name: str = None, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getSpongEffectsGeneModules
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: Best spongEffects gene modules for given disease
    """
    # get spongEffects_run_ID
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, "gene", sponge_db_version)
    # get modules
    # query = db.session.execute(
    #     "SELECT * FROM spongEffects_gene_module as A"
    #     " JOIN gene g ON A.gene_ID = g.gene_ID"
    #     f" WHERE spongEffects_run_ID = {spongEffects_run_ID}"
    #     " ORDER BY mean_accuracy_decrease DESC, mean_accuracy_decrease DESC;"
    # ).fetchall()

    query = db.select(models.SpongEffectsGeneModule) \
        .where(models.SpongEffectsGeneModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .order_by(models.SpongEffectsGeneModule.mean_accuracy_decrease.desc(), models.SpongEffectsGeneModule.mean_accuracy_decrease.desc())

    query = db.session.execute(query).scalars().all()

    if len(query) > 0:
        return models.SpongEffectsGeneModuleSchema(many=True).dump(query)
    else:
        abort(404, "No spongEffects modules found for given disease")


def get_gene_module_members(dataset_ID: int = None, disease_name: str = None, ensg_number: str = None, gene_symbol: str = None, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getGeneModuleMembers
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param ensg_number: ENSG number of gene
    :param gene_symbol: Gene symbol
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: spongEffects gene module members for given disease and gene identifier
    """
    # get spongEffects_run_ID
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, "gene", sponge_db_version)
    # test if any of the two identification possibilities is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identification parameter is given. Please choose one out of (ensg_number, gene symbol)")

    # determine search method
    if ensg_number is not None:
        search_key: str = "ensg_number"
        search_val = ensg_number
    else:
        search_key: str = "gene_symbol"
        search_val = gene_symbol

    search_split = search_val.split(",")
    if len(search_split) > 0:
        search_val = ["'"+s+"'" for s in search_split]
        search_val = ",".join(search_val)
    else:
        search_val = "'"+search_val+"'"
    # search DB
    # query = db.session.execute(
    #     "SELECT gA.ensg_number AS hub_ensg_number, gA.gene_symbol AS hub_gene_symbol,"
    #     " g.ensg_number AS member_ensg_number, g.gene_symbol as member_gene_symbol"
    #     " FROM spongEffects_gene_module_members as A"
    #     " JOIN spongEffects_gene_module sEgm on A.spongEffects_gene_module_ID = sEgm.spongEffects_gene_module_ID"
    #     " JOIN gene g on g.gene_ID = A.gene_ID"
    #     " JOIN gene gA on gA.gene_ID = sEgm.gene_ID"
    #     f" WHERE gA.{search_key} IN ({search_val}) AND spongEffects_run_ID = {spongEffects_run_ID};"
    # ).fetchall()

    query = db.select(models.SpongEffectsGeneModuleMembers) \
        .join(models.SpongEffectsGeneModule, models.SpongEffectsGeneModuleMembers.spongEffects_gene_module_ID == models.SpongEffectsGeneModule.spongEffects_gene_module_ID) \
        .join(models.Gene, models.SpongEffectsGeneModuleMembers.gene_ID == models.Gene.gene_ID) \
        .join(models.Gene, models.SpongEffectsGeneModule.gene_ID == models.Gene.gene_ID) \
        .where(models.SpongEffectsGeneModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .where(getattr(models.Gene, search_key).in_(search_val))
    
    query = db.session.execute(query).scalars().all()
    
    if len(query) > 0:
        return models.SpongEffectsGeneModuleMembersSchema(many=True).dump(query)
    else:
        abort(404, "No module members found for given disease name and gene identifier")


def get_transcript_modules(dataset_ID: int = None, disease_name: str = None, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getSpongEffectsTranscriptModules
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: module hub elements for a given disease and level
    """
    
    # get spongEffects_run_ID
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, "transcript", sponge_db_version)

    # get modules
    # query = db.session.execute(
    #     "SELECT * FROM spongEffects_transcript_module as A"
    #     " JOIN transcript t ON A.transcript_ID = t.transcript_ID"
    #     " JOIN gene g ON t.gene_ID = g.gene_ID"
    #     f" WHERE spongEffects_run_ID = {spongEffects_run_ID}"
    #     " ORDER BY mean_accuracy_decrease DESC, mean_accuracy_decrease DESC;"
    # ).fetchall()

    query = db.select(models.SpongEffectsTranscriptModule) \
        .join(models.Transcript, models.SpongEffectsTranscriptModule.transcript_ID == models.Transcript.transcript_ID) \
        .join(models.Gene, models.Transcript.gene_ID == models.Gene.gene_ID) \
        .where(models.SpongEffectsTranscriptModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .order_by(models.SpongEffectsTranscriptModule.mean_accuracy_decrease.desc(), models.SpongEffectsTranscriptModule.mean_accuracy_decrease.desc())
    
    query = db.session.execute(query).scalars().all()

    if len(query) > 0:
        return models.SpongEffectsTranscriptModuleSchema(many=True).dump(query)
    else:
        abort(404, "No spongEffects modules found for given disease")


def get_transcript_module_members(dataset_ID: int = None, disease_name: str = None, enst_number: str = None, ensg_number: str = None, gene_symbol: str = None, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getTranscriptModuleMembers
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param enst_number: ENST number of transcript
    :param ensg_number: ENSG number of gene
    :param gene_symbol: Gene symbol
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: spongEffects transcript module members for given disease and gene identifier    
    """
    # get spongEffects_run_ID
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, "gene", sponge_db_version)
    # test if any of the two identification possibilities is given
    tests: list = [enst_number is not None, ensg_number is not None, gene_symbol is not None]
    if sum(tests) == 0:
        abort(404, "One of the three possible identification numbers must be provided")
    elif sum(tests) > 1:
        abort(404,
              "More than one identification parameter is given. Please choose one out of (enst_number, ensg_number, or gene symbol)")

    # determine search method
    search_key: str
    search_val: str
    if tests[0]:
        search_key = "enst_number"
        search_val = enst_number
    elif tests[1]:
        search_key = "ensg_number"
        search_val = ensg_number
    else:
        search_key = "gene_symbol"
        search_val = gene_symbol
    if isinstance(search_val, list):
        search_val = "','".join(search_val)
    else:
        search_val = "'"+search_val+"'"
    # search DB
    # query = db.session.execute(
    #     "SELECT tA.enst_number as hub_enst_number, t.enst_number as member_enst_number"
    #     " gA.ensg_number AS hub_ensg_number, gA.gene_symbol AS hub_gene_symbol,"
    #     " g.ensg_number AS member_ensg_number, g.gene_symbol as member_gene_symbol"
    #     " FROM spongEffects_transcript_module_members as A"
    #     " JOIN spongEffects_transcript_module sEtm on A.spongEffects_transcript_module_ID = sEtm.spongEffects_transcript_module_ID"
    #     " JOIN transcript t on t.transcript_ID = A.transcript_ID"
    #     " JOIN transcript tA on tA.transcript_ID = sEtm.transcript_ID"
    #     " JOIN gene g on g.gene_ID = t.gene_ID"
    #     " JOIN gene gA on gA.gene_ID = tA.gene_ID"
    #     f" WHERE tA.{search_key} IN ({search_val}) AND spongEffects_run_ID = {spongEffects_run_ID};"
    # ).fetchall()

    query = db.select(models.SpongEffectsTranscriptModuleMembers) \
        .join(models.SpongEffectsTranscriptModule, models.SpongEffectsTranscriptModuleMembers.spongEffects_transcript_module_ID == models.SpongEffectsTranscriptModule.spongEffects_transcript_module_ID) \
        .join(models.Transcript, models.SpongEffectsTranscriptModuleMembers.transcript_ID == models.Transcript.transcript_ID) \
        .join(models.Transcript, models.SpongEffectsTranscriptModule.transcript_ID == models.Transcript.transcript_ID) \
        .join(models.Gene, models.Transcript.gene_ID == models.Gene.gene_ID) \
        .join(models.Gene, models.SpongEffectsTranscriptModule.gene_ID == models.Gene.gene_ID) \
        .where(models.SpongEffectsTranscriptModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .where(getattr(models.Gene, search_key).in_(search_val))
    
    query = db.session.execute(query).scalars().all()

    if len(query) > 0:
        return models.SpongEffectsGeneModuleMembersSchema(many=True).dump(query)
    else:
        abort(404, "No module members found for given disease name and gene identifier")

def generate_random_filename(length=12, extension=None):
    """
    Generate a random filename
    :param length: Length of the random string
    :param extension: Optional file extension
    :return: Random filename    
    """
    # Define characters to use for generating the random filename
    characters = string.ascii_letters + string.digits
    # Generate a random string of the specified length
    random_string = ''.join(random.choice(characters) for _ in range(length))
    # Add an extension if provided
    if extension:
        random_filename = f"{random_string}.{extension}"
    else:
        random_filename = random_string
    return random_filename


class Params:
    mscor: float
    fdr: float
    min_size: float
    max_size: float
    min_expr: float
    method: str

    def __init__(self, params):
        self.mscor = params["mscor"]
        self.fdr = params["fdr"]
        self.min_size = params["min_size"]
        self.max_size = params["max_size"]
        self.min_expr = params["min_expr"]
        self.method = params["method"]

    def get_cmd_options(self):
        cmd: list = []
        for name, value in vars(self).items():
            cmd.append(f'--{name}')
            cmd.append(value)
        return cmd


def run_spongEffects(file_path, out_path, params: Params = None, log: bool = False, subtype_level: bool = False):
    """
    Predict cancer type for an uploaded gene/transcript expression
    :param file_path: path to uploaded expression file
    :param out_path: output file path
    :param params: spongEffects run parameters
    :param log: Flag for R code
    :param subtype_level: Flag to predict subtypes
    :return: JSON object with type prediction for each sample
    """
    # build command
    cmd = [
        "Rscript", config.SPONGEFFECTS_PREDICT_SCRIPT,
        "--expr", file_path,
        "--model_path", config.MODEL_PATH,
        "--output", out_path,
        "--local"
    ]
    if subtype_level:
        cmd.append("--subtypes")
    if log:
        cmd.append("--log")
    if params and isinstance(params, Params):
        cmd.extend(params.get_cmd_options())
    try:
        # execute command
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # get prediction output
        stderr = process.stderr
        with open(out_path, 'r') as json_file:
            return json.load(json_file)
    except subprocess.CalledProcessError as e:
        abort(500, e)


def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    # save uploaded file
    uploaded_file = request.files['file']
    # save prediction level
    predict_subtypes: bool = request.form.get('subtypes') == "true"
    # save given parameters
    run_parameters: Params = Params(request.form)
    apply_log_scale: bool = request.form.get('log') == "true"
    if uploaded_file.filename == '':
        abort(404, "File upload failed")
    # create tmp upload file
    tempfile.tempdir = config.UPLOAD_DIR
    tmp_file = tempfile.NamedTemporaryFile(prefix="upload_", suffix=".txt")
    # save file to uploads folder
    uploaded_file.save(tmp_file.name)
    # create random output path
    tmp_out_file = tempfile.NamedTemporaryFile(prefix="prediction_", suffix=".json")
    # run spongEffects
    return jsonify(run_spongEffects(tmp_file.name, tmp_out_file.name, run_parameters,
                                    log=apply_log_scale, subtype_level=predict_subtypes))


def get_spongeffects_runs(dataset_ID: str = None, disease_name: str = None, include_empty_spongeffects: bool = False, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getSpongEffectsRun
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param include_empty: Include datasets/sponge runs without spongEffects runs
    :return: spongEffects runs for given disease and disease information
    """

    # Construct the query using db.select
    query = db.select(
        models.SpongeRun,
        models.SpongEffectsRun,
        models.Dataset
    ).join(
        models.SpongEffectsRun, models.SpongeRun.sponge_run_ID == models.SpongEffectsRun.sponge_run_ID, isouter=True
    ).join(
        models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID, isouter=True
    )

    if dataset_ID is not None:
        query = query.where(models.Dataset.dataset_ID == dataset_ID)

    if disease_name is not None:
        query = query.where(models.Dataset.disease_name.like(f"%{disease_name}%"))

    if sponge_db_version is not None:
        query = query.where(models.Dataset.sponge_db_version == sponge_db_version)

    # Execute the query
    result = db.session.execute(query)

    # Fetch results as a list of rows
    data = result.fetchall()

    # Did we find a dataset?
    if len(data) > 0:
        # Serialize the data for the response
        combined_data = []
        for sponge_run, sponge_effects_run, dataset in data:
            if sponge_effects_run is None and not include_empty_spongeffects:
                continue
            # append all attributes but not the nested ones. Add all keys, use None values for missing attributes.
            combined_data.append({
                **{x: y for x,y in models.DatasetSchema().dump(dataset or models.Dataset()).items() if type(y) is not dict},
                **{x: y for x,y in models.SpongEffectsRunSchema(exclude=['sponge_run']).dump(sponge_effects_run or models.SpongEffectsRun()).items() if type(y) is not dict},
                **{x: y for x,y in models.SpongeRunSchema(exclude=['dataset']).dump(sponge_run or models.SpongeRun()).items() if type(y) is not dict}
            })
        return jsonify(combined_data)
    else:
        abort(404, 'No spongEffects run found for name: {disease_name}'.format(disease_name=disease_name))
