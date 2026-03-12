

import sys
import os
from flask_sqlalchemy import SQLAlchemy
import csv
from proteomescout_worker.helpers import uniprot_mapping
import pandas as pd
import numpy as np
import datetime
import logging
from app import celery
from celery import chain


# Allows for the importing of modules from the proteomescout-3 app within the script
SCRIPT_DIR = '/Users/saqibrizvi/Documents/NaegleLab/ProteomeScout-3/proteomescout-3'
sys.path.append(SCRIPT_DIR)

from scripts.app_setup import create_app
from scripts.progressbar import ProgressBar
from app.utils.export_proteins import *
from app.database import protein, modifications, experiment



# directory variable to be imported
OUTPUT_DIR = "scripts/output"

# database instantiated for the script
db = SQLAlchemy()

# application created within which the script can be run
app = create_app()

# database linked to the app
db.init_app(app)

# fetching records from the database
#@celery.task
def fetch_accessions():
    with app.app_context():
        protein_acc = protein.ProteinAccession.query.all()

        # Create a list of dictionaries, where each dictionary represents a row of data
        data = []
        for p in protein_acc:
            data.append({
                'id': p.id,
                'type': p.type,
                'value': p.value, 
                'protein_id': p.protein_id
            })

        # Convert the list of dictionaries into a DataFrame
        df = pd.DataFrame(data)

        # Get the accessions from the 'value' column
        accessions = df[df['type'] == 'swissprot']['value'].tolist()

        # Submit a single job with all the accessions
        job_id = uniprot_mapping.submit_id_mapping(from_db="UniProtKB_AC-ID", to_db="UniProtKB-Swiss-Prot", ids=accessions)

        if uniprot_mapping.check_id_mapping_results_ready(job_id):
            link = uniprot_mapping.get_id_mapping_results_link(job_id)
            results = uniprot_mapping.get_id_mapping_results_search(link)

            # Create a dictionary to map accessions to results
            accession_to_result = {result['from']: result for result in results['results']}

            # Define a function that takes an accession and returns the requested value, primary accession, and sequence value
            def get_results(accession):
                if accession in accession_to_result:
                    result = accession_to_result[accession]
                    requested = result['from']
                    primary = result['to']['primaryAccession']
                    return pd.Series([requested, primary])
                else:
                    return pd.Series([np.nan, np.nan])

            # Apply the function to the 'value' column and create new columns in the DataFrame
            df[['requested', 'primary']] = df['value'].apply(get_results)

        return df
# processing to identify primary and new accessions
#@celery.task
def process_dataframe(df):
    df = df.dropna() # dropping NA values ie anything that is not swissprot
    df['primary_acc'] = (df['value'] == df['primary']).astype(int)
    mismatches = df[df['value'] != df['primary']]
    new_entries_primary = mismatches[~mismatches['primary'].isin(df['value'])]
    new_entries = new_entries_primary.copy()
    new_entries['value'] = new_entries['primary']
    new_entries['primary_acc'] = 1
    df = pd.concat([df, new_entries])
    df['date'] = datetime.datetime.now().date()
    df = df[['id', 'type', 'value', 'protein_id', 'primary_acc', 'date']]
    return df

# commiting the records to the database
#@celery.task
def commit_records(df):
    with app.app_context():
        try:
            for index, row in df.iterrows():
                try:
                    existing_record = db.session.query(protein.ProteinAccession).filter_by(id=row.id, value=row.value, type=row.type, primary_acc=row.primary_acc).first()
                    if existing_record is None:
                        record = protein.ProteinAccession(
                            id=row['id'],
                            type=row['type'],
                            value=row['value'],
                            protein_id=row['protein_id'],
                            primary_acc=row['primary_acc'],
                            date=row['date']
                        )
                        db.session.merge(record)
                    if index % 200 == 0:
                        db.session.commit()
                except Exception as e:
                    db.session.rollback()
            db.session.commit()
        except Exception as e:
            logging.error(f"An error occurred: {e}")

# Chain tasks
chain = fetch_accessions.s() | process_dataframe.s() | commit_records.s()
chain()


# defining function to connect to database for protein accessions 
''''
with app.app_context():
    protein_acc = protein.ProteinAccession.query.limit(2000).all()

    # Create a list of dictionaries, where each dictionary represents a row of data
    data = []
    for p in protein_acc:
        data.append({
            'id': p.id,
            'type': p.type,
            'value': p.value, 
            'protein_id': p.protein_id
        })

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(data)

    # Get the accessions from the 'value' column
    accessions = df[df['type'] == 'swissprot']['value'].tolist()

    # Submit a single job with all the accessions
    job_id = uniprot_mapping.submit_id_mapping(from_db="UniProtKB_AC-ID", to_db="UniProtKB-Swiss-Prot", ids=accessions)

    if uniprot_mapping.check_id_mapping_results_ready(job_id):
        link = uniprot_mapping.get_id_mapping_results_link(job_id)
        results = uniprot_mapping.get_id_mapping_results_search(link)

        # Create a dictionary to map accessions to results
        accession_to_result = {result['from']: result for result in results['results']}

        # Define a function that takes an accession and returns the requested value, primary accession, and sequence value
        def get_results(accession):
            if accession in accession_to_result:
                result = accession_to_result[accession]
                requested = result['from']
                primary = result['to']['primaryAccession']
                #sequence = result['to']['sequence']['value']
                return pd.Series([requested, primary]) #, sequence])
            else:
                return pd.Series([np.nan, np.nan])

        # Apply the function to the 'value' column and create new columns in the DataFrame
        #df[['requested', 'primary', 'sequence']] = df['value'].apply(get_results)
        df[['requested', 'primary']] = df['value'].apply(get_results)

    # Print the DataFrame
    print(df)


# processing the resulting accessions to find annotate primary and new accessions 
def process_dataframe_new(df):
    df = df.dropna() # dropping NA values ie anything that is not swissprot
    print(len(df))
    # type: ignore 
    # Create a new column 'primary_acc' and set its value to 1 where 'value' equals 'primary', and 0 otherwise
    df['primary_acc'] = (df['value'] == df['primary']).astype(int)

    # Find rows where 'value' does not equal 'primary'
    mismatches = df[df['value'] != df['primary']]

    # Find 'primary' values in mismatches that are not in 'value' column of df
    new_entries_primary = mismatches[~mismatches['primary'].isin(df['value'])]
    print(len(new_entries_primary))
    # Create new entries with 'primary' as 'value', and same 'id', 'type', 'protein_id' as the reference
    new_entries = new_entries_primary.copy()
    new_entries['value'] = new_entries['primary']
    new_entries['primary_acc'] = 1

    # Append these new entries to the DataFrame
    # Add a new column with the current date

    df = pd.concat([df, new_entries])
    df['date'] = datetime.datetime.now().date()
    print(len(df))
    # Retain only the 'id', 'type', 'value', 'protein_id', 'primary_acc', 'date' columns
    df = df[['id', 'type', 'value', 'protein_id', 'primary_acc', 'date']]
    print(len(df))

    return df



# Iterate over DataFrame rows
with app.app_context():
    try:
        for index, row in df.iterrows():
            try:
                # Check if the record already exists
                existing_record = db.session.query(protein.ProteinAccession).filter_by(id=row.id, value=row.value, type=row.type, primary_acc=row.primary_acc).first()
                if existing_record is None:
                    # Create a SQLAlchemy ORM object
                    record = protein.ProteinAccession(
                        id=row['id'],
                        type=row['type'],
                        value=row['value'],
                        protein_id=row['protein_id'],
                        primary_acc=row['primary_acc'],
                        date=row['date']
                    )
                    # Merge the record (update or insert)
                    db.session.merge(record)

                # If index is multiple of 200, commit the session and log progress
                if index % 200 == 0:
                    db.session.commit()
                    logging.info(f"Processed {index} records")
            except Exception as e:
                # If an error occurs with a single record, log the error and continue with the next record
                db.session.rollback()
                #logging.error(f"An error occurred at index {index}: {e}")

        # Commit any remaining records
        db.session.commit()
        #logging.info("Processing complete")
    except Exception as e:
        # If an error occurs outside the loop, log the error
        logging.error(f"An error occurred: {e}") 
'''