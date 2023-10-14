from marshmallow import fields, Schema
from sqlalchemy.orm import relationship

from config import db, ma


class Dataset(db.Model):
    __tablename__ = 'dataset'
    dataset_ID = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(32))
    data_origin = db.Column(db.String(32))
    disease_type = db.Column(db.String(32))
    download_url = db.Column(db.String(32))
    disease_subtype = db.Column(db.String(32))
    study_abbreviation = db.Column(db.String(32))
    version = db.Column(db.Integer)

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


class SelectedGenes(db.Model):
    __tablename__ = "selected_genes"
    selected_genes_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])


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
    __tablename__ = "interacting_miRNAs"
    interacting_miRNAs_ID = db.Column(db.Integer, primary_key=True)

    sponge_run_ID = db.Column(db.Integer, db.ForeignKey('sponge_run.sponge_run_ID'), nullable=False)
    sponge_run = relationship("SpongeRun", foreign_keys=[sponge_run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

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
    __tablename__ = "network_analysis"
    network_analysis_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

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
    normale_cancer = db.Column(db.String(32))


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
    __tablename__ = "occurences_miRNA"
    occurences_miRNA_ID = db.Column(db.Integer, primary_key=True)
    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])
    occurences = db.Column(db.Integer)
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
    __tablename__ = "survival_pValue"
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


class InteractionsTranscriptTranscript(db.Model):
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

class ExpressionDataTranscript(db.Model):
    __tablename__ = "expression_data_transcript"
    expression_data_transcript_ID = db.Column(db.Integer, primary_key=True)

    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    expr_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))


class DifferentialExpressionTranscript(db.Model):
    __tablename__ = "differential_expression_transcript"
    differential_expression_transcript_ID = db.Column(db.Integer, primary_key=True)

    expression_data_transcript_ID_1 = db.Column(db.Integer, db.ForeignKey('expression_data_transcript.expression_data_transcript_ID'), nullable=False)
    expression_data_transcript_1 = relationship("ExpressionDataTranscript", foreign_keys=[expression_data_transcript_ID_1])
    expression_data_transcript_ID_2 = db.Column(db.Integer, db.ForeignKey('expression_data_transcript.expression_data_transcript_ID'), nullable=False)
    expression_data_transcript_2 = relationship("ExpressionDataTranscript", foreign_keys=[expression_data_transcript_ID_2])

    score = db.Column(db.Float)
    fold_change = db.Column(db.Float)
    p_value = db.Column(db.Float)


class DifferentialExpressionGene(db.Model):
    __tablename__ = "differential_expression_gene"
    differential_expression_gene_ID = db.Column(db.Integer, primary_key=True)

    expression_data_gene_ID_1 = db.Column(db.Integer, db.ForeignKey('expression_data_gene.expression_data_gene_ID'), nullable=False)
    expression_data_gene_1 = relationship("GeneExpressionValues", foreign_keys=[expression_data_gene_ID_1])
    expression_data_gene_ID_2 = db.Column(db.Integer, db.ForeignKey('expression_data_gene.expression_data_gene_ID'), nullable=False)
    expression_data_gene_2 = relationship("GeneExpressionValues", foreign_keys=[expression_data_gene_ID_2])

    score = db.Column(db.Float)
    fold_change = db.Column(db.Float)
    p_value = db.Column(db.Float)


class EnrichmentScoreTranscript(db.Model):
    __tablename__ = "enrichment_score_transcript"
    enrichment_score_transcript_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    score_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))


class SpongEffectsTranscript(db.Model):
    __tablename__ = "spongEffects_transcript"
    spongEffects_transcript_ID = db.Column(db.Integer, primary_key=True)

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    enrichment_score_transcript_ID = db.Column(db.Integer, db.ForeignKey('enrichment_score_transcript.enrichment_score_transcript_ID'), nullable=False)
    enrichment_score_transcript = relationship("EnrichmentScoreTranscript", foreign_keys=[enrichment_score_transcript_ID])


class EnrichmentScoreGene(db.Model):
    __tablename__ = "enrichment_score_gene"
    enrichment_score_gene_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    score_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))


class SpongEffectsGene(db.Model):
    __tablename__ = "spongEffects_gene"
    spongEffects_gene_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    enrichment_score_gene_ID = db.Column(db.Integer, db.ForeignKey('enrichment_score_gene.enrichment_score_gene_ID'), nullable=False)
    enrichment_score_gene = relationship("EnrichmentScoreGene", foreign_keys=[enrichment_score_gene_ID])


class SpongEffectsTranscriptModule(db.Model):
    __tablename__ = "spongEffects_transcript_module"
    spongEffects_transcript_module_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    hub_transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    hub_transcript = relationship("Transcript", foreign_keys=[hub_transcript_ID])

    enrichment_score_transcript_ID = db.Column(db.Integer, db.ForeignKey('enrichment_score_transcript.enrichment_score_transcript_ID'), nullable=False)
    enrichment_score_transcript = relationship("EnrichmentScoreTranscript", foreign_keys=[enrichment_score_transcript_ID])


class SpongEffectsGeneModule(db.Model):
    __tablename__ = "spongEffects_gene_module"
    spongEffects_gene_module_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    hub_gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    hub_gene = relationship("Gene", foreign_keys=[hub_gene_ID])

    enrichment_score_gene_ID = db.Column(db.Integer, db.ForeignKey('enrichment_score_gene.enrichment_score_gene_ID'), nullable=False)
    enrichment_score_gene = relationship("EnrichmentScoreGene", foreign_keys=[enrichment_score_gene_ID])


class SpongEffectsGeneModuleMembers(db.Model):
    __tablename__ = "spongEffects_gene_module_members"
    spongEffects_gene_module_members_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    enrichment_score_gene_ID = db.Column(db.Integer, db.ForeignKey('enrichment_score_gene.enrichment_score_gene_ID'), nullable=False)
    enrichment_score_gene = relationship("EnrichmentScoreGene", foreign_keys=[enrichment_score_gene_ID])


class SpongEffectsTranscriptModuleMembers(db.Model):
    __tablename__ = "spongEffects_transcript_module_members"
    spongEffects_transcript_module_members_ID = db.Column(db.Integer, primary_key=True)

    spongEffects_run_ID = db.Column(db.Integer, db.ForeignKey('spongEffects_run.spongEffects_run_ID'), nullable=False)
    spongEffects_run = relationship("SpongEffectsRun", foreign_keys=[spongEffects_run_ID])

    transcript_ID = db.Column(db.Integer, db.ForeignKey('transcript.transcript_ID'), nullable=False)
    transcript = relationship("Transcript", foreign_keys=[transcript_ID])

    enrichment_score_transcript_ID = db.Column(db.Integer, db.ForeignKey('enrichment_score_transcript.enrichment_score_transcript_ID'), nullable=False)
    enrichment_score_transcript = relationship("EnrichmentScoreTranscript", foreign_keys=[enrichment_score_transcript_ID])


class DatasetSchema(ma.ModelSchema):
    class Meta:
        model = Dataset
        sqla_session = db.session

class SpongeRunSchema(ma.ModelSchema):
    class Meta:
        model = SpongeRun
        sqla_session = db.session

    dataset = ma.Nested(DatasetSchema, only=("dataset_ID", "disease_name", "data_origin"))

class DatasetDetailedSchema(ma.ModelSchema):
    class Meta:
        model = SpongeRun
        sqla_session = db.session
        fields = ["number_of_samples", "dataset"]
    dataset = ma.Nested(DatasetSchema, only=("study_abbreviation", "disease_name", "disease_subtype"))

class GeneSchema(ma.ModelSchema):
    class Meta:
        model = Gene
        sqla_session = db.session
        fields = ["chromosome_name", "description", "end_pos", "ensg_number", "gene_symbol", "gene_type", "start_pos", "cytoband"]

class GeneSchemaShort(ma.ModelSchema):
    class Meta:
        model = Gene
        sqla_session = db.session
        fields = ["ensg_number","gene_symbol"]

class SelectedGenesSchema(ma.ModelSchema):
    class Meta:
        model = SelectedGenes
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema)
    gene = ma.Nested(GeneSchema, only=("ensg_number"))


class TargetDatabasesSchema(ma.ModelSchema):
    class Meta:
        model = TargetDatabases
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema)


class AllSpongeRunInformationSchema(Schema):
    sponge_run = fields.Nested(SpongeRunSchema)
    target_databases = fields.Nested(TargetDatabasesSchema, only=("db_used", "url", "version"))
    selected_genes = fields.Nested(SelectedGenesSchema, only="gene")


class GeneInteractionLongSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID"))
    gene1 = ma.Nested(GeneSchema, exclude=("gene_ID"))
    gene2 = ma.Nested(GeneSchema, exclude=("gene_ID"))

class GeneInteractionShortSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number"))

class GeneInteractionDatasetLongSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "run", "gene1", "gene2"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    gene1 = ma.Nested(GeneSchema)
    gene2 = ma.Nested(GeneSchema)

class GeneInteractionDatasetShortSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "sponge_run", "gene1", "gene2"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class miRNASchema(ma.ModelSchema):
    class Meta:
        model = miRNA
        sqla_session = db.session
        fields = ["hs_nr", "id_type", "mir_ID", "seq", "chr", "start_position", "end_position", "cytoband"]

class miRNASchemaShort(ma.ModelSchema):
    class Meta:
        model = miRNA
        sqla_session = db.session
        fields = ["hs_nr","mir_ID"]

class SpongeRunForMirnaSchema(ma.ModelSchema):
    class Meta:
        model = SpongeRun
        sqla_session = db.session

    dataset = ma.Nested(DatasetSchema, only=("disease_name"))

class GeneInteractionDatasetForMiRNSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunForMirnaSchema, only=("sponge_run_ID","dataset"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class miRNAInteractionSchema(ma.ModelSchema):
    class Meta:
        model = miRNAInteraction
        sqla_session = db.session
        fields = ["sponge_run", "gene", "mirna", "coefficient"]

    sponge_run = ma.Nested(SpongeRunForMirnaSchema, only=("sponge_run_ID", "dataset"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    mirna = ma.Nested(miRNASchema, only=("mir_ID", "hs_nr"))

class networkAnalysisSchema(ma.ModelSchema):
    class Meta:
        model = networkAnalysis
        sqla_session = db.session
        fields = ["betweenness", "eigenvector", "gene", "node_degree", "sponge_run"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))


class geneExpressionSchema(ma.ModelSchema):
    class Meta:
        model = GeneExpressionValues
        sqla_session = db.session
        fields = ["dataset", "expr_value", "gene", "sample_ID"]

    dataset = ma.Nested(DatasetSchema, only=("disease_name"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))


class miRNAExpressionSchema(ma.ModelSchema):
    class Meta:
        model = MiRNAExpressionValues
        sqla_session = db.session
        fields = ["dataset", "expr_value", "mirna", "sample_ID"]

    dataset = ma.Nested(DatasetSchema, only=("disease_name"))
    mirna = ma.Nested(miRNASchema, only=("mir_ID", "hs_nr"))

class occurencesMiRNASchema(ma.ModelSchema):
    class Meta:
        model = OccurencesMiRNA
        sqla_session = db.session
        fields = ["mirna", "occurences", "sponge_run"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    mirna = ma.Nested(miRNASchema, only=("mir_ID", "hs_nr"))

class PatientInformationSchema(ma.ModelSchema):
    class Meta:
        model = PatientInformation
        sqla_session = db.session
        fields = ["dataset", "sample_ID", "disease_status", "survival_time"]
        
    dataset = ma.Nested(DatasetSchema, only=("disease_name"))

class SurvivalRateSchema(ma.ModelSchema):
    class Meta:
        model = SurvivalRate
        sql_session = db.session
        fields = ["dataset", "gene", "overexpression", "patient_information"]

    dataset = ma.Nested(DatasetSchema, only=("disease_name"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    patient_information = ma.Nested(PatientInformationSchema, only=("sample_ID", "disease_status", "survival_time"))

class SurvivalPValueSchema(ma.ModelSchema):
    class Meta:
        model = SurvivalPValue
        sql_session = db.session
        fields = ["dataset", "gene", "pValue"]

    dataset = ma.Nested(DatasetSchema, only=("disease_name"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class checkGeneInteractionProCancer(ma.ModelSchema):
    class Meta:
        strict = True

    data_origin = fields.String()
    disease_name = fields.String()
    sponge_run_ID = fields.Integer()
    include = fields.Integer()

class GeneCountSchema(ma.ModelSchema):
    class Meta:
        model = GeneCount
        sql_session = db.session
        fields = ["sponge_run", "gene", "count_all", "count_sign"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class OverallCountSchema(ma.ModelSchema):
    class Meta:
        strict = True

    count_interactions = fields.Integer()
    count_interactions_sign = fields.Integer()
    sponge_run_ID = fields.Integer()
    disease_name = fields.String()
    count_shared_miRNAs = fields.Integer()

class GeneOntologySchema(ma.ModelSchema):
    class Meta:
        model = GeneOntology
        sql_session = db.session
        fields = ["gene", "gene_ontology_symbol", "description"]

    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class HallmarksSchema(ma.ModelSchema):
    class Meta:
        model = hallmarks
        sql_session = db.session
        fields = ["gene", "hallmark"]

    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class WikipathwaySchema(ma.ModelSchema):
    class Meta:
        model = wikipathways
        sql_session = db.session
        fields = ["gene", "wp_key"]

    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class DistinctGeneSetSchema(ma.ModelSchema):
    #class Meta:
    #    strict = True

    #gene = fields.String()
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["gene1", "gene2"]

    gene1 = ma.Nested(GeneSchema, only=("ensg_number"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number"))

class TranscriptSchema(ma.ModelSchema):
    class Meta:
        model = Transcript
        sqla_session = db.session
        fields = ["gene", "enst_number", "transcript_type", "start_pos", "end_pos", "canonical_transcript"]

    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class SpongEffectsRunSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsRun
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema)

class SpongEffectsRunPerformanceSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsRunPerformance
        sqla_session = db.session
    sponge_effects_run_performance = ma.Nested(SpongEffectsRunSchema)

class SpongEffectsRunClassPerformanceSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsRunClassPerformance
        sqla_session = db.session

    sponge_effects_run_performance = ma.Nested(SpongEffectsRunPerformance)


class TranscriptInteractionLongSchema(ma.ModelSchema):
    class Meta:
        model = InteractionsTranscriptTranscript
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema, only="sponge_run_ID")
    transcript1 = ma.Nested(TranscriptSchema, exclude="transcript_ID")
    transcript2 = ma.Nested(TranscriptSchema, exclude="transcript_ID")

class TranscriptInteractionShortSchema(ma.ModelSchema):
    class Meta:
        model = InteractionsTranscriptTranscript
        sqla_session = db.session

    sponge_run = ma.Nested(SpongeRunSchema, only="sponge_run_ID")
    transcript1 = ma.Nested(TranscriptSchema, only="transcript_ID")
    transcript2 = ma.Nested(TranscriptSchema, only="transcript_ID")


class TranscriptInteractionDatasetLongSchema(ma.ModelSchema):
    class Meta:
        model = InteractionsTranscriptTranscript
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "sponge_run", "transcript1", "transcript2"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    transcript1 = ma.Nested(TranscriptSchema)
    transcript2 = ma.Nested(TranscriptSchema)

class TranscriptInteractionDatasetShortSchema(ma.ModelSchema):
    class Meta:
        model = InteractionsTranscriptTranscript
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "sponge_run", "transcript1", "transcript2"]

    sponge_run = ma.Nested(SpongeRunSchema, only=("sponge_run_ID", "dataset"))
    transcript1 = ma.Nested(TranscriptSchema, only="enst_number")
    transcript2 = ma.Nested(TranscriptSchema, only="enst_number")


class GeneEnrichmentScoreSchema(ma.ModelSchema):
    class Meta:
        model = EnrichmentScoreGene
        sqla_session = db.session
        fields = ["spongEffects_run", "gene", "score_value", "sample_ID"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))


class TranscriptEnrichmentScoreSchema(ma.ModelSchema):
    class Meta:
        model = EnrichmentScoreTranscript
        sqla_session = db.session
        fields = ["spongEffects_run", "transcript", "score_value", "sample_ID"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    transcript = ma.Nested(TranscriptSchema, only="enst_number")


class TranscriptCountSchema(ma.ModelSchema):
    class Meta:
        model = TranscriptCounts
        sqla_session = db.session
        fields = ["spongEffects_run", "transcript", "count_all", "count_sign"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    transcript = ma.Nested(TranscriptSchema, only="enst_number")


class ExpressionDataTranscriptSchema(ma.ModelSchema):
    class Meta:
        model = ExpressionDataTranscript
        sqla_session = db.session
        fields = ["dataset", "transcript", "expr_value", "sample_ID"]

    dataset = ma.Nested(DatasetSchema, only=("dataset_ID", "disease_name", "data_origin"))
    transcript = ma.Nested(TranscriptSchema, only="enst_number")


class AlternativeSplicingEventsTranscriptsSchema(ma.ModelSchema):
    class Meta:
        model = AlternativeSplicingEventTranscripts
        sqla_session = db.session
        fields = ["transcript", "event_name", "event_type"]

    transcript = ma.Nested(TranscriptSchema, only="enst_number")


class TranscriptElementPositionsSchema(ma.ModelSchema):
    class Meta:
        model = TranscriptElementPositions
        sqla_session = db.session
        fields = ["start_pos", "end_pos"]

class AlternativeSplicingEventsTranscriptElementsSchema(ma.ModelSchema):
    class Meta:
        model = AlternativeSplicingEventTranscriptElements
        sqla_session = db.session
        fields = ["alternative_splicing_event_transcripts", "transcript_element_positions", "order_number"]

    alternative_splicing_event_transcripts = ma.Nested(AlternativeSplicingEventsTranscriptsSchema)
    transcript_element_positions = ma.Nested(TranscriptElementPositionsSchema)


class TranscriptElementSchema(ma.ModelSchema):
    class Meta:
        model = TranscriptElement
        sqla_session = db.session
        fields = ["transcript_element_positions", "type", "ense_number"]

    transcript_element_positions = ma.Nested(TranscriptElementPositionsSchema)


class TranscriptSpongEffectsSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsTranscript
        sqla_session = db.session
        fields = ["transcript", "enrichment_score_transcript"]

    transcript = ma.Nested(TranscriptSchema, only="enst_number")
    enrichment_score_transcript = ma.Nested(TranscriptEnrichmentScoreSchema)


class GeneSpongEffectsSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsGene
        sqla_session = db.session
        fields = ["gene", "enrichment_score_gene"]

    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    enrichment_score_gene = ma.Nested(GeneEnrichmentScoreSchema)


class SpongEffectsTranscriptModuleSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsTranscriptModule
        sqla_session = db.session
        fields = ["spongEffects_run", "hub_transcript", "enrichment_score_transcript"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    hub_transcript = ma.Nested(TranscriptSchema, only="enst_number")
    enrichment_score_transcript = ma.Nested(TranscriptEnrichmentScoreSchema)


class SpongEffectsGeneModuleSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsGeneModule
        sqla_session = db.session
        fields = ["spongEffects_run", "hub_gene", "enrichment_score_gene"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    hub_gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    enrichment_score_gene = ma.Nested(GeneEnrichmentScoreSchema)


class SpongEffectsGeneModuleMembersSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsGeneModuleMembers
        sqla_session = db.session
        fields = ["spongEffects_run", "gene", "enrichment_score_gene"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    enrichment_score_gene = ma.Nested(GeneEnrichmentScoreSchema)


class SpongEffectsTranscriptModuleMembersSchema(ma.ModelSchema):
    class Meta:
        model = SpongEffectsTranscriptModuleMembers
        sqla_session = db.session
        fields = ["spongEffects_run", "transcript", "enrichment_score_transcript"]

    spongeEffects_run = ma.Nested(SpongEffectsRun, only=("spongEffects_run_ID", "sponge_run_ID"))
    transcript = ma.Nested(TranscriptSchema, only="enst_number")
    enrichment_score_transcript = ma.Nested(TranscriptEnrichmentScoreSchema)
