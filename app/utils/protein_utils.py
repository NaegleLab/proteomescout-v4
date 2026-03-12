import re
import math

def create_sequence_profile(measurements):
    peptides = [p.peptide for m in measurements for p in m.peptides]

    frequencies = [0]*15
    N = float(len(peptides))
    
    for i in range(0, 15):
        frequencies[i] = {}
       
    for pep in peptides:
        sequence = pep.pep_aligned.upper()
        
        for i, s in enumerate(sequence):
            if s == ' ':
                s = '-'
            val = frequencies[i].get(s, 0)
            frequencies[i][s] = val+1
        
    seqlogo = {'total':len(peptides), 'frequencies':[]}
    
    if len(peptides) == 0:
        return seqlogo
    
    en = 19 / (2 * math.log(2) * len(peptides)) 
    
    for i in range(0, 15):
        Ri = math.log(20, 2)
        
        for s in frequencies[i]:
            f = frequencies[i][s] / N
            Ri += f * math.log(f, 2)
        
        Ri -= en
        
        sorted_freqs = sorted([ (k, v) for (k,v) in frequencies[i].items() ], key=lambda item: -item[1])
        final = []
        
        d=0
        for k,v in sorted_freqs:
            final.append((k, v, d))
            d += v
                
        seqlogo['frequencies'].append({'R':Ri, 'f':final})
    
    return seqlogo

def get_accession_type(acc):
    acc_type = None
    
    if(re.search('^gi', acc) is not None):
        acc_type = 'gi'
    elif(re.search('^[NXZ]P_\d+', acc) is not None):
        acc_type = 'refseq'
    elif(re.search('^[O|P|Q]\d...\d([\.\-]\d+)?$', acc) is not None):
        acc_type = 'swissprot'
    elif(re.search('^[A-N|R-Z]\d[A-Z]..\d([\.\-]\d+)?$', acc) is not None):
        acc_type = 'swissprot'
    elif(re.search('^[A-Z]{3}\d{5}$', acc) is not None):
        acc_type = 'genbank'
    elif(re.search('^IPI\d+(\.\d+)?$', acc) is not None):
        acc_type = 'ipi'
    elif re.search('^ENS', acc) is not None:
        acc_type = 'ensembl'

#    elif(re.search('^[A-Z]{4}_[A-Z]+$', acc) != None):
#        acc_type = 'swissprot_'

    return acc_type

def normalize_site_list(sites):
    amino_acids = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    sites = [ s.strip() for s in sites.split(";") ]
    sites = [ (s[0], int(s[1:])) for s in sites ]
    for residue, _ in sites:
        if residue not in amino_acids:
            raise Exception()

    sorted(sites, key=lambda item: item[1])

    return ';'.join([ "%s%d" % (r, p) for (r, p) in sites ])

def check_peptide_alphabet(pep):
    amino_acids = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    for residue in pep.upper():
        if residue not in amino_acids:
            return False
    
    return True

def get_valid_accession_types():
    return set(['gi','refseq','swissprot','genbank','uniprot'])



