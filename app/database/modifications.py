# from app.database import Base, DBSession
from app.database import protein as protein_mod
# from sqlalchemy.schema import db.Column, db.ForeignKey, Table, UniqueConstraint
# from sqlalchemy.types import db.Integer, db.String, CHAR, Float, Enum, DateTime
# from sqlalchemy.orm import db.relationship
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy import Enum
from app import db
from functools import reduce
import enum

PTM_taxon = db.Table('PTM_taxonomy',
                    db.Column('PTM_id', db.Integer, db.ForeignKey('PTM.id')),
                    db.Column('taxon_id', db.Integer, db.ForeignKey('taxonomy.node_id')))

class PTMkeyword(db.Model):
    __tablename__ = 'PTM_keywords'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    PTM_id = db.Column(db.Integer, db.ForeignKey('PTM.id'))
    keyword = db.Column(db.String(100))

#class PosiitionEnum(enum.Enum):
  #  anywhere = 'anywhere'
  #  c_terminal = 'c-terminal'
  #  n_terminal = 'n-terminal'
  #  core = 'core'
  #  none = None  # Add this line

class PTM(db.Model):
    __tablename__ = 'PTM'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    ## testing different ways to define the enum
    position = db.Column(Enum('anywhere', 'c-terminal', 'n-terminal', 'core', name='positionenum'), nullable=True)
    
    accession = db.Column(db.String(10))
    target = db.Column(db.String(0))
    mono_mass_diff = db.Column(db.Float)
    avg_mass_diff = db.Column(db.Float)

    parent_id = db.Column(db.Integer, db.ForeignKey('PTM.id'))
    parent = db.relationship("PTM", backref="children", remote_side='PTM.id')

    taxons = db.relationship("Taxonomy", secondary=PTM_taxon)
    keywords = db.relationship("PTMkeyword")

    def get_level(self):
        i = 0
        p = self
        while(p.parent is not None):
            p = p.parent
            i+=1
        return i

    def get_all_parents(self):
        if self.parent:
            return set([self.parent]) | self.parent.getAllParents()
        return set()

    def get_taxons(self):
        my_taxons = set(t.formatted_name.lower() for t in self.taxons)
        for c in self.children:
            my_taxons |= c.getTaxons()
        return my_taxons

    def has_taxon(self, search_taxons):
        search_taxons = set([t.lower() for t in search_taxons])
        my_taxons = set([t.formatted_name.lower() for t in self.taxons])
        return len(my_taxons & search_taxons) > 0

    def is_parent(self, node):
        A = reduce(bool.__or__, [ c.id == node.id for c in self.children ], False)
        if A:
            return True
        return reduce(bool.__or__, [ c.is_parent(node) for c in self.children ], False)

    def get_targets(self):
        return reduce(set.__or__, [c.get_targets() for c in self.children], set([self.target]) )

    def has_target(self, residue):
        targets = self.get_targets()
        return residue.upper() in targets
    
    def has_keyword(self, key):
        k = key.lower()
        return k in set([kw.keyword.lower() for kw in self.keywords])

    def create_keyword(self, key):
        if not self.has_keyword(key):
            ptmkw = PTMkeyword()
            ptmkw.keyword = key
            self.keywords.append(ptmkw)

    def __eq__(self, other): return self.id == other.id
    def __ne__(self, other): return self.id != other.id
    def __lt__(self, other): return self.is_parent(other)
    def __le__(self, other): return self.is_parent(other) or self.id == other.id
    def __gt__(self, other): return other.is_parent(self)
    def __ge__(self, other): return other.is_parent(self) or self.id == other.id

#class ScansitePrediction(Base):
#    __tablename__ = 'peptide_predictions'
#    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
#    source = db.Column(db.String(40), default='scansite')
#    value = db.Column(db.String(20))
#    score = db.Column(Float)
#    percentile = db.Column(Float)
#    peptide_id = db.Column(db.Integer, db.ForeignKey('peptide.id'))
#    
#    UniqueConstraint('source', 'value', 'peptide_id', name="UNIQUE_pepId_source_value")

class Peptide(db.Model):
    __tablename__ = 'peptide'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pep_aligned = db.Column(db.String(15))
    
    site_pos = db.Column(db.Integer)
    site_type = db.Column(db.CHAR(1))
    
    protein_domain_id = db.Column(db.Integer, db.ForeignKey('protein_domain.id'))
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    scansite_date = db.Column(db.DateTime)
    
    protein = db.relationship("Protein")
    protein_domain = db.relationship("ProteinDomain")
    
    predictions = db.relationship("ProteinScansite",
            primaryjoin="and_(Peptide.site_pos==ProteinScansite.site_pos, Peptide.protein_id==ProteinScansite.protein_id)",
            foreign_keys=[ protein_mod.ProteinScansite.__table__.c.site_pos, protein_mod.ProteinScansite.__table__.c.protein_id ],
            lazy='joined')
    
    def get_peptide(self):
        return self.pep_aligned
    
    def get_name(self):
        return self.site_type + str(self.site_pos)


class PeptideModification(db.Model):
    __tablename__ = 'MS_modifications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MS_id = db.Column(db.Integer, db.ForeignKey('MS.id'))
    peptide_id = db.Column(db.Integer, db.ForeignKey('peptide.id'))
    modification_id = db.Column(db.Integer, db.ForeignKey('PTM.id'))
    
    peptide = db.relationship("Peptide", lazy='joined')
    modification = db.relationship("PTM", lazy='joined')


class PeptideAmbiguity(db.Model):
    __tablename__ = 'MS_ambiguity'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    locus = db.Column(db.String(30))
    alt_accession = db.Column(db.String(20))
    ms_id = db.Column(db.Integer, db.ForeignKey('MS.id'))

    def __init__(self, locus, alt_accession, ms_id):
        self.locus = locus
        self.alt_accession = alt_accession
        self.ms_id = ms_id


class MeasuredPeptide(db.Model):
    __tablename__ = 'MS'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    query_accession = db.Column(db.String(45))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    peptide = db.Column(db.String(150))
    
    experiment = db.relationship("Experiment")
    protein = db.relationship("Protein")
    
    peptides = db.relationship("PeptideModification", backref="measured_peptide", lazy='joined')
    data = db.relationship("ExperimentData")
    ambiguities = db.relationship("PeptideAmbiguity", cascade='all,delete-orphan')

    def __repr__(self):
        return 'MS:%d' % (self.id)
    
    def is_ambiguous(self):
        return len(self.ambiguities) > 1

    def add_peptide_modification(self, peptide, ptm):
        pmod = PeptideModification()
        
        pmod.peptide = peptide
        pmod.modification = ptm
        self.peptides.append(pmod)

    def has_peptide_modification(self, peptide, ptm):
        for modpep in self.peptides:
            if modpep.peptide_id == peptide.id and modpep.modification_id == ptm.id:
                return True
        return False

    def __has_modification(self, sequence, ptm):
        for modpep in self.peptides:
            if modpep.peptide.pep_aligned == sequence and modpep.modification_id == ptm.id:
                return True
        return False

    def has_modifications(self, mod_list):
        passed = True
        for seq, mod in mod_list:
            passed &= self.__has_modification(seq, mod)
        return passed

    def get_data_element(self, run_name, tp, x):
        for d in self.data:
            if d.run == run_name and d.type == tp and d.label == x:
                return d


class NoSuchPeptide(Exception):
    def __init__(self, pep_site, pep_type, protein_id):
        self.site = pep_site
        self.t = pep_type
        self.protein_id = protein_id
        
    def __repr__(self):
        return "No such peptide modification at site %d, residue: %s, protein: %d" % (self.site, self.t, self.protein_id)


def get_measured_peptide(exp_id, pep_seq, protein_id, filter_mods=None):
    everything = MeasuredPeptide.query.filter_by(experiment_id=exp_id, peptide=pep_seq, protein_id=protein_id).all()

    if filter_mods:
        everything = [ e for e in everything if e.has_modifications(filter_mods) ]

    if len(everything) > 0:
        return everything[0]

def get_measured_peptide_by_id(ms_id):
    return MeasuredPeptide.query.filter_by(id=ms_id).first()

def get_measured_peptides_by_protein(pid, user=None):
    modifications = MeasuredPeptide.query.filter_by(protein_id=pid).all()
    return [ mod for mod in modifications if mod.experiment.check_permissions(user) and mod.experiment.ready() and mod.experiment.is_experiment() ]

def query_proteins_by_experiment(exp_id):
    return db.session.query(MeasuredPeptide.protein_id).filter(MeasuredPeptide.experiment_id==exp_id).distinct()

def get_measured_peptides_by_experiment(eid, user=None, pids=None, secure=True, check_ready=True):
    if(pids != None):
        modifications = db.session.query(MeasuredPeptide).filter(and_(MeasuredPeptide.experiment_id==eid, MeasuredPeptide.protein_id.in_(pids))).all()
    else:
        modifications = db.session.query(MeasuredPeptide).filter_by(experiment_id=eid).all()
    return [ mod for mod in modifications if (not secure or mod.experiment.check_permissions(user)) and (not check_ready or mod.experiment.ready()) ]

def count_measured_peptides_for_experiment(eid):
    return db.session.query(MeasuredPeptide).filter_by(experiment_id=eid).count()

def count_proteins_for_experiment(eid):
    return db.session.query(protein_mod.Protein.id).join(MeasuredPeptide).filter(MeasuredPeptide.experiment_id==eid).distinct().count()

def get_peptide_by_site(pep_site, pep_type, prot_id):
    mod = db.session.query(Peptide).filter_by(site_pos=pep_site, site_type=pep_type, protein_id=prot_id).first()
    
    if mod is None: 
        raise NoSuchPeptide(pep_site, pep_type, prot_id)
    
    return mod

def get_modification_by_id(ptm_id):
    return db.session.query(PTM).filter_by(id=ptm_id).first()

def get_modification_by_name(ptm_name):
    return db.session.query(PTM).filter_by(name=ptm_name).first()

def find_matching_ptm(mod_type, residue=None, taxons=None):
    if mod_type == "None":
        return [], False, False
    
    mods = db.session.query(PTM).outerjoin(PTMkeyword).filter(or_(PTM.accession==mod_type, PTM.name==mod_type, PTMkeyword.keyword==mod_type)).all()
    
    mods_exist = len(mods) > 0
    
    if residue:
        mods = [mod for mod in mods if mod.has_target(residue)]

    mods_match_residue = len(mods) > 0

    if taxons:
        mods = [mod for mod in mods if mod.has_taxon(taxons) or len(mod.taxons) == 0]
    
    return mods, mods_exist, mods_match_residue

def get_peptide_by_id(pep_id):
    return db.session.query(Peptide).filter(Peptide.id==pep_id).first()

def delete_experiment_data(exp_id):
    db.session.query(MeasuredPeptide).filter_by(experiment_id=exp_id).delete()
    db.session.flush()

def get_experiments_reporting_modified_peptide(modified_peptide, other_exps):
    from app.database import experiment

    q = db.session.query(PeptideModification).join(MeasuredPeptide).filter( and_( PeptideModification.modification_id==modified_peptide.modification_id, PeptideModification.peptide_id==modified_peptide.peptide_id ) )

    found_exp_ids = set([ pm.measured_peptide.experiment_id for pm in q.all() ])
    found_exps = []

    for exp in other_exps:
        if exp.id in found_exp_ids:
            found_exps.append(exp)

    return found_exps

def count_PTMs():
    return db.session.query(PTM).count()

def get_all_PTMs():
    return db.session.query(PTM).all()

def get_all_measured_peptides():
    return db.session.query(MeasuredPeptide).all()

