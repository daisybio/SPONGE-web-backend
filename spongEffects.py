import json
import os
import random
import string
import subprocess

from flask import request, jsonify, abort
from sqlalchemy import desc
from werkzeug.utils import secure_filename
import sqlalchemy as sa

import config
import models

from config import app
from config import UPLOAD_DIR


def get_spongEffects_run_ID(disease_name: str, level: str = "gene", sponge_db_version: int = 2):
    # an Engine, which the Session will use for connection resources
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)
    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)
    # create a Session
    session = Session()
    query = session.execute(
        "SELECT sEr.spongEffects_run_ID from spongEffects_run_performance"
        " JOIN spongEffects_run sEr on spongEffects_run_performance.spongEffects_run_ID = sEr.spongEffects_run_ID"
        " JOIN sponge_run sr on sEr.sponge_run_ID = sr.sponge_run_ID"
        " JOIN dataset d on sr.dataset_ID = d.dataset_ID"
        f" WHERE d.disease_name LIKE '%{disease_name}%'"
        f" AND d.version = {sponge_db_version}"
        f" AND level = '{level}'"
        " AND split_type = 'train'"
        " ORDER BY accuracy_upper DESC"
        " LIMIT 1;"
    ).fetchall()
    # clean up resources
    session.close()
    some_engine.dispose()
    if len(query) > 0:
        return query[0].spongEffects_run_ID
    else:
        abort(404, "No spongEffects run found for given parameters")


def get_run_performance(disease_name: str, level: str):
    """
    API request for /spongEffects/getRunPerformance
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :return: Best spongEffects model performances for given disease and level
    """
    sponge_db_version: int = 2
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, level, sponge_db_version)
    query = models.SpongEffectsRunPerformance.query \
        .join(models.SpongEffectsRun, models.SpongEffectsRun.spongEffects_run_ID == models.SpongEffectsRunPerformance.spongEffects_run_ID) \
        .filter(models.SpongEffectsRun.spongEffects_run_ID == spongEffects_run_ID) \
        .all()

    if len(query) > 0:
        return models.SpongEffectsRunPerformanceSchema(many=True).dump(query).data
    else:
        abort(404, 'No spongEffects model performance found for name: {disease_name}'.format(disease_name=disease_name))


def get_run_class_performance(disease_name: str, level: str, sponge_db_version: int = 2):
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, level, sponge_db_version)
    query = models.SpongEffectsRunClassPerformance.query \
        .join(models.SpongEffectsRunPerformance,
              models.SpongEffectsRunPerformance.spongEffects_run_performance_ID == models.SpongEffectsRunClassPerformance.spongEffects_run_performance_ID) \
        .filter(models.SpongEffectsRunPerformance.spongEffects_run_ID == spongEffects_run_ID) \
        .all()
    if len(query) > 0:
        return models.SpongEffectsRunClassPerformanceSchema(many=True).dump(query).data
    else:
        abort(404, f'No spongEffects run class performance found for name: {disease_name}')


def get_enrichment_score_class_distributions(disease_name: str, level: str, sponge_db_version: int = 2):
    """
    API request for /spongEffects/enrichmentScoreDistributions?disease_name={disease_name}
    Get spongEffects enrichment score distributions for a given disease_name
    :param disease_name: Name of the disease to filter for
    :param level: one of gene/transcript
    :param sponge_db_version: Database version (defaults to most recent version 2)
    :return: enrichment score class distribution for all available subtypes of given disease
    """
    level = level.lower()
    if level not in ['gene', 'transcript']:
        abort(404, 'Provided level not recognised, please use one of gene/transcript')
    # extract spongEffects_run_ID
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, level, sponge_db_version)
    # extract density data for spongEffects run
    query = models.SpongEffectsEnrichmentClassDensity.query \
        .filter(models.SpongEffectsEnrichmentClassDensity.spongEffects_run_ID == spongEffects_run_ID) \
        .all()
    if len(query) > 0:
        return models.SpongEffectsEnrichmentClassDensitySchema(many=True).dump(query).data
    else:
        abort(404, 'No spongEffects class enrichment score distribution data found for given parameters')


def get_gene_modules(disease_name: str, sponge_db_version: int = 2):
    # get spongEffects_run_ID
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, "gene", sponge_db_version)
    # an Engine, which the Session will use for connection resources
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)
    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)
    # create a Session
    session = Session()
    # get modules
    query = session.execute(
        "SELECT * FROM spongEffects_gene_module as A"
        " JOIN gene g ON A.gene_ID = g.gene_ID"
        f" WHERE spongEffects_run_ID = {spongEffects_run_ID}"
        " ORDER BY mean_accuracy_decrease DESC, mean_accuracy_decrease DESC;"
    ).fetchall()
    # clean up resources
    session.close()
    some_engine.dispose()
    if len(query) > 0:
        return models.SpongEffectsGeneModuleSchema(many=True).dump(query).data
    else:
        abort(404, "No spongEffects modules found for given disease")


def get_gene_module_members(disease_name: str, ensg_number: str = None, gene_symbol: str = None, sponge_db_version: int = 2):
    # get spongEffects_run_ID
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, "gene", sponge_db_version)
    # test if any of the two identification possibilities is given
    if ensg_number is None and gene_symbol is None:
        abort(404, "One of the two possible identification numbers must be provided")

    if ensg_number is not None and gene_symbol is not None:
        abort(404,
              "More than one identification parameter is given. Please choose one out of (ensg_number, gene symbol)")

    # create search engine
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)
    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)
    # create a Session
    session = Session()
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
    query = session.execute(
        "SELECT gA.ensg_number AS hub_ensg_number, gA.gene_symbol AS hub_gene_symbol,"
        " g.ensg_number AS member_ensg_number, g.gene_symbol as member_gene_symbol"
        " FROM spongEffects_gene_module_members as A"
        " JOIN spongEffects_gene_module sEgm on A.spongEffects_gene_module_ID = sEgm.spongEffects_gene_module_ID"
        " JOIN gene g on g.gene_ID = A.gene_ID"
        " JOIN gene gA on gA.gene_ID = sEgm.gene_ID"
        f" WHERE gA.{search_key} IN ({search_val}) AND spongEffects_run_ID = {spongEffects_run_ID};"
    ).fetchall()
    # clean up resources
    session.close()
    some_engine.dispose()
    if len(query) > 0:
        return models.SpongEffectsGeneModuleMembersSchema(many=True).dump(query).data
    else:
        abort(404, "No module members found for given disease name and gene identifier")


def get_transcript_modules(disease_name: str, sponge_db_version: int = 2):
    # get spongEffects_run_ID
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, "transcript", sponge_db_version)
    # an Engine, which the Session will use for connection resources
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)
    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)
    # create a Session
    session = Session()
    # get modules
    query = session.execute(
        "SELECT * FROM spongEffects_transcript_module as A"
        " JOIN transcript t ON A.transcript_ID = t.transcript_ID"
        " JOIN gene g ON t.gene_ID = g.gene_ID"
        f" WHERE spongEffects_run_ID = {spongEffects_run_ID}"
        " ORDER BY mean_accuracy_decrease DESC, mean_accuracy_decrease DESC;"
    ).fetchall()
    # clean up resources
    session.close()
    some_engine.dispose()
    if len(query) > 0:
        return models.SpongEffectsTranscriptModuleSchema(many=True).dump(query).data
    else:
        abort(404, "No spongEffects modules found for given disease")


def get_transcript_module_members(disease_name: str, enst_number: str = None, ensg_number: str = None, gene_symbol: str = None, sponge_db_version: int = 2):
    # get spongEffects_run_ID
    spongEffects_run_ID = get_spongEffects_run_ID(disease_name, "gene", sponge_db_version)
    # test if any of the two identification possibilities is given
    tests: list = [enst_number is not None, ensg_number is not None, gene_symbol is not None]
    if sum(tests) == 0:
        abort(404, "One of the three possible identification numbers must be provided")
    elif sum(tests) > 1:
        abort(404,
              "More than one identification parameter is given. Please choose one out of (enst_number, ensg_number, or gene symbol)")

    # create search engine
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)
    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)
    # create a Session
    session = Session()
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
    query = session.execute(
        "SELECT tA.enst_number as hub_enst_number, t.enst_number as member_enst_number"
        " gA.ensg_number AS hub_ensg_number, gA.gene_symbol AS hub_gene_symbol,"
        " g.ensg_number AS member_ensg_number, g.gene_symbol as member_gene_symbol"
        " FROM spongEffects_transcript_module_members as A"
        " JOIN spongEffects_transcript_module sEtm on A.spongEffects_transcript_module_ID = sEtm.spongEffects_transcript_module_ID"
        " JOIN transcript t on t.transcript_ID = A.transcript_ID"
        " JOIN transcript tA on tA.transcript_ID = sEtm.transcript_ID"
        " JOIN gene g on g.gene_ID = t.gene_ID"
        " JOIN gene gA on gA.gene_ID = tA.gene_ID"
        f" WHERE tA.{search_key} IN ({search_val}) AND spongEffects_run_ID = {spongEffects_run_ID};"
    ).fetchall()
    # clean up resources
    session.close()
    some_engine.dispose()
    if len(query) > 0:
        return models.SpongEffectsGeneModuleMembersSchema(many=True).dump(query).data
    else:
        abort(404, "No module members found for given disease name and gene identifier")

def generate_random_filename(length=12, extension=None):
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
        "--model_dir", config.MODEL_DIR,
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
        print(process.stderr)
        with open(out_path, 'r') as json_file:
            return json.load(json_file)
    except subprocess.CalledProcessError as e:
        abort(500, e)
    finally:
        # remove uploaded file
        os.remove(file_path)


@app.route('/spongEffects/predictCancerType', methods=['GET', 'POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    # save uploaded file
    print("upload started")
    uploaded_file = request.files['file']
    # save prediction level
    predict_subtypes: bool = request.form.get('subtypes') == "true"
    # save given parameters
    run_parameters: Params = Params(request.form)
    apply_log_scale: bool = request.form.get('log') == "true"
    if uploaded_file.filename == '':
        abort(404, "File upload failed")
    # create random upload file name
    filename = generate_random_filename(extension="txt")
    uploaded_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    # save file to uploads folder
    uploaded_file.save(uploaded_file_path)
    # create random output path
    output_path = os.path.join(app.config["UPLOAD_FOLDER"], generate_random_filename(extension="json"))
    # run spongEffects
    return jsonify(run_spongEffects(uploaded_file_path, output_path, run_parameters,
                                    log=apply_log_scale, subtype_level=predict_subtypes))

