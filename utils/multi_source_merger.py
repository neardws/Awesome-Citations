#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Multi-Source BibTeX Data Merger

This module merges BibTeX data from multiple sources, selecting the most
complete and accurate fields from each source.
"""

from typing import Dict, List, Optional
import re


# Important fields with their priority weights
FIELD_WEIGHTS = {
    'author': 10,
    'title': 10,
    'year': 9,
    'journal': 8,
    'booktitle': 8,
    'volume': 7,
    'number': 7,
    'pages': 7,
    'doi': 9,
    'publisher': 6,
    'organization': 6,
    'address': 5,
    'month': 5,
    'issn': 6,
    'isbn': 6,
    'url': 5,
    'abstract': 8,
    'keywords': 7,
    'note': 4,
    'series': 5,
    'edition': 6
}


def calculate_completeness_score(entry: Dict) -> float:
    """
    Calculate a completeness score for a BibTeX entry.

    Args:
        entry: BibTeX entry dictionary

    Returns:
        Completeness score (0-100)
    """
    score = 0
    max_score = 0

    for field, weight in FIELD_WEIGHTS.items():
        max_score += weight
        if field in entry and entry[field] and entry[field].strip():
            value = entry[field].strip()
            # Add length bonus (longer fields are often more complete)
            length_bonus = min(len(value) / 100, 1.0)
            score += weight * (0.7 + 0.3 * length_bonus)

    return (score / max_score) * 100 if max_score > 0 else 0


def clean_field_value(value: str) -> str:
    """
    Clean a field value by removing extra whitespace and standardizing format.

    Args:
        value: Field value string

    Returns:
        Cleaned value
    """
    if not value:
        return ""

    # Remove extra whitespace
    value = re.sub(r'\s+', ' ', value.strip())

    # Remove surrounding quotes or braces if present
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith('{') and value.endswith('}')):
        value = value[1:-1]

    return value.strip()


def is_field_more_complete(value1: str, value2: str) -> bool:
    """
    Compare two field values to determine which is more complete.

    Args:
        value1: First field value
        value2: Second field value

    Returns:
        True if value1 is more complete than value2
    """
    v1 = clean_field_value(value1)
    v2 = clean_field_value(value2)

    if not v1:
        return False
    if not v2:
        return True

    # Longer is usually better (more information)
    len1, len2 = len(v1), len(v2)

    # If lengths are very different, choose the longer one
    if abs(len1 - len2) > len(max(v1, v2, key=len)) * 0.3:
        return len1 > len2

    # If similar length, prefer the one with more words
    words1 = len(v1.split())
    words2 = len(v2.split())

    return words1 >= words2


def merge_author_field(authors_list: List[str]) -> str:
    """
    Merge author fields from multiple sources, choosing the most complete.

    Args:
        authors_list: List of author strings from different sources

    Returns:
        Merged author string
    """
    if not authors_list:
        return ""

    # Remove empty entries
    authors_list = [a for a in authors_list if a and a.strip()]

    if not authors_list:
        return ""

    if len(authors_list) == 1:
        return authors_list[0]

    # Choose the author list with most authors
    # Split by 'and' to count authors
    def count_authors(author_str):
        return len(re.split(r'\s+and\s+', author_str, flags=re.IGNORECASE))

    return max(authors_list, key=lambda x: (count_authors(x), len(x)))


def merge_pages_field(pages_list: List[str]) -> str:
    """
    Merge page fields from multiple sources.

    Args:
        pages_list: List of page strings from different sources

    Returns:
        Merged page string
    """
    if not pages_list:
        return ""

    # Remove empty entries
    pages_list = [p for p in pages_list if p and p.strip()]

    if not pages_list:
        return ""

    if len(pages_list) == 1:
        return pages_list[0]

    # Prefer format with ranges (contains dash)
    range_pages = [p for p in pages_list if '-' in p or '--' in p or '–' in p]
    if range_pages:
        # Return the longest range
        return max(range_pages, key=len)

    # Otherwise return the longest
    return max(pages_list, key=len)


def merge_entries(entries: List[Dict], original_id: str, source_priority: List[str] = None) -> Dict:
    """
    Merge multiple BibTeX entries from different sources into one complete entry.

    Args:
        entries: List of BibTeX entry dictionaries from different sources
        original_id: Original entry ID to preserve
        source_priority: List of source names in priority order
                        (e.g., ['doi_official', 'dblp', 'crossref'])

    Returns:
        Merged BibTeX entry dictionary
    """
    if not entries:
        return {}

    if len(entries) == 1:
        return entries[0]

    # Initialize merged entry with the entry from highest priority source
    if source_priority:
        # Try to find entries from prioritized sources
        for source in source_priority:
            for entry in entries:
                if entry.get('_source') == source:
                    merged = entry.copy()
                    break
            else:
                continue
            break
        else:
            # No prioritized source found, use first entry
            merged = entries[0].copy()
    else:
        # Use the entry with highest completeness score
        merged = max(entries, key=calculate_completeness_score).copy()

    # Preserve original ID
    merged['ID'] = original_id

    # Merge each important field
    for field in FIELD_WEIGHTS.keys():
        field_values = []

        for entry in entries:
            if field in entry and entry[field] and entry[field].strip():
                field_values.append(entry[field])

        if not field_values:
            continue

        # Special handling for specific fields
        if field == 'author':
            merged[field] = merge_author_field(field_values)
        elif field == 'pages':
            merged[field] = merge_pages_field(field_values)
        else:
            # For other fields, choose the most complete one
            best_value = field_values[0]
            for value in field_values[1:]:
                if is_field_more_complete(value, best_value):
                    best_value = value
            merged[field] = best_value

    # Merge ENTRYTYPE - prefer more specific types
    entry_types = [e.get('ENTRYTYPE', '').lower() for e in entries if e.get('ENTRYTYPE')]
    type_priority = ['article', 'inproceedings', 'book', 'incollection', 'inbook',
                     'proceedings', 'conference', 'techreport', 'phdthesis', 'mastersthesis',
                     'unpublished', 'misc']

    for preferred_type in type_priority:
        if preferred_type in entry_types:
            merged['ENTRYTYPE'] = preferred_type
            break

    # Add metadata about sources
    merged['_merged_from'] = [e.get('_source', 'unknown') for e in entries]

    return merged


def get_field_source_info(field_name: str, entries: List[Dict], merged_value: str) -> str:
    """
    Determine which source provided the value for a specific field.

    Args:
        field_name: Name of the field
        entries: List of source entries
        merged_value: The final merged value

    Returns:
        Source name string
    """
    merged_value_clean = clean_field_value(merged_value)

    for entry in entries:
        if field_name in entry:
            entry_value_clean = clean_field_value(entry[field_name])
            if entry_value_clean == merged_value_clean:
                return entry.get('_source', 'unknown')

    return 'unknown'


def compare_entries(entry1: Dict, entry2: Dict) -> Dict:
    """
    Compare two BibTeX entries field by field.

    Args:
        entry1: First BibTeX entry
        entry2: Second BibTeX entry

    Returns:
        Dictionary with comparison results
    """
    comparison = {
        'entry1_completeness': calculate_completeness_score(entry1),
        'entry2_completeness': calculate_completeness_score(entry2),
        'common_fields': [],
        'only_in_entry1': [],
        'only_in_entry2': [],
        'different_values': []
    }

    all_fields = set(entry1.keys()) | set(entry2.keys())
    all_fields.discard('ID')
    all_fields.discard('ENTRYTYPE')
    all_fields.discard('_source')

    for field in all_fields:
        if field in entry1 and field in entry2:
            v1 = clean_field_value(entry1[field])
            v2 = clean_field_value(entry2[field])

            if v1 == v2:
                comparison['common_fields'].append(field)
            else:
                comparison['different_values'].append({
                    'field': field,
                    'entry1_value': v1[:100],
                    'entry2_value': v2[:100]
                })
        elif field in entry1:
            comparison['only_in_entry1'].append(field)
        else:
            comparison['only_in_entry2'].append(field)

    return comparison


if __name__ == "__main__":
    # Test the merger
    entry1 = {
        'ID': 'test2023',
        'ENTRYTYPE': 'article',
        'author': 'Smith, John and Doe, Jane',
        'title': 'A Test Paper',
        'year': '2023',
        'journal': 'IEEE Trans. on Testing',
        '_source': 'ieee'
    }

    entry2 = {
        'ID': 'different_id',
        'ENTRYTYPE': 'article',
        'author': 'Smith, John and Doe, Jane and Brown, Bob',
        'title': 'A Test Paper',
        'year': '2023',
        'journal': 'IEEE Transactions on Testing',
        'volume': '10',
        'number': '2',
        'pages': '100-110',
        'doi': '10.1109/test.2023.123456',
        '_source': 'crossref'
    }

    entry3 = {
        'ID': 'another_id',
        'ENTRYTYPE': 'article',
        'author': 'John Smith and Jane Doe and Bob Brown',
        'title': 'A Test Paper on Important Topics',
        'year': '2023',
        'journal': 'IEEE Trans. Test.',
        'volume': '10',
        'pages': '100--110',
        'abstract': 'This is a test abstract with more details...',
        '_source': 'dblp'
    }

    print("Testing multi-source merger...")
    print(f"\nEntry 1 completeness: {calculate_completeness_score(entry1):.1f}")
    print(f"Entry 2 completeness: {calculate_completeness_score(entry2):.1f}")
    print(f"Entry 3 completeness: {calculate_completeness_score(entry3):.1f}")

    merged = merge_entries([entry1, entry2, entry3], 'test2023', ['ieee', 'dblp', 'crossref'])

    print("\n=== Merged Entry ===")
    for key, value in merged.items():
        if not key.startswith('_'):
            print(f"{key}: {value}")

    print(f"\n_merged_from: {merged.get('_merged_from', [])}")

    print("\n=== Comparison: Entry1 vs Entry2 ===")
    comp = compare_entries(entry1, entry2)
    print(f"Entry1 completeness: {comp['entry1_completeness']:.1f}")
    print(f"Entry2 completeness: {comp['entry2_completeness']:.1f}")
    print(f"Common fields: {comp['common_fields']}")
    print(f"Only in entry1: {comp['only_in_entry1']}")
    print(f"Only in entry2: {comp['only_in_entry2']}")
    print(f"Different values: {len(comp['different_values'])} fields")
