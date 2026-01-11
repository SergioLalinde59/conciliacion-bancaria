import os
import ast

def find_classes_in_file(file_path):
    classes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=file_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append(node.name)
            except SyntaxError:
                pass
            except Exception:
                pass
    except Exception:
        pass
    return classes

def analyze_directory(root_dir):
    data = []
    for root, dirs, files in os.walk(root_dir):
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        if 'venv' in dirs: dirs.remove('venv') # Common ignore
        
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                classes = find_classes_in_file(full_path)
                for cls in classes:
                    data.append((rel_path, cls))
    return data

if __name__ == "__main__":
    root_dir = "."
    results = analyze_directory(root_dir)
    results.sort(key=lambda x: (x[0], x[1]))
    
    print("| Archivo | Clase |")
    print("|---|---|")
    for file, cls in results:
        print(f"| {file} | {cls} |")
