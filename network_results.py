import models
from flask import abort
import numpy as np
from sklearn import manifold


def get_network_results(disease_name="Breast invasive carcinoma",
                        level="gene"):
    """
    :param disease_name: disease_name of interest
    :param level: "gene" or "transcript"
    """

    if disease_name is None:
        abort(404, "A cancer type must be provided")

    if level is None:
        abort(404, "A level must be provided")

    dataset = models.Dataset.query \
        .filter(models.Dataset.disease_name == disease_name) \
        .all()

    if len(dataset) == 0:
        abort(404, f"No Dataset entries found for given cancer type: {disease_name}")
        return

    dataset_ids = [entry.dataset_ID for entry in dataset]
    subtypes = [entry.disease_subtype for entry in dataset]
    versions = [entry.version for entry in dataset]

    indices_to_remove = []
    for i, version in enumerate(versions):
        if version == 1:
            indices_to_remove.append(i)
    for index in sorted(indices_to_remove, reverse=True):
        del dataset_ids[index]
        del subtypes[index]
        del versions[index]

    if len(dataset_ids) == 0:
        abort(404, f"No Dataset entries found for given cancer type: {disease_name}")
        return

    elif len(dataset_ids) == 1:
        subtypes_result = {}

    else:
        run_ids = models.SpongeRun.query \
            .filter(models.SpongeRun.dataset_ID.in_(dataset_ids)) \
            .all()

        if len(run_ids) == 0:
            abort(404, f"No SPONGE runs found for given dataset IDs: {dataset_ids}")
            return

        sponge_run_ids = [entry.sponge_run_ID for entry in run_ids]

        results = models.NetworkResults.query \
            .filter(*[models.NetworkResults.sponge_run_ID_1.in_(sponge_run_ids),
                      models.NetworkResults.sponge_run_ID_2.in_(sponge_run_ids),
                      models.NetworkResults.level == level]) \
            .all()

        if len(results) == 0:
            abort(404, f"No network results runs found for given SPONGE run IDs: {sponge_run_ids}")
            return

        scores = [entry.score for entry in results]
        euclidean_distances = [entry.euclidean_distance for entry in results]

        euclidean_distances = np.array(euclidean_distances).reshape((len(sponge_run_ids), len(sponge_run_ids)))
        mds = manifold.MDS(2, dissimilarity='precomputed', normalized_stress=False)
        coords = mds.fit_transform(euclidean_distances)
        x, y = coords[:, 0], coords[:, 1]

        subtypes = [disease_name if subtype is None else subtype for subtype in subtypes]

        subtypes_result = {
            "scores": {
                'labels': subtypes,
                'values': np.array(scores).reshape((len(sponge_run_ids), len(sponge_run_ids))).tolist()
            },
            "euclidean_distances": {
                'labels': subtypes,
                'x': x.tolist(),
                'y': y.tolist()
            }
        }

    dataset = models.Dataset.query \
        .filter(models.Dataset.disease_subtype == None) \
        .all()

    if len(dataset) == 0:
        abort(404, f"No Cancer Type entries found")
        return
    elif len(dataset) == 1:
        abort(404, f"Found only 1 Cancer Type entry")
        return

    dataset_ids = [entry.dataset_ID for entry in dataset]
    cancer_types = [entry.disease_name for entry in dataset]
    versions = [entry.version for entry in dataset]

    indices_to_remove = []
    for i, version in enumerate(versions):
        if version == 1:
            indices_to_remove.append(i)
    for i, cancer_type in enumerate(cancer_types):
        if cancer_type == "Pan-Cancer":
            indices_to_remove.append(i)
    for index in sorted(indices_to_remove, reverse=True):
        del dataset_ids[index]
        del cancer_types[index]
        del versions[index]

    if len(dataset_ids) == 0:
        abort(404, f"No Dataset entries found for given cancer type: {disease_name}")
        return

    elif len(dataset_ids) == 1:
        abort(404, f"Found only 1 Cancer Type entry")
        return

    run_ids = models.SpongeRun.query \
        .filter(models.SpongeRun.dataset_ID.in_(dataset_ids)) \
        .all()

    if len(run_ids) == 0:
        abort(404, f"No SPONGE runs found for given dataset IDs: {dataset_ids}")
        return

    sponge_run_ids = [entry.sponge_run_ID for entry in run_ids]

    results = models.NetworkResults.query \
        .filter(*[models.NetworkResults.sponge_run_ID_1.in_(sponge_run_ids),
                  models.NetworkResults.sponge_run_ID_2.in_(sponge_run_ids),
                  models.NetworkResults.level == level]) \
        .all()

    if len(results) == 0:
        abort(404, f"No network results runs found for given SPONGE run IDs: {sponge_run_ids}")
        return

    scores = [entry.score for entry in results]
    euclidean_distances = [entry.euclidean_distance for entry in results]

    euclidean_distances = np.array(euclidean_distances).reshape((len(sponge_run_ids), len(sponge_run_ids)))
    mds = manifold.MDS(2, dissimilarity='precomputed', normalized_stress=False)
    coords = mds.fit_transform(euclidean_distances)
    x, y = coords[:, 0], coords[:, 1]

    return {
        "subtype": subtypes_result,
        "type": {
            "scores": {
                    'labels': cancer_types,
                    'values': np.array(scores).reshape((len(sponge_run_ids), len(sponge_run_ids))).tolist(),
            },
            "euclidean_distances": {
                    'labels': cancer_types,
                    'x': x.tolist(),
                    'y': y.tolist()
            }
        }
    }
