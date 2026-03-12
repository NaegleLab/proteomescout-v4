# from sqlalchemy.schema import db.Column, db.ForeignKey
# from sqlalchemy.types import db.Integer, db.VARCHAR
# from app.database import Base, DBSession
# from sqlalchemy.orm import db.relationship
from app import db

class Taxonomy(db.Model):
    __tablename__='taxonomy'
    node_id = db.Column(db.Integer, primary_key=True)
    kingdom = db.Column(db.VARCHAR(1), index=True)
    name = db.Column(db.VARCHAR(100))
    strain = db.Column(db.VARCHAR(100))
    
    parent_id = db.Column(db.Integer, db.ForeignKey('taxonomy.node_id'))

    parent = db.relationship('Taxonomy', remote_side=[node_id])

    def __format_name(self):
        if self.strain:
            return "%s (%s)" % (self.name.strip(), self.strain.strip())
        return self.name.strip()

    formatted_name = property(__format_name)

    # def save(self):
    #     DBSession.add(self)
    #     DBSession.flush()
    
class Species(db.Model):
    __tablename__='species'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.VARCHAR(100), unique=True)
    taxon_id = db.Column(db.Integer, db.ForeignKey(Taxonomy.node_id))

    taxon = db.relationship(Taxonomy)

    def __init__(self, name):
        self.name = name

    # def save(self):
    #     DBSession.add(self)
    #     DBSession.flush()
        
def get_species_by_name(name):
    return db.session.query(Species).filter_by(name=name).first()

def get_all_species():
    return db.session.query(Species).all()

def get_taxonomy_by_id(txid):
    return db.session.query(Taxonomy).filter_by(node_id=txid).first()

def get_taxon_by_name(taxon, strain=None):
    return db.session.query(Taxonomy).filter_by(name=taxon, strain=strain).first()
