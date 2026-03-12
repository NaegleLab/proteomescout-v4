from app.config import settings

accession_type_strings = {'ipi':"International Protein Index", 
                     'gene_synonym':"Gene Synonym",
                     'refseq': "RefSeq",
                     'swissprot': "UniProt",
                     'genbank': "GenBank",
                     'gi': "Gene Index",
                     'uniprot': "UniProt",
                     'ddbj': "DDBJ",
                     'embl': "EMBL",
                     'pdb': "PDB"
                     }

kinase_loop_name = 'Kinase Activation Loop'
possible_kinase_name = 'Possible Kinase Activation Loop'

success_header = "Success"

change_password_page_title = "Change Password"
change_password_success_message = "Password successfully changed."

about_page_title = "About ProteomeScout"

account_activation_page_title = "Account Activation"
account_activation_success_header = "Account Activation Succeeded"
account_activation_failed_header = "Account Activation Failure"
account_activation_success_message = "Your account is now active. Please <a href=\"%s\">login</a>"
account_activation_failed_message = "The specified account is not valid, please try <a href=\"%s\">registering</a>"

account_management_page_title = "Account Management"

compendia_download_page_title = 'ProteomeScout Flat File Data'
compendia_download_page_desc = ''

create_reviewer_account_page_title = "Create Reviewer Account"

create_reviewer_account_confirm_message = "Are you sure you wish to create an anonymous reviewer account for this experiment? Experiment data will be accessible only to authorized users and holders of a valid review token."
create_reviewer_account_confirm_header = "Create Reviewer Account?"
create_reviewer_account_created_header = "Reviewer account created"
create_reviewer_account_created_message = """
A reviewer account was created with the following credentials:<br />
<br />
username: %s<br />
password: %s<br />
<br />
Anonymous reviewers may login to view your data by visiting the following address in their browser: %s<br />
"""

dataset_upload_page_title = "Upload Sites of Interest for Exploration"
dataset_upload_configure_page_title = "Configure Sites of Interest Fields"

experiment_ambiguity_page_title = "Ambiguous Peptide Assignment Tool"
experiment_ambiguity_error_no_change = "No peptide assignments were changed from the current assignments"

experiment_compare_page_title = "Compare Datasets: %s"

experiment_subset_page_title = "Dataset Explorer: %s"

experiment_errors_page_title = "Experiment Data Upload Errors: %s"

experiments_page_title = "Home - Experiments"
experiment_page_title = "Experiment: %s"
experiment_summary_page_title = "Experiment Summary: %s"
experiment_browse_page_title = "Browsing Experiment: %s"
experiment_pfam_page_title = "Experiment Protein Families: %s"
experiments_scansite_page_title = "Experiment Scansite Predictions: %s"
experiment_GO_page_title = "Experiment GO Terms: %s"

experiment_upload_finished_subject = "ProteomeScout experiment upload completed" 
experiment_upload_finished_message = \
"""ProteomeScout has finished processing the upload of your experiment: '%s'

Upload Results:

Peptides: %d
Proteins: %d
Errors: %d

You may view the error log for this upload <a href="%s">here</a>.

Thanks for using ProteomeScout,
-The ProteomeScout Team"""
experiment_upload_configure_page_title = "Configure Experiment Data"
experiment_upload_configure_instructions = """
<span>Please verify and assign designations for the column types present in your experiment.</span><br />
<span>Some column types may have been automatically inferred from your headers.</span><br />
<span>You are required to specify the following columns:</span><br />
<ul>
    <li>Accession</li>
    <li>Modification</li>
    <li>Peptide or Site</li>
</ul>
<span>You may optionally have columns from the following categories:</span><br />
<ul>
    <li>Run</li>
    <li>Data</li>
    <li>Stddev</li>
</ul>

"""

annotation_upload_configure_instructions = """
<span>Please verify and assign designations for the column types present in your annotation file.</span><br />
<span>Some column types may have been automatically inferred from your headers.</span><br />
<span>You are required to specify the following columns:</span><br />
<ul>
    <li>MS id</li>
</ul>
<span>You may optionally have columns from the following categories:</span><br />
<ul>
    <li>Numeric</li>
    <li>Nominative</li>
    <li>Cluster</li>
</ul>
"""

dataset_upload_configure_instructions = """
<span>Please verify and assign designations for the column types present in your dataset.</span><br />
<span>Some column types may have been automatically inferred from your headers.</span><br />
<span>You are required to specify the following columns:</span><br />
<ul>
    <li>Accession</li>
    <li>Peptide or Sites</li>
</ul>
<span>You may optionally have columns from the following categories:</span><br />
<ul>
    <li>Run</li>
    <li>Data</li>
    <li>Stddev</li>
</ul>
"""

cancel_upload_successful_page_title = "Experiment Upload"
cancel_upload_successful_header = "Experiment Upload Cancelled"
cancel_upload_successful_message = "Experiment upload session cancelled"

cancel_upload_already_started_message = "This experiment upload session has already been completed, you cannot cancel it."
cancel_upload_already_started_header = "Experiment Upload Could Not Be Cancelled"

delete_experiment_page_title = "Delete Sites of Interest Set"
delete_experiment_success_message = "Data associated with this dataset has been purged from the database."
delete_experiment_confirm_message = "Are you sure you wish to delete this dataset? This action cannot be undone."


experiment_upload_error_ms_id_not_found = "MS_id %d was not found in this experiment"
experiment_upload_error_reasons_column_title = "Error Information"
experiment_upload_error_standard_deviation_label_does_not_match_any_data_column = "Standard deviation column number %d with label '%s' does not match any column label in data columns"
experiment_upload_error_limit_one_column_of_type = "Error: At most one column of type '%s' can exist in your data"
experiment_upload_error_column_type_not_defined = "Error: Column type for column number %d was not defined"
experiment_upload_error_data_column_empty_label = "Error: Label required for column number %d"
experiment_upload_error_data_column_label_duplicated = "Error: Label for data or stddev column %d is duplicated across multiple columns"
experiment_upload_error_multi_column_assignment = "Error: Found multiple column assignments for '%s'"
experiment_upload_error_no_column_assignment = "Error: Column assignment for '%s' not found"
experiment_upload_error_must_have_no_more_column_among = "Error: You must have at most one column from the following: %s"
experiment_upload_error_must_have_one_column_among = "Error: You must have at most one column from the following: %s"
experiment_upload_error_no_annotations = "You must specify at least one column containing annotation data"

experiment_upload_warning_columns_values_should_be = "Expected column value to be of type '%s'"
experiment_upload_warning_missing_column = "Warning: Row missing expected columns"
experiment_upload_warning_data_missing = "Warning: Data fields were not set for this run"
experiment_upload_warning_accession_not_found = "Warning: Protein accession '%s' was not found in any external databases queried by ProteomeScout"
experiment_upload_warning_acc_column_contains_bad_accessions = "Warning: Accession column contains accession with unrecognized types"
experiment_upload_warning_peptide_column_contains_bad_peptide_strings = "Warning: Peptide column contains peptide with incorrect formatting"

experiment_upload_warning_no_mods_found = "Warning: no modified residues were specified in peptide '%s', you must specify at least one modified residue in lower-case"
experiment_upload_warning_modifications_not_valid = "Warning: Specified modification '%s' is not valid"
experiment_upload_warning_modifications_do_not_match_amino_acids = "Warning: Specified modification '%s' does not match residue '%s' for any known species"
experiment_upload_warning_modifications_do_not_match_species = "Warning: Specified modification '%s' does not match residue '%s' for specified species '%s'"
experiment_upload_warning_wrong_number_of_mods = "Warning: Not enough modifications types specified for modified amino acids in peptide (%d for %d)"
experiment_upload_warning_ambiguous_modification_type_for_amino_acid = "Warning: Specified modification '%s' has multiple possible types for amino-acid '%s'"

experiment_upload_warning_no_run_column = "Warning: Experiment contains multiple datapoints for the same protein/peptide/modification tuplet, but no run column"
experiment_upload_warning_full_dupe = "Warning: Experiment contains multiple datapoints for the same protein/peptide/modification/run tuplet"

experiment_upload_warning_peptide_not_found_in_protein_sequence = "Warning: Peptide sequence not found in protein sequence"
experiment_upload_warning_peptide_ambiguous_location_in_protein_sequence = "Warning: Peptide sequence ambguity, peptide matches multiple positions in protein sequence"

experiment_upload_option_no_run_column_assign_in_order  = "Assign run numbers in order of occurrence"


experiment_upload_conditions_page_title = "Experimental Conditions"
experiment_upload_conditions_error_value_must_be_specified = "Error: values are required for all experiment conditions fields"


experiment_upload_confirm_page_title = "Confirm Submission"
experiment_upload_confirm_message = "Required experiment information is now complete. Are you sure you wish to proceed with the upload? Please review and accept the terms of use below. Pressing cancel will remove this upload session, you may start a new one later."

experiment_upload_started_page_title = "Upload Started"
experiment_upload_started_message = \
"""Experiment upload process successfully started. An e-mail will be sent to you when the experiment upload is complete. Additionally, you may check the status of the upload by visiting <a href=\"%s\">this page</a>"""

annotation_upload_confirm_page_title = "Confirm Submission"
annotation_upload_confirm_message = "Required annotation information is now complete. Are you sure you wish to proceed with the upload? Please review and accept the terms of use below. Pressing cancel will remove this upload session, you may start a new one later."
annotation_upload_started_page_title = "Upload Started"
annotation_upload_started_message = \
"""Annotation upload process successfully started. An e-mail will be sent to you when the annotation upload is complete. Additionally, you may check the status of the upload by visiting <a href=\"%s\">this page</a>"""

protein_batch_search_submitted_page_title = "Batch Search Started"
protein_batch_search_submitted_message = \
"""Protein batch annotation process was successfully started. An e-mail will be sent to you when the batch annotation is complete. Additionally, you may check the status of the search by visiting """

experiment_downloand_submitted_page_title = "Experiment Export Started"
experiment_downloadoad_submitted_message = \
"""Experiment export process was successfully started. An e-mail will be sent to you when the export is complete. Additionally, you may check the status of the search by visiting """


dataset_upload_confirm_page_title = "Confirm Submission"
dataset_upload_confirm_message = "Required dataset information is now complete. Are you sure you wish to proceed with the upload? Please review and accept the terms of use below. Pressing cancel will remove this upload session, you may start a new one later."
dataset_upload_started_page_title = "Upload Started"
dataset_upload_started_message = \
"""Sites of Interest upload process successfully started. An e-mail will be sent to you when the upload is complete. Additionally, you may check the status of the upload by visiting <a href=\"%s\">this page</a>"""


experiment_export_started_page_title = "Export Started"
experiment_export_started_message = \
"""Experiment export process successfully started. An e-mail will be sent to you when the experiment export is complete. Additionally, you may check the status of the export by visiting <a href=\"%s\">this page</a>"""

experiment_export_finished_message = \
"""Processing of your job '%s' succeeded.

You may download the results of this export <a href="%s">here</a>.

This file will be available for 24 hours.

-The ProteomeScout Team"""
experiment_export_finished_subject = "ProteomeScout Experiment Export Finished"



forgotten_password_page_title = "Forgotten Password Retrieval"
forgotten_password_success_header = "Password Reset Success"
forgotten_password_success_message = "Your username and a temporary password have been sent to your e-mail address"
forgotten_password_email_subject = "ProteomeScout password reset"
forgotten_password_email_message = \
"""%s,

Your password in ProteomeScout has been reset, your new login credentials are:
Username: %s
Password: %s

Please visit <a href="%s">ProteomeScout</a> to login.
After logging in, your can change your password <a href="%s">here</a>.

-ProteomeScout Administrator
"""

login_page_title = "Login"
login_page_success_header = "Login Successful"
login_page_success_message = "You have successfully logged in."

logout_page_title = "Logout"
logout_page_header = "Logout Successful"
logout_page_message = "You have successfully logged out."

my_experiments_page_title = "My Experiments"
publish_experiment_page_title = "Publish Experiment"
publish_experiment_confirm_message = "Are you sure you want to publish this data?"
publish_experiment_success_message = "You have successfully published this experiment."
publish_experiment_already_message = "Experiment has already been published."

privatize_experiment_page_title = "Set Experiment Private"
privatize_experiment_confirm_message = "Are you sure you want to make this data private?"
privatize_experiment_success_message = "You have successfully made this experiment private."
privatize_experiment_already_message = "Experiment has already been made private."

protein_summary_page_title = "Protein Accessions: %s"
protein_data_page_title = "Experiment Measurements: %s"
protein_ontology_page_title = "Gene Ontologies: %s"
protein_expression_page_title = "Protein Expression: %s"
protein_structure_page_title = "Protein Sequence Viewer: %s"
protein_modification_sites_page_title = "Protein Modification Sites: %s"
protein_search_page_title = "Protein Search"
protein_batch_search_page_title = "Protein Batch Search"

share_experiment_page_title = "Share Experiment"

share_subsets_page_title = "Share Subset: %s"

share_subset_email_subject = "ProteomeScout User %s has shared a subset with you"
share_subset_email_message = \
"""ProteomeScout User %s has shared a subset for experiment '%s' with you,
you may add this subset to your user account by visiting <a href="%s">this
page</a>."""

share_subsets_token_message = \
"""Subset '%s' for experiment '%s' has been shared. Colleagues can now access this subset
by visiting the following link: <a href="%s">%s</a>."""

share_subset_success_message = \
"""This subset has been added to experiment '%s' for your user account,
you may view it be visiting <a href="%s">this page</a> and choosing
the subset from the drop-down menu."""

statistics_page_title = "ProteomeScout Statistics"

upload_page_title = "Upload"
upload_page_header = "Data Upload"

upload_annotations_page_title = "Upload Annotations"
upload_configure_annotations_page_title = "Configure Annotation File"
upload_confirm_annotations_page_title = "Confirm Annotation File Upload"


user_invite_page_title = "Invite User"
user_invite_confirm = "User %s is not a registered user, are you sure you wish to invite this user?"
user_invite_email_required = "Email address is required"
user_invited = "An invitation to view your dataset has been sent to %s."
user_invite_email_subject = "ProteomeScout user %s has invited you to share a dataset"
user_invite_email_message = """
%s,

User %s has invited you to view their dataset '%s', available through ProteomeScout.

Please <a href=\"%s\">visit</a> to access and view this data.

Thanks,
-The ProteomeScout Team
"""


user_registration_page_title = "User Registration"
user_registration_success_header = "Registration Successful"
user_registration_success_message = "A confirmation e-mail has been sent to the specified e-mail address. Please check your e-mail to complete your registration."

user_registration_email_subject = "ProteomeScout Account Activation Details"
user_registration_email_message = """
%s,

Thank you for choosing ProteomeScout for your research.

You can activate your new account by visiting <a href=\"%s/activate_account?username=%s&token=%s\">this link</a>.

Thanks,
-The ProteomeScout Team<br>
"""

portal_page_title = 'ProteomeScout Portal'
view_page_title = "ProteomeScout Terms of Use"

failure_reason_experiment_file_not_enough_columns = "Not enough columns detected in data file. Verify that the file is TSV format and try again"
failure_reason_experiment_header_no_peptide_column = "Data file did not contain a peptide column"
failure_reason_experiment_header_multiple_peptide_column = "Data file contained multiple peptide columns. Check for the phrase 'pep' in all columns of the experiment header."
failure_reason_experiment_header_no_acc_column = "Data file did not contain an accession column"
failure_reason_experiment_header_multiple_acc_columns = "Data file contained multiple accession columns"

failure_reason_terms_of_use_not_accepted = "You must agree to the terms of use at the bottom of this form before submitting a dataset"
failure_reason_field_value_not_valid = "Field '%s' has invalid value"
failure_reason_field_must_be_integer = "Field '%s' must be integer"
failure_reason_field_must_be_numeric = "Field '%s' must be numeric"
failure_reason_required_fields_cannot_be_empty = "Required form field '%s' cannot be empty"

failure_reason_form_fields_cannot_be_empty = "Form fields cannot be empty"
failure_reason_new_passwords_not_matching = "Password confirmation did not match"
failure_reason_incorrect_password = "Supplied password was incorrect"

failure_reason_inactive_account = "Account has not been activated"
failure_reason_incorrect_credentials = "Credentials incorrect"
failure_reason_username_inuse = "Username is already in use"
failure_reason_email_not_valid = "Email address is invalid"
failure_reason_email_not_allowed = "Email address must belong to .edu or .gov domain"
failure_reason_password_too_short = "Password must be at least %d characters in length"
failure_reason_email_address_not_on_record = "E-mail address does not match any user record"


error_resource_not_found_page_title = "Resource Error"
error_protein_not_found_message = "No protein resource exists with the specified ID"

prediction_type_map = {'scansite': "Scansite",
                       'scansite_bind': "Scansite Bind",
                       'scansite_kinase': "Scansite Kinase"}



error_resource_not_ready_page_title = "Resource not ready"
error_resource_not_ready_message = "The resource you are trying to access is currently in processing. If you are the creator of this resource, please visit <a href=\"%s\">this page</a> to check on its status."


experiment_upload_failed_subject = "ProteomeScout experiment upload failed"
experiment_upload_failed_message = \
"""
The upload process for the experiment '%s' failed during the '%s' loading stage with the following error message:

    %s

You can restart the upload by visiting <a href="%s/accounts/experiments">this page</a>.

The ProteomeScout administrator has been notified of this error. If problems persist please contribute a bug report at our <a href="%s">issue tracker</a>.

-The ProteomeScout Team
""" % ("%s", "%s", "%s", "%s", settings.issueTrackerUrl)

error_message_subset_name_exists = "A subset with that name already exists for this experiment, please choose another name"
error_message_subset_name_does_not_exist = "No subset was found with that name"
error_message_subset_empty = "Subset foreground selection was empty, please try another query"

annotation_upload_finished_subject = "ProteomeScout annotation upload finished"
annotation_upload_finished_message = \
"""
ProteomeScout has finished processing your job '%s'.

Annotations Loaded: %d
Errors Encountered: %d

You may now use this annotation data by visiting the <a href="%s">dataset explorer</a>.

A listing of error reasons is provided below.

Thanks for using ProteomeScout,
-The ProteomeScout Team

Upload Errors:
--------------
"""

job_failed_subject = "ProteomeScout job failed"
job_failed_message = """
Processing of your job '%s' failure during '%s' with the following error message:

    %s

You may retry your job at any time. 

The ProteomeScout administrator has been notified of this error. If problems persist please contribute a bug report at our <a href="%s">issue tracker</a>.

-The ProteomeScout Team
"""

failure_reason_account_expired = "This account has expired"


mcam_enrichment_page_title = "MCAM Enrichment Analysis Export"
mcam_enrichment_started_page_title = "MCAM Enrichment Started"
mcam_enrichment_started_message = \
"""The MCAM enrichment process was successfully started. An e-mail will be sent to you containing a link to download your enrichment files when the process is complete. Additionally, you may check the status of the enrichment calculation by visiting <a href=\"%s\">this page</a>"""


mcam_enrichment_finished_message = \
"""Processing of your job '%s' succeeded.

You may download the results of this MCAM enrichment analysis <a href="%s">here</a>.

This file will be available for 24 hours.

-The ProteomeScout Team"""
mcam_enrichment_finished_subject = "ProteomeScout MCAM Export Finished"

batch_annotation_finished_subject = "ProteomeScout Batch Annotation Finished"
batch_annotation_finished_message = \
"""Processing of your job '%s' succeeded.

Proteins Loaded: %d
Errors Encountered: %d

You may download the results of this batch annotation <a href="%s">here</a>.

This file will be available for 24 hours.

-The ProteomeScout Team"""
