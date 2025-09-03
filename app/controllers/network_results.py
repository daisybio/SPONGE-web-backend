import app.models as models
from flask import jsonify
import numpy as np
from sklearn import manifold
import pandas as pd
from app.config import LATEST, cache
from app.controllers.dataset import _dataset_query


@cache.cached(query_string=True)
def get_network_results(dataset_ID: int = None, disease_name="Breast invasive carcinoma",
                        level="gene", sponge_db_version=LATEST):
    """
    This function handles the query for /networkResults
    and returns information about all available datasets to start browsing or search for a specific cancer type/dataset.
    :param disease_name: disease_name of interest
    :param version: version of the database
    :param level: "gene" or "transcript"
    :param sponge_db_version: version of the database
    :return: dictionary containing the network results
    """

    if disease_name is None:
        return jsonify({
            "detail": "A cancer type must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    if level is None:
        return jsonify({
            "detail": "A level must be provided",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    dataset = _dataset_query(disease_name=disease_name, sponge_db_version=sponge_db_version, dataset_ID=dataset_ID)

    if len(dataset) == 0:
        return jsonify({
            "detail": f"No Dataset entries found for given cancer type: {disease_name}",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    type_datasets = pd.DataFrame({'dataset_ID': [entry.dataset_ID for entry in dataset],
                                  'subtype': [entry.disease_subtype for entry in dataset]})

    run_ids = models.SpongeRun.query \
        .filter(models.SpongeRun.sponge_db_version == sponge_db_version) \
        .all()

    all_run_ids = pd.DataFrame({'sponge_run_ID': [entry.sponge_run_ID for entry in run_ids],
                                'dataset_ID': [entry.dataset_ID for entry in run_ids]})

    type_merge = type_datasets.merge(all_run_ids, how='inner')

    if type_merge.shape[0] == 0:
        return jsonify({
            "detail": f"No Dataset entries found for given cancer type: {disease_name}",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    elif type_merge.shape[0] == 1:
        subtypes_result = {}

    else:
        results = models.NetworkResults.query \
            .filter(*[models.NetworkResults.sponge_run_ID_1.in_(type_merge['sponge_run_ID']),
                      models.NetworkResults.sponge_run_ID_2.in_(type_merge['sponge_run_ID']),
                      models.NetworkResults.level == level]) \
            .all()

        if len(results) == 0:
            return jsonify({
                "detail": f"No network results runs found for given SPONGE run IDs: {type_merge['sponge_run_ID']}",
                "status": 400,
                "title": "Bad Request",
                "type": "about:blank"
            }), 400

        scores = [entry.score for entry in results]
        euclidean_distances = [entry.euclidean_distance for entry in results]

        euclidean_distances = np.array(euclidean_distances).reshape((len(type_merge['sponge_run_ID']), len(type_merge['sponge_run_ID'])))
        mds = manifold.MDS(2, dissimilarity='precomputed', normalized_stress=False)
        coords = mds.fit_transform(euclidean_distances)
        x, y = coords[:, 0], coords[:, 1]

        subtypes = [disease_name if subtype is None else subtype for subtype in type_merge['subtype']]

        subtypes_result = {
            "scores": {
                'labels': subtypes,
                'values': np.array(scores).reshape((len(type_merge['sponge_run_ID']), len(type_merge['sponge_run_ID']))).tolist()
            },
            "euclidean_distances": {
                'labels': subtypes,
                'x': x.tolist(),
                'y': y.tolist()
            }
        }

    dataset = models.Dataset.query \
        .filter(*[models.Dataset.disease_subtype == None,
                  models.Dataset.disease_name != "Parkinsons disease"]) \
        .filter(models.Dataset.sponge_db_version == sponge_db_version) \
        .all()

    if len(dataset) == 0:
        return jsonify({
            "detail": f"No Cancer Type entries found",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    elif len(dataset) == 1:
        return jsonify({
            "detail": f"Found only 1 Cancer Type entry",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    all_datasets = pd.DataFrame({'dataset_ID': [entry.dataset_ID for entry in dataset],
                                 'disease_name': [entry.disease_name for entry in dataset]})

    if len(all_datasets['dataset_ID']) == 0:
        return jsonify({
            "detail": f"No Dataset entries found for given cancer type: {disease_name}",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    elif len(all_datasets['dataset_ID']) == 1:
        return jsonify({
            "detail": f"No Dataset entries found for given cancer type: {disease_name}",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    all_merge = all_datasets.merge(all_run_ids, how='inner')

    results = models.NetworkResults.query \
        .filter(*[models.NetworkResults.sponge_run_ID_1.in_(all_merge['sponge_run_ID']),
                  models.NetworkResults.sponge_run_ID_2.in_(all_merge['sponge_run_ID']),
                  models.NetworkResults.level == level]) \
        .all()

    if len(results) == 0:
        return jsonify({
            "detail": f"No network results runs found for given SPONGE run IDs: {type_merge['sponge_run_ID']}",
            "status": 400,
            "title": "Bad Request",
            "type": "about:blank"
        }), 400

    scores = [entry.score for entry in results]
    euclidean_distances = [entry.euclidean_distance for entry in results]

    euclidean_distances = np.array(euclidean_distances).reshape((len(all_merge['sponge_run_ID']), len(all_merge['sponge_run_ID'])))
    mds = manifold.MDS(2, dissimilarity='precomputed', normalized_stress=False)
    coords = mds.fit_transform(euclidean_distances)
    x, y = coords[:, 0], coords[:, 1]

    return {
        "subtype": subtypes_result,
        "type": {
            "scores": {
                    'labels': all_merge['disease_name'].tolist(),
                    'values': np.array(scores).reshape((len(all_merge['sponge_run_ID']), len(all_merge['sponge_run_ID']))).tolist(),
            },
            "euclidean_distances": {
                    'labels': all_merge['disease_name'].tolist(),
                    'x': x.tolist(),
                    'y': y.tolist()
            }
        }
    }
