#!/usr/bin/env python3
"""
Schema Analysis Tool for SQL consolidation
Analyzes differences between schema.sql, schema_with_auth.sql, and section_tracking_schema.sql
"""

import re
import json
from typing import Dict, List, Set, Tuple
from pathlib import Path

class SQLSchemaAnalyzer:
    """Analizza differenze tra file schema SQL"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.sql_dir = self.project_root / "sql"
        
        # Definisci i file da analizzare
        self.schema_files = {
            'legacy': self.sql_dir / "schema.sql",
            'production': self.sql_dir / "schema_with_auth.sql", 
            'extension': self.sql_dir / "section_tracking_schema.sql"
        }
        
        # Storage per risultati analisi
        self.tables = {}
        self.functions = {}
        self.indexes = {}
        self.views = {}
        self.extensions = {}
        
    def extract_tables(self, sql_content: str, schema_name: str) -> Dict[str, Dict]:
        """Estrai definizioni tabelle da SQL"""
        tables = {}
        
        # Pattern per CREATE TABLE
        table_pattern = r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\((.*?)\);'
        
        for match in re.finditer(table_pattern, sql_content, re.DOTALL | re.IGNORECASE):
            table_name = match.group(1)
            table_def = match.group(2)
            
            # Estrai colonne
            columns = self._extract_columns(table_def)
            
            tables[table_name] = {
                'columns': columns,
                'schema': schema_name,
                'definition': table_def.strip()
            }
            
        return tables
    
    def _extract_columns(self, table_definition: str) -> List[Dict]:
        """Estrai colonne da definizione tabella"""
        columns = []
        
        # Pulisci e dividi per righe
        lines = [line.strip() for line in table_definition.split('\n') if line.strip()]
        
        for line in lines:
            # Salta righe che sono solo constraints (non definizioni colonne)
            if any(line.strip().upper().startswith(keyword) for keyword in ['CONSTRAINT', 'FOREIGN KEY', 'INDEX']):
                continue
                
            # Estrai nome colonna e tipo
            if ',' in line:
                line = line.rstrip(',')
            
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0]
                col_type = parts[1]
                
                # Estrai proprietà aggiuntive
                properties = []
                if 'NOT NULL' in line.upper():
                    properties.append('NOT NULL')
                if 'DEFAULT' in line.upper():
                    properties.append('DEFAULT')
                if 'PRIMARY KEY' in line.upper():
                    properties.append('PRIMARY KEY')
                    
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'properties': properties,
                    'definition': line
                })
                
        return columns
    
    def extract_functions(self, sql_content: str, schema_name: str) -> Dict[str, Dict]:
        """Estrai funzioni SQL"""
        functions = {}
        
        # Pattern per CREATE FUNCTION
        func_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)\s*\((.*?)\)(.*?)(?=CREATE|DROP|ALTER|\Z)'
        
        for match in re.finditer(func_pattern, sql_content, re.DOTALL | re.IGNORECASE):
            func_name = match.group(1)
            func_params = match.group(2)
            func_body = match.group(3)
            
            functions[func_name] = {
                'parameters': func_params.strip(),
                'body': func_body.strip(),
                'schema': schema_name
            }
            
        return functions
    
    def extract_indexes(self, sql_content: str, schema_name: str) -> Dict[str, Dict]:
        """Estrai definizioni indici"""
        indexes = {}
        
        # Pattern per CREATE INDEX
        index_pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\((.*?)\)(?:\s+WITH\s+\((.*?)\))?'
        
        for match in re.finditer(index_pattern, sql_content, re.IGNORECASE):
            index_name = match.group(1)
            table_name = match.group(2)
            columns = match.group(3)
            options = match.group(4) if match.group(4) else ""
            
            indexes[index_name] = {
                'table': table_name,
                'columns': columns.strip(),
                'options': options.strip(),
                'schema': schema_name
            }
            
        return indexes
    
    def extract_extensions(self, sql_content: str, schema_name: str) -> Set[str]:
        """Estrai estensioni PostgreSQL"""
        extensions = set()
        
        # Pattern per CREATE EXTENSION
        ext_pattern = r'CREATE EXTENSION(?:\s+IF\s+NOT\s+EXISTS)?\s+([^;]+);'
        
        for match in re.finditer(ext_pattern, sql_content, re.IGNORECASE):
            ext_name = match.group(1).strip().strip('"')
            extensions.add(ext_name)
            
        return extensions
    
    def analyze_schemas(self) -> Dict:
        """Analizza tutti i file schema"""
        results = {
            'tables': {},
            'functions': {},
            'indexes': {},
            'extensions': {},
            'analysis': {}
        }
        
        # Analizza ogni file schema
        for schema_name, file_path in self.schema_files.items():
            if not file_path.exists():
                print(f"⚠️  File {file_path} non trovato")
                continue
                
            print(f"📖 Analizzando {schema_name}: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estrai componenti
            tables = self.extract_tables(content, schema_name)
            functions = self.extract_functions(content, schema_name)
            indexes = self.extract_indexes(content, schema_name)
            extensions = self.extract_extensions(content, schema_name)
            
            # Aggiungi ai risultati
            for table_name, table_info in tables.items():
                if table_name not in results['tables']:
                    results['tables'][table_name] = {}
                results['tables'][table_name][schema_name] = table_info
                
            for func_name, func_info in functions.items():
                if func_name not in results['functions']:
                    results['functions'][func_name] = {}
                results['functions'][func_name][schema_name] = func_info
                
            for idx_name, idx_info in indexes.items():
                if idx_name not in results['indexes']:
                    results['indexes'][idx_name] = {}
                results['indexes'][idx_name][schema_name] = idx_info
                
            results['extensions'][schema_name] = list(extensions)
            
        # Analizza differenze
        results['analysis'] = self._analyze_differences(results)
        
        return results
    
    def _analyze_differences(self, results: Dict) -> Dict:
        """Analizza differenze tra schemi"""
        analysis = {
            'table_overlaps': {},
            'missing_tables': {},
            'column_differences': {},
            'function_conflicts': {},
            'extension_differences': {},
            'consolidation_recommendations': []
        }
        
        # Analizza sovrapposizioni tabelle
        for table_name, schemas in results['tables'].items():
            schema_list = list(schemas.keys())
            
            if len(schema_list) > 1:
                analysis['table_overlaps'][table_name] = {
                    'present_in': schema_list,
                    'differences': self._compare_table_definitions(schemas)
                }
            else:
                schema = schema_list[0]
                if table_name not in analysis['missing_tables']:
                    analysis['missing_tables'][table_name] = []
                analysis['missing_tables'][table_name].append(f"Only in {schema}")
        
        # Analizza conflitti funzioni
        for func_name, schemas in results['functions'].items():
            if len(schemas) > 1:
                analysis['function_conflicts'][func_name] = {
                    'present_in': list(schemas.keys()),
                    'parameter_differences': self._compare_function_params(schemas)
                }
        
        # Analizza differenze estensioni
        all_extensions = set()
        for schema_exts in results['extensions'].values():
            all_extensions.update(schema_exts)
            
        for ext in all_extensions:
            present_in = []
            for schema_name, schema_exts in results['extensions'].items():
                if ext in schema_exts:
                    present_in.append(schema_name)
            
            if len(present_in) < len(results['extensions']):
                analysis['extension_differences'][ext] = {
                    'present_in': present_in,
                    'missing_from': [s for s in results['extensions'].keys() if s not in present_in]
                }
        
        # Genera raccomandazioni
        analysis['consolidation_recommendations'] = self._generate_recommendations(results, analysis)
        
        return analysis
    
    def _compare_table_definitions(self, schemas: Dict) -> List[str]:
        """Confronta definizioni tabelle tra schemi"""
        differences = []
        
        # Confronta colonne tra schemi
        schema_names = list(schemas.keys())
        
        for i, schema1 in enumerate(schema_names):
            for schema2 in schema_names[i+1:]:
                cols1 = {col['name']: col for col in schemas[schema1]['columns']}
                cols2 = {col['name']: col for col in schemas[schema2]['columns']}
                
                # Colonne mancanti
                missing_in_2 = set(cols1.keys()) - set(cols2.keys())
                missing_in_1 = set(cols2.keys()) - set(cols1.keys())
                
                if missing_in_2:
                    differences.append(f"Columns in {schema1} but not {schema2}: {', '.join(missing_in_2)}")
                if missing_in_1:
                    differences.append(f"Columns in {schema2} but not {schema1}: {', '.join(missing_in_1)}")
                
                # Differenze tipo/proprietà nelle colonne comuni
                common_cols = set(cols1.keys()) & set(cols2.keys())
                for col_name in common_cols:
                    col1, col2 = cols1[col_name], cols2[col_name]
                    
                    if col1['type'] != col2['type']:
                        differences.append(f"Column {col_name}: type {col1['type']} in {schema1} vs {col2['type']} in {schema2}")
                    
                    props1, props2 = set(col1['properties']), set(col2['properties'])
                    if props1 != props2:
                        differences.append(f"Column {col_name}: different properties {props1} vs {props2}")
        
        return differences
    
    def _compare_function_params(self, schemas: Dict) -> List[str]:
        """Confronta parametri funzioni"""
        differences = []
        
        schema_names = list(schemas.keys())
        for i, schema1 in enumerate(schema_names):
            for schema2 in schema_names[i+1:]:
                params1 = schemas[schema1]['parameters']
                params2 = schemas[schema2]['parameters']
                
                if params1 != params2:
                    differences.append(f"Different parameters: {schema1} vs {schema2}")
                    differences.append(f"  {schema1}: {params1}")
                    differences.append(f"  {schema2}: {params2}")
        
        return differences
    
    def _generate_recommendations(self, results: Dict, analysis: Dict) -> List[str]:
        """Genera raccomandazioni per consolidation"""
        recommendations = []
        
        # Raccomandazioni generali
        if 'production' in results['extensions']:
            recommendations.append("🎯 Use schema_with_auth.sql as base (production-ready with multi-tenancy)")
        
        # Tabelle da consolidare
        overlapping_tables = len(analysis['table_overlaps'])
        if overlapping_tables > 0:
            recommendations.append(f"📋 {overlapping_tables} tables need consolidation (overlapping definitions)")
        
        # Estensioni mancanti
        if analysis['extension_differences']:
            recommendations.append("🔧 Standardize extensions across all schemas")
        
        # Funzioni conflittuali
        if analysis['function_conflicts']:
            recommendations.append("⚙️ Resolve function parameter conflicts for tenant-aware versions")
        
        # Integrazione extension schema
        if 'extension' in results['tables']:
            ext_tables = list(results['tables'].keys())
            ext_only = [t for t in ext_tables if 'extension' in results['tables'][t] and len(results['tables'][t]) == 1]
            if ext_only:
                recommendations.append(f"➕ Integrate {len(ext_only)} tables from section_tracking_schema.sql")
        
        return recommendations
    
    def generate_report(self, output_file: str = "schema_analysis_report.json"):
        """Genera report completo dell'analisi"""
        results = self.analyze_schemas()
        
        # Salva report JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Stampa summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict):
        """Stampa summary dell'analisi"""
        print("\n" + "="*60)
        print("📊 SCHEMA ANALYSIS SUMMARY")
        print("="*60)
        
        analysis = results['analysis']
        
        print(f"\n🏗️  TABLES FOUND:")
        for schema_name, schema_exts in results['extensions'].items():
            table_count = len([t for t in results['tables'].values() if schema_name in t])
            print(f"  {schema_name}: {table_count} tables")
        
        print(f"\n🔄 OVERLAPPING TABLES: {len(analysis['table_overlaps'])}")
        for table_name, info in analysis['table_overlaps'].items():
            print(f"  ➤ {table_name} (in: {', '.join(info['present_in'])})")
            
        print(f"\n📋 UNIQUE TABLES: {len(analysis['missing_tables'])}")
        for table_name, info in analysis['missing_tables'].items():
            print(f"  ➤ {table_name}: {', '.join(info)}")
            
        print(f"\n⚙️  FUNCTION CONFLICTS: {len(analysis['function_conflicts'])}")
        for func_name, info in analysis['function_conflicts'].items():
            print(f"  ➤ {func_name} (in: {', '.join(info['present_in'])})")
            
        print(f"\n🔧 EXTENSIONS:")
        for schema_name, exts in results['extensions'].items():
            print(f"  {schema_name}: {', '.join(exts)}")
            
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis['consolidation_recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)

def main():
    """Entry point"""
    print("🔍 Starting SQL Schema Analysis...")
    
    analyzer = SQLSchemaAnalyzer()
    results = analyzer.generate_report()
    
    print(f"\n✅ Analysis complete! Report saved to: schema_analysis_report.json")
    
    return results

if __name__ == "__main__":
    main()
