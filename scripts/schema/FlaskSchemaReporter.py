#!/usr/bin/env python3
"""
Flask-SQLAlchemy Database Schema Reporter
Extracts comprehensive schema information from a database and generates detailed reports
"""

import json
import csv
from datetime import datetime
from collections import defaultdict
import os

# Import your Flask app components
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

class FlaskSchemaReporter:
    def __init__(self, app=None, db=None):
        """
        Initialize with either a Flask app or existing db instance
        
        Args:
            app: Flask application instance
            db: SQLAlchemy database instance
        """
        if db is not None:
            self.db = db
            self.app = db.app if hasattr(db, 'app') else app
        elif app is not None:
            self.app = app
            # Try to get existing db instance or create new one
            try:
                # Check if db is already initialized in the app
                if hasattr(app, 'extensions') and 'sqlalchemy' in app.extensions:
                    self.db = app.extensions['sqlalchemy'].db
                else:
                    self.db = SQLAlchemy(app)
            except:
                self.db = SQLAlchemy(app)
        else:
            raise ValueError("Either app or db must be provided")
        
        self.inspector = inspect(self.db.engine)
        self.schema_data = {}
        
    def extract_all_schema_info(self):
        """Extract comprehensive schema information"""
        print("Extracting database schema information...")
        
        # Get all table names
        table_names = self.inspector.get_table_names()
        print(f"Found {len(table_names)} tables")
        
        self.schema_data = {
            'metadata': self._get_database_metadata(),
            'tables': {},
            'views': {},
            'indexes': {},
            'foreign_keys': {},
            'summary': {}
        }
        
        # Process each table
        for table_name in table_names:
            print(f"Processing table: {table_name}")
            self.schema_data['tables'][table_name] = self._extract_table_info(table_name)
        
        # Get views if supported
        try:
            view_names = self.inspector.get_view_names()
            for view_name in view_names:
                print(f"Processing view: {view_name}")
                self.schema_data['views'][view_name] = self._extract_view_info(view_name)
        except NotImplementedError:
            print("Views not supported by this database")
        
        # Generate summary
        self.schema_data['summary'] = self._generate_summary()
        
        print("Schema extraction complete!")
        return self.schema_data
    
    def _get_database_metadata(self):
        """Get database metadata"""
        metadata = {
            'extraction_time': datetime.now().isoformat(),
            'database_url': str(self.db.engine.url).replace(str(self.db.engine.url.password), '***') if self.db.engine.url.password else str(self.db.engine.url),
            'dialect': self.db.engine.dialect.name,
            'driver': self.db.engine.dialect.driver,
            'server_version': None
        }
        
        # Try to get server version
        try:
            with self.db.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                metadata['server_version'] = result.scalar()
        except:
            try:
                metadata['server_version'] = self.db.engine.dialect.server_version_info
            except:
                metadata['server_version'] = "Unknown"
        
        return metadata
    
    def _extract_table_info(self, table_name):
        """Extract comprehensive information for a single table"""
        table_info = {
            'columns': {},
            'primary_keys': {},
            'foreign_keys': [],
            'unique_constraints': [],
            'check_constraints': [],
            'indexes': [],
            'table_comment': None,
            'row_count': None
        }
        
        # Get columns
        columns = self.inspector.get_columns(table_name)
        for col in columns:
            col_info = {
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': str(col['default']) if col['default'] is not None else None,
                'autoincrement': col.get('autoincrement', False),
                'comment': col.get('comment', None)
            }
            
            # Add type-specific information
            if hasattr(col['type'], 'length') and col['type'].length:
                col_info['length'] = col['type'].length
            if hasattr(col['type'], 'precision') and col['type'].precision:
                col_info['precision'] = col['type'].precision
            if hasattr(col['type'], 'scale') and col['type'].scale:
                col_info['scale'] = col['type'].scale
            
            table_info['columns'][col['name']] = col_info
        
        # Get primary key
        pk_constraint = self.inspector.get_pk_constraint(table_name)
        table_info['primary_keys'] = pk_constraint
        
        # Get foreign keys
        fk_constraints = self.inspector.get_foreign_keys(table_name)
        table_info['foreign_keys'] = fk_constraints
        
        # Get unique constraints
        unique_constraints = self.inspector.get_unique_constraints(table_name)
        table_info['unique_constraints'] = unique_constraints
        
        # Get check constraints (if supported)
        try:
            check_constraints = self.inspector.get_check_constraints(table_name)
            table_info['check_constraints'] = check_constraints
        except NotImplementedError:
            table_info['check_constraints'] = []
        
        # Get indexes
        indexes = self.inspector.get_indexes(table_name)
        table_info['indexes'] = indexes
        
        # Get table comment (if supported)
        try:
            table_comment = self.inspector.get_table_comment(table_name)
            table_info['table_comment'] = table_comment.get('text') if table_comment else None
        except:
            table_info['table_comment'] = None
        
        # Try to get row count
        try:
            with self.db.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                table_info['row_count'] = result.scalar()
        except:
            table_info['row_count'] = "Unable to determine"
        
        return table_info
    
    def _extract_view_info(self, view_name):
        """Extract information for a view"""
        view_info = {
            'definition': None,
            'columns': {}
        }
        
        # Get view definition
        try:
            definition = self.inspector.get_view_definition(view_name)
            view_info['definition'] = definition
        except:
            view_info['definition'] = "Unable to retrieve"
        
        # Get view columns
        try:
            columns = self.inspector.get_columns(view_name)
            for col in columns:
                view_info['columns'][col['name']] = {
                    'type': str(col['type']),
                    'nullable': col['nullable']
                }
        except:
            view_info['columns'] = {}
        
        return view_info
    
    def _generate_summary(self):
        """Generate summary statistics"""
        summary = {
            'total_tables': len(self.schema_data['tables']),
            'total_views': len(self.schema_data['views']),
            'total_columns': 0,
            'total_indexes': 0,
            'total_foreign_keys': 0,
            'column_types': defaultdict(int),
            'tables_by_column_count': {},
            'largest_tables': []
        }
        
        # Analyze tables
        for table_name, table_info in self.schema_data['tables'].items():
            # Count columns
            col_count = len(table_info['columns'])
            summary['total_columns'] += col_count
            summary['tables_by_column_count'][table_name] = col_count
            
            # Count indexes and foreign keys
            summary['total_indexes'] += len(table_info['indexes'])
            summary['total_foreign_keys'] += len(table_info['foreign_keys'])
            
            # Analyze column types
            for col_name, col_info in table_info['columns'].items():
                col_type = col_info['type'].split('(')[0]  # Remove length/precision
                summary['column_types'][col_type] += 1
            
            # Track table sizes (by row count)
            if table_info['row_count'] and isinstance(table_info['row_count'], int):
                summary['largest_tables'].append({
                    'table': table_name,
                    'rows': table_info['row_count'],
                    'columns': col_count
                })
        
        # Sort largest tables
        summary['largest_tables'] = sorted(
            summary['largest_tables'], 
            key=lambda x: x['rows'], 
            reverse=True
        )[:10]  # Top 10
        
        # Convert defaultdict to regular dict for JSON serialization
        summary['column_types'] = dict(summary['column_types'])
        
        return summary
    
    def generate_csv_reports(self, base_filename="database_schema_report"):
        """Generate multiple CSV reports"""
        print(f"Generating CSV reports with base name: {base_filename}")
        
        # Summary CSV
        summary_filename = f"{base_filename}_summary.csv"
        self._write_summary_csv(summary_filename)
        
        # Tables overview CSV
        tables_filename = f"{base_filename}_tables.csv"
        self._write_tables_csv(tables_filename)
        
        # All columns CSV
        columns_filename = f"{base_filename}_columns.csv"
        self._write_columns_csv(columns_filename)
        
        # Foreign keys CSV
        fk_filename = f"{base_filename}_foreign_keys.csv"
        self._write_foreign_keys_csv(fk_filename)
        
        # Indexes CSV
        indexes_filename = f"{base_filename}_indexes.csv"
        self._write_indexes_csv(indexes_filename)
        
        # Column types summary CSV
        types_filename = f"{base_filename}_column_types.csv"
        self._write_column_types_csv(types_filename)
        
        print(f"CSV reports generated:")
        print(f"  - Summary: {summary_filename}")
        print(f"  - Tables: {tables_filename}")
        print(f"  - Columns: {columns_filename}")
        print(f"  - Foreign Keys: {fk_filename}")
        print(f"  - Indexes: {indexes_filename}")
        print(f"  - Column Types: {types_filename}")
    
    def _write_summary_csv(self, filename):
        """Write summary information to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Metric', 'Value'])
            
            metadata = self.schema_data['metadata']
            summary = self.schema_data['summary']
            
            writer.writerow(['Database URL', metadata['database_url']])
            writer.writerow(['Extraction Time', metadata['extraction_time']])
            writer.writerow(['Database Type', metadata['dialect']])
            writer.writerow(['Driver', metadata['driver']])
            writer.writerow(['Server Version', metadata['server_version']])
            writer.writerow(['', ''])
            writer.writerow(['Total Tables', summary['total_tables']])
            writer.writerow(['Total Views', summary['total_views']])
            writer.writerow(['Total Columns', summary['total_columns']])
            writer.writerow(['Total Indexes', summary['total_indexes']])
            writer.writerow(['Total Foreign Keys', summary['total_foreign_keys']])
    
    def _write_tables_csv(self, filename):
        """Write tables overview to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table Name', 'Column Count', 'Index Count', 'FK Count', 'Row Count', 'Comment'])
            
            for table_name, table_info in self.schema_data['tables'].items():
                writer.writerow([
                    table_name,
                    len(table_info['columns']),
                    len(table_info['indexes']),
                    len(table_info['foreign_keys']),
                    table_info['row_count'],
                    table_info['table_comment'] or ''
                ])
    
    def _write_columns_csv(self, filename):
        """Write detailed column information to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table', 'Column', 'Type', 'Nullable', 'Default', 'Auto Inc', 'Length', 'Precision', 'Scale', 'Comment'])
            
            for table_name, table_info in self.schema_data['tables'].items():
                for col_name, col_info in table_info['columns'].items():
                    writer.writerow([
                        table_name,
                        col_name,
                        col_info['type'],
                        'Yes' if col_info['nullable'] else 'No',
                        col_info['default'] or '',
                        'Yes' if col_info['autoincrement'] else 'No',
                        col_info.get('length', ''),
                        col_info.get('precision', ''),
                        col_info.get('scale', ''),
                        col_info['comment'] or ''
                    ])
    
    def _write_foreign_keys_csv(self, filename):
        """Write foreign keys information to CSV"""
        fk_data = []
        for table_name, table_info in self.schema_data['tables'].items():
            for fk in table_info['foreign_keys']:
                fk_data.append([
                    table_name,
                    ', '.join(fk['constrained_columns']),
                    fk['referred_table'],
                    ', '.join(fk['referred_columns']),
                    fk['name'] or ''
                ])
        
        if fk_data:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Table', 'Columns', 'Referenced Table', 'Referenced Columns', 'Constraint Name'])
                writer.writerows(fk_data)
        else:
            # Create empty file with headers
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Table', 'Columns', 'Referenced Table', 'Referenced Columns', 'Constraint Name'])
                writer.writerow(['No foreign keys found', '', '', '', ''])
    
    def _write_indexes_csv(self, filename):
        """Write indexes information to CSV"""
        index_data = []
        for table_name, table_info in self.schema_data['tables'].items():
            for idx in table_info['indexes']:
                index_data.append([
                    table_name,
                    idx['name'],
                    ', '.join(idx['column_names']),
                    'Yes' if idx['unique'] else 'No'
                ])
        
        if index_data:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Table', 'Index Name', 'Columns', 'Unique'])
                writer.writerows(index_data)
        else:
            # Create empty file with headers
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Table', 'Index Name', 'Columns', 'Unique'])
                writer.writerow(['No indexes found', '', '', ''])
    
    def _write_column_types_csv(self, filename):
        """Write column types summary to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Column Type', 'Count', 'Percentage'])
            
            summary = self.schema_data['summary']
            total_columns = summary['total_columns']
            
            sorted_types = sorted(summary['column_types'].items(), key=lambda x: x[1], reverse=True)
            for col_type, count in sorted_types:
                percentage = (count / total_columns * 100) if total_columns > 0 else 0
                writer.writerow([col_type, count, f"{percentage:.1f}%"])
    
    def generate_json_report(self, filename="database_schema_report.json"):
        """Generate JSON report"""
        print(f"Generating JSON report: {filename}")
        
        with open(filename, 'w') as f:
            json.dump(self.schema_data, f, indent=2, default=str)
        
        print(f"JSON report saved as: {filename}")
    
    def print_summary(self):
        """Print a summary to console"""
        summary = self.schema_data['summary']
        metadata = self.schema_data['metadata']
        
        print("\n" + "="*60)
        print("DATABASE SCHEMA SUMMARY")
        print("="*60)
        print(f"Database: {metadata['dialect']} ({metadata['driver']})")
        print(f"Extracted: {metadata['extraction_time']}")
        print(f"Server Version: {metadata['server_version']}")
        print()
        print(f"Tables: {summary['total_tables']}")
        print(f"Views: {summary['total_views']}")
        print(f"Total Columns: {summary['total_columns']}")
        print(f"Total Indexes: {summary['total_indexes']}")
        print(f"Total Foreign Keys: {summary['total_foreign_keys']}")
        
        if summary['largest_tables']:
            print(f"\nLargest Tables (by row count):")
            for table in summary['largest_tables'][:5]:
                print(f"  {table['table']}: {table['rows']:,} rows, {table['columns']} columns")
        
        print(f"\nMost Common Column Types:")
        sorted_types = sorted(summary['column_types'].items(), key=lambda x: x[1], reverse=True)
        for col_type, count in sorted_types[:10]:
            print(f"  {col_type}: {count}")

def main():
    """Example usage - modify this section for your specific Flask app"""
    
    # Option 1: If you have an existing Flask app instance
    # from your_app import app, db
    # reporter = FlaskSchemaReporter(app=app, db=db)
    
    # Option 2: Create a minimal Flask app for database connection
    app = Flask(__name__)
    
    # Configure your database URI here
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri_here'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    with app.app_context():
        reporter = FlaskSchemaReporter(app=app, db=db)
        
        # Extract schema information
        schema_data = reporter.extract_all_schema_info()
        
        # Generate reports
        reporter.print_summary()
        reporter.generate_csv_reports()
        reporter.generate_json_report()
        
        print("\nSchema analysis complete!")

if __name__ == "__main__":
    main()