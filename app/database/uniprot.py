# from app.database import Base, DBSession
# from sqlalchemy.schema import db.Column
# from sqlalchemy.types import Integer, db.VARCHAR, Text
# from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import and_
from app import db

class SwissprotRecord(db.Model):
    __tablename__ = 'uniprot_swissprot'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    accession = db.Column(db.VARCHAR(20))
    locus = db.Column(db.VARCHAR(30))
    name = db.Column(db.VARCHAR(150))
    species = db.Column(db.VARCHAR(100))
    sequence = db.Column(db.Text)

    def __init__(self, name, accession, locus, species, sequence):
        self.name = name
        self.accession = accession
        self.locus = locus
        self.species = species
        self.sequence = sequence.upper()

def find_peptide(seq, species=None):
    filter_clause = SwissprotRecord.sequence.like('%' + seq + '%')

    if species:
        filter_clause = and_(filter_clause, SwissprotRecord.species==species)

    return db.session.query(SwissprotRecord).filter(filter_clause).all()
