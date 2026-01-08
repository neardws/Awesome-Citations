#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced BibTeX Completion Tool

This tool provides comprehensive BibTeX entry completion including:
- Multi-source data fetching (IEEE, ACM, arXiv, CrossRef, DBLP)
- arXiv published version detection and replacement
- Parallel processing for large files
- Field standardization and formatting
- PDF generation with multiple citation styles
- Detailed change logging
"""

import os
import sys
import json
import time
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import convert_to_unicode
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from awesome_citations.scripts.complete_bibtex import (
    fetch_bibtex_from_ieee,
    fetch_bibtex_from_acm,
    fetch_bibtex_from_arxiv,
    fetch_bibtex_from_crossref,
    extract_doi,
    identify_publisher,
    merge_bibtex_entries
)
from awesome_citations.utils.arxiv_detector import find_published_version, is_arxiv_entry
from awesome_citations.utils.multi_source_merger import merge_entries, calculate_completeness_score
from awesome_citations.utils.change_logger import ChangeLogger
from awesome_citations.scripts.format_bibtex import standardize_entry, load_journal_abbreviations, load_protected_words, load_small_words
from awesome_citations.scripts.generate_pdf import generate_pdf_from_bibtex


def load_config(config_path: str = 'config.json') -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return {
            'arxiv_handling': 'replace_with_published',
            'merge_multiple_sources': True,
            'parallel_processing': False,
            'max_workers': 5,
            'request_delay': 1.0,
            'title_format': 'titlecase',
            'journal_format': 'abbreviation',
            'author_format': 'first_last',
            'page_format': 'double_dash',
            'pdf_output': {'enabled': True},
            'logging': {'enabled': True}
        }


def fetch_from_multiple_sources(entry: Dict, config: Dict) -> List[Dict]:
    """
    Fetch BibTeX data from multiple sources for a single entry.

    Args:
        entry: Original BibTeX entry
        config: Configuration dictionary

    Returns:
        List of BibTeX entries from different sources
    """
    results = []
    doi = extract_doi(entry)

    if not doi:
        return results

    publisher = identify_publisher(doi)
    delay = config.get('request_delay', 1.0)

    # Fetch from appropriate source based on DOI
    if publisher == 'IEEE':
        bibtex_str = fetch_bibtex_from_ieee(doi, delay)
        if bibtex_str:
            try:
                parser = BibTexParser(common_strings=True)
                db = bibtexparser.loads(bibtex_str, parser)
                if db.entries:
                    db.entries[0]['_source'] = 'ieee'
                    results.append(db.entries[0])
            except:
                pass

    elif publisher == 'ACM':
        bibtex_str = fetch_bibtex_from_acm(doi, delay)
        if bibtex_str:
            try:
                parser = BibTexParser(common_strings=True)
                db = bibtexparser.loads(bibtex_str, parser)
                if db.entries:
                    db.entries[0]['_source'] = 'acm'
                    results.append(db.entries[0])
            except:
                pass

    elif publisher == 'arXiv':
        bibtex_str = fetch_bibtex_from_arxiv(doi, delay)
        if bibtex_str:
            try:
                parser = BibTexParser(common_strings=True)
                db = bibtexparser.loads(bibtex_str, parser)
                if db.entries:
                    db.entries[0]['_source'] = 'arxiv'
                    results.append(db.entries[0])
            except:
                pass

    # Always try CrossRef as fallback
    bibtex_str = fetch_bibtex_from_crossref(doi, delay)
    if bibtex_str:
        try:
            parser = BibTexParser(common_strings=True)
            db = bibtexparser.loads(bibtex_str, parser)
            if db.entries:
                db.entries[0]['_source'] = 'crossref'
                results.append(db.entries[0])
        except:
            pass

    return results


def process_single_entry(entry: Dict, config: Dict, logger: Optional[ChangeLogger] = None) -> Dict:
    """
    Process a single BibTeX entry: complete, format, and log changes.

    Args:
        entry: BibTeX entry to process
        config: Configuration dictionary
        logger: Change logger instance

    Returns:
        Processed entry
    """
    entry_id = entry.get('ID', 'unknown')
    original_entry = entry.copy()

    # Step 1: Check if arXiv and find published version
    if config.get('arxiv_handling') == 'replace_with_published' and is_arxiv_entry(entry):
        print(f"  📄 Detected arXiv entry, searching for published version...")
        doi, bibtex_str = find_published_version(entry, config.get('request_delay', 1.0))

        if doi and bibtex_str:
            try:
                parser = BibTexParser(common_strings=True)
                db = bibtexparser.loads(bibtex_str, parser)
                if db.entries:
                    published_entry = db.entries[0]
                    published_entry['ID'] = entry_id  # Preserve original ID
                    entry = published_entry

                    if logger:
                        arxiv_id = entry.get('eprint', 'unknown')
                        logger.log_arxiv_replacement(entry_id, arxiv_id, doi, 'published_version')

                    print(f"  ✓ Replaced with published version (DOI: {doi})")
            except Exception as e:
                print(f"  ⚠️  Failed to parse published version: {e}")

    # Step 2: Fetch from multiple sources if configured
    if config.get('merge_multiple_sources', False):
        fetched_entries = fetch_from_multiple_sources(entry, config)

        if fetched_entries:
            print(f"  📥 Fetched data from {len(fetched_entries)} source(s)")

            # Merge with original entry
            all_entries = [entry] + fetched_entries
            source_priority = config.get('data_source_priority', ['doi_official', 'dblp', 'crossref'])
            entry = merge_entries(all_entries, entry_id, source_priority)

            # Log added fields
            if logger:
                for field in entry.keys():
                    if field not in original_entry and not field.startswith('_'):
                        if field not in ['ID', 'ENTRYTYPE']:
                            logger.log_field_added(entry_id, field, entry[field], 'multi_source')

    return entry


def process_entries_parallel(entries: List[Dict], config: Dict, logger: Optional[ChangeLogger] = None) -> List[Dict]:
    """
    Process multiple entries in parallel.

    Args:
        entries: List of BibTeX entries
        config: Configuration dictionary
        logger: Change logger instance

    Returns:
        List of processed entries
    """
    max_workers = config.get('max_workers', 5)
    processed = []

    print(f"\n🔄 Processing {len(entries)} entries with {max_workers} workers...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(process_single_entry, entry, config, logger): entry
            for entry in entries
        }

        for i, future in enumerate(as_completed(future_to_entry), 1):
            try:
                result = future.result()
                processed.append(result)
                print(f"  [{i}/{len(entries)}] Completed: {result.get('ID', 'unknown')}")
            except Exception as e:
                original = future_to_entry[future]
                entry_id = original.get('ID', 'unknown')
                print(f"  [{i}/{len(entries)}] Error processing {entry_id}: {e}")
                processed.append(original)
                if logger:
                    logger.log_error(entry_id, str(e))

    return processed


def enhanced_complete_bibtex(input_file: str, output_file: str = 'completed_output.bib',
                             config_path: str = 'config.json'):
    """
    Complete and format BibTeX file with all enhanced features.

    Args:
        input_file: Path to input BibTeX file
        output_file: Path to output BibTeX file
        config_path: Path to configuration file
    """
    print(f"\n{'=' * 70}")
    print("Enhanced BibTeX Completion and Formatting Tool")
    print(f"{'=' * 70}\n")

    # Load configuration
    config = load_config(config_path)
    journal_abbr = load_journal_abbreviations()
    protected_words = load_protected_words()
    small_words = load_small_words()

    # Initialize logger
    logger = ChangeLogger() if config.get('logging', {}).get('enabled', True) else None

    # Load BibTeX file
    print(f"📖 Loading BibTeX file: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            parser = BibTexParser(common_strings=True)
            parser.customization = convert_to_unicode
            bib_database = bibtexparser.load(f, parser)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    print(f"✓ Loaded {len(bib_database.entries)} entries\n")

    # Step 1: Complete entries (fetch missing data)
    print("=" * 70)
    print("STEP 1: Completing Entries")
    print("=" * 70)

    if config.get('parallel_processing', False) and len(bib_database.entries) > 10:
        processed_entries = process_entries_parallel(bib_database.entries, config, logger)
    else:
        processed_entries = []
        for i, entry in enumerate(bib_database.entries, 1):
            entry_id = entry.get('ID', f'entry_{i}')
            print(f"\n[{i}/{len(bib_database.entries)}] Processing: {entry_id}")

            if logger:
                logger.log_entry_processed(entry_id)

            try:
                result = process_single_entry(entry, config, logger)
                processed_entries.append(result)
            except Exception as e:
                print(f"  ❌ Error: {e}")
                processed_entries.append(entry)
                if logger:
                    logger.log_error(entry_id, str(e))

            time.sleep(config.get('request_delay', 1.0))

    bib_database.entries = processed_entries

    # Step 2: Format and standardize entries
    print(f"\n{'=' * 70}")
    print("STEP 2: Formatting and Standardizing")
    print("=" * 70 + "\n")

    for i, entry in enumerate(bib_database.entries, 1):
        entry_id = entry.get('ID', f'entry_{i}')
        print(f"[{i}/{len(bib_database.entries)}] Formatting: {entry_id}")

        try:
            standardize_entry(entry, config, journal_abbr, protected_words, small_words, logger)
        except Exception as e:
            print(f"  ⚠️  Error formatting: {e}")

    # Step 3: Write output file
    print(f"\n{'=' * 70}")
    print("STEP 3: Writing Output")
    print("=" * 70 + "\n")

    try:
        writer = BibTexWriter()
        writer.indent = '  '
        writer.order_entries_by = ('ID',)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(writer.write(bib_database))

        print(f"✓ Successfully wrote {len(bib_database.entries)} entries to: {output_file}\n")
    except Exception as e:
        print(f"❌ Error writing output: {e}")
        return

    # Step 4: Generate change log
    if logger:
        logger.print_summary()
        log_file = config.get('logging', {}).get('output_file', 'changes_log.md')
        logger.generate_markdown_report(log_file)

    # Step 5: Generate PDF if enabled
    if config.get('pdf_output', {}).get('enabled', False):
        print(f"\n{'=' * 70}")
        print("STEP 4: Generating PDF")
        print("=" * 70 + "\n")

        style = config.get('citation_style', 'ieee')
        pdf_file = output_file.replace('.bib', '.pdf')

        success = generate_pdf_from_bibtex(output_file, pdf_file, style, config_path)

        if success:
            print(f"✓ PDF generated: {pdf_file}")
        else:
            print("⚠️  PDF generation failed (LaTeX may not be installed)")

    print(f"\n{'=' * 70}")
    print("✓ Processing Complete!")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enhanced_complete.py <input_file> [output_file] [config_file]")
        print("\nExample:")
        print("  python enhanced_complete.py input.bib completed.bib config.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'completed_output.bib'
    config_file = sys.argv[3] if len(sys.argv) > 3 else 'config.json'

    enhanced_complete_bibtex(input_file, output_file, config_file)
