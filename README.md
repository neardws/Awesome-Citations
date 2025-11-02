# Awesome Citations

**Awesome Citations** is a comprehensive Python-based BibTeX bibliography management toolkit that automates the entire citation workflow. From completing incomplete entries by fetching from official sources (IEEE, ACM, arXiv, CrossRef, Semantic Scholar), to standardizing formatting, replacing arXiv preprints with published versions, and generating formatted PDF bibliographies - all in a single command.

Perfect for managing bibliographies for academic papers, theses, and research projects with support for multiple citation styles and bilingual (English/Chinese) journals.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Complete Workflow (Recommended)](#-complete-workflow-recommended)
  - [Individual Tools](#individual-tools)
- [Configuration](#configuration)
- [Data Sources](#data-sources)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Testing](#testing)
- [License](#license)

## Features

### Core Capabilities

- **🚀 Complete Workflow Automation** - One-stop BibTeX processing pipeline in a single command
  - Sort and deduplicate entries by ID
  - Complete missing fields from multiple sources
  - Standardize formatting across all entries
  - Replace arXiv preprints with published versions
  - Generate detailed change logs
  - Create formatted PDF bibliographies

- **📚 Multi-Source BibTeX Completion** - Fetch missing fields from 5 official sources:
  - **IEEE Xplore** - Primary source for IEEE publications (with Selenium fallback)
  - **ACM Digital Library** - For ACM publications
  - **arXiv API** - For preprints and arXiv papers
  - **CrossRef** - Universal fallback for any DOI
  - **Semantic Scholar** - For published versions of arXiv papers
  - Intelligent fallback chains ensure maximum success rate

- **🔄 Smart arXiv Preprint Replacement**
  - Automatically detects arXiv preprints in your bibliography
  - Searches for published versions using Semantic Scholar, DBLP, and CrossRef APIs
  - Replaces preprint entries with complete journal/conference publication data
  - Preserves original entry IDs for reference consistency

- **✨ Comprehensive Field Standardization**
  - **Title formatting**: Title Case, Sentence case, with protected acronyms (IoT, WiFi, etc.)
  - **Author formatting**: First-last or Last-first name ordering
  - **Journal normalization**: Full names, abbreviations, or preserve both (50+ journal mappings)
  - **Page formatting**: LaTeX double-dash (100--110) or single-dash (100-110)

- **📊 PDF Bibliography Generation**
  - Support for 4 citation styles: IEEE, ACM, APA, GB/T 7714 (Chinese standard)
  - Customizable templates for each style
  - Automatic LaTeX compilation with biber
  - Configurable document title, font size, paper size

- **📝 Detailed Change Tracking**
  - Every modification is logged with before/after values
  - Source attribution (which API provided the data)
  - Markdown-formatted change reports
  - Summary statistics (entries processed, fields added, errors)

- **🔍 Analysis Tools**
  - Analyze bibliography by reference types (article, inproceedings, etc.)
  - Publication year distribution (sorted newest first)
  - Publication venue frequency (sorted by count)
  - Formatted table output

- **🌏 Bilingual Support**
  - English and Chinese journal name mappings
  - Chinese journal metadata database
  - GB/T 7714 citation style for Chinese standards
  - Bilingual document titles support

- **🛡️ Robust Error Handling**
  - DOI validation via HEAD requests to doi.org
  - Title similarity checks (60% word overlap required)
  - Year consistency validation (±1 year tolerance)
  - Failed DOI tracking in `/data/failed_dois.json`
  - Manual DOI correction database support
  - Rate limiting to respect API limits (configurable delays)

## Installation

### Prerequisites

- **Python 3.8+** (tested on Python 3.12)
- **uv** - Modern Python package manager (recommended) or pip
- **LaTeX distribution** (optional, required for PDF generation)
  - macOS: `brew install --cask mactex`
  - Ubuntu/Debian: `sudo apt-get install texlive-full`
  - Windows: Install [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)

### Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Install Python Dependencies

**Method 1: Using uv (Recommended - Fast & Modern)**

```bash
# Install all dependencies
uv pip install -r requirements.txt

# Or create and activate a virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

**Method 2: Using pip (Traditional)**

```bash
pip install -r requirements.txt
```

**Method 3: Manual installation with uv**

```bash
uv pip install bibtexparser tabulate requests beautifulsoup4 lxml pyyaml habanero scholarly
```

**Optional dependencies for enhanced features:**

```bash
# For IEEE Selenium fallback (if API fails)
uv pip install selenium webdriver-manager

# For testing and development
uv pip install pytest pytest-cov pytest-timeout pytest-mock
```

### Verify Installation

```bash
# Test the complete workflow
uv run python scripts/workflow_complete.py examples/sample_input.bib --output output/test_result.bib

# Or if using activated virtual environment
python3 scripts/workflow_complete.py examples/sample_input.bib --output output/test_result.bib

# Check if LaTeX is installed (for PDF generation)
pdflatex --version
biber --version
```

## Quick Start

**Process your BibTeX file in one command:**

```bash
# Using uv (recommended)
uv run python scripts/workflow_complete.py refs.bib

# Or with activated virtual environment
python3 scripts/workflow_complete.py refs.bib
```

This will create:
- `refs_completed.bib` - Your processed bibliography
- `refs_completed_changes.md` - Detailed change log
- `refs_completed.pdf` - Formatted PDF (if LaTeX is installed)

**With custom configuration:**

```bash
uv run python scripts/workflow_complete.py refs.bib --output output/my_refs.bib --config config.json
```

## Usage

### 🚀 Complete Workflow (Recommended)

The **workflow_complete.py** script orchestrates the entire BibTeX processing pipeline in a single command. This is the recommended way to use Awesome Citations.

**Basic usage:**

```bash
# Using uv (recommended - handles dependencies automatically)
uv run python scripts/workflow_complete.py input.bib

# Or with activated virtual environment
python3 scripts/workflow_complete.py input.bib
```

**What it does** (7 automated steps):

1. ✅ **Sort and deduplicate** entries by ID
2. ✅ **Complete missing fields** from multiple sources (IEEE/ACM/arXiv/CrossRef/Semantic Scholar)
3. ✅ **Standardize formatting** (titles, authors, journals, pages)
4. ✅ **Replace arXiv preprints** with published versions
5. ✅ **Write output file** with all changes
6. ✅ **Generate change summary** (Markdown report with statistics)
7. ✅ **Generate PDF bibliography** (IEEE style by default)

**Output files:**
- `input_completed.bib` - Processed BibTeX file
- `input_completed_changes.md` - Detailed change log
- `input_completed.pdf` - Formatted PDF (if LaTeX is installed)

**Custom output path:**
```bash
uv run python scripts/workflow_complete.py refs.bib --output output/completed.bib --config config.json
```

**Process multiple files:**
```bash
# Process all .bib files in a directory
for file in *.bib; do
    uv run python scripts/workflow_complete.py "$file"
done
```

**Key features:**
- Progress tracking with detailed console output
- Error handling with fallback chains
- Rate limiting (1.0s delay between requests by default)
- Preserves original entry IDs
- Logs all failures for manual review

📖 **For detailed documentation, see [docs/WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md)**

---

### Individual Tools

For specific tasks, you can use individual scripts. Each script focuses on a single aspect of bibliography management.

#### 1. Complete BibTeX Entries

Complete incomplete BibTeX entries by automatically fetching missing information from official sources using DOI.

**File:** `scripts/complete_bibtex.py`

**Usage:**
```bash
uv run python scripts/complete_bibtex.py
```

Edit the script to set input and output file paths, or modify to accept command-line arguments.

**Features:**
- Extracts DOI from entry fields (doi, url, note) or URLs
- Validates DOI existence via HEAD request to doi.org
- Identifies publisher from DOI prefix (10.1109 = IEEE, 10.1145 = ACM, etc.)
- Fetches from appropriate source with intelligent fallback chain:
  - IEEE Xplore → Selenium fallback → CrossRef → Google Scholar
  - ACM Digital Library → CrossRef → Google Scholar
  - arXiv API → CrossRef → Google Scholar
- Validates fetched data (title similarity, year consistency, DOI match)
- Logs failed attempts to `/data/failed_dois.json`
- Respects rate limits (0.5s default delay)

**Note:** This feature uses web scraping and may be affected by website changes.

#### 2. Format BibTeX Fields

Standardize field formatting across all entries according to your preferences.

**File:** `scripts/format_bibtex.py`

**Usage:**
```bash
uv run python scripts/format_bibtex.py input.bib output.bib config.json
```

**Formatting options:**

- **Title formatting:**
  - `titlecase`: "A Survey on Machine Learning Techniques"
  - `sentencecase`: "A survey on machine learning techniques"
  - Protects acronyms: "{IoT}-Based {WiFi} System"

- **Author formatting:**
  - `first_last`: "John Smith and Jane Doe"
  - `last_first`: "Smith, John and Doe, Jane"

- **Journal formatting:**
  - `abbreviation`: "IEEE Trans. Pattern Anal. Mach. Intell."
  - `full`: "IEEE Transactions on Pattern Analysis and Machine Intelligence"
  - `both`: Keep original format

- **Page formatting:**
  - `double_dash`: "100--110" (LaTeX format)
  - `single_dash`: "100-110"

#### 3. Sort BibTeX File

Sort entries alphabetically by their citation keys (entry IDs).

**File:** `scripts/sort_bibtex.py`

**Usage:**
```bash
uv run python scripts/sort_bibtex.py
```

Edit the script to set input and output file paths.

**Features:**
- Alphabetical sorting by entry ID
- Preserves entry formatting
- Removes duplicate entries with the same ID

#### 4. Analyze BibTeX File

Generate statistical analysis and tables for your bibliography.

**File:** `scripts/analyze_bibtex.py`

**Usage:**
```bash
uv run python scripts/analyze_bibtex.py
```

Edit the script to set the input file path.

**Outputs three formatted tables:**

1. **Reference Types** (article, inproceedings, book, etc.)
   ```
   Type            Count
   -------------  -------
   article             45
   inproceedings       32
   book                 8
   ```

2. **Publication Years** (sorted newest first)
   ```
   Year    Count
   ------  -------
   2024         15
   2023         28
   2022         22
   ```

3. **Publication Venues** (sorted by frequency)
   ```
   Publication                                    Count
   -------------------------------------------  -------
   IEEE Transactions on Neural Networks            12
   ACM Computing Surveys                             8
   Nature Machine Intelligence                       5
   ```

#### 5. Generate PDF Bibliography

Create a formatted PDF bibliography using LaTeX templates.

**File:** `scripts/generate_pdf.py`

**Usage:**
```bash
uv run python scripts/generate_pdf.py input.bib output.pdf ieee config.json
```

**Supported citation styles:**
- `ieee` - IEEE numeric citations (default)
- `acm` - ACM author-year citations
- `apa` - APA psychology standard
- `gb7714` - Chinese GB/T 7714 standard

**Requirements:**
- LaTeX distribution (pdflatex + biber)
- Templates in `/templates/` directory

**Customization options** (via config.json):
```json
{
  "pdf_output": {
    "enabled": true,
    "document_title": "参考文献列表 / References",
    "sort_by": "author",          // or "year", "title"
    "font_size": "11pt",           // or "10pt", "12pt"
    "paper_size": "a4paper"        // or "letterpaper"
  }
}
```

#### 6. Replace arXiv Preprints

Detect arXiv preprints and replace them with published versions.

**File:** `utils/arxiv_detector.py`

**Usage:**
```python
from utils.arxiv_detector import detect_and_replace_arxiv

# Automatically called in workflow_complete.py
entries_updated = detect_and_replace_arxiv(bib_database)
```

**Detection methods:**
- Checks `journal` field for "arXiv"
- Checks `eprint` field for arXiv ID
- Checks DOI for arXiv format (10.48550/arXiv.*)

**Search strategy:**
1. Semantic Scholar API (most reliable for arXiv papers)
2. DBLP API (excellent for CS papers)
3. CrossRef API (comprehensive coverage)

**Filters:**
- Only replaces with journal or conference publications
- Ignores other preprints
- Preserves original entry ID

## Configuration

Awesome Citations uses a JSON configuration file to control all aspects of the processing workflow. The default configuration is in `config.json`.

### Configuration File Structure

```json
{
  "citation_style": "ieee",
  "custom_biblatex_style": null,
  "title_format": "titlecase",
  "journal_format": "both",
  "author_format": "first_last",
  "page_format": "double_dash",
  "arxiv_handling": "replace_with_published",
  "data_source_priority": ["doi_official", "dblp", "crossref"],
  "merge_multiple_sources": true,
  "parallel_processing": true,
  "max_workers": 5,
  "request_delay": 1.0,
  "pdf_output": {
    "enabled": true,
    "document_title": "参考文献列表 / References",
    "sort_by": "author",
    "font_size": "11pt",
    "paper_size": "a4paper"
  },
  "logging": {
    "enabled": true,
    "output_file": "changes_log.md",
    "verbose": true
  }
}
```

### Configuration Options Explained

#### General Settings

- **`citation_style`** (string): PDF citation style
  - Options: `"ieee"`, `"acm"`, `"apa"`, `"gb7714"`
  - Default: `"ieee"`

- **`custom_biblatex_style`** (string or null): Custom biblatex style file path
  - Use if you have a custom .bbx/.cbx file
  - Default: `null`

#### Formatting Options

- **`title_format`** (string): How to format entry titles
  - `"titlecase"`: "A Survey on Machine Learning" (capitalize major words)
  - `"sentencecase"`: "A survey on machine learning" (only first word)
  - `"preserve"`: Keep original formatting
  - Default: `"titlecase"`

- **`journal_format`** (string): Journal name formatting
  - `"abbreviation"`: "IEEE Trans. Pattern Anal." (abbreviated)
  - `"full"`: "IEEE Transactions on Pattern Analysis..." (full name)
  - `"both"`: Preserve original format
  - Default: `"both"`

- **`author_format`** (string): Author name ordering
  - `"first_last"`: "John Smith and Jane Doe"
  - `"last_first"`: "Smith, John and Doe, Jane"
  - Default: `"first_last"`

- **`page_format`** (string): Page number dash style
  - `"double_dash"`: "100--110" (LaTeX standard)
  - `"single_dash"`: "100-110"
  - Default: `"double_dash"`

#### Data Fetching Options

- **`arxiv_handling`** (string): How to handle arXiv preprints
  - `"replace_with_published"`: Auto-replace with published versions
  - `"keep"`: Preserve arXiv entries as-is
  - Default: `"replace_with_published"`

- **`data_source_priority`** (array): Order of data sources to try
  - Options: `"doi_official"` (IEEE/ACM/arXiv), `"dblp"`, `"crossref"`, `"google_scholar"`
  - Default: `["doi_official", "dblp", "crossref"]`
  - First successful source is used (unless merge_multiple_sources is true)

- **`merge_multiple_sources`** (boolean): Merge data from multiple sources
  - `true`: Fetch from all sources and intelligently merge fields
  - `false`: Use only first successful source
  - Default: `true`

#### Performance Options

- **`parallel_processing`** (boolean): Enable concurrent processing
  - `true`: Process multiple entries simultaneously (faster)
  - `false`: Process sequentially (safer for debugging)
  - Default: `true`

- **`max_workers`** (integer): Number of concurrent worker threads
  - Range: 1-10 (recommended: 3-5)
  - Default: `5`
  - Only applies if parallel_processing is true

- **`request_delay`** (float): Delay between API requests (seconds)
  - Prevents rate limiting from APIs
  - Range: 0.2-5.0 seconds
  - Default: `1.0`
  - Recommended: 0.5 for personal use, 1.0+ for large batches

#### PDF Output Settings

- **`pdf_output.enabled`** (boolean): Generate PDF bibliography
  - Default: `true`

- **`pdf_output.document_title`** (string): Title on PDF document
  - Default: `"参考文献列表 / References"` (bilingual)

- **`pdf_output.sort_by`** (string): Bibliography sorting order
  - Options: `"author"`, `"year"`, `"title"`, `"id"`
  - Default: `"author"`

- **`pdf_output.font_size`** (string): Document font size
  - Options: `"10pt"`, `"11pt"`, `"12pt"`
  - Default: `"11pt"`

- **`pdf_output.paper_size`** (string): Paper size
  - Options: `"a4paper"`, `"letterpaper"`, `"a5paper"`
  - Default: `"a4paper"`

#### Logging Settings

- **`logging.enabled`** (boolean): Enable change logging
  - Default: `true`

- **`logging.output_file`** (string): Change log filename
  - Default: `"changes_log.md"`

- **`logging.verbose`** (boolean): Include detailed logs
  - `true`: Log every field change
  - `false`: Only log summary statistics
  - Default: `true`

### Example Configurations

**Minimal processing (fast, conservative):**
```json
{
  "title_format": "preserve",
  "journal_format": "both",
  "arxiv_handling": "keep",
  "merge_multiple_sources": false,
  "parallel_processing": true,
  "max_workers": 10,
  "request_delay": 0.5
}
```

**Maximum quality (slow, comprehensive):**
```json
{
  "title_format": "titlecase",
  "journal_format": "full",
  "arxiv_handling": "replace_with_published",
  "merge_multiple_sources": true,
  "parallel_processing": false,
  "request_delay": 2.0,
  "logging": {
    "verbose": true
  }
}
```

**Chinese academic papers:**
```json
{
  "citation_style": "gb7714",
  "title_format": "preserve",
  "journal_format": "full",
  "pdf_output": {
    "document_title": "参考文献列表",
    "paper_size": "a4paper",
    "font_size": "12pt"
  }
}
```

## Data Sources

Awesome Citations fetches bibliographic data from multiple authoritative sources:

### Primary Sources (Publisher APIs)

1. **IEEE Xplore** - For IEEE publications (DOI: 10.1109/*)
   - Primary: POST API to `/xpl/downloadCitations`
   - Fallback: Selenium browser automation
   - Coverage: IEEE journals, conferences, standards

2. **ACM Digital Library** - For ACM publications (DOI: 10.1145/*)
   - Web scraping from `/doi/{doi}/bibtex`
   - Coverage: ACM journals, conferences, magazines

3. **arXiv API** - For preprints (DOI: 10.48550/arXiv.*)
   - Official arXiv public API
   - Coverage: All arXiv papers

### Fallback Sources

4. **CrossRef API** - Universal DOI resolver
   - REST API for any DOI
   - Coverage: 130+ million records across all publishers
   - Very reliable for basic metadata

5. **Semantic Scholar API** - Academic search engine
   - Best for finding published versions of arXiv papers
   - Provides publication venue information
   - Coverage: 200+ million papers

6. **DBLP API** - Computer Science bibliography
   - Excellent for CS conference and journal papers
   - Provides canonical venue names
   - Coverage: 5+ million CS publications

7. **Google Scholar** - Final fallback (title-based search)
   - Used when DOI lookup fails
   - Searches by title
   - Rate-limited, used sparingly

### Fallback Strategy

Each entry follows an intelligent fallback chain:

```
1. Extract DOI from entry
   ↓
2. Validate DOI exists (HEAD request to doi.org)
   ↓
3. Identify publisher from DOI prefix
   ↓
4. Try primary source (IEEE/ACM/arXiv API)
   ↓
5. If fails → Try CrossRef
   ↓
6. If fails → Try Google Scholar
   ↓
7. If fails → Log to failed_dois.json
```

For arXiv papers specifically:
```
1. Check if entry is arXiv preprint
   ↓
2. Try Semantic Scholar API (find published version)
   ↓
3. If found → Fetch complete BibTeX from new DOI
   ↓
4. If not found → Try DBLP API
   ↓
5. If not found → Try CrossRef API
   ↓
6. If no published version → Keep arXiv entry
```

### Data Validation

All fetched data undergoes validation:

- **Title similarity**: At least 60% word overlap with original title
- **Year consistency**: Within ±1 year of original (if present)
- **DOI match**: Exact match with expected DOI
- **Field completeness**: Must have at minimum: title, author, year

Failed validations are logged and the entry is skipped.

### Manual Corrections

For persistent DOI fetch failures, you can add manual corrections to `/data/doi_corrections.json`:

```json
{
  "10.1109/EXAMPLE.2024.1234567": {
    "title": "Correct Title",
    "author": "Smith, John and Doe, Jane",
    "journal": "IEEE Transactions on Example",
    "year": "2024",
    "volume": "15",
    "number": "3",
    "pages": "100--110",
    "doi": "10.1109/EXAMPLE.2024.1234567"
  }
}
```

These corrections are checked before attempting API fetches.

## Project Structure

```
Awesome-Citations/
├── README.md                   # This file
├── LICENSE                     # GNU GPL v3.0
├── requirements.txt            # Python dependencies
├── config.json                 # Default configuration
├── refs.bib                    # Example BibTeX file
│
├── scripts/                    # Main executable scripts
│   ├── workflow_complete.py   # 🚀 Complete workflow (recommended)
│   ├── complete_bibtex.py     # BibTeX completion from APIs
│   ├── format_bibtex.py       # Field standardization
│   ├── sort_bibtex.py         # Alphabetical sorting
│   ├── analyze_bibtex.py      # Statistical analysis
│   ├── generate_pdf.py        # PDF generation
│   ├── utilities.py           # Core utility functions
│   └── enhanced_complete.py   # Enhanced multi-source completion
│
├── utils/                      # Utility modules
│   ├── change_logger.py       # Change tracking and logging
│   ├── arxiv_detector.py      # arXiv preprint detection
│   ├── title_formatter.py     # Title formatting utilities
│   └── multi_source_merger.py # Multi-source data merging
│
├── data/                       # Data files and databases
│   ├── journal_abbr.json      # Journal abbreviation mappings (50+)
│   ├── protected_words.json   # Acronyms to protect in titles
│   ├── small_words.json       # Articles/prepositions for Title Case
│   ├── chinese_journals.json  # Chinese journal metadata
│   ├── doi_corrections.json   # Manual DOI corrections
│   └── failed_dois.json       # Failed DOI fetch log (auto-generated)
│
├── templates/                  # LaTeX templates for PDF generation
│   ├── ieee_template.tex      # IEEE citation style
│   ├── acm_template.tex       # ACM citation style
│   ├── apa_template.tex       # APA citation style
│   └── gb7714_template.tex    # Chinese GB/T 7714 standard
│
├── docs/                       # Documentation (16 files)
│   ├── WORKFLOW_GUIDE.md      # Complete workflow documentation
│   ├── USAGE_GUIDE.md         # Detailed usage instructions
│   ├── TEST_REPORT.md         # Testing results and coverage
│   ├── IEEE_FAILURE_ANALYSIS.md # IEEE API troubleshooting
│   └── ...                    # Implementation and optimization docs
│
├── examples/                   # Example files
│   ├── sample_input.bib       # Sample BibTeX entries
│   └── sample_config.json     # Example configuration
│
├── tests/                      # Comprehensive test suite (2,579 lines)
│   ├── conftest.py            # Pytest fixtures and configuration
│   ├── test_complete_bibtex.py # BibTeX completion tests (1,057 lines)
│   ├── test_format_bibtex.py  # Formatting tests (485 lines)
│   ├── test_ieee_integration.py # IEEE-specific tests (401 lines)
│   ├── test_integration.py    # End-to-end workflow tests (171 lines)
│   ├── test_utils.py          # Utility function tests (161 lines)
│   └── test_data/             # Test BibTeX files (14+ files)
│       ├── ieee_papers.bib
│       ├── acm_papers.bib
│       ├── arxiv_papers.bib
│       ├── mixed_entries.bib
│       └── ...
│
├── research/                   # Research and exploration scripts
│   └── ieee_api_research.py   # IEEE API endpoint exploration
│
├── output/                     # Generated outputs (auto-created)
│   ├── *.bib                  # Processed BibTeX files
│   ├── *_changes.md           # Change logs
│   └── *.pdf                  # Generated PDFs
│
└── .cache/                     # API response cache (auto-created)
    └── *.json                 # Cached responses (30-day expiry)
```

### Key Directories Explained

- **`scripts/`** - All main executable scripts. Start here for any task.
- **`utils/`** - Reusable Python modules imported by scripts.
- **`data/`** - JSON databases for journal names, acronyms, corrections, and failure logs.
- **`templates/`** - LaTeX templates for generating PDFs in different citation styles.
- **`docs/`** - Comprehensive documentation covering implementation, testing, and usage.
- **`examples/`** - Sample files to test the tool and learn usage patterns.
- **`tests/`** - Full test suite with fixtures, test data, and comprehensive coverage.
- **`output/`** - Auto-created directory for all generated files.
- **`.cache/`** - Auto-created cache for API responses to reduce redundant requests.

## Documentation

Comprehensive documentation is available in the `/docs` directory:

### User Documentation

- **[WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md)** - Complete workflow documentation
  - Step-by-step walkthrough of the complete workflow
  - Configuration options explained
  - Troubleshooting common issues

- **[USAGE_GUIDE.md](docs/USAGE_GUIDE.md)** - Detailed usage instructions
  - Individual script usage examples
  - Advanced configuration scenarios
  - Best practices for different use cases

### Developer Documentation

- **[IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** - Implementation details
  - Architecture overview
  - Core algorithms and data flows
  - API integration details

- **[TEST_REPORT.md](docs/TEST_REPORT.md)** - Testing results and coverage
  - Test suite overview
  - Coverage statistics
  - Known issues and limitations

- **[IEEE_FAILURE_ANALYSIS.md](docs/IEEE_FAILURE_ANALYSIS.md)** - IEEE API troubleshooting
  - Common IEEE API errors
  - Selenium fallback strategies
  - Debugging tips

### Project History

- **COMPLETION_SUMMARY.md** - BibTeX completion feature development
- **OPTIMIZATION_RESULTS.md** - Performance optimization results
- **FILE_REORGANIZATION_SUMMARY.md** - Project restructuring notes
- **WORKFLOW_IMPLEMENTATION_SUMMARY.md** - Complete workflow development

All documentation files are in Markdown format and contain detailed explanations with code examples.

## Testing

Awesome Citations includes a comprehensive test suite to ensure reliability and correctness.

### Test Suite Overview

- **Total test code**: 2,579 lines
- **Test files**: 6 main test files
- **Test data**: 14+ specialized BibTeX files
- **Framework**: pytest with coverage, timeout, and mock support

### Running Tests

**Run all tests:**
```bash
pytest tests/
```

**Run with coverage report:**
```bash
pytest --cov=scripts --cov=utils --cov-report=html tests/
```

**Run specific test file:**
```bash
pytest tests/test_complete_bibtex.py -v
```

**Run tests matching a pattern:**
```bash
pytest tests/ -k "test_ieee" -v
```

### Test Categories

1. **Unit Tests** (`test_utils.py`)
   - Core utility functions
   - Deduplication logic
   - Sorting algorithms

2. **BibTeX Completion Tests** (`test_complete_bibtex.py`)
   - DOI extraction and validation
   - Publisher identification
   - API fetching and fallback chains
   - Data validation
   - Error handling

3. **Formatting Tests** (`test_format_bibtex.py`)
   - Title formatting (Title Case, Sentence case)
   - Author name formatting
   - Journal normalization
   - Page formatting

4. **IEEE Integration Tests** (`test_ieee_integration.py`)
   - IEEE API integration
   - Selenium fallback testing
   - Real IEEE DOI fetching
   - Error scenarios

5. **End-to-End Tests** (`test_integration.py`)
   - Complete workflow execution
   - Configuration handling
   - Output file generation
   - Change log creation

### Test Data Files

Located in `/tests/test_data/`:
- `ieee_papers.bib` - IEEE journal and conference papers
- `acm_papers.bib` - ACM publications
- `arxiv_papers.bib` - arXiv preprints
- `crossref_papers.bib` - CrossRef-sourced entries
- `duplicate_entries.bib` - Duplicate detection tests
- `malformed_entries.bib` - Error handling tests
- `mixed_entries.bib` - Mixed publisher entries
- `chinese_journals.bib` - Chinese publications
- And more...

### Continuous Testing

The test suite is designed to:
- Catch regressions early
- Validate API integrations
- Ensure data quality
- Test error handling paths
- Verify configuration options

**For detailed test results, see [docs/TEST_REPORT.md](docs/TEST_REPORT.md)**

## Troubleshooting

### Common Issues

**1. IEEE API fails frequently**
- The IEEE Xplore API can be unstable
- Selenium fallback is automatically used
- See [docs/IEEE_FAILURE_ANALYSIS.md](docs/IEEE_FAILURE_ANALYSIS.md) for details
- Consider increasing `request_delay` in config

**2. LaTeX not found**
- PDF generation requires LaTeX (pdflatex + biber)
- Install TeX Live (Linux), MacTeX (macOS), or MiKTeX (Windows)
- Verify: `pdflatex --version` and `biber --version`

**3. Rate limiting errors**
- Increase `request_delay` in config.json (try 2.0 or higher)
- Reduce `max_workers` (try 3 or less)
- Some APIs have strict rate limits (especially Google Scholar)

**4. Title similarity validation fails**
- Fetched data must match original title (60% word overlap)
- Check if original title is correct in your .bib file
- Add manual correction to `/data/doi_corrections.json`

**5. DOI not found**
- Check `/data/failed_dois.json` for error details
- Verify DOI is correct and exists at https://doi.org/
- Some DOIs may not be indexed by all APIs

**6. Module import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: 3.8+ required (tested on 3.12)

### Getting Help

If you encounter issues not covered here:
1. Check the documentation in `/docs`
2. Review test files for usage examples
3. Check GitHub issues (if applicable)
4. Review error logs in console output and `/data/failed_dois.json`



## Contributing

Contributions are welcome! If you'd like to contribute to Awesome Citations:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the test suite to ensure nothing breaks (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Areas for Contribution

- Adding support for new citation styles
- Improving API reliability and fallback strategies
- Adding new data sources (e.g., Springer, Elsevier APIs)
- Enhancing journal abbreviation database
- Writing additional tests
- Improving documentation
- Fixing bugs and issues

## Acknowledgment

Special thanks to:
- **Claude Code** for providing valuable assistance in the development of this project
- All contributors to the open-source libraries used in this project (bibtexparser, requests, BeautifulSoup, etc.)
- The maintainers of IEEE Xplore, ACM Digital Library, arXiv, CrossRef, Semantic Scholar, and DBLP for their excellent APIs

## License

[GNU General Public License v3.0](LICENSE)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

---

**Built with ❤️ for researchers, academics, and anyone managing BibTeX bibliographies**

For issues, questions, or suggestions, please check the [documentation](docs/) or open an issue on GitHub.