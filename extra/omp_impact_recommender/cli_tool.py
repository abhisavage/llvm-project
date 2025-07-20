import argparse
import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from clang import cindex
from omp_impact_recommender.ast_analyzer import initialize_clang, extract_and_match_functions
from dotenv import load_dotenv, find_dotenv
from omp_impact_recommender.rules import keyword_map

# Load environment variables from .env file
github_token = None
llvm_local_path = None

def load_model(model_path):
    tok = AutoTokenizer.from_pretrained(model_path)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return tok, mdl.to(device), device

def suggest(tok, mdl, device, prompt):
    i = tok(prompt, return_tensors="pt", truncation=True, padding=True).to(device)
    o = mdl.generate(**i, max_length=256, num_beams=4, early_stopping=True)
    return tok.decode(o[0], skip_special_tokens=True)

def parse_model_output(text):
    files_set, full_funcs = set(), []
    parts = [s.strip() for s in text.split(",") if "::" in s]
    for part in parts:
        try:
            file, func = part.split("::", 1)
            files_set.add(file.strip())
            full_funcs.append(f"{file.strip()}::{func.strip()}")
        except ValueError:
            continue
    return sorted(files_set), sorted(set(full_funcs))

def rule_based_lookup(prompt):
    # Split prompt into keywords and check for any in the keyword_map
    found = set()
    for word in prompt.lower().split():
        if word in keyword_map:
            found.add(word)
    if found:
        # Merge all unique file::funcs for all found keywords
        results = set()
        for word in found:
            results.update(keyword_map[word])
        return sorted(results), True, list(found)
    return None, False, []

def set_libclang(libclang_path=None):
    if libclang_path:
        cindex.Config.set_library_file(libclang_path)
    else:
        default_path = "C:/Program Files/LLVM/bin/libclang.dll"
        if os.path.exists(default_path):
            cindex.Config.set_library_file(default_path)
        else:
            raise FileNotFoundError("❌ libclang.dll not found. Please install LLVM or pass --libclang path.")

def batch_test(tok, mdl, device):
    prompts = [
        "taskwait codegen", "flush ir target", "parallel parse runtime",
        "atomic sema", "for codegen parse", "sections runtime ast",
        "ordered flush", "barrier codegen", "masked parse ast",
        "taskgroup codegen"
    ]
    for prompt in prompts:
        print(f"\n🧠 Prompt: {prompt}")
        out = suggest(tok, mdl, device, prompt)
        files, full_funcs = parse_model_output(out)
        print("  📁 Predicted Files:")
        for f in files:
            print(f"    • {f}")
        print("  🔧 Predicted Functions:")
        for f in full_funcs:
            print(f"    • {f}")


default_model_path = os.path.abspath("extra/omp_t5_model2")
def main():
    # ---vvv--- NEW DEBUGGING AND LOADING LOGIC ---vvv---
    # print(f"DEBUG: Running from CWD: {os.getcwd()}")
    # Force dotenv to look for the .env file in the current working directory
    env_path = find_dotenv(usecwd=True)

    if not env_path:
        # print("DEBUG: .env file not found in current directory.")
        pass
    else:
        # print(f"DEBUG: Found .env file at: {env_path}")
        load_dotenv(dotenv_path=env_path)
    # ---^^^--- END NEW LOGIC ---^^^---

    global github_token, llvm_local_path
    github_token = os.getenv("GITHUB_TOKEN")
    llvm_local_path = os.getenv("LOCAL_LLVM_PATH")
    print("📦 LOCAL_LLVM_PATH =", llvm_local_path)

    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", help="Prompt like 'taskwait codegen'")
    parser.add_argument("--model", default=default_model_path, help="Path to T5 model")
    parser.add_argument("--libclang", help="Path to libclang shared library (libclang.dll)")
    parser.add_argument("--batch", action="store_true", help="Run 10 sample prompts instead of interactive mode")
    args = parser.parse_args()

    if not llvm_local_path:
        raise ValueError("❌ LOCAL_LLVM_PATH not set in .env")

    # Setup Clang
    set_libclang(args.libclang)
    initialize_clang(args.libclang)

    # Load model
    tok, mdl, device = load_model(args.model)

    if args.batch:
        batch_test(tok, mdl, device)
        return

    if args.prompt:
        feature_prompt = args.prompt.strip()
    else:
        feature_prompt = input("📝 Enter feature prompt (e.g. 'taskwait codegen'): ").strip()

    # --- Hybrid: Try rules first, then model ---
    rule_files, used_rule, matched_keywords = rule_based_lookup(feature_prompt)
    if used_rule:
        print(f"\n🔎 Used RULES for keywords: {', '.join(matched_keywords)}")
        files = []
        full_funcs = rule_files
    else:
        out = suggest(tok, mdl, device, feature_prompt)
        files, full_funcs = parse_model_output(out)
        print("\n🤖 Used MODEL prediction")

    print("\n🔮 Predicted Files:")
    # If using rules, extract file part from file::func
    if used_rule:
        file_set = sorted(set(f.split('::')[0] for f in full_funcs))
        for f in file_set:
            print(f"  • {f}")
    else:
        for f in files:
            print(f"  • {f}")

    print("\n🔧 Predicted Functions:")
    for ff in full_funcs:
        print(f"  • {ff}")

    # For AST, always extract file list from full_funcs
    ast_files = sorted(set(f.split('::')[0] for f in full_funcs))
    ast_map = extract_and_match_functions(llvm_local_path, ast_files, full_funcs)

    print("\n🧩 AST Match Results:")
    for file in ast_files:
        print(f"\n📄 {file}:")
        for func in ast_map.get(file, []):
            flag = "✅" if f"{file}::{func['name']}" in full_funcs else "  "
            print(f"  {flag} {func['name']} @ line {func['line']}")

if __name__ == "__main__":
    main()
