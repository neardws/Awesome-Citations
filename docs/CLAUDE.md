# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Awesome Citations is a Python utility for analyzing and managing BibTeX bibliography files. It provides functionality to sort entries, remove duplicates, complete incomplete entries by fetching from official sources, and generate statistical reports about reference types, publication years, and publication venues.

## Architecture

The project consists of four main Python modules plus enhanced utilities:

1. **complete_bibtex.py** - Validates and completes BibTeX entries with advanced features:
   - `extract_doi()` - Extracts DOI from entry fields or URLs
   - `verify_doi_exists()` - Pre-validates DOI before fetching (HEAD request to DOI.org)
   - `identify_publisher()` - Maps DOI prefix to publisher (IEEE/ACM/arXiv/etc.)
   - `fetch_bibtex_from_ieee()` - Scrapes complete BibTeX from IEEE Xplore (API method)
   - `fetch_bibtex_from_ieee_selenium()` - Selenium-based IEEE scraper (fallback for API failures)
   - `fetch_bibtex_from_acm()` - Scrapes complete BibTeX from ACM Digital Library
   - `fetch_bibtex_from_arxiv()` - Fetches BibTeX from arXiv API
   - `fetch_bibtex_from_crossref()` - Uses CrossRef API as fallback
   - `fetch_bibtex_from_scholar()` - Google Scholar fallback (title-based search)
   - `validate_fetched_bibtex()` - Validates fetched data against original entry
   - `check_completeness()` - Identifies missing important fields
   - `merge_bibtex_entries()` - Merges fetched data into original entry
   - `log_failed_doi()` - Logs failed attempts to data/failed_dois.json
   - `apply_doi_correction()` - Applies manual DOI corrections from database
   - `complete_bibtex_file()` - Main function with interactive mode

2. **utilities.py** - Consolidated module containing all core functionality:
   - `remove_duplicates()` - Deduplicates BibTeX entries by ID
   - `sort_bibtex_file()` - Sorts entries alphabetically by reference ID
   - `analyze_bibtex_file()` - Generates statistics on entry types, years, and venues
   - `print_table()` - Formats and displays analysis results as tables

3. **analyze_bibtex.py** - Standalone script for analyzing a single BibTeX file and displaying statistics

4. **sort_bibtex.py** - Standalone script for sorting a single BibTeX file by reference ID

5. **ieee_api_research.py** - NEW: Research script to explore alternative IEEE API endpoints

### Data Flow

**complete_bibtex.py workflow (Enhanced):**
1. Load BibTeX file and check each entry for completeness
2. Extract DOI from 'doi' field or 'url' field
3. **Apply manual DOI corrections** from data/doi_corrections.json if available
4. **Pre-validate DOI** using HEAD request to DOI.org (HTTP 200/302 = valid)
5. Identify publisher from DOI prefix (10.1109=IEEE, 10.1145=ACM, etc.)
6. Fetch complete BibTeX via **multi-layered fallback chain**:
   - **Publisher-specific API** (IEEE/ACM/arXiv)
   - **IEEE Selenium fallback** (if API fails for IEEE)
   - **CrossRef API fallback** (for any publisher)
   - **Google Scholar fallback** (title-based search if title available)
7. **Validate fetched BibTeX** (title similarity, year consistency, DOI match)
8. Parse and merge fetched data, preserving original entry ID
9. **Log failures** to data/failed_dois.json with detailed error messages
10. Interactive prompts for entries without DOI or failed fetches
11. Adaptive rate limiting (0.2s for cache, 0.5s for new requests, 2s for Scholar)

**utilities.py workflow:**
- Load BibTeX file using bibtexparser with UTF-8 encoding
- Sort entries by ID using `itemgetter('ID')`
- Remove duplicates by converting to dict with ID as key
- Analyze using Counter objects for aggregation
- Output results using tabulate for formatted tables

### BibTeX Parsing

All modules use bibtexparser with:
- `BibTexParser(common_strings=True)` - Recognizes standard BibTeX abbreviations
- `convert_to_unicode` customization - Ensures proper character encoding
- UTF-8 file encoding for international character support

### BibTeX Completion (complete_bibtex.py)

**Enhanced Implementation Details:**

#### DOI Validation & Correction
- **DOI Extraction**: Checks 'doi' field first, then extracts from 'url' field using regex
- **DOI Correction Database**: Checks data/doi_corrections.json for known invalid/corrected DOIs
- **DOI Pre-Validation**: Uses HEAD request to verify DOI exists in DOI.org database
- **DOI Format Validation**: Ensures DOI starts with '10.' and contains '/'

#### Publisher Detection & Fetching
- **Publisher Detection**: Maps DOI prefixes (10.1109→IEEE, 10.1145→ACM, 10.48550→arXiv)
- **Scraping Strategy**:
  - **IEEE**:
    1. POST to /xpl/downloadCitations endpoint with article number (primary)
    2. Selenium browser automation (fallback if API fails)
  - **ACM**: Parse HTML from /doi/{doi}/bibtex page
  - **arXiv**: Use public API (no auth required)
  - **CrossRef**: REST API fallback for any DOI
  - **Google Scholar**: Title-based search as final fallback

#### Error Handling & Diagnostics
- **Enhanced Error Messages**: Include HTTP status codes, failure reasons, and context
- **Failed DOI Logging**: All failures logged to data/failed_dois.json with:
  - DOI, entry ID, publisher, error message, HTTP status, timestamp
- **Error Propagation**: Errors bubble up through fetch chain with detailed messages

#### Validation & Quality Control
- **Multi-Source Validation**: Validates fetched BibTeX against original entry:
  - Title similarity (60% word overlap required)
  - Year consistency (allow 1 year difference)
  - DOI match (normalized comparison)
- **Interactive Prompts**: Option to accept/reject validated data in interactive mode

#### Field Priority & Merging
- **Important Fields**: author, title, year, journal/booktitle, volume, number, pages, publisher, doi
- **Merge Strategy**: Only fills missing fields by default, preserves original entry ID
- **Entry Type Awareness**: Skips journal field for inproceedings, booktitle for articles

#### Rate Limiting & Caching
- **Adaptive Rate Limiting**:
  - 0.2s delay for cached responses
  - 0.5s delay for new API requests
  - 2s delay for Google Scholar (to avoid rate limiting)
- **Caching**: 30-day cache in .cache/ directory
- **Cache Format**: JSON with DOI, BibTeX, and timestamp

#### Interactive Features
- **Manual DOI Input**: Prompts for DOI if not found in entry
- **Validation Overrides**: Option to use data even if validation fails
- **DOI Correction Prompts**: Asks before using corrected/invalid DOIs
- **Progress Tracking**: Shows processing status for each entry

## Common Commands

### Setup
```bash
# Core dependencies
pip install bibtexparser tabulate requests beautifulsoup4 lxml

# Enhanced features
pip install scholarly  # For Google Scholar fallback

# Optional: Selenium for advanced IEEE scraping
pip install selenium webdriver-manager

# All dependencies
pip install -r requirements.txt
```

### Running Scripts
```bash
# Complete incomplete BibTeX entries (edit input_file variable in script first)
python complete_bibtex.py

# Research IEEE API endpoints
python ieee_api_research.py

# Analyze a BibTeX file (edit input_file variable in script first)
python analyze_bibtex.py

# Sort a BibTeX file (edit input/output file variables in script first)
python sort_bibtex.py

# Full workflow: sort, deduplicate, and analyze (edit input_file variable in utilities.py first)
python utilities.py
```

## Key Implementation Details

- **Duplicate Detection**: Based on exact ID match, keeping the first occurrence
- **Publication Extraction**: Falls back from 'journal' to 'booktitle' field for conferences
- **Year Handling**: Converts years to integers and filters out 'Unknown' entries for sorting
- **Sorting**: Analysis tables sort by count (descending), year tables sort by year (descending)
- All file I/O uses UTF-8 encoding explicitly
- **Error Resilience**: Multiple fallback layers ensure high success rate
- **Validation**: Cross-checks fetched data to prevent incorrect merges

## File Paths & Data Files

Scripts expect BibTeX files in the repository root. Default file names:
- complete_bibtex.py: `input.bib` → `completed_output.bib`
- analyze_bibtex.py: `input.bib`
- sort_bibtex.py: `input.bib` → `sorted_output.bib`
- utilities.py: `refs.bib` → `sorted_output.bib` → `deduplicated_output.bib`

**Data directory** (auto-created):
- `data/failed_dois.json` - Log of all failed DOI fetch attempts
- `data/doi_corrections.json` - Manual DOI correction database
- `.cache/*.json` - Cached BibTeX entries (30-day expiry)

Modify the `if __name__ == '__main__'` section to change file paths.

## DOI Corrections Database

The `data/doi_corrections.json` file allows manual correction of known problematic DOIs:

```json
{
  "corrections": [
    {
      "original_doi": "10.1109/INVALID.DOI",
      "corrected_doi": "10.1109/CORRECT.DOI",
      "status": "corrected",
      "reason": "DOI typo in original source",
      "date_added": "2025-11-02",
      "notes": "Verified with publisher"
    },
    {
      "original_doi": "10.1109/NONEXISTENT.DOI",
      "corrected_doi": null,
      "status": "invalid",
      "reason": "DOI does not exist in any database",
      "date_added": "2025-11-02",
      "notes": "Confirmed with IEEE"
    }
  ]
}
```

**Status values**:
- `corrected`: DOI has a valid replacement (use corrected_doi)
- `invalid`: DOI does not exist (skip fetching)
- `pending`: Needs further research

## Troubleshooting

### IEEE Fetch Failures
1. Check `data/failed_dois.json` for detailed error messages
2. Verify DOI format (should be 10.1109/...)
3. Try `ieee_api_research.py` to test alternative endpoints
4. If Selenium fails, ensure Chrome/Chromium is installed
5. Check if DOI is in `data/doi_corrections.json` as invalid

### Google Scholar Rate Limiting
- Script includes 2-second delays for Scholar requests
- If still rate-limited, increase `RATE_LIMIT_DELAY` in script
- Scholar is final fallback - earlier fallbacks may succeed

### Validation Failures
- Check title similarity between original and fetched entry
- Verify year consistency (±1 year tolerance)
- Use interactive mode to manually approve/reject

