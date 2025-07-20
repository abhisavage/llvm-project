import os
from clang import cindex

def initialize_clang(libclang_path=None):
    if libclang_path:
        cindex.Config.set_library_file(libclang_path)

def extract_and_match_functions(local_repo_path, file_paths, predicted_entries):
    """
    Parses local LLVM files. Returns matches for functions, methods, classes, structs, and enums.
    """
    index = cindex.Index.create()
    results = {}

    # Map of filename -> set of expected names
    expected_map = {} 
    for full in predicted_entries:
        if "::" in full:
            file, name = full.split("::", 1)
            expected_map.setdefault(file.strip(), set()).add(name.strip())

    for file in file_paths:
        abs_path = os.path.join(local_repo_path, file.replace("/", os.sep))
        if not os.path.exists(abs_path):
            print(f"⚠️ {file}: File not found at {abs_path}")
            continue

        try:
            tu = index.parse(
                abs_path,
                args=["-std=c++17"],
                options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            )

            matches = []

            def visit(node):
                if node.kind in {
                    cindex.CursorKind.FUNCTION_DECL,
                    cindex.CursorKind.CXX_METHOD,
                    cindex.CursorKind.CONSTRUCTOR,
                    cindex.CursorKind.CLASS_DECL,
                    cindex.CursorKind.STRUCT_DECL,
                    cindex.CursorKind.ENUM_DECL
                }:
                    symbol_name = node.spelling or node.displayname
                    if symbol_name and any(expected in symbol_name for expected in expected_map.get(file, set())):
                        matches.append({
                            "name": symbol_name,
                            "line": node.location.line,
                            "kind": node.kind.name
                        })
                for c in node.get_children():
                    visit(c)

            visit(tu.cursor)
            if matches:
                results[file] = matches

        except Exception as e:
            print(f"⚠️ {file}: {e}")

    return results
