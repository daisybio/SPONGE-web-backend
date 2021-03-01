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

class Run(db.Model):
    __tablename__ = "run"
    run_ID = db.Column(db.Integer, primary_key=True)

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


class SelectedGenes(db.Model):
    __tablename__ = "selected_genes"
    selected_genes_ID = db.Column(db.Integer, primary_key=True)

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])


class TargetDatabases(db.Model):
    __tablename__ = "target_databases"
    td_ID = db.Column(db.Integer, primary_key=True)

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

    db_used = db.Column(db.String(32))
    version = db.Column(db.String(32))
    url = db.Column(db.String(32))

class GeneInteraction(db.Model):
    __tablename__ = 'interactions_genegene'
    interactions_genegene_ID = db.Column(db.Integer, primary_key=True)

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

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

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

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

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

    eigenvector = db.Column(db.Float)
    betweenness = db.Column(db.Float)
    node_degree = db.Column(db.Float)


class GeneExpressionValues(db.Model):
    __tablename__ = "expression_data_gene"
    expr_ID = db.Column(db.Integer, primary_key=True)
    dataset_ID = db.Column(db.Integer, db.ForeignKey('dataset.dataset_ID'), nullable=False)
    dataset = relationship("Dataset", foreign_keys=[dataset_ID])
    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])
    expr_value = db.Column(db.Float)
    sample_ID = db.Column(db.String(32))


class MiRNAExpressionValues(db.Model):
    __tablename__ = "expression_data_mirna"
    expr_ID = db.Column(db.Integer, primary_key=True)
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
    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

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

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

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

class DatasetSchema(ma.ModelSchema):
    class Meta:
        model = Dataset
        sqla_session = db.session

class RunSchema(ma.ModelSchema):
    class Meta:
        model = Run
        sqla_session = db.session

    dataset = ma.Nested(DatasetSchema, only=("dataset_ID", "disease_name", "data_origin"))

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

    run = ma.Nested(RunSchema)
    gene = ma.Nested(GeneSchema, olny=("ensg_number"))


class TargetDatabasesSchema(ma.ModelSchema):
    class Meta:
        model = TargetDatabases
        sqla_session = db.session

    run = ma.Nested(RunSchema)


class AllRunInformationSchema(Schema):
    run = fields.Nested(RunSchema)
    target_databases = fields.Nested(TargetDatabasesSchema, only=("db_used", "url", "version"))
    selected_genes = fields.Nested(SelectedGenesSchema, only="gene")


class GeneInteractionLongSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    run = ma.Nested(RunSchema, only=("run_ID"))
    gene1 = ma.Nested(GeneSchema, exclude=("gene_ID"))
    gene2 = ma.Nested(GeneSchema, exclude=("gene_ID"))

class GeneInteractionShortSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    run = ma.Nested(RunSchema, only=("run_ID"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number"))

class GeneInteractionDatasetLongSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "run", "gene1", "gene2"]

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
    gene1 = ma.Nested(GeneSchema)
    gene2 = ma.Nested(GeneSchema)

class GeneInteractionDatasetShortSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        fields = ["correlation", "mscor", "p_value", "run", "gene1", "gene2"]

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
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

class RunForMirnaSchema(ma.ModelSchema):
    class Meta:
        model = Run
        sqla_session = db.session

    dataset = ma.Nested(DatasetSchema, only=("disease_name"))

class GeneInteractionDatasetForMiRNSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    run = ma.Nested(RunForMirnaSchema, only=("run_ID","dataset"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class miRNAInteractionSchema(ma.ModelSchema):
    class Meta:
        model = miRNAInteraction
        sqla_session = db.session
        fields = ["run", "gene", "mirna", "coefficient"]

    run = ma.Nested(RunForMirnaSchema, only=("run_ID", "dataset"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))
    mirna = ma.Nested(miRNASchema, only=("mir_ID", "hs_nr"))

class networkAnalysisSchema(ma.ModelSchema):
    class Meta:
        model = networkAnalysis
        sqla_session = db.session
        fields = ["betweenness", "eigenvector", "gene", "node_degree", "run"]

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
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
        fields = ["mirna", "occurences", "run"]

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
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
    run_ID = fields.Integer()
    include = fields.Integer()

class GeneCountSchema(ma.ModelSchema):
    class Meta:
        model = GeneCount
        sql_session = db.session
        fields = ["run", "gene", "count_all", "count_sign"]

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
    gene = ma.Nested(GeneSchema, only=("ensg_number", "gene_symbol"))

class OverallCountSchema(ma.ModelSchema):
    class Meta:
        strict = True

    count_interactions = fields.Integer()
    count_interactions_sign = fields.Integer()
    run_ID = fields.Integer()
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