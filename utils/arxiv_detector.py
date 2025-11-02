#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
arXiv Published Version Detector

This module detects whether an arXiv preprint has been formally published
in a journal or conference, and retrieves the published version's metadata.
"""

import re
import requests
import time
from typing import Dict, Optional, Tuple
from bs4 import BeautifulSoup


def extract_arxiv_id(entry: Dict) -> Optional[str]:
    """
    Extract arXiv ID from a BibTeX entry.

    Args:
        entry: BibTeX entry dictionary

    Returns:
        arXiv ID if found, None otherwise
    """
    # Check eprint field
    if 'eprint' in entry and entry['eprint'].strip():
        return entry['eprint'].strip()

    # Check arxivId field
    if 'arxivid' in entry and entry['arxivid'].strip():
        return entry['arxivid'].strip()

    # Check archivePrefix field combined with eprint
    if 'archiveprefix' in entry and 'arxiv' in entry['archiveprefix'].lower():
        if 'eprint' in entry:
            return entry['eprint'].strip()

    # Extract from URL field
    if 'url' in entry:
        url = entry['url']
        # Pattern: arxiv.org/abs/1234.5678 or arxiv.org/pdf/1234.5678
        match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url, re.IGNORECASE)
        if match:
            return match.group(1)

    # Extract from DOI (arXiv DOIs: 10.48550/arXiv.1234.5678)
    if 'doi' in entry:
        doi = entry['doi']
        match = re.search(r'10\.48550/arXiv\.(\d{4}\.\d{4,5})', doi, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def is_arxiv_entry(entry: Dict) -> bool:
    """
    Check if a BibTeX entry is an arXiv preprint.

    Args:
        entry: BibTeX entry dictionary

    Returns:
        True if entry is arXiv preprint, False otherwise
    """
    # Check entry type
    if entry.get('ENTRYTYPE', '').lower() == 'misc':
        return extract_arxiv_id(entry) is not None

    # Check for arXiv-specific fields
    if 'archiveprefix' in entry and 'arxiv' in entry['archiveprefix'].lower():
        return True

    # Check journal/publisher fields
    journal = entry.get('journal', '').lower()
    publisher = entry.get('publisher', '').lower()

    if 'arxiv' in journal or 'arxiv' in publisher:
        return True

    return False


def search_crossref_by_title(title: str, delay: float = 1.0) -> Optional[Dict]:
    """
    Search CrossRef API by article title to find published version.

    Args:
        title: Article title
        delay: Delay between requests (seconds)

    Returns:
        CrossRef metadata if found, None otherwise
    """
    try:
        time.sleep(delay)

        # Clean title for search
        clean_title = re.sub(r'[{}\\]', '', title)

        url = "https://api.crossref.org/works"
        params = {
            'query.title': clean_title,
            'rows': 5,
            'select': 'DOI,title,container-title,published-print,published-online,type'
        }

        headers = {'User-Agent': 'BibTeX-Completion-Tool/1.0 (mailto:user@example.com)'}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('message', {}).get('items'):
            # Return the first result with highest relevance
            for item in data['message']['items']:
                item_title = item.get('title', [''])[0].lower()
                search_title = clean_title.lower()

                # Check title similarity (simple substring match)
                if search_title in item_title or item_title in search_title:
                    # Filter out preprints
                    item_type = item.get('type', '')
                    if 'posted-content' not in item_type:
                        return item

        return None

    except Exception as e:
        print(f"  ⚠️  CrossRef search failed: {str(e)}")
        return None


def search_semantic_scholar(arxiv_id: str, delay: float = 1.0) -> Optional[Dict]:
    """
    Search Semantic Scholar API for published version of arXiv paper.

    Args:
        arxiv_id: arXiv ID (e.g., "1234.5678")
        delay: Delay between requests (seconds)

    Returns:
        Semantic Scholar metadata if found, None otherwise
    """
    try:
        time.sleep(delay)

        # Remove version suffix (e.g., v1, v2)
        clean_id = re.sub(r'v\d+$', '', arxiv_id)

        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{clean_id}"
        params = {
            'fields': 'externalIds,title,venue,year,publicationVenue,publicationTypes'
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()

        # Check if it has a DOI (indicating formal publication)
        external_ids = data.get('externalIds', {})
        doi = external_ids.get('DOI')

        if doi:
            # Check publication types to filter out preprints
            pub_types = data.get('publicationTypes', [])
            if pub_types and 'JournalArticle' in pub_types or 'Conference' in pub_types:
                return {
                    'doi': doi,
                    'title': data.get('title'),
                    'venue': data.get('venue'),
                    'year': data.get('year'),
                    'source': 'semantic_scholar'
                }

        return None

    except Exception as e:
        print(f"  ⚠️  Semantic Scholar search failed: {str(e)}")
        return None


def search_dblp(title: str, delay: float = 1.0) -> Optional[Dict]:
    """
    Search DBLP API by title for published version.

    Args:
        title: Article title
        delay: Delay between requests (seconds)

    Returns:
        DBLP metadata if found, None otherwise
    """
    try:
        time.sleep(delay)

        # Clean title
        clean_title = re.sub(r'[{}\\]', '', title)

        url = "https://dblp.org/search/publ/api"
        params = {
            'q': clean_title,
            'format': 'json',
            'h': 5  # Return top 5 results
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        hits = data.get('result', {}).get('hits', {}).get('hit', [])

        if hits:
            for hit in hits:
                info = hit.get('info', {})

                # Check if it's a journal or conference paper (not arXiv)
                venue = info.get('venue', '').lower()
                if 'arxiv' not in venue and venue:
                    # Check title similarity
                    dblp_title = info.get('title', '').lower()
                    search_title = clean_title.lower()

                    if search_title in dblp_title or dblp_title in search_title:
                        doi = info.get('doi')
                        if doi:
                            return {
                                'doi': doi,
                                'title': info.get('title'),
                                'venue': info.get('venue'),
                                'year': info.get('year'),
                                'type': info.get('type'),
                                'source': 'dblp'
                            }

        return None

    except Exception as e:
        print(f"  ⚠️  DBLP search failed: {str(e)}")
        return None


def fetch_bibtex_from_doi(doi: str, delay: float = 1.0) -> Optional[str]:
    """
    Fetch BibTeX entry from DOI using CrossRef API.

    Args:
        doi: DOI string
        delay: Delay between requests (seconds)

    Returns:
        BibTeX string if successful, None otherwise
    """
    try:
        time.sleep(delay)

        url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
        headers = {'User-Agent': 'BibTeX-Completion-Tool/1.0'}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        return response.text

    except Exception as e:
        print(f"  ⚠️  Failed to fetch BibTeX from DOI {doi}: {str(e)}")
        return None


def find_published_version(entry: Dict, delay: float = 1.0) -> Tuple[Optional[str], Optional[str]]:
    """
    Find the published version of an arXiv preprint.

    Args:
        entry: BibTeX entry dictionary
        delay: Delay between API requests (seconds)

    Returns:
        Tuple of (published_doi, bibtex_string) if found, (None, None) otherwise
    """
    if not is_arxiv_entry(entry):
        return None, None

    title = entry.get('title', '').strip()
    if not title:
        print("  ⚠️  No title found, cannot search for published version")
        return None, None

    print(f"  🔍 Searching for published version of: {title[:60]}...")

    # Method 1: Try Semantic Scholar API (most reliable for arXiv)
    arxiv_id = extract_arxiv_id(entry)
    if arxiv_id:
        print(f"     → Searching Semantic Scholar for arXiv:{arxiv_id}")
        result = search_semantic_scholar(arxiv_id, delay)
        if result and result.get('doi'):
            doi = result['doi']
            print(f"     ✓ Found published version via Semantic Scholar: {doi}")
            bibtex = fetch_bibtex_from_doi(doi, delay)
            if bibtex:
                return doi, bibtex

    # Method 2: Try DBLP (excellent for computer science papers)
    print(f"     → Searching DBLP by title")
    result = search_dblp(title, delay)
    if result and result.get('doi'):
        doi = result['doi']
        print(f"     ✓ Found published version via DBLP: {doi}")
        bibtex = fetch_bibtex_from_doi(doi, delay)
        if bibtex:
            return doi, bibtex

    # Method 3: Try CrossRef (comprehensive but may have false positives)
    print(f"     → Searching CrossRef by title")
    result = search_crossref_by_title(title, delay)
    if result and result.get('DOI'):
        doi = result['DOI']
        print(f"     ✓ Found published version via CrossRef: {doi}")
        bibtex = fetch_bibtex_from_doi(doi, delay)
        if bibtex:
            return doi, bibtex

    print(f"     ✗ No published version found")
    return None, None


if __name__ == "__main__":
    # Test the detector
    test_entry = {
        'ENTRYTYPE': 'article',
        'ID': 'test',
        'title': 'Attention Is All You Need',
        'author': 'Vaswani, Ashish and others',
        'journal': 'arXiv preprint arXiv:1706.03762',
        'year': '2017',
        'eprint': '1706.03762',
        'archiveprefix': 'arXiv'
    }

    print("Testing arXiv detector...")
    print(f"Is arXiv entry: {is_arxiv_entry(test_entry)}")
    print(f"arXiv ID: {extract_arxiv_id(test_entry)}")

    doi, bibtex = find_published_version(test_entry)
    if doi:
        print(f"\nPublished DOI: {doi}")
        print(f"BibTeX preview: {bibtex[:200]}...")
    else:
        print("\nNo published version found")
