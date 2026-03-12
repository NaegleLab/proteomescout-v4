import sys
import os
from flask_sqlalchemy import SQLAlchemy
import csv

# Get the absolute path to the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the root of proteome-scout-3
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

# Add proteome-scout-3 and scripts/schema to sys.path
sys.path.append(PROJECT_ROOT)
sys.path.append(CURRENT_DIR)


from scripts.app_setup import create_app
from scripts.progressbar import ProgressBar
from app.utils.export_proteins import *
from app.database import protein, modifications, experiment
from app.utils.downloadutils import experiment_metadata_to_tsv, zip_package

from FlaskSchemaReporter import FlaskSchemaReporter
import pathlib

# directory variable to be imported
OUTPUT_DIR = "scripts/output"

# database instantiated for the script
db = SQLAlchemy()

# application created within which the script can be run
app = create_app()
# database linked to the app
db.init_app(app)

def main(output_file):
    with app.app_context():
        reporter = FlaskSchemaReporter(app=app, db=db)
        reporter.extract_all_schema_info()
        reporter.print_summary()  # Console output
        #reporter.generate_csv_reports("my_schema")  # CSV files
        reporter.generate_json_report(output_file)  # JSON file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_schema.py <output_file>")
        sys.exit(1)
    output_file = sys.argv[1]
    main(output_file)