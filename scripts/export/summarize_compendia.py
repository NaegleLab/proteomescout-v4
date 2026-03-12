import sys
import csv
import os
import zipfile
import time
import pickle
import io

# Allows for the importing of modules from the proteomescout-3 app within the script
SCRIPT_DIR = '/Users/saqibrizvi/Documents/NaegleLab/ProteomeScout-3/proteomescout-3'
sys.path.append(SCRIPT_DIR)

# local imports
from app.config import settings

# script helper function
def format_size( size ):
    postfix = ['B','KB','MB','GB','TB']

    i = 0
    while size > 1024:
        size /= float(1024)
        i+=1

    return "%.1f %s" % ( size, postfix[i] )

# script

files = ['proteomescout_everything.zip']

summary_struct = {}
for filename in files:
    if filename.find('.zip') == -1:
        continue
    fpath = os.path.join(settings.ptmscout_path, settings.export_file_path, filename)

    i = 0
    j = 0
    with open(fpath, 'r') as f:
        zf = zipfile.ZipFile(fpath, 'r')
        zf_content = zf.open('data.tsv', 'r')
        dr = csv.DictReader(io.StringIO(zf_content.read().decode('utf-8')), dialect='excel-tab')

        for row in dr:
            i+=1
            mods = row['modifications'].strip().split(';')
            if len(mods) == 1 and mods[0].strip() == '':
                mods.pop()
            j += len(mods)

    mod_time = time.ctime( os.path.getmtime(fpath) )
    size = format_size( os.path.getsize(fpath) )
    summary_struct[filename] = {'proteins':i,'modifications':j,'date':mod_time,'size':size}

with open(os.path.join(settings.ptmscout_path, settings.export_file_path, "listing.pyp"), 'wb') as f:
    pickle.dump(summary_struct, f)