import ast
from pathlib import Path

def parse_file(file_path, language='auto'):
    if language == 'auto':
        language = detect_language(file_path)
    if language == 'python':
        return parse_python(file_path)
    raise NotImplementedError(f"Language {language} not supported yet")

def detect_language(file_path):
    suffix = Path(file_path).suffix
    language_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java'}
    return language_map.get(suffix, 'unknown')

def parse_python(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    return ast.parse(code, filename=file_path)
