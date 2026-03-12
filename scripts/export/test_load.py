import sys
import pickle
import os

# Allows for the importing of modules from the proteomescout-3 app within the script
SCRIPT_DIR = '/Users/saqibrizvi/Documents/NaegleLab/ProteomeScout-3/proteomescout-3'
sys.path.append(SCRIPT_DIR)

with open(os.path.join("data", "listing.pyp"), "rb") as listing_file:
    listing = pickle.load(listing_file)

files = []