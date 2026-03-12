# from app.datadb.Model import db.Model, DBSession
# from sqlalchemy.schema import db.Column, db.ForeignKey
# from sqlalchemy.types import db.String, Text, Enum, db.Integer, db.Float
# from sqlalchemy.orm import db.relationship
from sqlalchemy.sql.expression import and_
from app import db
import enum

class ExpressionCollection(db.Model):
    __tablename__ = 'expression_collection'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(45), unique=True)

class ExpressionTissue(db.Model):
    __tablename__ = 'expression_tissue'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(45), unique=True)

class ExpressionSample(db.Model):
    __tablename__ = 'expression_samples'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    probeset_id = db.Column(db.Integer, db.ForeignKey('expression.id'))
    collection_id = db.Column(db.Integer, db.ForeignKey('expression_collection.id'))
    tissue_id = db.Column(db.Integer, db.ForeignKey('expression_tissue.id'))
    
    value = db.Column(db.Float)
    
    collection = db.relationship(ExpressionCollection)
    tissue = db.relationship(ExpressionTissue)

class ExpressionTypeEnum(enum.Enum):
    gene_symbol = 'gene_symbol'
    refseq = 'refseq'
    uniprot = 'uniprot'
    alias = 'alias'

class ExpressionAccession(db.Model):
    __tablename__ = 'expression_acc'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Enum(ExpressionTypeEnum))
    value = db.Column(db.String(45))
    probeset_id = db.Column(db.Integer, db.ForeignKey('expression.id'))
    
    def __init__(self, t, value, probeset_id):
        self.type = t
        self.value = value
        self.probeset_id = probeset_id

class GenechipEnum(enum.Enum):
    gnf1h = 'gnf1h'
    gnf1m = 'gnf1m'
    hg_u133a = 'HG-U133A'

class ExpressionProbeset(db.Model):
    __tablename__ = 'expression'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    probeset_id = db.Column(db.String(45), unique=True, index=True)
    genechip    = db.Column(db.Enum('gnf1h','gnf1m', 'HG-U133A', validate_strings=True), default='gnf1h')
    species_id  = db.Column(db.Integer, db.ForeignKey('species.id'))
    name        = db.Column(db.Text)
    
    species = db.relationship("Species")
    
    samples = db.relationship(ExpressionSample, lazy='subquery')
    accessions = db.relationship(ExpressionAccession, lazy='subquery')
    

def get_expression_probesets_for_protein(protein_accessions, species_id):
    probesets = \
        db.session \
            .query(ExpressionProbeset) \
            .join(ExpressionAccession) \
            .filter(
                and_(
                    ExpressionAccession.value.in_(protein_accessions),
                    ExpressionProbeset.species_id==species_id)).all()

    return probesets
    
    
