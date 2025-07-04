import json
import os
import random
import string
import subprocess
import tempfile
from flask import request, jsonify
import app.config as config
from app.controllers.externalInformation import get_genes, get_transcripts
import app.models as models
from app.config import LATEST, db, logger
import traceback    


def get_spongEffects_run_ID(dataset_ID: int = None, disease_name: str = None, level: str = "gene", 
                            spongEffects_params: dict = None,
                            sponge_db_version: int = LATEST):
    """
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param spongEffects_params: Select only runs with given parameters
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

    query = db.select(models.SpongeRun.sponge_run_ID).join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID)

    # Filter for sponge_db_version
    query = query.where(models.Dataset.sponge_db_version == sponge_db_version)

    if dataset_ID is not None:
        query = query.where(models.SpongeRun.dataset_ID == dataset_ID)
    if disease_name is not None:
        query = query.where(models.Dataset.disease_name.like(f"%{disease_name}%"))

    # Execute the query and fetch the sponge_run_ID
    sponge_run_IDs = db.session.execute(query).scalars().all()

    if len(sponge_run_IDs) == 0:
        return jsonify({
            "detail": f"No sponge run found for disease_name: {disease_name} and dataset_ID: {dataset_ID}",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # Build the query to get spong_effects_run_ID
    query = db.select(models.SpongEffectsRun).where(models.SpongEffectsRun.sponge_run_ID.in_(sponge_run_IDs))

    # filter for level 
    if level is not None:
        query = query.where(models.SpongEffectsRun.level == level)

    # filter for spongEffects_params
    if spongEffects_params is not None:
        for key, value in spongEffects_params.items():
            if value is None:
                continue
            if hasattr(models.SpongEffectsRun, key):
                query = query.where(getattr(models.SpongEffectsRun, key) == value)
            else:
                return ValueError("Invalid parameter: {key}")

    # Execute the query and fetch the result
    spong_effects_run_IDs = db.session.execute(query).scalars().all()

    spong_effects_run_IDs = [spong_effects_run_ID.spongEffects_run_ID for spong_effects_run_ID in spong_effects_run_IDs]
    
    return spong_effects_run_IDs


def get_run_performance(dataset_ID: int = None, disease_name: str = None, level: str = 'gene', 
                        m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None,
                        sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getRunPerformance
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param m_scor_threshold: Minimum m_scor threshold
    :param p_adj_threshold: Minimum p_adj threshold
    :param modules_cutoff: Minimum number of modules
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: Best spongEffects model performances for given disease and level
    """
    spongEffects_params = {
        "m_scor_threshold": m_scor_threshold,
        "p_adj_threshold": p_adj_threshold,
        "modules_cutoff": modules_cutoff
    }
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, level, spongEffects_params, sponge_db_version)
    query = models.SpongEffectsRunPerformance.query \
        .join(models.SpongEffectsRun, models.SpongEffectsRun.spongEffects_run_ID == models.SpongEffectsRunPerformance.spongEffects_run_ID) \
        .filter(models.SpongEffectsRun.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .all()

    if len(query) > 0:
        return models.SpongEffectsRunPerformanceSchema(many=True).dump(query)
    else:
        return jsonify({
            "detail": 'No spongEffects model performance found for name: {disease_name}'.format(disease_name=disease_name),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_run_class_performance(dataset_ID: int = None, disease_name: str = None, level: str = 'gene', 
                              m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None,                    
                              sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getRunClassPerformance
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param m_scor_threshold: Minimum m_scor threshold
    :param p_adj_threshold: Minimum p_adj threshold
    :param modules_cutoff: Minimum number of modules
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: Best spongEffects model class performances for given disease and level
    """
    spongEffects_params = {
        "m_scor_threshold": m_scor_threshold,
        "p_adj_threshold": p_adj_threshold,
        "modules_cutoff": modules_cutoff
    }
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, level, spongEffects_params, sponge_db_version)
    query = models.SpongEffectsRunClassPerformance.query \
        .join(models.SpongEffectsRunPerformance,
              models.SpongEffectsRunPerformance.spongEffects_run_performance_ID == models.SpongEffectsRunClassPerformance.spongEffects_run_performance_ID) \
        .filter(models.SpongEffectsRunPerformance.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .all()
    if len(query) > 0:
        return models.SpongEffectsRunClassPerformanceSchema(many=True).dump(query)
    else:
        return jsonify({
            "detail": f'No spongEffects run class performance found for name: {disease_name}',
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_enrichment_score_class_distributions(dataset_ID: int = None, disease_name: str = None, level: str = 'gene', 
                                             m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None, 
                                             sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/enrichmentScoreDistributions?disease_name={disease_name}
    Get spongEffects enrichment score distributions for a given disease_name
    :param dataset_ID: Dataset ID as string
    :param disease_name: Name of the disease to filter for
    :param level: one of gene/transcript
    :param m_scor_threshold: Minimum m_scor threshold
    :param p_adj_threshold: Minimum p_adj threshold
    :param modules_cutoff: Minimum number of modules
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: enrichment score class distribution for all available subtypes of given disease
    """
    level = level.lower()
    if level not in ['gene', 'transcript']:
        return jsonify({
            "detail": "Provided level not recognised, please use one of gene/transcript'",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400


    # extract spongEffects_run_ID
    spongEffects_params = {
        "m_scor_threshold": m_scor_threshold,
        "p_adj_threshold": p_adj_threshold,
        "modules_cutoff": modules_cutoff
    }
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, level, spongEffects_params, sponge_db_version)
        # extract density data for spongEffects run
    query = models.SpongEffectsEnrichmentClassDensity.query \
        .filter(models.SpongEffectsEnrichmentClassDensity.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .all()
    if len(query) > 0:
        return models.SpongEffectsEnrichmentClassDensitySchema(many=True).dump(query)
    else:
        return jsonify({
            "detail": 'No spongEffects class enrichment score distribution data found for given parameters',
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_gene_modules(spongEffects_gene_module_ID: int = None, dataset_ID: int = None, disease_name: str = None, gene_ID: str = None, ensg_number: str = None, gene_symbol: str = None, limit: int = None, offset: int = None, 
                     m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None, 
                     sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getSpongEffectsGeneModules
    :param spongEffects_gene_module_ID: Gene module ID as string
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param gene_ID: Gene ID as string
    :param ensg_number: ENSG number of gene
    :param gene_symbol: Gene symbol
    :param limit: Limit for the number of results
    :param offset: Offset for the number of results
    :param m_scor_threshold: Minimum m_scor threshold
    :param p_adj_threshold: Minimum p_adj threshold
    :param modules_cutoff: Minimum number of modules
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: Best spongEffects gene modules for given disease
    """
    # get spongEffects_run_ID
    spongEffects_params = {
        "m_scor_threshold": m_scor_threshold,
        "p_adj_threshold": p_adj_threshold,
        "modules_cutoff": modules_cutoff
    }
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, 'gene', spongEffects_params, sponge_db_version)
    
    # get the gene ids
    gene_data = get_genes(gene_ID, ensg_number, gene_symbol)
    gene_IDs = [gene.gene_ID for gene in gene_data]
    
    # get the modules
    query = db.select(models.SpongEffectsGeneModule) \
        .where(models.SpongEffectsGeneModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .where(models.SpongEffectsGeneModule.gene_ID.in_(gene_IDs)) \
        .order_by(models.SpongEffectsGeneModule.mean_accuracy_decrease.desc(), models.SpongEffectsGeneModule.mean_accuracy_decrease.desc())

    if spongEffects_gene_module_ID is not None:
        query = query.where(models.SpongEffectsGeneModule.spongEffects_gene_module_ID == spongEffects_gene_module_ID)

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    query = db.session.execute(query).scalars().all()

    if len(query) > 0:
        return models.SpongEffectsGeneModuleSchema(many=True).dump(query)
    else:
        return []


def get_gene_module_members(spongEffects_gene_module_ID: int = None, dataset_ID: int = None, disease_name: str = None, gene_ID: str = None, ensg_number: str = None, gene_symbol: str = None, limit: int = None, offset: int = None, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getSpongEffectsGeneModuleMembers
    :param spongEffects_gene_module_ID: Gene module ID as string
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param gene_ID: Gene ID as string
    :param ensg_number: ENSG number of gene
    :param gene_symbol: Gene symbol
    :param limit: Limit for the number of results
    :param offset: Offset for the number of results
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: spongEffects gene module members for given disease and gene identifier
    """
    # get the modules using get_gene_modules
    modules = get_gene_modules(spongEffects_gene_module_ID, dataset_ID, disease_name, gene_ID, ensg_number, gene_symbol, sponge_db_version)
    module_IDs = [module['spongEffects_gene_module_ID'] for module in modules]
    if len(module_IDs) == 0:
        return jsonify({
            "detail": "No spongEffects gene modules found for given parameters",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # get the members
    query = db.select(models.SpongEffectsGeneModuleMembers) \
        .where(models.SpongEffectsGeneModuleMembers.spongEffects_gene_module_ID.in_(module_IDs))

    # # get the members directly by joins (this is slower):
    # query = db.select(models.SpongEffectsGeneModuleMembers) \
    #     .join(models.SpongEffectsGeneModule, models.SpongEffectsGeneModuleMembers.spongEffects_gene_module_ID == models.SpongEffectsGeneModule.spongEffects_gene_module_ID) \
    #     .join(models.Gene, models.SpongEffectsGeneModule.gene_ID == models.Gene.gene_ID) \
    #     .where(models.SpongEffectsGeneModule.spongEffects_run_ID.in_(spongEffects_run_IDs))

    # if ensg_number is not None:
    #     query = query.where(models.Gene.ensg_number == ensg_number)

    # if gene_symbol is not None:
    #     query = query.where(models.Gene.gene_symbol == gene_symbol)

    # elif gene_ID is not None:
    #     query.where(models.Gene.gene_ID == gene_ID)

    # add limit to the query
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    data = db.session.execute(query).scalars().all()
    
    if len(data) > 0:
        return models.SpongEffectsGeneModuleMembersSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": "No module members found for given disease name and gene identifier",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


def get_transcript_modules(spongEffects_transcript_module_ID: int = None, dataset_ID: int = None, disease_name: str = None, gene_ID: str = None, ensg_number: str = None, gene_symbol: str = None, transcript_ID: int = None, enst_number: int = None, limit: int = None, offset: int = None, 
                           m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None, 
                           sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getSpongEffectsTranscriptModules
    :param spongEffects_transcript_module_ID: Transcript module ID as string
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param gene_ID: Gene ID as string
    :param ensg_number: ENSG number of gene
    :param gene_symbol: Gene symbol
    :param transcript_ID: Transcript ID as string
    :param enst_number: ENST number of transcript
    :param limit: Limit for the number of results
    :param offset: Offset for the number of results
    :param m_scor_threshold: Minimum m_scor threshold
    :param p_adj_threshold: Minimum p_adj threshold
    :param modules_cutoff: Minimum number of modules
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: module hub elements for a given disease and level
    """

    # get spongEffects_run_ID
    spongEffects_params = {
        "m_scor_threshold": m_scor_threshold,
        "p_adj_threshold": p_adj_threshold,
        "modules_cutoff": modules_cutoff
    }
    spongEffects_run_IDs = get_spongEffects_run_ID(dataset_ID, disease_name, 'transcript', spongEffects_params, sponge_db_version)
    
    # get the transcripts
    transcript_data = get_transcripts(gene_ID, ensg_number, gene_symbol, transcript_ID, enst_number)
    transcript_IDs = [transcript.transcript_ID for transcript in transcript_data]

    query = db.select(models.SpongEffectsTranscriptModule) \
        .where(models.SpongEffectsTranscriptModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .where(models.SpongEffectsTranscriptModule.transcript_ID.in_(transcript_IDs)) \
        .order_by(models.SpongEffectsTranscriptModule.mean_accuracy_decrease.desc(), models.SpongEffectsTranscriptModule.mean_accuracy_decrease.desc())

    if spongEffects_transcript_module_ID is not None:
        modules_query = modules_query.where(models.SpongEffectsTranscriptModule.spongEffects_transcript_module_ID == spongEffects_transcript_module_ID)

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
        
    query = db.session.execute(query).scalars().all()

    if len(query) > 0:
        return models.SpongEffectsTranscriptModuleSchema(many=True).dump(query)
    else:
        return []


def get_transcript_module_members(spongEffects_transcript_module_ID: int = None, dataset_ID: int = None, disease_name: str = None, gene_ID: int = None, ensg_number: str = None, gene_symbol: str = None, transcript_ID: int = None, enst_number: str = None, limit: int = None, offset: int = None, sponge_db_version: int = LATEST):
    """
    API request for /spongEffects/getTranscriptModuleMembers
    :param spongEffects_transcript_module_ID: Transcript module ID as string
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param gene_ID: Gene ID as string
    :param ensg_number: ENSG number of gene
    :param gene_symbol: Gene symbol
    :param transcript_ID: Transcript ID as string
    :param enst_number: ENST number of transcript
    :param limit: Limit for the number of results
    :param offset: Offset for the number of results
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: spongEffects transcript module members for given disease and gene identifier    
    """
    limit = request.args.get('limit', default=100, type=int)

    # get the modules using get_transcript_modules
    modules = get_transcript_modules(spongEffects_transcript_module_ID, dataset_ID, disease_name, gene_ID, ensg_number, gene_symbol, transcript_ID, enst_number, sponge_db_version)
    module_IDs = [module['spongEffects_transcript_module_ID'] for module in modules]

    if len(module_IDs) == 0:
        return jsonify({
            "detail": "No spongEffects transcript modules found for given parameters",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # get the members
    query = db.select(models.SpongEffectsTranscriptModuleMembers) \
        .where(models.SpongEffectsTranscriptModuleMembers.spongEffects_transcript_module_ID.in_(module_IDs))

    # add limit to the query
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    data = db.session.execute(query).scalars().all()

    if len(data) > 0:
        return models.SpongEffectsTranscriptModuleMembersSchema(many=True).dump(data)
    else:
        return jsonify({
            "detail": "No module members found for given disease name and gene identifier",
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200


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
            if name == "method":
                value = value.lower()
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
        logger.info(f"Running spongEffects with command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # get prediction output
        stderr = process.stderr
        logger.info(stderr)
        with open(out_path, 'r') as json_file:
            return json.load(json_file)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running spongEffects: {e}, traceback: {traceback.print_exception(type(e), e, e.__traceback__)})")
        logger.error("Rscript output: " + e.stderr)
        return {
            "detail": f"{e}",
            "status": 500,
            "title": "Error",
            "type": "about:blank"
        }, 500


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
        return jsonify({
            "detail": "File upload failed",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    # create tmp upload file
    if not os.path.exists(config.UPLOAD_DIR):
        os.makedirs(config.UPLOAD_DIR)
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
    API request for /spongEffects/getSpongEffectsRuns
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
        return jsonify({
            "detail": 'No spongEffects run found for name: {disease_name}'.format(disease_name=disease_name),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200
