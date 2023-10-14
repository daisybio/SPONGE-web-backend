import json
import os
import random
import string
import subprocess

from flask import request, jsonify, abort
from werkzeug.utils import secure_filename
import sqlalchemy as sa

import config
import models
import numpy as np
from scipy.stats import gaussian_kde

from config import app
from config import UPLOAD_DIR


def get_run_performance(disease_name: str):
    """
    API request for /spongEffects/getRunPerformance
    :param disease_name: Disease name as string (fuzzy search)
    :return: Best spongEffects model performances for given disease
    """
    sponge_db_version: int = 2
    query = models.Dataset.query \
        .join(models.SpongeRun, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID) \
        .join(models.SpongEffectsRun, models.SpongEffectsRun.sponge_run_ID == models.SpongeRun.sponge_run_ID) \
        .join(models.SpongEffectsRunPerformance, models.SpongEffectsRunPerformance.spongEffects_run_ID == models.SpongEffectsRun.spongEffects_run_ID) \
        .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version) \
        .all()

    if len(query) > 0:
        return models.SpongEffectsRunPerformanceSchema(many=True).dump(query).data
    else:
        abort(404, 'No spongEffects model performance found for name: {disease_name}'.format(disease_name=disease_name))


def get_enrichment_score_class_distributions(disease_name: str, level: str):
    """
    API request for /sponge/spongEffects/enrichmentScoreDistributions?disease_name={disease_name}
    Get spongEffects enrichment score distributions for a given disease_name
    :param disease_name:
    :param level:
    :return: enrichment score class distribution for all available subtypes of given disease
    """
    # an Engine, which the Session will use for connection resources
    some_engine = sa.create_engine(os.getenv("SPONGE_DB_URI"), pool_recycle=30)
    # create a configured "Session" class
    Session = sa.orm.sessionmaker(bind=some_engine)
    session = Session()
    # get spongEffects_run_ID that matches the disease
    dataset = models.Dataset.query \
        .filter(models.Dataset.disease_name.like("%" + disease_name + "%")) \
        .first()
    dataset_id = dataset[0].dataset_ID


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
        self.mscor = params.mscor
        self.fdr = params.fdr
        self.min_size = params.min_size
        self.max_size = params.max_size
        self.min_expr = params.min_expr
        self.method = params.method

    def get_cmd_options(self):
        cmd: list = []
        for name, value in vars(self).items():
            cmd.append(f'--{name}')
            cmd.append(value)
        return cmd


def run_spongEffects(file_path, out_path, params: Params = None, log: bool = False):
    """
    Predict cancer type for an uploaded gene/transcript expression
    :param file_path: path to uploaded expression file
    :param out_path: output file path
    :param params: spongEffects run parameters
    :param log: Flag for R code
    :return: JSON object with type prediction for each sample
    """
    # build command
    cmd = [
        "Rscript", config.SPONGEFFECTS_PREDICT_SCRIPT,
        "--expr", file_path,
        "--model_dir", config.MODEL_DIR,
        "--output", out_path
    ]
    if log:
        cmd.append("--log")
    if params and isinstance(params, Params):
        cmd.extend(params.get_cmd_options())

    try:
        # execute command
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # get prediction output
        with open(out_path, 'r') as json_file:
            print(process.returncode)
            return json.load(json_file)
    except subprocess.CalledProcessError as e:
        return f'Error running spongEffects script: {e}'


@app.route('/spongEffects/predictCancerType', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    uploaded_file = request.files['file']
    run_parameters: Params = Params(request.form['params'])
    apply_log_scale: bool = request.form.get('log') is not None
    if uploaded_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    # create upload file name
    filename = secure_filename(uploaded_file.filename)
    uploaded_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    # save file to uploads folder
    uploaded_file.save(uploaded_file_path)
    # create random output path
    output_path = generate_random_filename(extension="json")
    # run spongEffects
    prediction_json = run_spongEffects(uploaded_file_path, output_path,
                                       run_parameters,
                                       log=apply_log_scale)
    # handle predict script error
    if prediction_json.startswith("Error"):
        abort(400, prediction_json)
    else:
        return prediction_json

