# from app.database import Base, DBSession
# from sqlalchemy.schema import db.Column, db.ForeignKey
# from sqlalchemy.types import db.Integer, db.String, DateTime
# from sqlalchemy.orm import db.relationship
# from sqlalchemy.dialects.mysql import db.Integer as db.Integer 
from app import db
import datetime
import re

class Mutation(db.Model):
    __tablename__= 'protein_mutations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    acc_id = db.Column(db.String(30))
    mutationType = db.Column(db.String(25))
    location = db.Column(db.Integer)
    original = db.Column(db.String(3))
    mutant = db.Column(db.String(3))
    date = db.Column(db.DateTime)
    annotation = db.Column(db.String(256))
    clinical = db.Column(db.String(100))

    protein = db.relationship("Protein")

    def __init__(self, mtype, location, original, mutant, acc_ID, annotation, PID):
        self.protein_id = PID
        self.acc_id = acc_ID
        self.mutationType = mtype
        self.location = location
        self.original = original
        self.mutant = mutant
        self.date = datetime.datetime.now()
        self.annotation = annotation
        self.clinical = ""

    def __repr__(self):
        if self.clinical != "":
            return "%s%d%s:%s" % (self.original, self.location, self.mutant, self.clinical)
        else:
            return "%s%d%s" % (self.original, self.location, self.mutant)

    def equals(self, other):
        type_eq = self.mutationType == other.mutationType
        loc_eq = self.location == other.location
        mut_eq = self.mutant == other.mutant

        return type_eq and loc_eq and mut_eq

    def consistent(self, prot_seq):
        start = self.location-1
        return prot_seq[start:start+len(self.original)] == self.original

    def get_dbsnp_id(self):
        m = re.findall('rs[0-9]+', self.annotation)
        if len(m) == 0:
            return None
        return m[0]

    def get_reference_ids(self):
        dbSNP = re.findall('rs[0-9]+', self.annotation)
        uniVar = re.findall('VAR_[0-9]+', self.annotation)
        return uniVar + dbSNP
