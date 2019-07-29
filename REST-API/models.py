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

class GeneInteraction(db.Model):
    __tablename__ = 'interactions_genegene'
    interactions_genegene_ID = db.Column(db.Integer, primary_key=True)

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

    gene_ID1 = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene1 = relationship("Gene", foreign_keys=[gene_ID1])
    gene_ID2 = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene2 = relationship("Gene", foreign_keys=[gene_ID2]
                         )
    p_value = db.Column(db.Float)
    mscore = db.Column(db.Float)
    correlation = db.Column(db.Float)

class miRNAInteraction(db.Model):
    __tablename__ = "interacting_miRNAs"
    interacting_miRNAs_ID = db.Column(db.Integer, primary_key=True)
    interactions_genegene_ID = db.Column(db.Integer, db.ForeignKey('interactions_genegene.interactions_genegene_ID'), nullable=False)
    interactions_genegene = relationship("GeneInteraction", foreign_keys=[interactions_genegene_ID])

    miRNA_ID = db.Column(db.Integer, db.ForeignKey('mirna.miRNA_ID'), nullable=False)
    mirna = relationship("miRNA", foreign_keys=[miRNA_ID])

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

class miRNA(db.Model):
    __tablename__ = "mirna"
    miRNA_ID = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.String(32))
    mir_ID = db.Column(db.String(32))
    seq = db.Column(db.String(32))
    hs_nr = db.Column(db.String(32))


class networkAnalysis(db.Model):
    __tablename__ = "network_analysis"
    network_analysis_ID = db.Column(db.Integer, primary_key=True)

    gene_ID = db.Column(db.Integer, db.ForeignKey('gene.gene_ID'), nullable=False)
    gene = relationship("Gene", foreign_keys=[gene_ID])

    run_ID = db.Column(db.Integer, db.ForeignKey('run.run_ID'), nullable=False)
    run = relationship("Run", foreign_keys=[run_ID])

    eigenvector = db.Column(db.Float)
    betweeness = db.Column(db.Float)
    node_degree = db.Column(db.Float)


class DatasetSchema(ma.ModelSchema):
    class Meta:
        model = Dataset
        sqla_session = db.session

class RunSchema(ma.ModelSchema):
    class Meta:
        model = Run
        sqla_session = db.session

    dataset = ma.Nested(DatasetSchema, only=("dataset_ID", "disease_name"))

class GeneSchema(ma.ModelSchema):
    class Meta:
        model = Gene
        sqla_session = db.session

class GeneInteractionLongSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        #include_fk = True

    run = ma.Nested(RunSchema, only=("run_ID"))
    gene1 = ma.Nested(GeneSchema, exclude=("gene_ID"))
    gene2 = ma.Nested(GeneSchema, exclude=("gene_ID"))

class GeneInteractionShortSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session
        #include_fk = True

    run = ma.Nested(RunSchema, only=("run_ID"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number"))

class GeneInteractionDatasetLongSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
    gene1 = ma.Nested(GeneSchema, exclude=("gene_ID"))
    gene2 = ma.Nested(GeneSchema, exclude=("gene_ID"))

class GeneInteractionDatasetShortSchema(ma.ModelSchema):
    class Meta:
        model = GeneInteraction
        sqla_session = db.session

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
    gene1 = ma.Nested(GeneSchema, only=("ensg_number"))
    gene2 = ma.Nested(GeneSchema, only=("ensg_number"))

class miRNASchema(ma.ModelSchema):
    class Meta:
        model = miRNA
        sqla_session = db.session

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

class miRNAInteractionLongSchema(ma.ModelSchema):
    class Meta:
        model = miRNAInteraction
        sqla_session = db.session

    interactions_genegene = ma.Nested(GeneInteractionDatasetForMiRNSchema,only=("run", "gene1","gene2"))
    mirna = ma.Nested(miRNASchema)

class miRNAInteractionShortSchema(ma.ModelSchema):
    class Meta:
        model = miRNAInteraction
        sqla_session = db.session

    interactions_genegene = ma.Nested(GeneInteractionDatasetForMiRNSchema,only=("run", "gene1","gene2"))
    mirna = ma.Nested(miRNASchema, only=("mir_ID", "hs_nr"))

class miRNAInteractionAllSeachLongSchema(Schema):
    class Meta:
        strict = True

    mir_ID = fields.String()
    hs_nr = fields.String()
    id_type = fields.String()
    seq = fields.String()
    count = fields.Integer()
    run_ID = fields.Integer()
    disease_name = fields.String()

class miRNAInteractionAllSeachShortSchema(Schema):
    class Meta:
        strict = True

    mir_ID = fields.String()
    hs_nr = fields.String()
    count = fields.Integer()
    run_ID = fields.Integer()
    disease_name = fields.String()


class networkAnalysisSchema(ma.ModelSchema):
    class Meta:
        model = networkAnalysis
        sqla_session = db.session

    run = ma.Nested(RunSchema, only=("run_ID", "dataset"))
    gene = ma.Nested(GeneSchema, only=("gene_ID", "ensg_number", "gene_symbol"))
