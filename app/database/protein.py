# from app.database import Base, DBSession
# from sqlalchemy.schema import db.Column, db.ForeignKey, UniqueConstraint, Table
# from sqlalchemy.types import db.Integer, TEXT, db.String, Enum, Text, db.Float, DateTime
# from sqlalchemy.orm import relationship
from sqlalchemy.sql import null, or_, and_
from app.config import strings, settings
from app.database import taxonomies
from app import db
from functools import reduce
import datetime
import enum

from app.database import Species,  ExpressionProbeset, Mutation

go_hierarchy_table = db.Table('GO_hierarchy',
    db.Column('parent_id', db.Integer, db.ForeignKey('GO.id')),
    db.Column('child_id', db.Integer, db.ForeignKey('GO.id')))
    
expression_association_table = db.Table('protein_expression',
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('protein_id', db.Integer, db.ForeignKey('protein.id')),
    db.Column('probeset_id', db.Integer, db.ForeignKey('expression.probeset_id')))



# class AspectEnum(enum.Enum):
#     F = 'F'
#     P = 'P'
#     C = 'C'


class GeneOntology(db.Model):
    __tablename__='GO'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aspect = db.Column(db.Enum('F', 'P', 'C', validate_strings=True))
    GO = db.Column(db.String(10))
    term = db.Column(db.Text)
    date = db.Column(db.DateTime)
    version = db.Column(db.String(10))
    db.UniqueConstraint('aspect', 'GO', name="uniqueEntry")
    
    children = db.relationship("GeneOntology", secondary=go_hierarchy_table, backref="parents",
                        primaryjoin=id == go_hierarchy_table.c.parent_id,
                        secondaryjoin=id == go_hierarchy_table.c.child_id)
    
    def __init__(self):
        self.date = datetime.datetime.now()
    
    def has_child(self, goId):
        goId = goId.lower()
        for c in self.children:
            if c.GO.lower() == goId:
                return True
        return False

    def full_name(self):
        return "%s: %s" % (self.GO, self.term)

    def save(self):
        db.session.add(self)
        db.session.commit()    

    def get_url(self):
        return settings.accession_urls['GO'] % (self.GO)


class GeneOntologyEntry(db.Model):
    __tablename__ = 'protein_GO'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    GO_id = db.Column(db.Integer, db.ForeignKey('GO.id'))
    date = db.Column(db.DateTime)
    
    GO_term = db.relationship("GeneOntology", lazy='joined')


class ProteinScansite(db.Model):
    __tablename__ = 'protein_scansite'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    source = db.Column(db.String(40), default='scansite')
    value = db.Column(db.String(20))
    score = db.Column(db.Float)
    percentile = db.Column(db.Float)
    site_pos = db.Column(db.Integer)
    
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    
    db.UniqueConstraint('source', 'value', 'peptide_id', name="UNIQUE_pepId_source_value")


class ProteinAccession(db.Model):
    __tablename__='protein_acc'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(30))
    value = db.Column(db.String(45))
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    primary_acc = db.Column(db.Boolean, default=0)
    date = db.Column(db.DateTime)
    out_of_date = db.Column(db.Boolean, default=0)

    
    def get_type(self):
        return strings.accession_type_strings[self.type]
    
    def get_url(self):
        if self.type in settings.accession_urls:
            return settings.accession_urls[self.type] % (self.value)
        return None
        
    def get_accession_name(self):
        return self.value
    

class ProteinDomain(db.Model):    
    __tablename__='protein_domain'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(45))
    start = db.Column(db.Integer)
    stop = db.Column(db.Integer)
    p_value = db.Column(db.Float)
    source = db.Column(db.Text, default='pfam')
    params = db.Column(db.String(45))
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))
    version = db.Column(db.Integer)

    # check to see why this one does not have flush
    def save(self):
        db.session.add(self)

    def has_site(self, site_pos):
        if self.start is None or self.stop is None or site_pos is None:
            # Handle the case where one of the values is None. 
            # You might want to return False or raise a more specific error.
            return False
        return self.start <= site_pos and site_pos <= self.stop

# class ProteinSourceEnum(enum.Enum):
#     predicted = 'predicted'
#     parsed = 'parsed'
#     uniprot = 'uniprot'
#     ncbi = 'ncbi'


class ProteinRegion(db.Model):
    __tablename__ = 'protein_regions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(20))
    label = db.Column(db.String(100))
    source = db.Column(db.Enum(
        'predicted', 'parsed', 'uniprot', 'ncbi', validate_strings=True))
    start = db.Column(db.Integer)
    stop = db.Column(db.Integer)
    protein_id = db.Column(db.Integer, db.ForeignKey('protein.id'))

    def __init__(self, type, label, source, start, stop, protein_id=None):
        self.type = type
        self.label = label
        self.source = source
        self.start = start
        self.stop = stop
        self.protein_id = protein_id

    def __eq__(self, o):
        c0 = self.type == o.type
        c1 = self.label == o.label
        c2 = self.start == o.start
        c3 = self.stop == o.stop
        return c0 and c1 and c2 and c3
    # needs to be hashable for annotation tasks to work properly
    def __hash__(self):
        return hash((self.type, self.label, self.start, self.stop))


    def has_site(self, site_pos):
        if self.start is not None and self.stop is not None:
            return self.start <= site_pos and site_pos <= self.stop
        else:
        # Handle the case where self.start or self.stop is None.
        # This might involve returning False, or implementing some other logic
        # that makes sense for your application.
            return False

class Protein(db.Model):
    __tablename__='protein'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sequence = db.Column(db.Text)
    acc_gene = db.Column(db.String(30))
    locus = db.Column(db.String(30))
    name = db.Column(db.String(100))
    date = db.Column(db.DateTime)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'))
    current = db.Column(db.Boolean, default=False)
    
    accessions = db.relationship("ProteinAccession", order_by=ProteinAccession.type, cascade="all,delete-orphan")
    domains = db.relationship("ProteinDomain")
    
    species = db.relationship("Species", lazy='joined')
    GO_terms = db.relationship("GeneOntologyEntry", lazy='joined')
    expression_probes = db.relationship("ExpressionProbeset", secondary=expression_association_table)
    mutations = db.relationship("Mutation", cascade="all,delete-orphan")
    regions = db.relationship("ProteinRegion")
    scansite = db.relationship("ProteinScansite")

    def __init__(self):
        self.date = datetime.datetime.now()
    
    def has_prediction(self, source, value, site_pos):
        for pred in self.scansite:
            if source == pred.source and \
                value == pred.value and \
                site_pos == pred.site_pos:
                return True
        return False
    
    def save_protein(self):
        db.session.add(self)
        db.session.commit()
   
    def save_no_flush(self):
        db.session.add(self)

    def get_gene_name(self):
        if self.acc_gene is not None and self.acc_gene != '':
            return self.acc_gene
        return self.locus

    def has_accession(self, acc):
        lower_acc = acc.lower()
        for dbacc in self.accessions:
            if dbacc.value.lower() == lower_acc:
                return True
        return False
        
    def add_taxonomy(self, taxon):
        if taxon not in self.taxonomy:
            self.taxonomy.append(taxon)
    
    def add_go_term(self, GO_term, date_added=datetime.datetime.now()):
        goe = GeneOntologyEntry()
        goe.GO_term = GO_term
        goe.date = date_added

        self.GO_terms.append(goe)
    
    def get_go_ids(self):
        return set([goe.GO_term.GO for goe in self.GO_terms])
     
    def has_go_term(self, GO_id):
        for goe in self.GO_terms:
            if goe.GO_term.GO.lower() == GO_id.lower():
                return True
        return False

    def has_mutation(self, m):
        compare = [m.equals(m2) for m2 in self.mutations]
        return reduce(bool.__or__, compare, False)

    def has_region(self, region):
        compare = [region == r2 for r2 in self.regions]
        return reduce(bool.__or__, compare, False)

    def get_kmer(self, site_pos, k=7):
        prot_seq = self.sequence
        site_pos = site_pos - 1
        low_bound = max([site_pos-k, 0])
        high_bound = min([len(prot_seq), site_pos+k+1])

        pep_aligned = prot_seq[low_bound:site_pos] + prot_seq[site_pos].lower() + prot_seq[site_pos+1:high_bound]
        
        if site_pos-k < 0:
            pep_aligned = (" " * (k - site_pos)) + pep_aligned
        if site_pos+k+1 > len(prot_seq):
            pep_aligned = pep_aligned + (" " * (site_pos + k+1 - len(prot_seq)))

        return pep_aligned

    def get_domain(self, site_pos):
        for d in self.domains:
            if d.start <= site_pos and site_pos < d.stop:
                return d


class NoSuchProtein(Exception):
    def __init__(self, prot):
        self.prot = prot
    
    def __str__(self):
        return "No such protein: %s" % (str(self.prot))


def get_go_annotation_by_id(goId):
    value = db.session.query(GeneOntology).filter_by(GO=goId).first()
    
    return value


def get_protein_by_id(pid):
    value = db.session.query(Protein).filter_by(id=pid).first()
    
    if value is None:
        raise NoSuchProtein(pid)
    
    return value


def get_proteins_by_gene(gene_name, species=None):
    if species is None:
        q = db.session.query(Protein).join(Protein.accessions).filter( or_( Protein.acc_gene==gene_name, ProteinAccession.value==gene_name ) )
    else:
        q = db.session.query(Protein).join(Protein.accessions).join(Protein.species).filter( or_( Protein.acc_gene==gene_name, ProteinAccession.value==gene_name ), taxonomies.Species.name == species)
    
    return q.all()


def search_proteins(search=None, species=None, sequence=None, page=None, exp_id=None, includeNames=False):
    q = db.session.query(Protein.id).join(Protein.accessions).join(Protein.species)

    clause = "1=1"
    if search:
        search = ( "%" + search + "%" ) if search else "%"
        if includeNames:
            clause = or_(Protein.acc_gene.like(search),
                    ProteinAccession.value.like(search),
                    Protein.name.like(search))
        else:
            clause = or_(Protein.acc_gene.like(search),
                    ProteinAccession.value.like(search))

    if sequence:
        clause = and_(clause, Protein.sequence.op('regexp')(sequence))

    if exp_id:
        from app.database import modifications
        sq = modifications.queryProteinsByExperiment(exp_id).subquery()
        q = q.join(sq, Protein.id == sq.c.protein_id)

    if species:
        clause = and_(clause, taxonomies.Species.name == species)

    q = q.filter(clause).distinct().order_by(Protein.acc_gene)

    if page is None:
        sq = q.subquery()
    else:
        limit, offset = page
        sq = q.limit(limit).offset(offset).subquery()

    fq = db.session.query(Protein).join(sq, Protein.id == sq.c.id)
    return q.count(), fq.all()


def get_proteins_by_experiment(exp_id, page=None):
    from app.database import modifications

    sq = modifications.query_proteins_by_experiment(exp_id).subquery()
    q = db.session.query(Protein.id).join(sq, Protein.id == sq.c.protein_id).order_by(Protein.acc_gene)
    result_size = q.count()

    if page:
        limit, offset = page
        q = q.limit(limit).offset(offset)
    sq = q.subquery()

    return result_size, db.session.query(Protein).join(sq, Protein.id == sq.c.id).all()


def get_protein_domain(prot_id, site_pos):
    return db.session.query(ProteinDomain).filter(and_(ProteinDomain.protein_id==prot_id, ProteinDomain.start <= site_pos, site_pos <= ProteinDomain.stop)).first()    


def get_protein_by_sequence(seq, species):
    return db.session.query(Protein).join(Protein.species).filter(Protein.sequence == seq, taxonomies.Species.name == species).first()


def get_proteins_by_accession(accession):
    return db.session.query(Protein).join(ProteinAccession).\
        filter(ProteinAccession.value == accession).all()


def get_all_proteins():
    return db.session.query(Protein).all()


def count_proteins():
    return db.session.query(Protein).count()
