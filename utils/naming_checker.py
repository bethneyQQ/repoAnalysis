import re
import ast

def check_naming_convention(ast_tree, rules):
    violations = []
    # 类名
    if 'class' in rules:
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef):
                if not matches_convention(node.name, rules['class']):
                    violations.append({'type':'class','name':node.name,'line':node.lineno,'expected':rules['class']})
    # 函数名
    if 'function' in rules:
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                if not matches_convention(node.name, rules['function']):
                    violations.append({'type':'function','name':node.name,'line':node.lineno,'expected':rules['function']})
    return violations

def matches_convention(name, convention):
    patterns = {
        'kebab-case': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',
        'snake_case': r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$',
        'camelCase': r'^[a-z][a-zA-Z0-9]*$',
        'PascalCase': r'^[A-Z][a-zA-Z0-9]*$',
        'UPPER_SNAKE_CASE': r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$',
    }
    pattern = patterns.get(convention)
    if not pattern:
        return True
    return bool(re.match(pattern, name))
