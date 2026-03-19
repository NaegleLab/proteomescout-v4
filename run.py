import os
import sys

from proteomescout_app import create_app


app = create_app()


def _validate_data_file_paths(flask_app):
    protein_path = flask_app.config.get('PROTEIN_DATA_TSV_PATH')
    citations_path = flask_app.config.get('CITATIONS_TSV_PATH')
    missing = [path for path in (protein_path, citations_path) if not path or not os.path.isfile(path)]

    if not missing:
        return

    print('ERROR: Required TSV files were not found.', file=sys.stderr)
    print(f'  - Expected protein data TSV: {protein_path}', file=sys.stderr)
    print(f'  - Expected citations TSV:    {citations_path}', file=sys.stderr)
    print('', file=sys.stderr)
    print('Set PROTEOMESCOUT_DATA_DIR to a directory containing both data.tsv and citations.tsv.', file=sys.stderr)
    print('Example:', file=sys.stderr)
    print('  PROTEOMESCOUT_DATA_DIR=/path/to/proteomescout_data python run.py', file=sys.stderr)
    raise SystemExit(1)


if __name__ == '__main__':
    _validate_data_file_paths(app)
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5001'))
    debug = os.environ.get('DEBUG', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
    app.run(host=host, port=port, debug=debug)