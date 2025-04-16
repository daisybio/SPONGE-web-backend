from marshmallow import fields
from sqlalchemy.orm import relationship

from app.config import db, ma


class Disease(db.Model):
    __tablename__ = 'disease'
    disease_ID = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(32))
    disease_subtype = db.Column(db.String(32))
    versions = db.Column(db.String(255))

class Dataset(db.Model):
    __tablename__ = 'dataset'
    dataset_ID = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(32))
    data_origin = db.Column(db.String(32))
    disease_type = db.Column(db.String(32))
    download_url = db.Column(db.String(32))
    disease_subtype = db.Column(db.String(32))
    sponge_db_version = db.Column(db.Integer)
    disease_ID = db.Column(db.Integer, db.ForeignKey('disease.disease_ID'), nullable=False)
    disease = relationship("Disease", foreign_keys=[disease_ID])

    
class SpongeRun(db.Model):
    __tablename__ = "sponge_run"
    sponge_run_ID = db.Column(db.Integer, primary_key=True)

    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])

    variance_cutoff = db.Column(db.Integer)
    f_test = db.Column(db.Integer)
    f_test_p_adj_threshold = db.Column(db.Float)
    coefficient_threshold = db.Column(db.Float)
    coefficient_direction = db.Column(db.String(32))
    min_corr = db.Column(db.Float)
    number_of_datasets = db.Column(db.Integer)
    number_of_samples = db.Column(db.Integer)
    ks = db.Column(db.String(32))
    m_max = db.Column(db.Integer)
    log_level = db.Column(db.String(32))
    sponge_db_version = db.Column(db.Integer)


class TargetDatabases(db.Model):
    __tablename__ = "target_databases"
    target_databases_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    db_used = db.Column(db.String(32))
    version = db.Column(db.String(32))
    url = db.Column(db.String(32))

class GeneInteraction(db.Model):
    __tablename__ = 'interactions_genegene'
    interactions_genegene_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    gene_ID1 = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene1 = relationship("Gene", foreign_keys=[gene_ID1])
    gene_ID2 = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene2 = relationship("Gene", foreign_keys=[gene_ID2])

    p_value = db.Column(db.Float)
    mscor = db.Column(db.Float)
    correlation = db.Column(db.Float)

class miRNAInteraction(db.Model):
    __tablename__ = "interactions_genemirna"
    interactions_genemirna_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])

    coefficient = db.Column(db.Float)

class miRNAInteractionTranscript(db.Model):
    __tablename__ = "interactions_transcriptmirna"
    interactions_transcriptmirna_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])

    coefficient = db.Column(db.Float)

class Gene(db.Model):
    __tablename__ = "gene"
    gene_ID = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(32))
    gene_symbol = db.Column(db.String(32))
    ensg_number = db.Column(db.String(32))
    chromosome_name = db.Column(db.String(32))
    start_pos = db.Column(db.Integer)
    end_pos = db.Column(db.Integer)
    gene_type = db.Column(db.String(32))
    cytoband = db.Column(db.String(100))
    strand = db.Column(db.String(1))

class miRNA(db.Model):
    __tablename__ = "mirna"
    miRNA_ID = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.String(32))
    mir_ID = db.Column(db.String(32))
    seq = db.Column(db.String(32))
    hs_nr = db.Column(db.String(32))
    chr = db.Column(db.String(32))
    start_position = db.Column(db.Integer)
    end_position = db.Column(db.Integer)
    cytoband = db.Column(db.String(100))

class networkAnalysis(db.Model):
    __tablename__ = "network_analysis_gene"
    network_analysis_gene_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    eigenvector = db.Column(db.Float)
    betweenness = db.Column(db.Float)
    node_degree = db.Column(db.Float)

# chris: Change
class networkAnalysisTranscript(db.Model):
    __tablename__ = "network_analysis_transcript"
    network_analysis_transcript_ID = db.Column(db.Integer, primary_key=True)

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript= relationship("Transcript", foreign_keys=[transcript_ID])

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    eigenvector = db.Column(db.Float)
    betweenness = db.Column(db.Float)
    node_degree = db.Column(db.Float)


class GeneExpressionValues(db.Model):
    __tablename__ = "expression_data_gene"
    expression_data_gene_ID = db.Column(db.Integer, primary_key=True)
    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])
    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])
    expr_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))
    normal_cancer = db.Column(db.String(32))


class MiRNAExpressionValues(db.Model):
    __tablename__ = "expression_data_mirna"
    expression_data_mirna_ID = db.Column(db.Integer, primary_key=True)
    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])
    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])
    expr_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))


class OccurencesMiRNA(db.Model):
    __tablename__ = "occurences_mirna_gene"
    occurences_mirna_gene_ID = db.Column(db.Integer, primary_key=True, nullable=False)
    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])
    occurences = db.Column(db.Integer, nullable=False)
    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

class OccurencesMiRNATranscript(db.Model):
    __tablename__ = "occurences_mirna_transcript"
    occurences_mirna_transcript_ID = db.Column(db.Integer, primary_key=True, nullable=False)
    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])
    occurences = db.Column(db.Integer, nullable=False)
    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

class PatientInformation(db.Model):
    __tablename__ = "patient_information"
    patient_information_ID =  db.Column(db.Integer, primary_key=True)
    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])
    sample_ID = db.Column(db.String(32))
    disease_status = db.Column(db.Integer)
    survival_time = db.Column(db.Integer)

class SurvivalRate(db.Model):
    __tablename__ = "survival_rate"
    survival_rate_ID = db.Column(db.Integer, primary_key=True)
    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])
    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])
    patient_information_ID = db.Column(db.Integer, db.ForeignKey('patient_information.patient_information_ID'), nullable=False)
    patient_information = relationship("PatientInformation", foreign_keys=[patient_information_ID])
    overexpression = db.Column(db.Integer)

class SurvivalPValue(db.Model):
    __tablename__ = "survival_pvalue"
    survival_pValue_ID = db.Column(db.Integer, primary_key=True)
    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])
    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])
    pValue = db.Column(db.Float)

class GeneCount(db.Model):
    __tablename__ = "gene_counts"
    gene_count_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    count_all = db.Column(db.Integer)
    count_sign = db.Column(db.Integer)

class GeneOntology(db.Model):
    __tablename__ = "gene_ontology"
    gene_ontology_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    gene_ontology_symbol = db.Column(db.String(32))
    description = db.Column(db.String(32))

class hallmarks(db.Model):
    __tablename__ = "hallmarks"
    hallmarks_ID = db.Column(db.Integer, primary_key=True)


    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    hallmark = db.Column(db.String(32))

class wikipathways(db.Model):
    __tablename__ = "wikipathways"
    wikipathways_id = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    wp_key = db.Column(db.String(32))

class Transcript(db.Model):
    __tablename__ = "transcript"
    transcript_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    enst_number = db.Column(db.String(32))
    transcript_type = db.Column(db.String(32))
    start_pos = db.Column(db.Integer)
    end_pos = db.Column(db.Integer)
    canonical_transcript = db.Column(db.Integer)

class AlternativeSplicingEventTranscripts(db.Model):
    __tablename__ = "alternative_splicing_event_transcripts"
    alternative_splicing_event_transcripts_ID = db.Column(db.Integer, primary_key=True)

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    event_name = db.Column(db.String(32))
    event_type = db.Column(db.String(32))

class TranscriptElementPositions(db.Model):
    __tablename = "transcript_element_positions"
    transcript_element_positions_ID = db.Column(db.Integer, primary_key=True)

    start_pos = db.Column(db.Integer)
    end_pos = db.Column(db.Integer)
    order_number = db.Column(db.Integer)

class AlternativeSplicingEventTranscriptElements(db.Model):
    __tablename__ = "alternative_splicing_event_transcript_elements"
    alternative_splicing_event_transcript_elements_ID = db.Column(db.Integer, primary_key=True)

    alternative_splicing_event_transcripts_ID = db.Column(db.Integer, db.ForeignKey('alternative_splicing_event_transcripts.alternative_splicing_event_transcripts_ID'), nullable=False)
    alternative_splicing_event_transcripts = relationship("AlternativeSplicingEventTranscripts", foreign_keys=[alternative_splicing_event_transcripts_ID])

    transcript_element_positions_ID = db.Column(db.Integer, db.ForeignKey('transcript_element_positions.transcript_element_positions_ID'), nullable=False)
    transcript_element_positions = relationship("TranscriptElementPositions", foreign_keys=[transcript_element_positions_ID])

    order_number = db.Column(db.Integer)

class TranscriptElement(db.Model):
    __tablename__ = "transcript_element"
    transcript_element_ID = db.Column(db.Integer, primary_key=True)

    transcript_element_positions_ID = db.Column(db.Integer, db.ForeignKey('transcript_element_positions.transcript_element_positions_ID'), nullable=False)
    transcript_element_positions = relationship("TranscriptElementPositions", foreign_keys=[transcript_element_positions_ID])

    type = db.Column(db.String(32))
    ense_number = db.Column(db.String(32))

# chris: Change
class TranscriptInteraction(db.Model):
    __tablename__ = "interactions_transcripttranscript"
    interactions_transcripttranscript_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    transcript_ID_1 = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript_1 = relationship("Transcript", foreign_keys=[transcript_ID_1])
    transcript_ID_2 = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript_2 = relationship("Transcript", foreign_keys=[transcript_ID_2])

    p_value = db.Column(db.Float)
    mscor = db.Column(db.Float)
    correlation = db.Column(db.Float)


class TranscriptCounts(db.Model):
    __tablename__ = "transcript_counts"
    transcript_counts_ID = db.Column(db.Integer, primary_key=True)

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    count_all = db.Column(db.Integer)
    count_sign = db.Column(db.Integer)


class SpongEffectsRun(db.Model):
    __tablename__ = "spongEffects_run"
    spongEffects_run_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    m_scor_threshold = db.Column(db.Float)
    p_adj_threshold = db.Column(db.Float)
    modules_cutoff = db.Column(db.Integer)
    bin_size = db.Column(db.Integer)
    min_size = db.Column(db.Integer)
    max_size = db.Column(db.Integer)
    method = db.Column(db.String(32))
    cv_folds = db.Column(db.Integer)
    level = db.Column(db.String(32))

class SpongEffectsRunPerformance(db.Model):
    __tablename__ = "spongEffects_run_performance"
    spongEffects_run_performance_ID = db.Column(db.Integer, primary_key=True)
    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'))
    spongEffects_run = relationship('SpongEffectsRun', foreign_keys=[spongEffects_run_ID])

    model_type = db.Column(db.String(32))
    split_type = db.Column(db.String(32))
    accuracy = db.Column(db.Float)
    kappa = db.Column(db.Float)
    accuracy_lower = db.Column(db.Float)
    accuracy_upper = db.Column(db.Float)
    accuracy_null = db.Column(db.Float)
    accuracy_p_value = db.Column(db.Float)
    mcnemar_p_value = db.Column(db.Float)


class SpongEffectsRunClassPerformance(db.Model):
    __tablename__ = 'spongEffects_run_class_performance'
    spongEffects_run_class_performance_ID = db.Column(db.Integer, primary_key=True)
    spongEffects_run_performance_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run_performance.spongEffects_run_performance_ID'))
    spongEffects_run = relationship('SpongEffectsRunPerformance', foreign_keys=[spongEffects_run_performance_ID])

    prediction_class = db.Column(db.String(32))
    sensitivity = db.Column(db.Float)
    specificity = db.Column(db.Float)
    pos_pred_value = db.Column(db.Float)
    neg_pred_value = db.Column(db.Float)
    precision_value = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1 = db.Column(db.Float)
    prevalence = db.Column(db.Float)
    detection_rate = db.Column(db.Float)
    detection_prevalence = db.Column(db.Float)
    balanced_accuracy = db.Column(db.Float)


class SpongEffectsEnrichmentClassDensity(db.Model):
    __tablename__ = 'spongEffects_enrichment_class_density'
    spongEffects_enrichment_class_density_ID = db.Column(db.Integer, primary_key=True)
    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'))
    spongEffects_run = relationship('SpongEffectsRun', foreign_keys=[spongEffects_run_ID])

    prediction_class = db.Column(db.String(32))
    enrichment_score = db.Column(db.Float)
    density = db.Column(db.Float)

class ExpressionDataTranscript(db.Model):
    __tablename__ = "expression_data_transcript"
    expression_data_transcript_ID = db.Column(db.Integer, primary_key=True)

    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])
    
    expr_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))
    normal_cancer = db.Column(db.String(32))

class NetworkResults(db.Model):
    tablename = 'network_results'
    network_results_ID = db.Column(db.Integer, primary_key=True)
    sponge_run_ID_1 = db.Column(db.Integer)
    sponge_run_ID_2 = db.Column(db.Integer)
    score = db.Column(db.Integer)
    euclidean_distance = db.Column(db.Integer)
    level = db.Column(db.String(32))

class SpongEffectsTranscriptModule(db.Model):
    __tablename__ = "spongEffects_transcript_module"
    spongEffects_transcript_module_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer,
                                    db.ForeignKey("spongEffects_run.spongEffects_run_ID"), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    mean_gini_decrease = db.Column(db.Float)
    mean_accuracy_decrease = db.Column(db.Float)


class EnrichmentScoreTranscript(db.Model):
    __tablename__ = "enrichment_score_transcript"
    enrichment_score_transcript_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_transcript_module_ID = db.Column(db.Integer,
                                                  db.ForeignKey('spongEffects_transcript_module.spongEffects_transcript_module_ID'),
                                                  nullable=False)
    spongEffects_transcript_module = relationship('SpongEffectsTranscriptModule', foreign_keys=[spongEffects_transcript_module_ID])

    score_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))

class SpongEffectsTranscriptModuleMembers(db.Model):
    __tablename__ = "spongEffects_transcript_module_members"
    spongEffects_transcript_module_members_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_transcript_module_ID = db.Column(db.Integer,
                                                  db.ForeignKey(
                                                      'spongEffects_transcript_module.spongEffects_transcript_module_ID'),
                                                  nullable=False)
    spongEffects_transcript_module = relationship('SpongEffectsTranscriptModule',
                                                  foreign_keys=[spongEffects_transcript_module_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])


class SpongEffectsGeneModule(db.Model):
    __tablename__ = "spongEffects_gene_module"
    spongEffects_gene_module_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer,
                                    db.ForeignKey("spongEffects_run.spongEffects_run_ID"), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    mean_gini_decrease = db.Column(db.Float)
    mean_accuracy_decrease = db.Column(db.Float)


class EnrichmentScoreGene(db.Model):
    __tablename__ = "enrichment_score_gene"
    enrichment_score_gene_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_gene_module_ID = db.Column(db.Integer,
                                            db.ForeignKey('spongEffects_gene_module.spongEffects_gene_module_ID'), nullable=False)
    spongEffects_gene_module = relationship('SpongEffectsGeneModule', foreign_keys=[spongEffects_gene_module_ID])

    score_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))


class SpongEffectsGeneModuleMembers(db.Model):
    __tablename__ = "spongEffects_gene_module_members"
    spongEffects_gene_module_members_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_gene_module_ID = db.Column(db.Integer,
                                            db.ForeignKey('spongEffects_gene_module.spongEffects_gene_module_ID'),
                                            nullable=False)
    spongEffects_gene_module = relationship('SpongEffectsGeneModule', foreign_keys=[spongEffects_gene_module_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    
class Comparison(db.Model):
    __tablename__ = "comparison"
    comparison_ID = db.Column(db.Integer, primary_key=True)
    dataset_ID_1 = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset_1 = relationship("Dataset", foreign_keys=[dataset_ID_1])
    dataset_ID_2 = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset_2 = relationship("Dataset", foreign_keys=[dataset_ID_2])
    condition_1 = db.Column(db.String(32))
    condition_2 = db.Column(db.String(32))
    gene_transcript = db.Column(db.String(32))

class DifferentialExpression(db.Model):
    __tablename__ = "differential_expression_gene"
    differential_expression_gene_ID = db.Column(db.Integer, primary_key=True)
    comparison_ID = db.Column(db.Integer, db.ForeignKey('comparison.comparison_ID'), nullable=False)
    baseMean = db.Column(db.Float)
    log2FoldChange = db.Column(db.Float)
    lfcSE = db.Column(db.Float)
    pvalue = db.Column(db.Float)
    padj = db.Column(db.Float)
    stat = db.Column(db.Float)
    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

class DifferentialExpressionTranscript(db.Model):
    __tablename__ = "differential_expression_transcript"
    differential_expression_transcript_ID = db.Column(db.Integer, primary_key=True)
    comparison_ID = db.Column(db.Integer, db.ForeignKey('comparison.comparison_ID'), nullable=False)
    baseMean = db.Column(db.Float)
    log2FoldChange = db.Column(db.Float)
    lfcSE = db.Column(db.Float)
    pvalue = db.Column(db.Float)
    padj = db.Column(db.Float)
    stat = db.Column(db.Float)
    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

class Gsea(db.Model):
    __tablename__ = "gsea"
    gsea_ID = db.Column(db.Integer, primary_key=True)

    comparison_ID = db.Column(db.Integer, db.ForeignKey('comparison.comparison_ID'), nullable=False)
    comparison = relationship("Comparison", foreign_keys=[comparison_ID])

    term = db.Column(db.String(32))
    gene_set = db.Column(db.String(32))
    es = db.Column(db.Float)
    nes = db.Column(db.Float)
    pvalue = db.Column(db.Float)
    fdr = db.Column(db.Float)
    fwerp = db.Column(db.Float)
    gene_percent = db.Column(db.Float)

    lead_genes = relationship("GseaLeadGenes", back_populates="gsea", lazy="select") 
    matched_genes = relationship("GseaMatchedGenes", back_populates="gsea")
    gsea_ranking_genes = relationship("GseaRankingGenes", back_populates="gsea")
    res = relationship("GseaRes", back_populates="gsea")
    

class GseaLeadGenes(db.Model):
    __tablename__ = "gsea_lead_genes"

    gsea_lead_genes_ID = db.Column(db.Integer, nullable=False, primary_key=True)

    gsea_ID = db.Column(db.Integer, db.ForeignKey('gsea.gsea_ID'))
    gsea = relationship("Gsea", foreign_keys=[gsea_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])
    
class GseaMatchedGenes(db.Model):
    __tablename__ = "gsea_matched_genes"

    gsea_matched_genes_ID = db.Column(db.Integer, nullable=False, primary_key=True)

    gsea_ID = db.Column(db.Integer, db.ForeignKey('gsea.gsea_ID'))
    gsea = relationship("Gsea", foreign_keys=[gsea_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

class GseaRes(db.Model):
    __tablename__ = "gsea_res"
    gsea_ID = db.Column(db.Integer, db.ForeignKey('gsea.gsea_ID'), primary_key=True)
    gsea = relationship("Gsea", foreign_keys=[gsea_ID])

    res_ID = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float)

class GseaRankingGenes(db.Model):
    __tablename__ = "gsea_ranking_genes"
    gsea_ranking_genes_ID = db.Column(db.Integer, nullable=False, primary_key=True)

    gsea_ID = db.Column(db.Integer, db.ForeignKey('gsea.gsea_ID'))
    gsea = relationship("Gsea", foreign_keys=[gsea_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'))
    gene_symbol = relationship("Gene", foreign_keys=[gene_ID])

class PsiVec(db.Model):
    __tablename__ = 'psivec'
    psivec_ID = db.Column(db.Integer, primary_key=True)

    alternative_splicing_event_transcripts_ID = db.Column(db.Integer, db.ForeignKey('alternative_splicing_event_transcripts.alternative_splicing_event_transcripts_ID'), nullable=False)
    alternative_splicing_event_transcripts = relationship("AlternativeSplicingEventTranscripts", foreign_keys=[alternative_splicing_event_transcripts_ID])

    sample_ID = db.Column(db.String(32))
    psi_value = db.Column(db.Float)


class TissueSourceSite(db.Model):
    __tablename__ = 'tissue_source_site'
    tissue_source_site_ID = db.Column(db.Integer, primary_key=True)
    tissue_source_site_code = db.Column(db.String(32))
    disease_name = db.Column(db.String(255))



####################################
############# SCHEMAS ##############
####################################

class DiseaseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Disease
        sqla_session = db.session

    dataset_IDs = fields.List(fields.Integer)

class DatasetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Dataset
        sqla_session = db.session    

class SpongeRunSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongeRun
        sqla_session = db.session

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name", "data_origin")))

class GeneSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Gene
        sqla_session = db.session
        fields = ["chromosome_name", "description", "end_pos", "ensg_number", "gene_symbol", "gene_type", "start_pos", "cytoband"]

class GeneSchemaShort(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Gene
        sqla_session = db.session
        fields = ["ensg_number","gene_symbol"]

class TargetDatabasesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TargetDatabases
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema)


# never used 
# class AllSpongeRunInformationSchema(Schema):
#     sponge_run = fields.Nested(SpongeRunSchema)
#     target_databases = fields.Nested(lambda: TargetDatabasesSchema(only=("db_used", "url", "version")))


# class GeneInteractionLongSchema(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = GeneInteraction
#         sqla_session = db.session

#     sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID")))
#     gene1 = ma.Nested(lambda: GeneSchema(exclude=("gene_ID")))
#     gene2 = ma.Nested(lambda: GeneSchema(exclude=("gene_ID")))

# class GeneInteractionShortSchema(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = GeneInteraction
#         sqla_session = db.session

#     sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID")))
#     gene1 = ma.Nested(lambda: GeneSchema(only=("ensg_number")))
#     gene2 = ma.Nested(lambda: GeneSchema(only=("ensg_number")))

class GeneInteractionDatasetLongSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "run", "gene1", "gene2"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    gene1 = ma.Nested(GeneSchema)
    gene2 = ma.Nested(GeneSchema)

class GeneInteractionDatasetShortSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "sponge_run", "gene1", "gene2"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    gene1 = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))
    gene2 = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class miRNASchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = miRNA
        sqla_session = db.session
        fields = ["hs_nr", "id_type", "mir_ID", "seq", "chr", "start_position", "end_position", "cytoband"]

class miRNASchemaShort(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = miRNA
        sqla_session = db.session
        fields = ["hs_nr","mir_ID"]

class SpongeRunForMirnaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongeRun
        sqla_session = db.session

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name", )))

# never used, unclear
# class GeneInteractionDatasetForMiRNSchema(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = GeneInteraction
#         sqla_session = db.session

#     sponge_run = ma.Nested(lambda: SpongeRunForMirnaSchema(only=("sponge_run_ID","dataset")))
#     gene1 = ma.Nested(lambda:GeneSchema(only=("ensg_number", "gene_symbol")))
#     gene2 = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class miRNAInteractionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = miRNAInteraction
        sqla_session = db.session
        fields = ["sponge_run", "gene", "mirna", "coefficient"]

    sponge_run = ma.Nested(lambda: SpongeRunForMirnaSchema(only=("sponge_run_ID", "dataset")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))
    mirna = ma.Nested(lambda: miRNASchema(only=("mir_ID", "hs_nr")))

#chris: Change
class miRNAInteractionSchemaTranscript(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = miRNAInteractionTranscript
        sqla_session = db.session
        fields = ["sponge_run", "transcript", "mirna", "coefficient"]

    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", "gene")))
    sponge_run = ma.Nested(lambda: SpongeRunForMirnaSchema(only=("sponge_run_ID", "dataset")))
    mirna = ma.Nested(lambda: miRNASchema(only=("mir_ID", "hs_nr")))

class networkAnalysisSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = networkAnalysis
        sqla_session = db.session
        fields = ["betweenness", "eigenvector", "gene", "node_degree", "sponge_run"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

# chris: Change
class networkAnalysisSchemaTranscript(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = networkAnalysisTranscript
        sqla_session = db.session
        fields = ["betweenness", "eigenvector", "transcript", "node_degree", "sponge_run"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", "gene")))


class geneExpressionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GeneExpressionValues
        sqla_session = db.session
        fields = ["dataset", "expr_value", "gene", "sample_ID"]

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name", "disease_subtype")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class miRNAExpressionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MiRNAExpressionValues
        sqla_session = db.session
        fields = ["dataset", "expr_value", "mirna", "sample_ID"]

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name")))
    mirna = ma.Nested(lambda: miRNASchema(only=("mir_ID", "hs_nr")))

class occurencesMiRNASchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OccurencesMiRNA
        sqla_session = db.session
        fields = ["mirna", "occurences", "sponge_run"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    mirna = ma.Nested(lambda: miRNASchema(only=("mir_ID", "hs_nr")))

# chris: Change
class occurencesMiRNASchemaTranscript(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OccurencesMiRNATranscript
        sqla_session = db.session
        fields = ["mirna", "occurences", "sponge_run"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    mirna = ma.Nested(lambda: miRNASchema(only=("mir_ID", "hs_nr")))



class PatientInformationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PatientInformation
        sqla_session = db.session
        fields = ["dataset", "sample_ID", "disease_status", "survival_time"]
        
    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name")))

class SurvivalRateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SurvivalRate
        sql_session = db.session
        fields = ["dataset", "gene", "overexpression", "patient_information"]

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))
    patient_information = ma.Nested(lambda: PatientInformationSchema(only=("sample_ID", "disease_status", "survival_time")))

class SurvivalPValueSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SurvivalPValue
        sql_session = db.session
        fields = ["dataset", "gene", "pValue"]

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class checkGeneInteractionProCancer(ma.SQLAlchemyAutoSchema):
    class Meta:
        strict = True

    data_origin = fields.String()
    disease_name = fields.String()
    disease_subtype = fields.String()
    sponge_run_ID = fields.Integer()
    include = fields.Integer()

class checkTranscriptInteractionProCancer(ma.SQLAlchemyAutoSchema):
    class Meta:
        strict = True

    data_origin = fields.String()
    disease_name = fields.String()
    disease_subtype = fields.String()
    sponge_run_ID = fields.Integer()
    include = fields.Integer()

class GeneCountSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GeneCount
        sql_session = db.session
        fields = ["sponge_run", "gene", "count_all", "count_sign"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class OverallCountSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        strict = True

    count_interactions = fields.Integer()
    count_interactions_sign = fields.Integer()
    sponge_run_ID = fields.Integer()
    disease_name = fields.String()
    count_shared_miRNAs = fields.Integer()

class GeneOntologySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GeneOntology
        sql_session = db.session
        fields = ["gene", "gene_ontology_symbol", "description"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class HallmarksSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = hallmarks
        sql_session = db.session
        fields = ["gene", "hallmark"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class WikipathwaySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = wikipathways
        sql_session = db.session
        fields = ["gene", "wp_key"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class TranscriptSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Transcript
        sqla_session = db.session
        fields = ["gene", "enst_number", "transcript_type", "start_pos", "end_pos", "canonical_transcript"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class SpongEffectsRunSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongEffectsRun
        sqla_session = db.session
    sponge_run = ma.Nested(SpongeRunSchema)

class SpongEffectsRunPerformanceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongEffectsRunPerformance
        sqla_session = db.session
    spongEffects_run = ma.Nested(SpongEffectsRunSchema)

class SpongEffectsRunClassPerformanceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongEffectsRunClassPerformance
        sqla_session = db.session

    spongEffects_run = ma.Nested(lambda: SpongEffectsRunPerformanceSchema(only=("model_type", "split_type")))


class TranscriptInteractionLongSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TranscriptInteraction
        sqla_session = db.session

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", )))
    transcript_1 = ma.Nested(lambda: TranscriptSchema(exclude="transcript_ID"))
    transcript_2 = ma.Nested(lambda: TranscriptSchema(exclude="transcript_ID"))
    
# never used
# class TranscriptInteractionShortSchema(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = TranscriptInteraction
#         sqla_session = db.session

#     sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", )))
#     transcript_1 = ma.Nested(lambda: TranscriptSchema(only=("transcript_ID", )))
#     transcript_2 = ma.Nested(lambda: TranscriptSchema(only=("transcript_ID", )))


class TranscriptInteractionDatasetLongSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TranscriptInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "sponge_run", "transcript_1", "transcript_2"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    transcript_1 = ma.Nested(TranscriptSchema)
    transcript_2 = ma.Nested(TranscriptSchema)

class TranscriptInteractionDatasetShortSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TranscriptInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "sponge_run", "transcript_1", "transcript_2"]

    sponge_run = ma.Nested(lambda: SpongeRunSchema(only=("sponge_run_ID", "dataset")))
    transcript_1 = ma.Nested(lambda: TranscriptSchema(only=("enst_number", )))
    transcript_2 = ma.Nested(lambda: TranscriptSchema(only=("enst_number", )))

class GeneEnrichmentScoreSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = EnrichmentScoreGene
        sqla_session = db.session
        fields = ["spongEffects_run", "gene", "score_value", "sample_ID"]

    spongeEffects_run = ma.Nested(lambda: SpongEffectsRun(only=("spongEffects_run_ID", "sponge_run_ID")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class TranscriptEnrichmentScoreSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = EnrichmentScoreTranscript
        sqla_session = db.session
        fields = ["spongEffects_run", "transcript", "score_value", "sample_ID"]

    spongeEffects_run = ma.Nested(lambda: SpongEffectsRun(only=("spongEffects_run_ID", "sponge_run_ID")))
    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", )))


class TranscriptCountSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TranscriptCounts
        sqla_session = db.session
        fields = ["spongEffects_run", "transcript", "count_all", "count_sign"]

    spongeEffects_run = ma.Nested(lambda: SpongEffectsRun(only=("spongEffects_run_ID", "sponge_run_ID")))
    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", )))


class ExpressionDataTranscriptSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ExpressionDataTranscript
        sqla_session = db.session
        fields = ["dataset", "transcript", "expr_value", "sample_ID"]

    dataset = ma.Nested(lambda: DatasetSchema(only=("dataset_ID", "disease_name", "disease_subtype")))
    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", "gene")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class AlternativeSplicingEventsTranscriptsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AlternativeSplicingEventTranscripts
        sqla_session = db.session
        fields = ['alternative_splicing_event_transcripts_ID', "transcript", "event_name", "event_type"]

    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", )))


class TranscriptElementPositionsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TranscriptElementPositions
        sqla_session = db.session
        fields = ["start_pos", "end_pos"]

class AlternativeSplicingEventsTranscriptElementsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AlternativeSplicingEventTranscriptElements
        sqla_session = db.session
        fields = ["alternative_splicing_event_transcripts", "transcript_element_positions", "order_number"]

    alternative_splicing_event_transcripts = ma.Nested(AlternativeSplicingEventsTranscriptsSchema)
    transcript_element_positions = ma.Nested(TranscriptElementPositionsSchema)


class TranscriptElementSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TranscriptElement
        sqla_session = db.session
        fields = ["transcript_element_positions", "type", "ense_number"]

    transcript_element_positions = ma.Nested(TranscriptElementPositionsSchema)


class SpongEffectsEnrichmentClassDensitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongEffectsEnrichmentClassDensity
        sqla_session = db.session


class SpongEffectsGeneModuleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongEffectsGeneModule
        sqla_session = db.session
        fields = ['spongEffects_gene_module_ID', 
                  'spongEffects_run_ID', 
                  'gene',
                  'mean_gini_decrease',
                  'mean_accuracy_decrease']
        
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class SpongEffectsGeneModuleMembersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        strict = True
        model = SpongEffectsGeneModuleMembers
        sqla_session = db.session
        fields = ['spongEffects_gene_module_members_ID', 
                  'spongEffects_gene_module_ID', 
                  'gene']
        
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class SpongEffectsTranscriptModuleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SpongEffectsTranscriptModule
        sqla_session = db.session
        fields = ['spongEffects_transcript_module_ID', 
                  'spongEffects_run_ID', 
                  'transcript',
                  'mean_gini_decrease',
                  'mean_accuracy_decrease']
        
    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", "gene")))


class SpongEffectsTranscriptModuleMembersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        strict = True
        model = SpongEffectsTranscriptModuleMembers
        sqla_session = db.session
        fields = ['spongEffects_transcript_module_members_ID',
                  'spongEffects_transcript_module_ID',
                   'transcript']
        
    transcript = ma.Nested(lambda: TranscriptSchema(only=("enst_number", "gene")))
    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class DESchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DifferentialExpression
        sqla_session = db.session
    
    gene = ma.Nested(lambda: GeneSchemaShort(only=("gene_symbol")))

class DETranscriptSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DifferentialExpression
        sqla_session = db.session
    transcript = ma.Nested(lambda: GeneSchemaShort(only=("enst_number")))

class DESchemaShort(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DifferentialExpression
        sqla_session = db.session
        fields = ["gene_ID", "log2FoldChange"]
    
class GseaResSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GseaRes
        sqla_session = db.session
        fields = ["res_ID", "score"]

class GseaLeadGenesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GseaLeadGenes
        sqla_session = db.session
        fields = ["gsea_lead_genes_ID", "gene"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))


class GseaMatchedGenesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GseaMatchedGenes
        sqla_session = db.session
        fields = ["gsea_matched_genes_ID", "gene"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))

class GseaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Gsea
        sqla_session = db.session
        load_instance = True
        fields = ["term", "es", "nes", "pvalue", "fdr", "fwerp", "gene_percent", "lead_genes", "matched_genes", "res"]

    lead_genes = ma.Nested(GseaLeadGenesSchema, many=True)
    matched_genes = ma.Nested(GseaMatchedGenesSchema, many=True)
    res = ma.Nested(lambda: GseaResSchema(only=("res_ID", "score")))

class GseaRankingGenesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GseaRankingGenes
        sqla_session = db.session
        fields = ["gsea_ranking_genes_ID", "gene", "gsea"]

    gene = ma.Nested(lambda: GeneSchema(only=("ensg_number", "gene_symbol")))
    gsea = ma.Nested(lambda: GseaSchema(only=("term", )))

class GseaSchemaPlot(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Gsea
        sqla_session = db.session
        fields = ["term", "nes", "pvalue", "fdr", "res", "matched_genes", "gsea_ranking_genes"]

    # res = ma.Nested(lambda: GseaResSchema(only=("res_ID", "score")))
    # matched_genes = ma.Nested(lambda: GseaMatchedGenesSchema())
    # gsea_ranking_genes = ma.Nested(lambda: GseaRankingGenesSchema())


class GseaTermsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Gsea
        sqla_session = db.session
        fields = ["term"]
    
class GseaSetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Gsea
        sqla_session = db.session
        fields = ["gene_set"]
    
class ComparisonSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Comparison
        sqla_session = db.session

    dataset_1 = ma.Nested(DatasetSchema)
    dataset_2 = ma.Nested(DatasetSchema)

class PsiVecSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PsiVec
        sqla_session = db.session

    alternative_splicing_event_transcripts = ma.Nested(AlternativeSplicingEventsTranscriptsSchema)

