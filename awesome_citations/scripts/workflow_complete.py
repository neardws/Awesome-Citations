#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BibTeX Complete Workflow

A simplified workflow script that orchestrates the complete BibTeX processing pipeline:
1. Sort and deduplicate entries
2. Complete missing fields from multiple sources
3. Standardize formatting
4. Replace arXiv preprints with published versions
5. Generate change summary report
6. Generate PDF bibliography

Usage:
    python workflow_complete.py <input_file> [--output output.bib] [--config config.json]

Example:
    python workflow_complete.py refs.bib --output completed.bib --config config.json
"""

import sys
import os

import argparse
import json
import time
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import convert_to_unicode
from typing import Dict, Optional

from awesome_citations.scripts.utilities import remove_duplicates, sort_bibtex_file
from awesome_citations.scripts.complete_bibtex import (
    extract_doi, verify_doi_exists, identify_publisher,
    fetch_complete_bibtex, merge_bibtex_entries, check_completeness
)
from awesome_citations.scripts.format_bibtex import (
    load_config, load_journal_abbreviations, standardize_entry,
    load_protected_words, load_small_words
)
from awesome_citations.scripts.generate_pdf import generate_pdf_from_bibtex, check_latex_installation
from awesome_citations.utils.change_logger import ChangeLogger
from awesome_citations.utils.arxiv_detector import is_arxiv_entry, extract_arxiv_id, find_published_version


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}\n")


def load_bibtex_file(file_path: str) -> BibDatabase:
    """Load BibTeX file and return parsed database."""
    with open(file_path, 'r', encoding='utf-8') as f:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        return bibtexparser.load(f, parser=parser)


def save_bibtex_file(bib_database: BibDatabase, file_path: str):
    """Save BibTeX database to file."""
    writer = BibTexWriter()
    writer.indent = '  '
    writer.order_entries_by = ('ID',)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(writer.write(bib_database))


def workflow_complete_bibtex(input_file: str, output_file: str,
                              config_path: str = 'config.json'):
    """
    Execute complete BibTeX processing workflow.

    Args:
        input_file: Path to input BibTeX file
        output_file: Path to output BibTeX file
        config_path: Path to configuration file
    """
    start_time = time.time()

    # Load configuration
    config = load_config(config_path) if os.path.exists(config_path) else {}

    # Initialize change logger
    logger = ChangeLogger()

    # Load formatting resources
    journal_abbr = load_journal_abbreviations()
    protected_words = load_protected_words()
    small_words = load_small_words()

    print("\n" + "=" * 70)
    print("BibTeX Complete Workflow")
    print("=" * 70)
    print(f"\nInput file:  {input_file}")
    print(f"Output file: {output_file}")
    print(f"Config file: {config_path}")

    # =========================================================================
    # STEP 1: Sort and Deduplicate
    # =========================================================================
    print_header("STEP 1: Sorting and Deduplicating")

    temp_sorted = input_file + '.sorted.tmp'
    temp_dedup = input_file + '.dedup.tmp'

    try:
        # Sort entries
        print("Sorting entries by ID...")
        sort_bibtex_file(input_file, temp_sorted)
        print("✓ Entries sorted\n")

        # Remove duplicates
        print("Removing duplicate entries...")
        bib_database = load_bibtex_file(temp_sorted)
        original_count = len(bib_database.entries)

        remove_duplicates(temp_sorted, temp_dedup)
        bib_database = load_bibtex_file(temp_dedup)

        duplicates_removed = original_count - len(bib_database.entries)
        if duplicates_removed > 0:
            print(f"✓ Removed {duplicates_removed} duplicate(s)")
        else:
            print("✓ No duplicates found")

        print(f"✓ Total entries: {len(bib_database.entries)}\n")

        # Clean up temp files
        os.remove(temp_sorted)
        os.remove(temp_dedup)

    except Exception as e:
        print(f"❌ Error in sorting/deduplication: {e}")
        return

    # =========================================================================
    # STEP 2: Complete Missing Fields
    # =========================================================================
    print_header("STEP 2: Completing Missing Fields")

    completed_count = 0
    failed_count = 0

    for i, entry in enumerate(bib_database.entries, 1):
        entry_id = entry.get('ID', f'entry_{i}')
        print(f"[{i}/{len(bib_database.entries)}] Processing: {entry_id}")

        logger.log_entry_processed(entry_id)

        try:
            # Check if entry is already complete
            present_fields, missing_fields = check_completeness(entry)

            if not missing_fields:
                print(f"  ✓ Entry is already complete\n")
                continue

            print(f"  Missing fields: {', '.join(missing_fields)}")

            # Extract and validate DOI
            doi = extract_doi(entry)

            if not doi:
                print(f"  ⚠️  No DOI found, skipping completion\n")
                failed_count += 1
                continue

            print(f"  DOI: {doi}")

            # Verify DOI exists
            if not verify_doi_exists(doi):
                print(f"  ⚠️  DOI verification failed\n")
                logger.log_error(entry_id, f"Invalid DOI: {doi}")
                failed_count += 1
                continue

            # Identify publisher
            publisher = identify_publisher(doi)
            print(f"  Publisher: {publisher}")

            # Fetch complete BibTeX
            fetched_bibtex_str, error_msg = fetch_complete_bibtex(
                doi, publisher,
                title=entry.get('title'),
                author=entry.get('author')
            )

            if fetched_bibtex_str:
                # Parse BibTeX string to dictionary
                from scripts.complete_bibtex import parse_bibtex_string
                fetched_bib = parse_bibtex_string(fetched_bibtex_str)

                if fetched_bib:
                    # Merge fetched data
                    original_entry = entry.copy()
                    merged_entry = merge_bibtex_entries(entry, fetched_bib)
                    # Update the entry in the database
                    bib_database.entries[i-1] = merged_entry

                    # Log changes
                    for field in missing_fields:
                        if field in merged_entry and merged_entry[field]:
                            logger.log_field_added(
                                entry_id, field, merged_entry[field], publisher
                            )

                    print(f"  ✓ Completed successfully\n")
                    completed_count += 1
                else:
                    print(f"  ⚠️  Failed to parse fetched BibTeX\n")
                    logger.log_error(entry_id, "Failed to parse fetched BibTeX")
                    failed_count += 1
            else:
                error_display = error_msg if error_msg else "Unknown error"
                print(f"  ⚠️  Failed to fetch: {error_display}\n")
                logger.log_error(entry_id, f"Failed to fetch: {error_display}")
                failed_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            logger.log_error(entry_id, str(e))
            failed_count += 1

        # Rate limiting
        time.sleep(config.get('request_delay', 0.5))

    print(f"Completion summary: {completed_count} succeeded, {failed_count} failed\n")

    # =========================================================================
    # STEP 3: Format and Standardize
    # =========================================================================
    print_header("STEP 3: Formatting and Standardizing")

    for i, entry in enumerate(bib_database.entries, 1):
        entry_id = entry.get('ID', f'entry_{i}')
        print(f"[{i}/{len(bib_database.entries)}] Formatting: {entry_id}")

        try:
            standardize_entry(entry, config, journal_abbr,
                            protected_words, small_words, logger)
            print(f"  ✓ Formatted\n")
        except Exception as e:
            print(f"  ⚠️  Error: {e}\n")
            logger.log_error(entry_id, f"Formatting error: {e}")

    # =========================================================================
    # STEP 4: Replace arXiv Preprints
    # =========================================================================
    if config.get('arxiv_handling') == 'replace_with_published':
        print_header("STEP 4: Replacing arXiv Preprints")

        arxiv_count = 0
        replaced_count = 0

        for i, entry in enumerate(bib_database.entries, 1):
            entry_id = entry.get('ID', f'entry_{i}')

            if is_arxiv_entry(entry):
                arxiv_count += 1
                arxiv_id = extract_arxiv_id(entry)
                print(f"[{arxiv_count}] Found arXiv entry: {entry_id} ({arxiv_id})")

                try:
                    published_doi, published_bibtex = find_published_version(entry, config.get('request_delay', 1.0))

                    if published_doi and published_bibtex:
                        print(f"  ✓ Found published version: {published_doi}")
                        
                        # Parse published BibTeX
                        from scripts.complete_bibtex import parse_bibtex_string
                        published_entry = parse_bibtex_string(published_bibtex)
                        
                        if published_entry:
                            # Merge published version into entry
                            merged_entry = merge_bibtex_entries(entry, published_entry)
                            # Update the entry in the database
                            bib_database.entries[i-1] = merged_entry
                            
                            # Log the replacement
                            for field in ['author', 'journal', 'booktitle', 'volume', 'number', 'pages']:
                                if field in merged_entry and merged_entry[field]:
                                    logger.log_field_added(entry_id, field, merged_entry[field], 'published_version')

                            logger.log_arxiv_replacement(
                                entry_id, arxiv_id, published_doi, 'published_version'
                            )
                            replaced_count += 1
                            print(f"  ✓ Replaced with published version\n")
                    else:
                        print(f"  ⚠️  No published version found\n")

                except Exception as e:
                    print(f"  ❌ Error: {e}\n")
                    logger.log_error(entry_id, f"arXiv replacement error: {e}")

                time.sleep(config.get('request_delay', 1.0))

        print(f"arXiv summary: {replaced_count}/{arxiv_count} replaced\n")

    # =========================================================================
    # STEP 5: Write Output File
    # =========================================================================
    print_header("STEP 5: Writing Output")

    try:
        save_bibtex_file(bib_database, output_file)
        print(f"✓ Successfully wrote {len(bib_database.entries)} entries to: {output_file}\n")
    except Exception as e:
        print(f"❌ Error writing output: {e}")
        return

    # =========================================================================
    # STEP 6: Generate Change Summary
    # =========================================================================
    print_header("STEP 6: Generating Change Summary")

    logger.print_summary()

    summary_file = output_file.replace('.bib', '_changes.md')
    logger.generate_markdown_report(summary_file)
    print(f"✓ Change summary saved to: {summary_file}\n")

    # =========================================================================
    # STEP 7: Generate PDF
    # =========================================================================
    if config.get('pdf_output', {}).get('enabled', True):
        print_header("STEP 7: Generating PDF")

        # Check LaTeX installation
        if not check_latex_installation():
            print("⚠️  LaTeX not installed, skipping PDF generation")
            print("   Install LaTeX (TeX Live/MiKTeX) to enable PDF output\n")
        else:
            style = config.get('citation_style', 'ieee')
            pdf_file = output_file.replace('.bib', '.pdf')

            print(f"Generating PDF with {style.upper()} style...")

            success = generate_pdf_from_bibtex(
                output_file, pdf_file, style, config_path
            )

            if success:
                print(f"✓ PDF generated: {pdf_file}\n")
            else:
                print("⚠️  PDF generation failed\n")

    # =========================================================================
    # COMPLETION
    # =========================================================================
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("✓ Workflow Complete!")
    print("=" * 70)
    print(f"\nTotal time: {elapsed_time:.2f} seconds")
    print(f"Output files:")
    print(f"  - BibTeX: {output_file}")
    print(f"  - Changes: {summary_file}")

    pdf_file = output_file.replace('.bib', '.pdf')
    if os.path.exists(pdf_file):
        print(f"  - PDF:     {pdf_file}")

    print("\n")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Complete BibTeX processing workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python workflow_complete.py refs.bib
  python workflow_complete.py refs.bib --output completed.bib
  python workflow_complete.py refs.bib --output completed.bib --config config.json

The workflow performs the following steps:
  1. Sort and deduplicate entries
  2. Complete missing fields from multiple sources (IEEE/ACM/arXiv/CrossRef)
  3. Standardize formatting (title, authors, journals)
  4. Replace arXiv preprints with published versions
  5. Generate detailed change summary report
  6. Generate PDF bibliography (IEEE style by default)
        """
    )

    parser.add_argument(
        'input_file',
        help='Input BibTeX file'
    )
    parser.add_argument(
        '--output', '-o',
        dest='output_file',
        help='Output BibTeX file (default: <input>_completed.bib)'
    )
    parser.add_argument(
        '--config', '-c',
        dest='config_file',
        default='config.json',
        help='Configuration file (default: config.json)'
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    # Set default output file
    if not args.output_file:
        base_name = os.path.splitext(args.input_file)[0]
        args.output_file = f"{base_name}_completed.bib"

    # Execute workflow
    try:
        workflow_complete_bibtex(
            args.input_file,
            args.output_file,
            args.config_file
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
