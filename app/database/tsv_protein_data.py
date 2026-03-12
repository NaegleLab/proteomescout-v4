"""
TSV-based protein data loader with optimized caching for fast protein lookups.
Replaces database queries with flat text file format.
"""

import pandas as pd
from collections import defaultdict
from app.config import settings


# Global caches - loaded once on first access
_protein_data_cache = None
_citations_cache = None


def _load_protein_data():
    """Load protein data from TSV file with caching."""
    global _protein_data_cache
    if _protein_data_cache is None:
        tsv_path = getattr(settings, 'protein_data_tsv_path', 'data/proteomescout_data.tsv')
        df = pd.read_csv(tsv_path, sep='\t', dtype={'protein_id': str})
        # Index by protein_id for O(1) lookup
        _protein_data_cache = {row['protein_id']: row for _, row in df.iterrows()}
    return _protein_data_cache


def _load_citations():
    """Load citation/experiment data from TSV file with caching."""
    global _citations_cache
    if _citations_cache is None:
        citations_path = getattr(settings, 'citations_tsv_path', 'data/citations.tsv')
        df = pd.read_csv(citations_path, sep='\t', dtype={'Experiment ID': str})
        # Index by Experiment ID for O(1) lookup
        _citations_cache = {str(row['Experiment ID']): row for _, row in df.iterrows()}
    return _citations_cache


def get_protein_by_id(protein_id):
    """Get protein data from TSV by protein_id."""
    data = _load_protein_data()
    return data.get(str(protein_id))


def get_citation_by_id(experiment_id):
    """Get citation/experiment information by experiment ID."""
    data = _load_citations()
    return data.get(str(experiment_id))


def parse_modifications(mod_string):
    """
    Parse modifications field from TSV into structured format.
    Format: 'A2-N-acetylalanine; K6-Ubiquitination; T24-Phosphothreonine; ...'
    Returns list of dicts with position, residue, modification type
    """
    if not mod_string or pd.isna(mod_string):
        return []
    
    mods = []
    for mod_entry in str(mod_string).split(';'):
        mod_entry = mod_entry.strip()
        if not mod_entry:
            continue
        
        # Format: X123-ModificationType where X is residue, 123 is position
        # E.g., "K6-Ubiquitination" or "T24-Phosphothreonine"
        parts = mod_entry.split('-', 1)
        if len(parts) == 2:
            residue_pos = parts[0]
            mod_type = parts[1]
            
            # Extract residue and position
            residue = residue_pos[0]
            try:
                position = int(residue_pos[1:])
                mods.append({
                    'position': position,
                    'residue': residue,
                    'modification': mod_type
                })
            except ValueError:
                continue
    
    return mods


def parse_evidence_ids(evidence_string):
    """
    Parse evidence IDs from TSV field.
    Format: '1886,1575,1803' (comma-separated experiment IDs)
    Returns list of experiment IDs
    """
    if not evidence_string or pd.isna(evidence_string):
        return []
    
    exp_ids = []
    for exp_id in str(evidence_string).split(','):
        exp_id = exp_id.strip()
        if exp_id:
            exp_ids.append(exp_id)
    
    return exp_ids


def parse_uniprot_domains(domain_string):
    """
    Parse UniProt domains field from TSV.
    Format: 'IBB:2:58;NLS binding site (major):137:229;NLS binding site (minor):306:394'
    Returns list of dicts with label, start, stop
    """
    if not domain_string or pd.isna(domain_string):
        return []
    
    domains = []
    for domain_entry in str(domain_string).split(';'):
        domain_entry = domain_entry.strip()
        if not domain_entry:
            continue
        
        # Format: Label:start:stop
        parts = domain_entry.split(':')
        if len(parts) >= 3:
            try:
                label = ':'.join(parts[:-2])  # In case label has colons
                start = int(parts[-2])
                stop = int(parts[-1])
                domains.append({
                    'label': label,
                    'start': start,
                    'stop': stop,
                    'source': 'uniprot'
                })
            except ValueError:
                continue
    
    return domains


def parse_structure(structure_string):
    """
    Parse secondary structure field from TSV.
    Format: 'HELIX:73:80;STRAND:82:84;HELIX:85:100;...'
    Returns list of dicts with type, start, stop
    """
    if not structure_string or pd.isna(structure_string):
        return []
    
    structures = []
    for struct_entry in str(structure_string).split(';'):
        struct_entry = struct_entry.strip()
        if not struct_entry:
            continue
        
        # Format: TYPE:start:stop
        parts = struct_entry.split(':')
        if len(parts) == 3:
            try:
                struct_type = parts[0]
                start = int(parts[1])
                stop = int(parts[2])
                structures.append({
                    'type': struct_type.lower(),
                    'start': start,
                    'stop': stop,
                    'source': 'uniprot'
                })
            except ValueError:
                continue
    
    return structures


def parse_go_terms(go_string):
    """
    Parse GO terms field from TSV.
    Format: '  GO:0014046-P:dopamine secretion;  GO:0010467-P:gene expression; ...'
    Returns list of GO term strings
    """
    if not go_string or pd.isna(go_string):
        return []
    
    go_terms = []
    for term in str(go_string).split(';'):
        term = term.strip()
        if term and term.startswith('GO:'):
            go_terms.append(term)
    
    return go_terms


def get_site_regions(regions, pos):
    """Get region labels that contain the given position."""
    region_names = []
    for r in regions:
        if r['start'] <= pos <= r['stop']:
            region_names.append(r['label'])
    return region_names


def clear_cache():
    """Clear all cached data. Useful for testing or refreshing data."""
    global _protein_data_cache, _citations_cache
    _protein_data_cache = None
    _citations_cache = None
