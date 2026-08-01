import json
import os
import random
import string
import subprocess
import tempfile
from flask import request, jsonify
import pandas as pd
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn import cluster
import app.config as config
from app.controllers.externalInformation import get_genes, get_transcripts
import app.models as models
from app.config import LATEST, db, logger, cache
import traceback    


@cache.cached(query_string=True)
def get_spongEffects_run_ID(dataset_ID: int = None, disease_name: str = None, level: str = "gene", 
                            spongEffects_params: dict = None,
                            sponge_db_version: int = LATEST):
    """
    :param dataset_ID: Dataset ID as string
    :param disease_name: Disease name as string (fuzzy search)
    :param level: One of gene/transcript
    :param spongEffects_params: Select only runs with given parameters
    :param sponge_db_version: Database version (defaults to most recent version)
    :return: spongEffects_run_ID for given disease name and level, ordered by best model performance (accuracy desc)
    """
    query = (
        db.select(models.SpongEffectsRun.spongEffects_run_ID)
        .join(models.SpongeRun, models.SpongEffectsRun.sponge_run_ID == models.SpongeRun.sponge_run_ID)
        .join(models.Dataset, models.SpongeRun.dataset_ID == models.Dataset.dataset_ID)
        .outerjoin(models.SpongEffectsRunPerformance, models.SpongEffectsRunPerformance.spongEffects_run_ID == models.SpongEffectsRun.spongEffects_run_ID)
        .where(models.Dataset.sponge_db_version == sponge_db_version)
    )

    if dataset_ID is not None:
        query = query.where(models.SpongeRun.dataset_ID == dataset_ID)
    if disease_name is not None:
        query = query.where(models.Dataset.disease_name.like(f"%{disease_name}%"))
    if level is not None:
        query = query.where(models.SpongEffectsRun.level == level)

    if spongEffects_params is not None:
        for key, value in spongEffects_params.items():
            if value is None:
                continue
            if hasattr(models.SpongEffectsRun, key):
                query = query.where(getattr(models.SpongEffectsRun, key) == value)
            else:
                return ValueError(f"Invalid parameter: {key}")

    query = query.order_by(models.SpongEffectsRunPerformance.accuracy.desc())

    raw_ids = db.session.execute(query).scalars().all()
    spong_effects_run_IDs = []
    for rid in raw_ids:
        if rid not in spong_effects_run_IDs:
            spong_effects_run_IDs.append(rid)

    return spong_effects_run_IDs


@cache.cached(query_string=True)
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
    if not spongEffects_run_IDs:
        return jsonify({
            "detail": 'No spongEffects model performance found for name: {disease_name}'.format(disease_name=disease_name),
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

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


@cache.cached(query_string=True)
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
    if not spongEffects_run_IDs:
        return jsonify({
            "detail": f'No spongEffects run class performance found for name: {disease_name}',
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

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


@cache.cached(query_string=True)
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
    if not spongEffects_run_IDs:
        return jsonify({
            "detail": 'No spongEffects class enrichment score distribution data found for given parameters',
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

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


@cache.memoize()
def get_gene_modules(spongEffects_gene_module_ID: int = None, dataset_ID: int = None, disease_name: str = None, gene_ID: str = None, ensg_number: str = None, gene_symbol: str = None, limit: int = None, offset: int = None, 
                     m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None, 
                     get_best: bool = True,
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
    :param get_best: If true, limits selection to the top-accuracy best model run
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
    if not spongEffects_run_IDs:
        return []
    has_identifier = (gene_ID is not None or ensg_number is not None or gene_symbol is not None or spongEffects_gene_module_ID is not None)
    if get_best and not has_identifier:
        spongEffects_run_IDs = spongEffects_run_IDs[:1]
    
    # get the modules
    query = db.select(models.SpongEffectsGeneModule) \
        .where(models.SpongEffectsGeneModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .order_by(models.SpongEffectsGeneModule.mean_accuracy_decrease.desc(), models.SpongEffectsGeneModule.mean_gini_decrease.desc())

    # Only filter by gene if at least one gene identifier is provided
    if gene_ID is not None or ensg_number is not None or gene_symbol is not None:
        gene_data = get_genes(gene_ID, ensg_number, gene_symbol)
        gene_IDs = [gene.gene_ID for gene in gene_data]
        query = query.where(models.SpongEffectsGeneModule.gene_ID.in_(gene_IDs))

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


@cache.cached(query_string=True)
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
    modules = get_gene_modules(
        spongEffects_gene_module_ID=spongEffects_gene_module_ID,
        dataset_ID=dataset_ID,
        disease_name=disease_name,
        gene_ID=gene_ID,
        ensg_number=ensg_number,
        gene_symbol=gene_symbol,
        sponge_db_version=sponge_db_version
    )
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


@cache.cached(query_string=True)
def get_gene_module_enrichment_score(spongEffects_gene_module_ID = None, cluster: bool = False, average: bool = False, sponge_db_version: int = LATEST): 
    """
    API request for /spongEffects/getSpongEffectsGeneModuleScores
    :param spongEffects_gene_module_ID: Gene module ID as int, list or comma-separated string
    :return: enrichment scores of all modules for a given gene
    """
    if spongEffects_gene_module_ID is not None:
        if isinstance(spongEffects_gene_module_ID, str):
            spongEffects_gene_module_ID = [int(x.strip()) for x in spongEffects_gene_module_ID.split(',') if x.strip().lstrip('-').isdigit()]
        elif isinstance(spongEffects_gene_module_ID, int):
            spongEffects_gene_module_ID = [spongEffects_gene_module_ID]
        elif isinstance(spongEffects_gene_module_ID, (list, tuple)):
            spongEffects_gene_module_ID = [int(x) for x in spongEffects_gene_module_ID if str(x).lstrip('-').isdigit()]

    if average:
        avg_query = db.session.query(
            models.EnrichmentScoreGene.spongEffects_gene_module_ID,
            db.func.avg(models.EnrichmentScoreGene.score_value).label('avg_score'),
            db.func.variance(models.EnrichmentScoreGene.score_value).label('var_score')
        )
        if spongEffects_gene_module_ID:
            avg_query = avg_query.filter(models.EnrichmentScoreGene.spongEffects_gene_module_ID.in_(spongEffects_gene_module_ID))
        avg_query = avg_query.group_by(models.EnrichmentScoreGene.spongEffects_gene_module_ID).all()

        modules_query = models.SpongEffectsGeneModule.query
        if spongEffects_gene_module_ID:
            modules_query = modules_query.filter(models.SpongEffectsGeneModule.spongEffects_gene_module_ID.in_(spongEffects_gene_module_ID))
        modules = modules_query.all()
        module_map = {m.spongEffects_gene_module_ID: m for m in modules}

        result = []
        for r in avg_query:
            m = module_map.get(r.spongEffects_gene_module_ID)
            result.append({
                "spongEffects_gene_module_ID": r.spongEffects_gene_module_ID,
                "score_value": r.avg_score,
                "variance_score": float(r.var_score) if getattr(r, 'var_score', None) is not None else 0.0,
                "gene": {
                    "ensg_number": m.gene.ensg_number if m and m.gene else None,
                    "gene_symbol": m.gene.gene_symbol if m and m.gene else None
                }
            })
        return jsonify(result)

    query = models.EnrichmentScoreGene.query
    if spongEffects_gene_module_ID:
        query = query.filter(models.EnrichmentScoreGene.spongEffects_gene_module_ID.in_(spongEffects_gene_module_ID))
    query = query.all()

    if len(query) == 0:
        return jsonify({
        "detail": f'No spongEffects gene module scores found for module ID: {spongEffects_gene_module_ID}',
        "status": 200,
        "title": "No Content",
        "type": "about:blank",
        "data": []
    }), 200
    
    # cluster the  scores
    if cluster: 
        data = pd.DataFrame([{
                "gene_ID": r.spongEffects_gene_module.gene.gene_symbol if r.spongEffects_gene_module.gene.gene_symbol else r.spongEffects_gene_module.gene.ensg_number,
                "sample_ID": r.sample_ID,
                "score_value": r.score_value,
            }for r in query])
        score_matrix = data.pivot(index="gene_ID", columns="sample_ID", values="score_value").fillna(0)
        try:
            row_linkage = linkage(score_matrix, method='ward', optimal_ordering=False)
            col_linkage = linkage(score_matrix.T, method='ward', optimal_ordering=False)
        except Exception as e:
                return jsonify({
                    "detail": str(e),
                    "status": 400,
                    "title": "Bad Request",
                    "type": "about:blank"
                }), 400
        row_order = dendrogram(row_linkage, labels=score_matrix.index, no_plot=True).get('leaves')
        col_order = dendrogram(col_linkage, labels=score_matrix.columns, no_plot=True).get('leaves')
        score_matrix = score_matrix.iloc[row_order, col_order]
        result = score_matrix.reset_index().melt(id_vars='gene_ID', var_name='sample_ID', value_name='score_value')
        result = [{
                "gene": {"gene_symbol": row['gene_ID'], "ensg_number": None},  # or fetch ensg_number if needed
                "sample_ID": row['sample_ID'],
                "score_value": row['score_value']
            } for _, row in result.iterrows()]

        return jsonify(result)
    else:
        return models.EnrichmentScoreGeneSchema(many=True).dump(query)

    

@cache.memoize()
def get_transcript_modules(spongEffects_transcript_module_ID: int = None, dataset_ID: int = None, disease_name: str = None, gene_ID: str = None, ensg_number: str = None, gene_symbol: str = None, transcript_ID: int = None, enst_number: int = None, limit: int = None, offset: int = None, 
                           m_scor_threshold: float = None, p_adj_threshold: float = None, modules_cutoff = None, 
                           get_best: bool = True,
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
    :param get_best: If true, limits selection to the top-accuracy best model run
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
    if not spongEffects_run_IDs:
        return []
    has_identifier = (gene_ID is not None or ensg_number is not None or gene_symbol is not None or transcript_ID is not None or enst_number is not None or spongEffects_transcript_module_ID is not None)
    if get_best and not has_identifier:
        spongEffects_run_IDs = spongEffects_run_IDs[:1]
    
    # get the modules
    query = db.select(models.SpongEffectsTranscriptModule) \
        .where(models.SpongEffectsTranscriptModule.spongEffects_run_ID.in_(spongEffects_run_IDs)) \
        .order_by(models.SpongEffectsTranscriptModule.mean_accuracy_decrease.desc(), models.SpongEffectsTranscriptModule.mean_gini_decrease.desc())

    # Only filter by transcript if any transcript/gene identifier is provided
    if (gene_ID is not None or ensg_number is not None or gene_symbol is not None or 
            transcript_ID is not None or enst_number is not None):
        transcript_data = get_transcripts(gene_ID, ensg_number, gene_symbol, transcript_ID, enst_number)
        transcript_IDs = [transcript.transcript_ID for transcript in transcript_data]
        query = query.where(models.SpongEffectsTranscriptModule.transcript_ID.in_(transcript_IDs))

    if spongEffects_transcript_module_ID is not None:
        query = query.where(models.SpongEffectsTranscriptModule.spongEffects_transcript_module_ID == spongEffects_transcript_module_ID)

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
        
    query = db.session.execute(query).scalars().all()

    if len(query) > 0:
        return models.SpongEffectsTranscriptModuleSchema(many=True).dump(query)
    else:
        return []


@cache.cached(query_string=True)
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
    modules = get_transcript_modules(
        spongEffects_transcript_module_ID=spongEffects_transcript_module_ID,
        dataset_ID=dataset_ID,
        disease_name=disease_name,
        gene_ID=gene_ID,
        ensg_number=ensg_number,
        gene_symbol=gene_symbol,
        transcript_ID=transcript_ID,
        enst_number=enst_number,
        sponge_db_version=sponge_db_version
    )
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


@cache.cached(query_string=True)
def get_transcript_module_enrichment_score(spongEffects_transcript_module_ID = None, cluster: bool = False, average: bool = False, sponge_db_version: int = LATEST): 
    """
    API request for /spongEffects/getSpongEffectsTranscriptModuleScores
    :param spongEffects_transcript_module_ID: Transcript module ID as int, list or comma-separated string
    :param cluster: Whether to cluster the output (default: False)
    :param sponge_db_version: currently not used
    :return: enrichment scores of all modules for a given transcript
    """
    if spongEffects_transcript_module_ID is not None:
        if isinstance(spongEffects_transcript_module_ID, str):
            spongEffects_transcript_module_ID = [int(x.strip()) for x in spongEffects_transcript_module_ID.split(',') if x.strip().lstrip('-').isdigit()]
        elif isinstance(spongEffects_transcript_module_ID, int):
            spongEffects_transcript_module_ID = [spongEffects_transcript_module_ID]
        elif isinstance(spongEffects_transcript_module_ID, (list, tuple)):
            spongEffects_transcript_module_ID = [int(x) for x in spongEffects_transcript_module_ID if str(x).lstrip('-').isdigit()]

    if average:
        avg_query = db.session.query(
            models.EnrichmentScoreTranscript.spongEffects_transcript_module_ID,
            db.func.avg(models.EnrichmentScoreTranscript.score_value).label('avg_score'),
            db.func.variance(models.EnrichmentScoreTranscript.score_value).label('var_score')
        )
        if spongEffects_transcript_module_ID:
            avg_query = avg_query.filter(models.EnrichmentScoreTranscript.spongEffects_transcript_module_ID.in_(spongEffects_transcript_module_ID))
        avg_query = avg_query.group_by(models.EnrichmentScoreTranscript.spongEffects_transcript_module_ID).all()

        modules_query = models.SpongEffectsTranscriptModule.query
        if spongEffects_transcript_module_ID:
            modules_query = modules_query.filter(models.SpongEffectsTranscriptModule.spongEffects_transcript_module_ID.in_(spongEffects_transcript_module_ID))
        modules = modules_query.all()
        module_map = {m.spongEffects_transcript_module_ID: m for m in modules}

        result = []
        for r in avg_query:
            m = module_map.get(r.spongEffects_transcript_module_ID)
            result.append({
                "spongEffects_transcript_module_ID": r.spongEffects_transcript_module_ID,
                "score_value": r.avg_score,
                "variance_score": float(r.var_score) if getattr(r, 'var_score', None) is not None else 0.0,
                "transcript": {
                    "enst_number": m.transcript.enst_number if m and m.transcript else None,
                    "gene": {
                        "gene_symbol": m.transcript.gene.gene_symbol if m and m.transcript and m.transcript.gene else None
                    }
                }
            })
        return jsonify(result)

    query = models.EnrichmentScoreTranscript.query
    if spongEffects_transcript_module_ID:
        query = query.filter(models.EnrichmentScoreTranscript.spongEffects_transcript_module_ID.in_(spongEffects_transcript_module_ID))
    query = query.all()
    if len(query) == 0:
        return jsonify({
            "detail": f'No spongEffects transcript module scores found for module ID: {spongEffects_transcript_module_ID}',
            "status": 200,
            "title": "No Content",
            "type": "about:blank",
            "data": []
        }), 200

    if cluster:
        import pandas as pd
        from scipy.cluster.hierarchy import linkage, dendrogram

        data = pd.DataFrame([
            {
                "transcript_ID": (
                    r.spongEffects_transcript_module.transcript.enst_number
                    if r.spongEffects_transcript_module and r.spongEffects_transcript_module.transcript
                    else None
                ),
                "sample_ID": r.sample_ID,
                "score_value": r.score_value,
            }
            for r in query
        ])
        # Remove rows with missing transcript_ID
        data = data.dropna(subset=["transcript_ID"])
        if data.empty:
            return jsonify([])

        score_matrix = data.pivot(index="transcript_ID", columns="sample_ID", values="score_value").fillna(0)
        row_linkage = linkage(score_matrix, method='ward', optimal_ordering=False)
        col_linkage = linkage(score_matrix.T, method='ward', optimal_ordering=False)
        row_order = dendrogram(row_linkage, labels=score_matrix.index, no_plot=True).get('leaves')
        col_order = dendrogram(col_linkage, labels=score_matrix.columns, no_plot=True).get('leaves')
        score_matrix = score_matrix.iloc[row_order, col_order]
        result = score_matrix.reset_index().melt(id_vars='transcript_ID', var_name='sample_ID', value_name='score_value')
        result = [
            {
                "transcript": {"enst_number": row['transcript_ID']},
                "sample_ID": row['sample_ID'],
                "score_value": row['score_value']
            }
            for _, row in result.iterrows()
        ]
        return jsonify(result)
    else:
        return models.EnrichmentScoreTranscriptSchema(many=True).dump(query)


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
    model: str
    log: bool
    subtypes: bool

    def __init__(self, params):
        self.mscor = params["mscor"]
        self.fdr = params["fdr"]
        self.min_size = params["min_size"]
        self.max_size = params["max_size"]
        self.min_expr = params["min_expr"]
        self.method = params["method"]
        self.model = params["model"]
        self.log = str(params.get("log")).lower() == "true"
        self.subtypes = str(params.get("subtypes")).lower() == "true"
        invalid_keys = [k for k in params.keys() if k not in ["mscor", "fdr", "min_size", "max_size", "min_expr", "method", "model", "log", "subtypes"]]
        if invalid_keys:
            raise ValueError(f"Invalid parameters: {invalid_keys}")

    def get_cmd_options(self):
        cmd: list = []
        for name, value in vars(self).items():
            # check for wrong params
                    
            if value == "None" or value is None:
                continue
            if type(value) != bool or (type(value) == bool and value is True):
                cmd.append(f'--{name}')
            if name == "method":
                value = str(value).lower()
            if type(value) != bool:    
                cmd.append(str(value))
        return cmd


def run_spongEffects(file_path, out_path, params: Params = None, 
# log: bool = False, subtype_level: bool = False
):
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
    # if subtype_level:
    #     cmd.append("--subtypes")
    # if log:
    #     cmd.append("--log")
    if params and isinstance(params, Params):
        cmd.extend(params.get_cmd_options())
    try:
        # execute command
        logger.info(f"Running spongEffects with command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # get prediction output
        # stderr = process.stderr
        # logger.info(f"Rscript stderr:\n{stderr}")

        if not os.path.exists(out_path):
             return {
                "detail": f"Output file not found at {out_path}. R Script output: {stderr}",
                "status": 500,
                "title": "Execution Error",
                "type": "about:blank"
            }, 500

        with open(out_path, 'r') as json_file:
            return json.load(json_file), 200

    except subprocess.CalledProcessError as e:
        # construct log path for error reading
        log_path = os.path.join(config.UPLOAD_DIR, os.path.basename(out_path).replace(".json", ".log"))
        log_content = ""
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    log_lines = f.readlines()
                    # find "Error in"
                    error_line_index = None
                    for i, line in enumerate(log_lines):
                        if "Error in" in line:
                            error_line_index = i
                            break
                    
                    if error_line_index is not None:
                        # find where error ends (usually at warning messages or end of file)
                        error_end_index = len(log_lines)
                        for i in range(error_line_index, len(log_lines)):
                            if log_lines[i].startswith("In addition: Warning messages:"):
                                error_end_index = i
                                break
                        log_content = "\n--- Specific R Error ---\n" + "".join(log_lines[error_line_index:error_end_index])
                    else:
                        # just get last 15 lines if no specific error found
                        log_content = "\n--- Log Tail ---\n" + "".join(log_lines[-15:])
            except Exception as read_err:
                logger.error(f"Could not read log file: {read_err}")

        error_msg = f"{e.stderr}\n{e.stdout}".strip()
        if not error_msg or len(error_msg) < 5:
            error_msg = str(e)
            
        logger.error(f"Error running spongEffects: {e}")
        logger.error(f"Rscript combined output: {error_msg}")
        
        return {
            "detail": f"R Script error:\n{error_msg}{log_content}",
            "status": 500,
            "title": "Execution Error",
            "type": "about:blank"
        }, 500
    except Exception as e:
        logger.error(f"Unexpected error in run_spongEffects: {e}\n{traceback.format_exc()}")
        return {
            "detail": f"Unexpected error: {str(e)}",
            "status": 500,
            "title": "System Error",
            "type": "about:blank"
        }, 500


def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    # save uploaded file
    uploaded_file = request.files['file']
    # save prediction level
    # predict_subtypes: bool = request.form.get('subtypes') == "true"
    # save given parameters
    run_parameters: Params = Params(request.form)
    # apply_log_scale: bool = request.form.get('log') == "true"
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
    response, status_code = run_spongEffects(tmp_file.name, os.path.join(config.UPLOAD_DIR, tmp_out_file.name), run_parameters)
    
    if status_code == 200 and isinstance(response, dict) and 'scores' in response:
        try:
            meta_list = response.get('meta', [])
            level = meta_list[0].get('level', 'gene') if isinstance(meta_list, list) and len(meta_list) > 0 else 'gene'
            umap_dir = "/Users/lena/Projects/SPONGE/SPONGE-web-backend/umap_data"
            model_path = os.path.join(umap_dir, f"umap_{level}_model.joblib")
            coords_path = os.path.join(umap_dir, f"umap_{level}_tcga_coords.json")
            
            if os.path.exists(model_path) and os.path.exists(coords_path):
                import joblib
                import numpy as np
                # Load UMAP model info
                model_info = joblib.load(model_path)
                
                # Extract and format user scores if present
                scores = response.get('scores')
                user_umap = {}
                if scores and scores.get('samples') and scores.get('genes') and scores.get('values') and len(scores['samples']) > 0 and len(scores['genes']) > 0 and len(scores['values']) > 0:
                    # values: list of lists, shape (n_features, n_samples)
                    data_matrix = np.array(scores['values']).T # shape (n_samples, n_features)
                    user_df = pd.DataFrame(data_matrix, index=scores['samples'], columns=scores['genes'])
                    
                    # Reindex columns to align with training features
                    user_df = user_df.reindex(columns=model_info['feature_names'], fill_value=0.0)
                    
                    # Scale and transform
                    scaled_data = model_info['scaler'].transform(user_df)
                    user_embedding = model_info['reducer'].transform(scaled_data)
                    
                    # Format user coordinates
                    for idx, sample in enumerate(scores['samples']):
                        user_umap[sample] = {
                            'x': float(user_embedding[idx, 0]),
                            'y': float(user_embedding[idx, 1]),
                        }
                response['user_umap'] = user_umap
                
                # Load precalculated TCGA coordinates
                with open(coords_path, 'r') as f:
                    tcga_umap = json.load(f)
                response['tcga_umap'] = tcga_umap
                
        except Exception as e:
            logger.error(f"Error calculating UMAP projection for user samples: {e}\n{traceback.format_exc()}")
            
    return jsonify(response), status_code


@cache.cached(query_string=True)
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


def get_umap_projection():
    """
    API request for /spongEffects/getUmapProjection
    Calculate UMAP coordinates for any given scores and level.
    """
    if request.method == 'POST':
        req_data = request.get_json(silent=True) or {}
        level = req_data.get('level') or request.args.get('level', default='gene')
        scores = req_data.get('scores')
    else:
        level = request.args.get('level', default='gene')
        scores = None

    if not level:
        level = 'gene'

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        umap_dir = os.path.join(base_dir, "umap_data")
        model_path = os.path.join(umap_dir, f"umap_{level}_model.joblib")
        coords_path = os.path.join(umap_dir, f"umap_{level}_tcga_coords.json")
        
        if not os.path.exists(model_path) or not os.path.exists(coords_path):
            return jsonify({'error': 'UMAP models not trained yet on the backend'}), 500
            
        import joblib
        import numpy as np
        
        model_info = joblib.load(model_path)
        
        # Extract and format user scores if present
        user_umap = {}
        if scores and isinstance(scores, dict) and scores.get('samples') and scores.get('genes') and scores.get('values') and len(scores['samples']) > 0 and len(scores['genes']) > 0 and len(scores['values']) > 0:
            data_matrix = np.array(scores['values']).T
            user_df = pd.DataFrame(data_matrix, index=scores['samples'], columns=scores['genes'])
            
            # Reindex columns to align with training features
            user_df = user_df.reindex(columns=model_info['feature_names'], fill_value=0.0)
            
            # Scale and transform
            scaled_data = model_info['scaler'].transform(user_df)
            user_embedding = model_info['reducer'].transform(scaled_data)
            
            # Format user coordinates
            for idx, sample in enumerate(scores['samples']):
                user_umap[sample] = {
                    'x': float(user_embedding[idx, 0]),
                    'y': float(user_embedding[idx, 1]),
                }
            
        # Load precalculated TCGA coordinates
        with open(coords_path, 'r') as f:
            tcga_umap = json.load(f)
            
        return jsonify({
            'user_umap': user_umap,
            'tcga_umap': tcga_umap
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_umap_projection: {e}\n{traceback.format_exc()}")
        return jsonify({"detail": str(e), "status": 500}), 500
        return jsonify({'error': f"Internal error during UMAP projection: {str(e)}"}), 500
