#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BibTeX Field Standardization and Formatting

This module standardizes BibTeX fields including:
- Title formatting (Title Case, Sentence Case, etc.)
- Journal/conference name normalization
- Author name formatting
- Page number formatting
- Field ordering
"""

import re
import json
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import convert_to_unicode
from typing import Dict, Optional
from awesome_citations.utils.title_formatter import format_title, load_protected_words, load_small_words
from awesome_citations.utils.change_logger import ChangeLogger


def load_journal_abbreviations(config_path: str = None) -> Dict[str, str]:
    """
    Load journal abbreviation mappings from configuration file.

    Args:
        config_path: Path to journal_abbr.json

    Returns:
        Dictionary mapping full names to abbreviations
    """
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        config_path = os.path.join(parent_dir, 'data', 'journal_abbr.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load journal abbreviations: {e}")
        return {}


def load_config(config_path: str = 'config.json') -> Dict:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return {}


def format_author_names(authors: str, format_type: str = 'first_last') -> str:
    """
    Format author names consistently.

    Args:
        authors: Author string (multiple authors separated by 'and')
        format_type: 'first_last' or 'last_first'

    Returns:
        Formatted author string
    """
    if not authors or not authors.strip():
        return authors

    # Split by 'and'
    author_list = re.split(r'\s+and\s+', authors, flags=re.IGNORECASE)
    formatted_authors = []

    for author in author_list:
        author = author.strip()

        if not author:
            continue

        # Check if already in "Last, First" format
        if ',' in author:
            parts = author.split(',', 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip() if len(parts) > 1 else ''

            if format_type == 'first_last':
                formatted = f"{first_name} {last_name}".strip()
            else:
                formatted = f"{last_name}, {first_name}".strip()
        else:
            # Assume "First Last" format
            # Handle special prefixes (van, von, de, etc.)
            parts = author.split()

            if len(parts) == 1:
                formatted = author
            else:
                # Simple heuristic: last word is last name
                last_name = parts[-1]
                first_names = ' '.join(parts[:-1])

                if format_type == 'first_last':
                    formatted = f"{first_names} {last_name}"
                else:
                    formatted = f"{last_name}, {first_names}"

        formatted_authors.append(formatted)

    return ' and '.join(formatted_authors)


def format_pages(pages: str, format_type: str = 'double_dash') -> str:
    """
    Format page numbers consistently.

    Args:
        pages: Page number string
        format_type: 'double_dash' (1--10) or 'single_dash' (1-10)

    Returns:
        Formatted page string
    """
    if not pages or not pages.strip():
        return pages

    pages = pages.strip()

    # Replace various dash types with standard format
    if format_type == 'double_dash':
        # Convert to double dash
        pages = re.sub(r'[-–—]+', '--', pages)
    else:
        # Convert to single dash
        pages = re.sub(r'[-–—]+', '-', pages)

    return pages


def normalize_journal_name(journal: str, journal_abbr: Dict[str, str],
                           format_type: str = 'abbreviation') -> str:
    """
    Normalize journal/conference names.

    Args:
        journal: Original journal name
        journal_abbr: Dictionary of journal abbreviations
        format_type: 'abbreviation' or 'full'

    Returns:
        Normalized journal name
    """
    if not journal or not journal.strip():
        return journal

    journal = journal.strip()

    # Create reverse mapping (abbr -> full) if needed
    if format_type == 'full':
        reverse_map = {v: k for k, v in journal_abbr.items()}
        mapping = reverse_map
    else:
        mapping = journal_abbr

    # Try exact match (case-insensitive)
    for key, value in mapping.items():
        if journal.lower() == key.lower():
            return value

    # Try partial match
    for key, value in mapping.items():
        if key.lower() in journal.lower() or journal.lower() in key.lower():
            # Verify it's a reasonable match
            if len(key) > 5:  # Avoid matching very short strings
                return value

    # Return original if no match found
    return journal


def standardize_entry(entry: Dict, config: Dict, journal_abbr: Dict[str, str],
                     protected_words: set, small_words: set,
                     logger: Optional[ChangeLogger] = None) -> Dict:
    """
    Standardize all fields in a BibTeX entry.

    Args:
        entry: BibTeX entry dictionary
        config: Configuration dictionary
        journal_abbr: Journal abbreviation dictionary
        protected_words: Set of protected words for title formatting
        small_words: Set of small words for title formatting
        logger: Change logger instance

    Returns:
        Standardized entry dictionary
    """
    entry_id = entry.get('ID', 'unknown')
    modified = False

    # 1. Format title
    if 'title' in entry and entry['title'].strip():
        old_title = entry['title']
        title_format = config.get('title_format', 'titlecase')

        try:
            new_title = format_title(old_title, title_format, protected_words, small_words)

            if new_title != old_title:
                entry['title'] = new_title
                modified = True
                if logger:
                    logger.log_title_formatted(entry_id, old_title, new_title, title_format)
        except Exception as e:
            print(f"  Warning: Failed to format title for {entry_id}: {e}")

    # 2. Format author names
    if 'author' in entry and entry['author'].strip():
        old_author = entry['author']
        author_format = config.get('author_format', 'first_last')

        try:
            new_author = format_author_names(old_author, author_format)

            if new_author != old_author:
                entry['author'] = new_author
                modified = True
                if logger:
                    logger.log_field_updated(entry_id, 'author', old_author, new_author, 'formatting')
        except Exception as e:
            print(f"  Warning: Failed to format authors for {entry_id}: {e}")

    # 3. Normalize journal/conference name
    journal_format = config.get('journal_format', 'abbreviation')

    # Check both 'journal' and 'booktitle' fields
    for field_name in ['journal', 'booktitle']:
        if field_name in entry and entry[field_name].strip():
            old_value = entry[field_name]

            try:
                # For 'both' mode, keep as-is but ensure it exists in our mapping
                if journal_format == 'both':
                    # Don't change, but could validate here
                    continue
                else:
                    new_value = normalize_journal_name(old_value, journal_abbr, journal_format)

                    if new_value != old_value:
                        entry[field_name] = new_value
                        modified = True
                        if logger:
                            logger.log_journal_normalized(entry_id, old_value, new_value, journal_format)
            except Exception as e:
                print(f"  Warning: Failed to normalize {field_name} for {entry_id}: {e}")

    # 4. Format page numbers
    if 'pages' in entry and entry['pages'].strip():
        old_pages = entry['pages']
        page_format = config.get('page_format', 'double_dash')

        try:
            new_pages = format_pages(old_pages, page_format)

            if new_pages != old_pages:
                entry['pages'] = new_pages
                modified = True
                if logger:
                    logger.log_field_updated(entry_id, 'pages', old_pages, new_pages, 'formatting')
        except Exception as e:
            print(f"  Warning: Failed to format pages for {entry_id}: {e}")

    # 5. Clean up whitespace in all fields
    for field, value in entry.items():
        if isinstance(value, str) and field not in ['ID', 'ENTRYTYPE']:
            cleaned = re.sub(r'\s+', ' ', value.strip())
            if cleaned != value:
                entry[field] = cleaned

    return entry


def format_bibtex_file(input_file: str, output_file: str, config_path: str = 'config.json'):
    """
    Format and standardize all entries in a BibTeX file.

    Args:
        input_file: Path to input BibTeX file
        output_file: Path to output BibTeX file
        config_path: Path to configuration file
    """
    print(f"\n{'=' * 60}")
    print("BibTeX Field Standardization and Formatting")
    print(f"{'=' * 60}\n")

    # Load configuration
    config = load_config(config_path)
    journal_abbr = load_journal_abbreviations()
    protected_words = load_protected_words()
    small_words = load_small_words()

    # Initialize logger
    logger = ChangeLogger() if config.get('logging', {}).get('enabled', True) else None

    # Load BibTeX file
    print(f"Loading BibTeX file: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            parser = BibTexParser(common_strings=True)
            parser.customization = convert_to_unicode
            bib_database = bibtexparser.load(f, parser)
    except Exception as e:
        print(f"Error loading BibTeX file: {e}")
        return

    print(f"Found {len(bib_database.entries)} entries\n")

    # Process each entry
    print("Formatting entries...")
    for i, entry in enumerate(bib_database.entries, 1):
        entry_id = entry.get('ID', f'entry_{i}')
        print(f"  [{i}/{len(bib_database.entries)}] Processing {entry_id}")

        if logger:
            logger.log_entry_processed(entry_id)

        try:
            standardize_entry(entry, config, journal_abbr, protected_words,
                            small_words, logger)
        except Exception as e:
            print(f"    Error processing {entry_id}: {e}")
            if logger:
                logger.log_error(entry_id, str(e))

    # Write output file
    print(f"\nWriting formatted BibTeX to: {output_file}")
    try:
        writer = BibTexWriter()
        writer.indent = '  '
        writer.order_entries_by = ('ID',)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(writer.write(bib_database))

        print(f"✓ Successfully wrote {len(bib_database.entries)} entries\n")
    except Exception as e:
        print(f"Error writing output file: {e}")
        return

    # Generate logs if enabled
    if logger:
        logger.print_summary()

        log_file = config.get('logging', {}).get('output_file', 'changes_log.md')
        logger.generate_markdown_report(log_file)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python format_bibtex.py <input_file> [output_file] [config_file]")
        print("\nExample:")
        print("  python format_bibtex.py input.bib formatted_output.bib config.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'formatted_output.bib'
    config_file = sys.argv[3] if len(sys.argv) > 3 else 'config.json'

    format_bibtex_file(input_file, output_file, config_file)
