#!/usr/bin/env python3
"""
IEEE API Research Script

This script explores alternative IEEE API endpoints to find more reliable methods
for fetching BibTeX citations from IEEE Xplore.

Usage:
    python ieee_api_research.py
"""

import requests
import re
import time
from typing import Dict, List, Optional

# Test DOIs from the IEEE_FAILURE_ANALYSIS.md
TEST_DOIS = [
    "10.1109/TWC.2024.3396161",  # Known working DOI
    "10.1109/ICCAKM54721.2021.9675934",  # Known failing DOI
    "10.1109/ACCESS.2020.3013148",  # Known failing DOI
    "10.1109/ACCESS.2023.3276915",  # Known failing DOI
]

# Alternative API endpoints to test
API_ENDPOINTS = {
    "citation_download": "https://ieeexplore.ieee.org/xpl/downloadCitations",
    "rest_citation": "https://ieeexplore.ieee.org/rest/search/citation/download",
    "rest_document": "https://ieeexplore.ieee.org/rest/document/{article_num}/citation",
    "ielx_export": "https://ieeexplore.ieee.org/ielx/export/cite",
}


def extract_article_number(doi: str) -> Optional[str]:
    """Extract article number from IEEE DOI"""
    # Try direct resolution
    try:
        response = requests.get(f"https://doi.org/{doi}", allow_redirects=True, timeout=10)
        match = re.search(r'/document/(\d+)', response.url)
        if match:
            return match.group(1)
    except:
        pass

    # Try regex extraction from DOI
    patterns = [
        r'10\.1109/[^/]+/(\d+)',
        r'10\.1109/[^.]+\.(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, doi)
        if match:
            return match.group(1)

    return None


def test_citation_download(doi: str, article_num: str) -> Dict:
    """Test the /xpl/downloadCitations endpoint"""
    url = API_ENDPOINTS["citation_download"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Try different parameter combinations
    test_cases = [
        {
            'recordIds': article_num,
            'citations-format': 'citation-abstract',
            'download-format': 'download-bibtex'
        },
        {
            'recordIds': article_num,
            'download-format': 'download-bibtex',
            'format': 'bibtex'
        },
        {
            'recordIds': article_num,
            'fromPage': 'true',
            'recordType': 'cite',
            'citations-format': 'download-bibtex'
        },
    ]

    results = []
    for i, data in enumerate(test_cases):
        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            results.append({
                'case': i + 1,
                'status': response.status_code,
                'success': response.status_code == 200 and len(response.text) > 100,
                'length': len(response.text),
                'preview': response.text[:200] if response.text else None
            })
        except Exception as e:
            results.append({
                'case': i + 1,
                'error': str(e)
            })

    return {
        'endpoint': 'citation_download',
        'results': results
    }


def test_rest_citation(doi: str, article_num: str) -> Dict:
    """Test the /rest/search/citation/download endpoint"""
    url = API_ENDPOINTS["rest_citation"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.post(url, json={'articleNumber': article_num}, headers=headers, timeout=10)
        return {
            'endpoint': 'rest_citation',
            'status': response.status_code,
            'success': response.status_code == 200,
            'length': len(response.text),
            'preview': response.text[:200] if response.text else None
        }
    except Exception as e:
        return {
            'endpoint': 'rest_citation',
            'error': str(e)
        }


def test_rest_document(doi: str, article_num: str) -> Dict:
    """Test the /rest/document/{article_num}/citation endpoint"""
    url = API_ENDPOINTS["rest_document"].format(article_num=article_num)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return {
            'endpoint': 'rest_document',
            'status': response.status_code,
            'success': response.status_code == 200,
            'length': len(response.text),
            'preview': response.text[:200] if response.text else None
        }
    except Exception as e:
        return {
            'endpoint': 'rest_document',
            'error': str(e)
        }


def run_research():
    """Run comprehensive API research"""
    print("="*80)
    print("IEEE API RESEARCH RESULTS")
    print("="*80)
    print()

    for doi in TEST_DOIS:
        print(f"\nTesting DOI: {doi}")
        print("-" * 80)

        # Extract article number
        article_num = extract_article_number(doi)
        if not article_num:
            print(f"  ✗ Could not extract article number")
            continue

        print(f"  Article Number: {article_num}")
        print()

        # Test each endpoint
        endpoints = [
            ("Citation Download", test_citation_download),
            ("REST Citation", test_rest_citation),
            ("REST Document", test_rest_document),
        ]

        for name, test_func in endpoints:
            print(f"  Testing: {name}")
            result = test_func(doi, article_num)

            if 'error' in result:
                print(f"    ✗ Error: {result['error']}")
            elif 'results' in result:
                # Multiple test cases
                for case in result['results']:
                    if 'error' in case:
                        print(f"    Case {case['case']}: ✗ {case['error']}")
                    else:
                        status = "✓" if case['success'] else "✗"
                        print(f"    Case {case['case']}: {status} HTTP {case['status']} - {case['length']} bytes")
                        if case.get('preview'):
                            print(f"      Preview: {case['preview'][:100]}...")
            else:
                status = "✓" if result.get('success') else "✗"
                print(f"    {status} HTTP {result.get('status')} - {result.get('length', 0)} bytes")
                if result.get('preview'):
                    print(f"      Preview: {result['preview'][:100]}...")

            print()

        # Rate limiting
        time.sleep(2)

    print("="*80)
    print("RESEARCH COMPLETE")
    print("="*80)


if __name__ == '__main__':
    run_research()
