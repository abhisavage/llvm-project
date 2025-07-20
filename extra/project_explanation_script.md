# GenAI-Powered OpenMP Feature Impact Recommender - Complete Project Explanation

## Project Overview
This project builds an intelligent tool that predicts which files and functions in the LLVM codebase are impacted when implementing OpenMP features. It combines historical data analysis, machine learning, and static code analysis to provide accurate recommendations.

## Complete Workflow: From Data to Deployment

### Phase 1: Data Extraction and Preparation

#### 1.1 Data Sources (`all_openmp_prs2.jsonl`)
- **Purpose**: Raw repository of OpenMP pull requests from LLVM
- **Content**: PR metadata, commit messages, file changes, feature descriptions
- **Format**: JSONL with PR numbers, URLs, titles, bodies, and file change information
- **Size**: 3.1MB containing comprehensive OpenMP PR history

#### 1.2 Data Processing (`extract6.py`)
- **Purpose**: Extracts meaningful feature-to-code mappings from raw PR data
- **Process**: 
  - Parses PR titles and commit messages for OpenMP feature keywords
  - Identifies changed files and functions in each PR
  - Maps feature descriptions to specific code locations
  - Filters for relevant OpenMP-related changes
- **Output**: Structured mappings between feature descriptions and file/function pairs

#### 1.3 Data Preprocessing (`preprocessing.py`)
- **Purpose**: Converts extracted data into training-ready format
- **Process**:
  - Cleans and normalizes feature descriptions
  - Formats file/function pairs consistently
  - Splits data into training and validation sets
  - Creates JSONL format with 'input' (feature prompt) and 'output' (file::function list)
- **Output**: `omp_train2.jsonl` and `omp_val2.jsonl`

### Phase 2: Model Training and Development

#### 2.1 Training Data Structure
- **Input Format**: Feature prompts like "taskwait codegen", "atomic flush", "parallel parse"
- **Output Format**: Comma-separated file::function pairs
- **Example**: `{"input": "codegen flush", "output": "llvm/lib/CodeGen/CodeGenFunction.cpp::EmitOMPTaskwaitDirective, flang/lib/Optimizer/CodeGen/Target.cpp::getSizeAndAlignment"}`

#### 2.2 Model Training (Google Colab)
- **Framework**: HuggingFace Transformers
- **Model**: T5-small (Text-to-Text Transfer Transformer)
- **Process**:
  - Tokenizes input prompts and output file/function lists
  - Trains for 5 epochs with learning rate 5e-4
  - Uses beam search for generation
  - Saves model to `omp_t5_model2/` directory
- **Output**: Fine-tuned T5 model for feature-to-code mapping

#### 2.3 Rule Generation (`rules.py`)
- **Purpose**: Creates deterministic mappings for high-confidence patterns
- **Process**: Analyzes training data to identify common keyword-to-file mappings
- **Content**: Dictionary mapping keywords like "codegen", "parse", "runtime" to specific file::function pairs
- **Example**: `"codegen": ["llvm/lib/CodeGen/CodeGenFunction.cpp::EmitOMPTaskwaitDirective", ...]`

### Phase 3: Core System Components

#### 3.1 AST Analyzer (`ast_analyzer.py`)
- **Purpose**: Performs static code analysis using Clang
- **Process**:
  - Initializes Clang with libclang library
  - Parses C++ files to extract function declarations, methods, classes
  - Matches predicted function names against actual code
  - Returns line numbers and function details
- **Key Functions**:
  - `initialize_clang()`: Sets up Clang environment
  - `extract_and_match_functions()`: Main analysis function
- **Output**: Function names, line numbers, and code locations

#### 3.2 CLI Tool (`cli_tool.py`)
- **Purpose**: Main user interface and orchestration component
- **Process**:
  - Loads environment variables (LLVM path, model path)
  - Initializes Clang and loads trained model
  - Processes user input through hybrid system
  - Coordinates between rules, model, and AST analysis
- **Key Functions**:
  - `rule_based_lookup()`: Checks keyword mappings
  - `suggest()`: Uses T5 model for predictions
  - `parse_model_output()`: Extracts file/function pairs from model output
  - `main()`: Orchestrates the entire workflow

### Phase 4: Hybrid Recommendation System

#### 4.1 Rule-Based Lookup
- **Process**:
  - Splits user prompt into keywords
  - Checks each keyword against `keyword_map` in `rules.py`
  - If matches found, returns pre-defined file/function mappings
  - Provides fast, deterministic results for common patterns
- **Example**: "taskwait codegen" → finds "codegen" keyword → returns codegen-related files

#### 4.2 GenAI Model Fallback
- **Process**:
  - If no rule matches, uses trained T5 model
  - Tokenizes input prompt
  - Generates file/function predictions using beam search
  - Decodes output to get comma-separated file::function pairs
- **Example**: "atomic flush masked" → model predicts relevant files/functions

#### 4.3 AST Verification
- **Process**:
  - Takes predicted file::function pairs
  - Uses Clang to parse each file
  - Matches function names against actual code
  - Extracts line numbers and function details
  - Validates predictions against real codebase

### Phase 5: User Experience Flow

#### 5.1 Input Processing
- **User Input**: Feature prompt (e.g., "taskwait codegen")
- **System Response**: 
  - Checks rules first (fast path)
  - Falls back to model if needed
  - Shows which method was used (rules vs model)

#### 5.2 Output Generation
- **File List**: Extracts unique file paths from predictions
- **Function List**: Shows all predicted file::function pairs
- **AST Results**: Displays actual line numbers and function details
- **Format**: Clean, organized output with emojis and clear structure

### Phase 6: Technical Architecture

#### 6.1 Dependencies (`requirements.txt`)
- **Core**: transformers, torch, clang, python-dotenv
- **Data**: datasets, sentencepiece
- **Utilities**: pathlib, argparse

#### 6.2 Environment Setup (`.env`)
- **LOCAL_LLVM_PATH**: Path to LLVM codebase
- **GITHUB_TOKEN**: For API access (if needed)
- **Model Path**: Location of trained T5 model

#### 6.3 Packaging (`setup.py`)
- **Purpose**: Makes tool installable as Python package
- **Configuration**: Defines package metadata and dependencies
- **Installation**: `pip install -e .` for development

### Phase 7: Complete User Workflow Example

#### 7.1 User Command
```bash
omp_impact "taskwait codegen"
```

#### 7.2 System Processing
1. **Environment Check**: Loads LLVM path and model
2. **Input Analysis**: Splits "taskwait codegen" into keywords
3. **Rule Check**: Finds "codegen" in keyword_map
4. **Rule Match**: Returns pre-defined codegen-related files
5. **AST Analysis**: Uses Clang to find actual line numbers
6. **Output Display**: Shows files, functions, and line numbers

#### 7.3 Sample Output
```
🔎 Used RULES for keywords: codegen

🔮 Predicted Files:
  • flang/lib/Optimizer/CodeGen/Target.cpp
  • llvm/lib/CodeGen/CodeGenFunction.cpp

🔧 Predicted Functions:
  • flang/lib/Optimizer/CodeGen/Target.cpp::getSizeAndAlignment
  • llvm/lib/CodeGen/CodeGenFunction.cpp::EmitOMPTaskwaitDirective

🧩 AST Match Results:
📄 flang/lib/Optimizer/CodeGen/Target.cpp:
  ✅ getSizeAndAlignment @ line 508
```

### Phase 8: Key Innovations

#### 8.1 Hybrid Approach
- **Rule-Based**: Fast, deterministic for common patterns
- **GenAI**: Flexible, learns from historical data
- **Combination**: Best of both worlds

#### 8.2 AST Integration
- **Grounding**: Maps predictions to actual code
- **Validation**: Ensures predictions are real
- **Precision**: Provides exact line numbers

#### 8.3 Developer-Friendly
- **CLI Interface**: Easy to use command-line tool
- **Clear Output**: Organized, readable results
- **Fast Response**: Quick recommendations

### Phase 9: Technical Challenges and Solutions

#### 9.1 Data Quality
- **Challenge**: Raw PR data is noisy and inconsistent
- **Solution**: Careful preprocessing and filtering

#### 9.2 Model Accuracy
- **Challenge**: Complex feature-to-code mappings
- **Solution**: Fine-tuned T5 model with beam search

#### 9.3 Code Parsing
- **Challenge**: C++ code is complex to parse
- **Solution**: Clang AST for robust parsing

#### 9.4 Performance
- **Challenge**: Need fast response times
- **Solution**: Rule-based lookup for common cases

### Phase 10: Future Enhancements

#### 10.1 Model Improvements
- Larger training dataset
- Better model architecture
- More sophisticated prompting

#### 10.2 Code Analysis
- Support for more C++ constructs
- Compilation database integration
- Cross-file dependency analysis

#### 10.3 User Experience
- Web interface
- IDE integration
- Real-time suggestions

## Summary
This project successfully combines historical data analysis, machine learning, and static code analysis to create an intelligent tool that helps developers quickly identify code areas impacted by OpenMP feature changes. The hybrid approach ensures both speed and accuracy, while the AST integration provides grounding in actual code. 