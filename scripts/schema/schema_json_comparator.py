#!/usr/bin/env python3
"""
JSON Schema Comparator
Compares two database schema JSON files and generates detailed difference reports
"""

import json
import csv
from datetime import datetime
from collections import defaultdict

class SchemaJSONComparator:
    def __init__(self, prod_json_file, test_json_file):
        """
        Initialize comparator with two JSON schema files
        
        Args:
            prod_json_file: Path to production schema JSON
            test_json_file: Path to test schema JSON
        """
        self.prod_json_file = prod_json_file
        self.test_json_file = test_json_file
        self.prod_schema = None
        self.test_schema = None
        self.differences = {}
        
    def load_schemas(self):
        """Load both JSON schema files"""
        print(f"Loading production schema: {self.prod_json_file}")
        try:
            with open(self.prod_json_file, 'r') as f:
                self.prod_schema = json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: Could not find {self.prod_json_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {self.prod_json_file}: {e}")
            return False
        
        print(f"Loading test schema: {self.test_json_file}")
        try:
            with open(self.test_json_file, 'r') as f:
                self.test_schema = json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: Could not find {self.test_json_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {self.test_json_file}: {e}")
            return False
        
        print("✅ Both schema files loaded successfully")
        return True
    
    def compare_schemas(self):
        """Compare the two schemas and identify all differences"""
        if not self.prod_schema or not self.test_schema:
            print("❌ Schemas not loaded. Call load_schemas() first.")
            return False
        
        print("🔍 Comparing schemas...")
        
        self.differences = {
            'metadata': self._compare_metadata(),
            'tables': self._compare_tables(),
            'views': self._compare_views(),
            'summary': {}
        }
        
        # Generate comparison summary
        self.differences['summary'] = self._generate_comparison_summary()
        
        print("✅ Schema comparison completed")
        return True
    
    def _compare_metadata(self):
        """Compare database metadata"""
        metadata_diff = {
            'prod': self.prod_schema.get('metadata', {}),
            'test': self.test_schema.get('metadata', {}),
            'differences': {}
        }
        
        prod_meta = self.prod_schema.get('metadata', {})
        test_meta = self.test_schema.get('metadata', {})
        
        # Compare each metadata field
        all_keys = set(prod_meta.keys()) | set(test_meta.keys())
        for key in all_keys:
            prod_val = prod_meta.get(key)
            test_val = test_meta.get(key)
            
            if prod_val != test_val:
                metadata_diff['differences'][key] = {
                    'prod': prod_val,
                    'test': test_val
                }
        
        return metadata_diff
    
    def _compare_tables(self):
        """Compare tables between schemas"""
        prod_tables = set(self.prod_schema.get('tables', {}).keys())
        test_tables = set(self.test_schema.get('tables', {}).keys())
        
        tables_diff = {
            'only_in_prod': list(prod_tables - test_tables),
            'only_in_test': list(test_tables - prod_tables),
            'common_tables': list(prod_tables & test_tables),
            'table_differences': {}
        }
        
        # Compare common tables in detail
        for table_name in tables_diff['common_tables']:
            table_diff = self._compare_single_table(table_name)
            if table_diff:
                tables_diff['table_differences'][table_name] = table_diff
        
        return tables_diff
    
    def _compare_single_table(self, table_name):
        """Compare a single table between schemas"""
        prod_table = self.prod_schema['tables'][table_name]
        test_table = self.test_schema['tables'][table_name]
        
        table_diff = {}
        
        # Compare columns
        column_diff = self._compare_columns(prod_table.get('columns', {}), test_table.get('columns', {}))
        if column_diff:
            table_diff['columns'] = column_diff
        
        # Compare primary keys
        prod_pk = prod_table.get('primary_keys', {})
        test_pk = test_table.get('primary_keys', {})
        if prod_pk != test_pk:
            table_diff['primary_keys'] = {'prod': prod_pk, 'test': test_pk}
        
        # Compare foreign keys
        prod_fks = prod_table.get('foreign_keys', [])
        test_fks = test_table.get('foreign_keys', [])
        if prod_fks != test_fks:
            table_diff['foreign_keys'] = {'prod': prod_fks, 'test': test_fks}
        
        # Compare unique constraints
        prod_unique = prod_table.get('unique_constraints', [])
        test_unique = test_table.get('unique_constraints', [])
        if prod_unique != test_unique:
            table_diff['unique_constraints'] = {'prod': prod_unique, 'test': test_unique}
        
        # Compare indexes
        prod_indexes = prod_table.get('indexes', [])
        test_indexes = test_table.get('indexes', [])
        if prod_indexes != test_indexes:
            table_diff['indexes'] = {'prod': prod_indexes, 'test': test_indexes}
        
        # Compare row counts
        prod_rows = prod_table.get('row_count')
        test_rows = test_table.get('row_count')
        if prod_rows != test_rows:
            table_diff['row_count'] = {'prod': prod_rows, 'test': test_rows}
        
        # Compare table comments
        prod_comment = prod_table.get('table_comment')
        test_comment = test_table.get('table_comment')
        if prod_comment != test_comment:
            table_diff['table_comment'] = {'prod': prod_comment, 'test': test_comment}
        
        return table_diff if table_diff else None
    
    def _compare_columns(self, prod_columns, test_columns):
        """Compare columns between two tables"""
        prod_col_names = set(prod_columns.keys())
        test_col_names = set(test_columns.keys())
        
        column_diff = {}
        
        # Columns only in prod
        only_in_prod = prod_col_names - test_col_names
        if only_in_prod:
            column_diff['only_in_prod'] = list(only_in_prod)
        
        # Columns only in test
        only_in_test = test_col_names - prod_col_names
        if only_in_test:
            column_diff['only_in_test'] = list(only_in_test)
        
        # Compare common columns
        common_columns = prod_col_names & test_col_names
        different_columns = {}
        
        for col_name in common_columns:
            prod_col = prod_columns[col_name]
            test_col = test_columns[col_name]
            
            col_differences = {}
            
            # Compare each column attribute
            all_attrs = set(prod_col.keys()) | set(test_col.keys())
            for attr in all_attrs:
                prod_val = prod_col.get(attr)
                test_val = test_col.get(attr)
                
                if prod_val != test_val:
                    col_differences[attr] = {'prod': prod_val, 'test': test_val}
            
            if col_differences:
                different_columns[col_name] = col_differences
        
        if different_columns:
            column_diff['different_columns'] = different_columns
        
        return column_diff if column_diff else None
    
    def _compare_views(self):
        """Compare views between schemas"""
        prod_views = set(self.prod_schema.get('views', {}).keys())
        test_views = set(self.test_schema.get('views', {}).keys())
        
        views_diff = {
            'only_in_prod': list(prod_views - test_views),
            'only_in_test': list(test_views - prod_views),
            'common_views': list(prod_views & test_views),
            'view_differences': {}
        }
        
        # Compare common views
        for view_name in views_diff['common_views']:
            prod_view = self.prod_schema['views'][view_name]
            test_view = self.test_schema['views'][view_name]
            
            if prod_view != test_view:
                views_diff['view_differences'][view_name] = {
                    'prod': prod_view,
                    'test': test_view
                }
        
        return views_diff
    
    def _generate_comparison_summary(self):
        """Generate summary of differences"""
        summary = {
            'total_differences_found': 0,
            'metadata_differences': len(self.differences['metadata']['differences']),
            'tables_only_in_prod': len(self.differences['tables']['only_in_prod']),
            'tables_only_in_test': len(self.differences['tables']['only_in_test']),
            'tables_with_differences': len(self.differences['tables']['table_differences']),
            'views_only_in_prod': len(self.differences['views']['only_in_prod']),
            'views_only_in_test': len(self.differences['views']['only_in_test']),
            'views_with_differences': len(self.differences['views']['view_differences']),
        }
        
        # Calculate total differences
        summary['total_differences_found'] = (
            summary['metadata_differences'] +
            summary['tables_only_in_prod'] +
            summary['tables_only_in_test'] +
            summary['tables_with_differences'] +
            summary['views_only_in_prod'] +
            summary['views_only_in_test'] +
            summary['views_with_differences']
        )
        
        return summary
    
    def print_summary_report(self):
        """Print a summary of differences to console"""
        if not self.differences:
            print("❌ No comparison data available. Run compare_schemas() first.")
            return
        
        summary = self.differences['summary']
        
        print("\n" + "="*70)
        print("DATABASE SCHEMA COMPARISON SUMMARY")
        print("="*70)
        print(f"Production Schema: {self.prod_json_file}")
        print(f"Test Schema: {self.test_json_file}")
        print(f"Comparison Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if summary['total_differences_found'] == 0:
            print("🎉 NO DIFFERENCES FOUND! Schemas are identical.")
            return
        
        print(f"⚠️  TOTAL DIFFERENCES FOUND: {summary['total_differences_found']}")
        print()
        
        # Metadata differences
        if summary['metadata_differences'] > 0:
            print(f"📊 Metadata Differences: {summary['metadata_differences']}")
            for key, diff in self.differences['metadata']['differences'].items():
                print(f"  - {key}: Prod='{diff['prod']}' vs Test='{diff['test']}'")
            print()
        
        # Table differences
        if summary['tables_only_in_prod'] > 0:
            print(f"📋 Tables only in PRODUCTION ({summary['tables_only_in_prod']}):")
            for table in self.differences['tables']['only_in_prod']:
                print(f"  - {table}")
            print()
        
        if summary['tables_only_in_test'] > 0:
            print(f"🧪 Tables only in TEST ({summary['tables_only_in_test']}):")
            for table in self.differences['tables']['only_in_test']:
                print(f"  - {table}")
            print()
        
        if summary['tables_with_differences'] > 0:
            print(f"🔄 Tables with differences ({summary['tables_with_differences']}):")
            for table_name, table_diff in self.differences['tables']['table_differences'].items():
                print(f"  - {table_name}:")
                if 'columns' in table_diff:
                    col_diff = table_diff['columns']
                    if 'only_in_prod' in col_diff:
                        print(f"    Columns only in prod: {col_diff['only_in_prod']}")
                    if 'only_in_test' in col_diff:
                        print(f"    Columns only in test: {col_diff['only_in_test']}")
                    if 'different_columns' in col_diff:
                        print(f"    Modified columns: {list(col_diff['different_columns'].keys())}")
                
                for diff_type in ['primary_keys', 'foreign_keys', 'indexes', 'row_count']:
                    if diff_type in table_diff:
                        print(f"    {diff_type.replace('_', ' ').title()} differ")
            print()
        
        # View differences
        if summary['views_only_in_prod'] > 0:
            print(f"👁️  Views only in PRODUCTION ({summary['views_only_in_prod']}):")
            for view in self.differences['views']['only_in_prod']:
                print(f"  - {view}")
            print()
        
        if summary['views_only_in_test'] > 0:
            print(f"🔬 Views only in TEST ({summary['views_only_in_test']}):")
            for view in self.differences['views']['only_in_test']:
                print(f"  - {view}")
            print()
        
        if summary['views_with_differences'] > 0:
            print(f"🔄 Views with differences ({summary['views_with_differences']}):")
            for view in self.differences['views']['view_differences']:
                print(f"  - {view}")
            print()
    
    def generate_detailed_csv_reports(self, base_filename="schema_comparison"):
        """Generate detailed CSV reports of all differences"""
        if not self.differences:
            print("❌ No comparison data available. Run compare_schemas() first.")
            return
        
        print(f"📝 Generating detailed CSV reports...")
        
        # Summary report
        self._write_summary_csv(f"{base_filename}_summary.csv")
        
        # Table differences report
        self._write_table_differences_csv(f"{base_filename}_table_differences.csv")
        
        # Column differences report  
        self._write_column_differences_csv(f"{base_filename}_column_differences.csv")
        
        # Missing tables report
        self._write_missing_tables_csv(f"{base_filename}_missing_tables.csv")
        
        # Constraint differences report
        self._write_constraint_differences_csv(f"{base_filename}_constraint_differences.csv")
        
        print("✅ CSV reports generated successfully!")
    
    def _write_summary_csv(self, filename):
        """Write summary comparison to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Metric', 'Count'])
            
            summary = self.differences['summary']
            writer.writerow(['Total Differences Found', summary['total_differences_found']])
            writer.writerow(['Metadata Differences', summary['metadata_differences']])
            writer.writerow(['Tables Only in Production', summary['tables_only_in_prod']])
            writer.writerow(['Tables Only in Test', summary['tables_only_in_test']])
            writer.writerow(['Tables with Differences', summary['tables_with_differences']])
            writer.writerow(['Views Only in Production', summary['views_only_in_prod']])
            writer.writerow(['Views Only in Test', summary['views_only_in_test']])
            writer.writerow(['Views with Differences', summary['views_with_differences']])
    
    def _write_table_differences_csv(self, filename):
        """Write table-level differences to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table Name', 'Difference Type', 'Details'])
            
            # Tables only in production
            for table in self.differences['tables']['only_in_prod']:
                writer.writerow([table, 'Only in Production', 'Table exists in prod but not in test'])
            
            # Tables only in test
            for table in self.differences['tables']['only_in_test']:
                writer.writerow([table, 'Only in Test', 'Table exists in test but not in prod'])
            
            # Tables with differences
            for table_name, table_diff in self.differences['tables']['table_differences'].items():
                diff_types = list(table_diff.keys())
                writer.writerow([table_name, 'Modified', f"Differences in: {', '.join(diff_types)}"])
    
    def _write_column_differences_csv(self, filename):
        """Write column-level differences to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table', 'Column', 'Difference Type', 'Attribute', 'Production Value', 'Test Value'])
            
            for table_name, table_diff in self.differences['tables']['table_differences'].items():
                if 'columns' not in table_diff:
                    continue
                
                col_diff = table_diff['columns']
                
                # Columns only in production
                for col in col_diff.get('only_in_prod', []):
                    writer.writerow([table_name, col, 'Only in Production', '', '', ''])
                
                # Columns only in test
                for col in col_diff.get('only_in_test', []):
                    writer.writerow([table_name, col, 'Only in Test', '', '', ''])
                
                # Modified columns
                for col_name, col_changes in col_diff.get('different_columns', {}).items():
                    for attr, values in col_changes.items():
                        writer.writerow([
                            table_name, col_name, 'Modified', attr, 
                            values['prod'], values['test']
                        ])
    
    def _write_missing_tables_csv(self, filename):
        """Write missing tables report to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table Name', 'Missing From', 'Impact Level'])
            
            for table in self.differences['tables']['only_in_prod']:
                writer.writerow([table, 'Test Environment', 'HIGH - Missing in test'])
            
            for table in self.differences['tables']['only_in_test']:
                writer.writerow([table, 'Production Environment', 'MEDIUM - Extra in test'])
    
    def _write_constraint_differences_csv(self, filename):
        """Write constraint and index differences to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table', 'Constraint Type', 'Production', 'Test'])
            
            for table_name, table_diff in self.differences['tables']['table_differences'].items():
                for constraint_type in ['primary_keys', 'foreign_keys', 'unique_constraints', 'indexes']:
                    if constraint_type in table_diff:
                        prod_val = str(table_diff[constraint_type]['prod'])
                        test_val = str(table_diff[constraint_type]['test'])
                        writer.writerow([table_name, constraint_type, prod_val, test_val])
    
    def save_detailed_json_report(self, filename="schema_comparison_detailed.json"):
        """Save detailed comparison results to JSON"""
        if not self.differences:
            print("❌ No comparison data available. Run compare_schemas() first.")
            return
        
        report_data = {
            'comparison_metadata': {
                'prod_file': self.prod_json_file,
                'test_file': self.test_json_file,
                'comparison_time': datetime.now().isoformat(),
            },
            'differences': self.differences
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📄 Detailed JSON report saved: {filename}")

def main():
    """Main function to run schema comparison"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare two database schema JSON files')
    parser.add_argument('prod_json', help='Production schema JSON file')
    parser.add_argument('test_json', help='Test schema JSON file')
    parser.add_argument('--output', '-o', default='schema_comparison', 
                       help='Base filename for output reports (default: schema_comparison)')
    
    args = parser.parse_args()
    
    # Create comparator
    comparator = SchemaJSONComparator(args.prod_json, args.test_json)
    
    # Load and compare schemas
    if not comparator.load_schemas():
        return 1
    
    if not comparator.compare_schemas():
        return 1
    
    # Generate reports
    comparator.print_summary_report()
    comparator.generate_detailed_csv_reports(args.output)
    comparator.save_detailed_json_report(f"{args.output}_detailed.json")
    
    return 0

if __name__ == "__main__":
    # Example usage when run directly
    # You can also import and use the class directly
    
    # Direct usage example:
    # comparator = SchemaJSONComparator('prod_schema.json', 'test_schema.json')
    # comparator.load_schemas()
    # comparator.compare_schemas()
    # comparator.print_summary_report()
    # comparator.generate_detailed_csv_reports('my_comparison')
    
    exit(main())