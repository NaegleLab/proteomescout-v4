import math
import re
from functools import lru_cache

import pandas as pd
from flask import current_app


ACCESSION_SPLIT_RE = re.compile(r'[;,|]')


def _config(key, default=None):
    try:
        return current_app.config.get(key, default)
    except RuntimeError:
        return default


@lru_cache(maxsize=1)
def load_protein_data():
    data_path = _config('PROTEIN_DATA_TSV_PATH', 'data/data.tsv')
    dataframe = pd.read_csv(data_path, sep='\t', dtype={'protein_id': str}).fillna('')
    return {
        str(row['protein_id']): row.to_dict()
        for _, row in dataframe.iterrows()
    }


@lru_cache(maxsize=1)
def load_citations():
    citations_path = _config('CITATIONS_TSV_PATH', 'data/citations.tsv')
    dataframe = pd.read_csv(citations_path, sep='\t', dtype={'Experiment ID': str}).fillna('')
    return {
        str(row['Experiment ID']): row.to_dict()
        for _, row in dataframe.iterrows()
    }


def clear_cache():
    load_protein_data.cache_clear()
    load_citations.cache_clear()


def get_protein_by_id(protein_id):
    return load_protein_data().get(str(protein_id))


def get_citation_by_id(experiment_id):
    return load_citations().get(str(experiment_id))


def parse_modifications(mod_string):
    if not mod_string or pd.isna(mod_string):
        return []

    modifications = []
    for mod_entry in str(mod_string).split(';'):
        mod_entry = mod_entry.strip()
        if not mod_entry:
            continue

        residue_position, separator, modification_type = mod_entry.partition('-')
        if not separator or len(residue_position) < 2:
            continue

        residue = residue_position[0]
        try:
            position = int(residue_position[1:])
        except ValueError:
            continue

        modifications.append(
            {
                'position': position,
                'residue': residue,
                'modification': modification_type,
            }
        )

    return modifications


def parse_evidence_ids(evidence_string):
    if not evidence_string or pd.isna(evidence_string):
        return []

    return [item.strip() for item in str(evidence_string).split(',') if item.strip()]


def parse_site_evidence_entries(evidence_string):
    """
    Parse evidence entries aligned to modification entries.

    Primary expected format is semicolon-separated (one evidence entry per PTM entry),
    e.g. "1886;1887;1803" where the nth evidence maps to the nth modification.
    Falls back to comma-separated input for legacy datasets.
    """
    if not evidence_string or pd.isna(evidence_string):
        return []

    text = str(evidence_string).strip()
    if not text:
        return []

    if ';' in text:
        return [item.strip() for item in text.split(';') if item.strip()]

    return [item.strip() for item in text.split(',') if item.strip()]


def parse_uniprot_domains(domain_string):
    if not domain_string or pd.isna(domain_string):
        return []

    domains = []
    for domain_entry in str(domain_string).split(';'):
        domain_entry = domain_entry.strip()
        if not domain_entry:
            continue

        parts = domain_entry.split(':')
        if len(parts) < 3:
            continue

        try:
            start = int(parts[-2])
            stop = int(parts[-1])
        except ValueError:
            continue

        domains.append(
            {
                'label': ':'.join(parts[:-2]),
                'start': start,
                'stop': stop,
                'source': 'uniprot',
            }
        )

    return domains


def parse_interpro_domains(domain_string):
    """
    Parse InterPro domains from TSV.
    Expected format example:
    Importin-a_IBB:IPR002652:1:93;DomainName:IPR000001:120:260
    """
    if not domain_string or pd.isna(domain_string):
        return []

    domains = []
    for domain_entry in str(domain_string).split(';'):
        domain_entry = domain_entry.strip()
        if not domain_entry:
            continue

        parts = domain_entry.split(':')
        if len(parts) < 4:
            continue

        try:
            start = int(parts[-2])
            stop = int(parts[-1])
        except ValueError:
            continue

        accession = parts[-3]
        label = ':'.join(parts[:-3]).strip() or accession

        domains.append(
            {
                'label': label,
                'interpro_id': accession,
                'start': start,
                'stop': stop,
                'source': 'interpro',
            }
        )

    return domains


def parse_structure(structure_string):
    if not structure_string or pd.isna(structure_string):
        return []

    structures = []
    for struct_entry in str(structure_string).split(';'):
        struct_entry = struct_entry.strip()
        if not struct_entry:
            continue

        parts = struct_entry.split(':')
        if len(parts) != 3:
            continue

        try:
            start = int(parts[1])
            stop = int(parts[2])
        except ValueError:
            continue

        structures.append(
            {
                'type': parts[0].lower(),
                'start': start,
                'stop': stop,
                'source': 'uniprot',
            }
        )

    return structures


def parse_accessions(accession_string):
    if not accession_string or pd.isna(accession_string):
        return []
    return [item.strip() for item in ACCESSION_SPLIT_RE.split(str(accession_string)) if item.strip()]


def get_species_options():
    species = {protein.get('species', '').strip() for protein in load_protein_data().values()}
    return sorted(item for item in species if item)


def _normalize(value):
    return str(value or '').strip().lower()


def _protein_matches(protein, query, peptide, species):
    if species and _normalize(protein.get('species')) != species:
        return None

    if peptide:
        sequence = _normalize(protein.get('sequence'))
        if peptide not in sequence:
            return None

    if not query:
        return (0, 0, protein.get('protein_name', ''), protein.get('protein_id', ''))

    searchable_fields = [
        protein.get('protein_id', ''),
        protein.get('acc_gene', ''),
        protein.get('protein_name', ''),
        protein.get('uniprot_id', ''),
        protein.get('accessions', ''),
    ]

    normalized_fields = [_normalize(field) for field in searchable_fields]
    exact_match = any(field == query for field in normalized_fields)
    starts_match = any(field.startswith(query) for field in normalized_fields)
    contains_match = any(query in field for field in normalized_fields)

    if not contains_match:
        return None

    return (
        0 if exact_match else 1,
        0 if starts_match else 1,
        protein.get('protein_name', ''),
        protein.get('protein_id', ''),
    )


def search_proteins(query='', peptide='', species='', limit=None):
    normalized_query = _normalize(query)
    normalized_peptide = _normalize(peptide)
    normalized_species = _normalize(species)
    max_results = limit or _config('MAX_SEARCH_RESULTS', 200)

    if not any([normalized_query, normalized_peptide, normalized_species]):
        return []

    matches = []
    for protein in load_protein_data().values():
        ranking = _protein_matches(protein, normalized_query, normalized_peptide, normalized_species)
        if ranking is not None:
            matches.append((ranking, protein))

    matches.sort(key=lambda item: item[0])
    return [protein for _, protein in matches[:max_results]]