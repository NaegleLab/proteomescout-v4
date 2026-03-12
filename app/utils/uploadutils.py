# from ptmscout.config import strings, settings
import csv
import os
from app.utils.webutils import call_catch
import re
import codecs
from app.utils import protein_utils
# to_utf8
from app.database import modifications
import time
from flask import current_app
from app.config import strings, settings

MAX_ROW_CHECK=100


class ErrorList(Exception):
    def __init__(self, errors, critical=True):
        self.errors = errors
        self.critical = critical
        
    def __repr__(self):
        st = ""
        for err in self.errors:
            st += "%s\n" % (err)
    
    def error_list(self):
        return [ e.message for e in self.errors ]
            
class ParseError(Exception):
    def __init__(self, row, col, msg):
        self.row = row
        self.col = col
        self.msg = msg
    
    def __repr__(self):
        if(self.col != None):
            return "Line %d, Column %d: %s" % (self.row, self.col, self.msg)
        elif(self.row != None):
            return "Line %d: %s" % (self.row, self.msg)
        else:
            return self.msg
    
    message = property(__repr__)    

class ColumnError(Exception):
    def __init__(self, message):
        self.message = message
        
    def __repr__(self):
        return repr(self.message)

def get_columns_of_type(session, tp):
    cols = []
    for col in session.columns:
        if tp == col.type:
            cols.append(col)
    return cols

# def save_data_file(file_field, prefix):
#     exp_file = prefix + str(time.time())
#     # file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
#     exp_filename = os.path.join(settings.ptmscout_path, settings.experiment_data_file_path, exp_file)
#     exp_filename_tmp = exp_filename + '.tmp'

#     input_file = file_field.file
#     output_file = open(exp_filename_tmp, 'wb')
    
#     input_file.seek(0)
#     while 1:
#         data = input_file.read(2<<16)
#         if not data:
#             break
#         output_file.write(data)
#     output_file.close()
    
#     os.system("mac2unix -q %s" % (exp_filename_tmp))
#     os.system("dos2unix -q %s" % (exp_filename_tmp))
#     to_utf8.convert_encoding_to_utf8(exp_filename_tmp, exp_filename)

#     os.remove(exp_filename_tmp)

#     return exp_file

def check_unique_column(session, ctype, required=False):
    cols = get_columns_of_type(session, ctype)

    if required and len(cols) == 0:
        raise ColumnError(strings.experiment_upload_error_no_column_assignment % (ctype,))
    if len(cols) > 1:
        raise ColumnError(strings.experiment_upload_error_limit_one_column_of_type % (ctype,))
    
    if len(cols) == 0:
        return None
    return cols[0]

def require_exactly_one(session, ctypes):
    found_type, col = None, None
    for ctype in ctypes:
        cols = get_columns_of_type(session, ctype)
        if len(cols) > 1:
            raise ColumnError(strings.experiment_upload_error_limit_one_column_of_type % (ctype,))
        elif len(cols) == 1 and col != None:
            raise ColumnError(strings.experiment_upload_error_must_have_no_more_column_among % (', '.join(ctypes),))
        elif len(cols) == 1:
            col = cols[0]
            found_type = ctype

    if col == None:
        raise ColumnError(strings.experiment_upload_error_must_have_one_column_among % (', '.join(ctypes),))

    return found_type, col

def find_root(row, parents):
    for p1 in parents:
        is_root = True
        for p2 in parents:
            is_root = is_root and p1 <= p2

        if is_root: return p1

    raise ParseError(row, None, "Unexpected error: parser encountered multiple possible parent modification type assignments without any root node")

def find_most_specific_parent(p, target):
    valid = [c for c in p.children if c.hasTarget(target) ]
    if len(valid) != 1:
        return p

    return find_most_specific_parent(valid[0], target)

def check_modification_type_matches_residues(row, modified_residues, modification, taxon_nodes):
    mod_list = [ m.strip() for m in modification.split(settings.mod_separator_character) ]

    if len(mod_list) > 1 and len(modified_residues) != len(mod_list):
        raise ParseError(row, None, strings.experiment_upload_warning_wrong_number_of_mods % (len(mod_list), len(modified_residues)))
    
    if len(mod_list) == 1 and len(modified_residues) > 1:
        mod_list = mod_list * len(modified_residues)

    mod_object = []
    mod_indices = []
    
    for i, (r, residue) in enumerate(modified_residues):
        residue = residue.upper()
        mod_type = mod_list[i]
        mods, found_type, match_residue = modifications.find_matching_ptm(mod_type, residue, taxon_nodes)
        
        if len(mods) == 0:
            msg = ""
            if not found_type: msg = strings.experiment_upload_warning_modifications_not_valid % (mod_type)
            elif not match_residue: msg = strings.experiment_upload_warning_modifications_do_not_match_amino_acids % (mod_type, residue)
            else:
                if taxon_nodes == None:
                    msg = strings.experiment_upload_warning_modifications_do_not_match_species % (mod_type, residue, "None")
                else:
                    msg = strings.experiment_upload_warning_modifications_do_not_match_species % (mod_type, residue, taxon_nodes[-1])

            raise ParseError(row, None, msg)
        
        matches = [ mod for mod in mods if mod.target == residue ]
        parents = [ mod for mod in mods if mod.target == None ]

        if len(matches) == 0:
            if taxon_nodes == None:
                raise ParseError(row, None, strings.experiment_upload_warning_modifications_do_not_match_species % (mod_type, residue, "None"))
            else:
                raise ParseError(row, None, strings.experiment_upload_warning_modifications_do_not_match_species % (mod_type, residue, taxon_nodes[-1]))

        selected_mod = matches[0]
        if len(matches) > 1:
            if len(parents) == 0:
                raise ParseError(row, None, strings.experiment_upload_warning_ambiguous_modification_type_for_amino_acid % (mod_type, residue))
            else:
                selected_mod = find_most_specific_parent(find_root(row, parents), residue)

        mod_indices.append(r)
        mod_object.append(selected_mod)
        
    return mod_indices, mod_object

def check_modification_type_matches_sites(row, sites, modification, taxon_nodes=None):
    modified_residues = [ (int(s[1:]), s[0]) for s in sites.split(';') ]
    return check_modification_type_matches_residues(row, modified_residues, modification, taxon_nodes)

def check_modification_type_matches_peptide(row, peptide, modification, taxon_nodes=None):
    modified_alphabet = set("abcdefghijklmnopqrstuvwxyz")
    modified_residues = [ (i, r) for i, r in enumerate(peptide) if r in modified_alphabet ]

    if len(modified_residues) == 0:
        raise ParseError(row, None, strings.experiment_upload_warning_no_mods_found % (peptide))

    return check_modification_type_matches_residues(row, modified_residues, modification, taxon_nodes)
   
def check_data_row(r, row, acc_col, pep_col, site_col, mod_col, run_col, data_cols, stddev_cols, keys, mod_col_required=True):
    errors = []
    
    try:
        accession = row[acc_col.column_number].strip()
        
        modification = None
        if mod_col_required:
            modification = row[mod_col.column_number].strip()

        acc_type = protein_utils.get_accession_type(accession)
        if acc_type not in protein_utils.get_valid_accession_types():
            errors.append(ParseError(r, acc_col.column_number+1, strings.experiment_upload_warning_acc_column_contains_bad_accessions))

        site_index = None

        if pep_col != None:
            peptide = row[pep_col.column_number].strip()
                    
            if not protein_utils.check_peptide_alphabet(peptide):
                errors.append(ParseError(r, pep_col.column_number+1, strings.experiment_upload_warning_peptide_column_contains_bad_peptide_strings))
            
            if mod_col_required:
                call_catch(ParseError, errors, check_modification_type_matches_peptide, r, peptide, modification)

            site_index = peptide
        else:
            sites = row[site_col.column_number].strip()
            try:
                normed_sites = protein_utils.normalize_site_list(sites)
                if mod_col_required:
                    call_catch(ParseError, errors, check_modification_type_matches_sites, r, normed_sites, modification)
                sites = normed_sites
            except:
                errors.append( ParseError(r, None, "Invalid formatting for sites: %s" % (sites) ) )

            site_index = sites
        
        run = None
        if run_col != None:
            run = row[run_col.column_number].strip()
            k = (accession, site_index, modification, run)
            if k in keys:
                errors.append(ParseError(r, None, strings.experiment_upload_warning_full_dupe))
            keys.add(k)
        else:
            k = (accession, site_index, modification)
            if k in keys:
                errors.append(ParseError(r, None, strings.experiment_upload_warning_no_run_column))
            keys.add(k)
        
        has_data = False
        for c in data_cols + stddev_cols:
            try:
                float(row[c.column_number].strip())
                has_data = True
            except ValueError:
                row[c.column_number] = None
        
        if len(data_cols) > 0 and not has_data:
            errors.append(ParseError(r, None, strings.experiment_upload_warning_data_missing))
    except IndexError:
        errors.append(ParseError(r, None, strings.experiment_upload_warning_missing_column))

    return errors
    
def check_data_rows(session, acc_col, pep_col, site_col, mod_col, run_col, data_cols, stddev_cols, mod_col_required=True, N=MAX_ROW_CHECK):
    errors = []
    _, data = load_header_and_data_rows(session.data_file, N)
    
    keys = set([])
    
    r = 0
    for row in data:
        r+=1
        errors.extend( check_data_row(r, row, acc_col, pep_col, site_col, mod_col, run_col, data_cols, stddev_cols, keys, mod_col_required) )
    
    return errors


def check_data_column_assignments(session, mod_col_required=True):
    errors = []
    
    acc_col     = call_catch(ColumnError, errors, check_unique_column, session, 'accession', required=True)
    pep_col     = None
    site_col    = None
    type_col    = call_catch(ColumnError, errors, require_exactly_one, session, ['peptide', 'sites'])

    if type_col and type_col[0] == 'peptide':
        pep_col = type_col[1]
    if type_col and type_col[0] == 'sites':
        site_col = type_col[1]

    mod_col     = call_catch(ColumnError, errors, check_unique_column, session, 'modification', required=mod_col_required)
    run_col     = call_catch(ColumnError, errors, check_unique_column, session, 'run')
    
    critical = True
    
    if len(errors) == 0:
        critical = False
        data_cols   = get_columns_of_type(session, 'data')
        stddev_cols = get_columns_of_type(session, 'stddev')
        errors.extend( check_data_rows(session, acc_col, pep_col, site_col, mod_col, run_col, data_cols, stddev_cols, mod_col_required) )
        
    if len(errors) > 0:
        raise ErrorList( errors, critical)
    


def get_column_from_header(header):
    for h in header:
        hl = h.lower()
        col = {'type':'','label':''}
        
        m = re.match('^(data|stddev):(.+):(.+)$', h, re.IGNORECASE)
        if m:
            tp = m.group(1).lower()
            unit = m.group(2).lower()
            col['type'] = 'stddev' if tp == 'stddev' or unit.find('stddev') == 0 else 'data'
            col['label'] = m.group(3)
        elif hl.find('data') == 0:
            col['type'] = 'data'
        elif hl.find('stddev') == 0:
            col['type'] = 'stddev'
        elif hl.find('acc') == 0:
            col['type'] = 'accession'
        elif hl.find('mod') == 0:
            col['type'] = 'modification'
        elif hl.find('pep') == 0:
            col['type'] = 'peptide'
        elif hl.find('site') == 0:
            col['type'] = 'sites'
        elif hl == 'run':
            col['type'] = 'run'
        else:
            col['type'] = 'none'
        
        
        yield col
    
def find_units(header):
    for h in header:
        m = re.match('^data:(.+):.+$',h)
        if m:
            return m.group(1)
    return ""

def assign_columns_by_name(header):
    columns = {}

    c = 0
    for col in get_column_from_header(header):
        columns[c] = col
        c += 1
    
    units = find_units(header)
    
    return {'columns':columns, 'units':units}

def assign_columns_from_session(session):
    columns = {}
    
    for col in session.columns:
        columns[col.column_number] = {'type':col.type, 'label':col.label}

    return {'columns':columns, 'units':session.units}

def assign_columns_from_session_history(session, header):
    history_session = session.getAncestor()
    result = assign_columns_from_session(history_session)
    
    keys = result['columns'].keys()
    for c in keys:
        if not c < len(header):
            del result['columns'][c]
    
    return result

def assign_column_defaults(session):
    header, _ = load_header_and_data_rows(session.data_file)
    columns = assign_columns_by_name(header)

    if session.columns != []:
        result = assign_columns_from_session(session)
        columns['columns'].update( result['columns'] )
        if result['units'] != '':
            columns['units'] = result['units']

    elif session.parent_experiment != None:
        result = assign_columns_from_session_history(session, header)
        columns['columns'].update( result['columns'] )
        if result['units'] != '':
            columns['units'] = result['units']

    return columns


def load_header_and_data_rows(data_file, N=-1, truncate=0):
    ifile = csv.reader(codecs.open(os.path.join(current_app.config['UPLOAD_FOLDER'], data_file), 'rb', encoding='utf-8'), delimiter='\t')
    i = 0
    
    header = next(ifile)
    
    width = len(header)
    while(width > 0 and header[width-1].strip() == ''):
        width-=1
    
    start_index = 0

    if header[0].strip().lower() == strings.experiment_upload_error_reasons_column_title.strip().lower():
        start_index = 1

    header = header[start_index:width]
    
    rows = []
    for row in ifile:
        if i >= N:
            break
        row = row[start_index:width]
        if(truncate > 0):
            row = [ (col[0:truncate] + "..." if len(col) > truncate else col) for col in row ]
        rows.append(row)
        i+=1

    return header, rows
