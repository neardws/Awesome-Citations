import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
import time
import json
import os
from typing import Dict, Optional, Tuple, List

# DOI prefix to publisher mapping
DOI_PUBLISHERS = {
    '10.1109': 'IEEE',
    '10.1145': 'ACM',
    '10.1007': 'Springer',
    '10.1016': 'Elsevier',
    '10.48550': 'arXiv',
}

# Important BibTeX fields to check for completeness
IMPORTANT_FIELDS = ['author', 'title', 'year', 'journal', 'booktitle',
                    'volume', 'number', 'pages', 'publisher', 'doi']

# Cache configuration
CACHE_DIR = '.cache'
CACHE_EXPIRY_DAYS = 30

# Failed DOI log configuration
FAILED_DOI_LOG_DIR = 'data'
FAILED_DOI_LOG_FILE = 'failed_dois.json'

# DOI corrections database
DOI_CORRECTIONS_FILE = 'doi_corrections.json'

# Network configuration
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 1  # Results in delays: 1s, 2s, 4s
RATE_LIMIT_DELAY = 0.5  # seconds between API calls
RATE_LIMIT_CACHE_DELAY = 0.2  # seconds for cached responses

def create_session(use_proxy: bool = True, verify_ssl: bool = True) -> requests.Session:
    """Create a requests session with retry strategy and error handling."""
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"]
    )

    # Mount adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Configure proxies
    if not use_proxy:
        session.proxies = {}
        session.trust_env = False

    # Configure SSL verification
    if not verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False

    return session

def safe_request(url: str, method: str = 'GET', session: Optional[requests.Session] = None,
                 retry_without_proxy: bool = True, **kwargs) -> Optional[requests.Response]:
    """Make a request with error handling and automatic proxy fallback."""
    if session is None:
        session = create_session()

    # Set default timeout if not provided
    if 'timeout' not in kwargs:
        kwargs['timeout'] = REQUEST_TIMEOUT

    try:
        if method == 'GET':
            response = session.get(url, **kwargs)
        elif method == 'POST':
            response = session.post(url, **kwargs)
        elif method == 'HEAD':
            response = session.head(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response

    except requests.exceptions.ProxyError as e:
        if retry_without_proxy:
            print(f"  ⚠️  Proxy error detected, retrying without proxy...")
            # Create new session without proxy
            no_proxy_session = create_session(use_proxy=False)
            return safe_request(url, method, no_proxy_session, retry_without_proxy=False, **kwargs)
        else:
            print(f"  ✗ Proxy error: {e}")
            return None

    except requests.exceptions.SSLError as e:
        if kwargs.get('verify', True):
            print(f"  ⚠️  SSL error detected, retrying with SSL verification disabled...")
            # Retry with SSL verification disabled
            kwargs['verify'] = False
            ssl_session = create_session(verify_ssl=False)
            return safe_request(url, method, ssl_session, retry_without_proxy=False, **kwargs)
        else:
            print(f"  ✗ SSL error: {e}")
            return None

    except requests.exceptions.Timeout as e:
        print(f"  ✗ Timeout error: {e}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Request error: {e}")
        return None

    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return None

def init_cache():
    """Initialize cache directory."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(doi: str) -> str:
    """Get cache file path for a DOI."""
    # Replace problematic characters in DOI for filename
    safe_doi = doi.replace('/', '_').replace('\\', '_')
    return os.path.join(CACHE_DIR, f"{safe_doi}.json")

def get_cached_bibtex(doi: str) -> Optional[str]:
    """Retrieve cached BibTeX entry if available and not expired."""
    cache_path = get_cache_path(doi)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # Check expiry
        cached_time = cache_data.get('timestamp', 0)
        current_time = time.time()
        days_elapsed = (current_time - cached_time) / (24 * 3600)

        if days_elapsed > CACHE_EXPIRY_DAYS:
            print(f"  Cache expired (age: {days_elapsed:.1f} days)")
            return None

        print(f"  ✓ Using cached data (age: {days_elapsed:.1f} days)")
        return cache_data.get('bibtex')

    except Exception as e:
        print(f"  Cache read error: {e}")
        return None

def cache_bibtex(doi: str, bibtex: str):
    """Cache a BibTeX entry."""
    try:
        init_cache()
        cache_path = get_cache_path(doi)

        cache_data = {
            'doi': doi,
            'bibtex': bibtex,
            'timestamp': time.time()
        }

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"  Cache write error: {e}")


def init_failed_doi_log():
    """Initialize failed DOI log directory."""
    if not os.path.exists(FAILED_DOI_LOG_DIR):
        os.makedirs(FAILED_DOI_LOG_DIR)

def get_failed_doi_log_path() -> str:
    """Get the path to the failed DOI log file."""
    return os.path.join(FAILED_DOI_LOG_DIR, FAILED_DOI_LOG_FILE)

def load_failed_dois() -> List[Dict]:
    """Load existing failed DOI log."""
    log_path = get_failed_doi_log_path()
    if not os.path.exists(log_path):
        return []

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  Warning: Could not load failed DOI log: {e}")
        return []

def log_failed_doi(doi: str, entry_id: str, publisher: Optional[str],
                   error_message: str, http_status: Optional[int] = None):
    """Log a failed DOI fetch attempt."""
    try:
        init_failed_doi_log()
        failed_dois = load_failed_dois()

        # Create log entry
        log_entry = {
            'doi': doi,
            'entry_id': entry_id,
            'publisher': publisher or 'Unknown',
            'error_message': error_message,
            'http_status': http_status,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Append new entry
        failed_dois.append(log_entry)

        # Write back to file
        log_path = get_failed_doi_log_path()
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(failed_dois, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"  Warning: Could not log failed DOI: {e}")

def get_doi_corrections_path() -> str:
    """Get the path to the DOI corrections file."""
    return os.path.join(FAILED_DOI_LOG_DIR, DOI_CORRECTIONS_FILE)

def load_doi_corrections() -> Dict[str, Dict]:
    """
    Load DOI corrections database.

    Returns:
        Dictionary mapping original DOI to correction info
    """
    corrections_path = get_doi_corrections_path()
    if not os.path.exists(corrections_path):
        return {}

    try:
        with open(corrections_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            corrections_list = data.get('corrections', [])

            # Convert list to dict for easy lookup
            corrections_dict = {}
            for correction in corrections_list:
                orig_doi = correction.get('original_doi')
                if orig_doi:
                    corrections_dict[orig_doi] = correction

            return corrections_dict

    except Exception as e:
        print(f"  Warning: Could not load DOI corrections: {e}")
        return {}

def apply_doi_correction(doi: str) -> Tuple[Optional[str], bool, str]:
    """
    Apply DOI correction if available.

    Args:
        doi: Original DOI to check

    Returns:
        Tuple of (corrected_doi: Optional[str], is_corrected: bool, message: str)
    """
    corrections = load_doi_corrections()

    if doi in corrections:
        correction = corrections[doi]
        status = correction.get('status')
        corrected_doi = correction.get('corrected_doi')
        reason = correction.get('reason', '')

        if status == 'invalid':
            return None, True, f"DOI marked as invalid in corrections database: {reason}"
        elif status == 'corrected' and corrected_doi:
            return corrected_doi, True, f"DOI corrected: {doi} → {corrected_doi} ({reason})"
        elif status == 'pending':
            return None, True, f"DOI correction pending research: {reason}"

    return doi, False, ""

def extract_doi(entry: Dict) -> Optional[str]:
    """Extract DOI from a BibTeX entry."""
    # Check doi field
    if 'doi' in entry and entry['doi']:
        doi = entry['doi'].strip()
        # Remove common prefixes
        doi = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', doi)
        return doi

    # Try to extract from URL
    if 'url' in entry and entry['url']:
        url = entry['url']

        # Check for DOI in URL
        match = re.search(r'doi\.org/(10\.\d+/[^\s]+)', url)
        if match:
            return match.group(1)

        # Check for arXiv URL and extract arXiv ID
        # Supports both formats: arxiv.org/abs/2410.03805 and arxiv.org/abs/cs/0704001
        arxiv_match = re.search(r'arxiv\.org/(?:abs|pdf)/([a-zA-Z-]+/\d+|\d+\.\d+)', url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            # Convert arXiv ID to DOI format
            doi = f'10.48550/arXiv.{arxiv_id}'
            print(f"  Extracted arXiv ID from URL: {arxiv_id} → DOI: {doi}")
            return doi

    return None

def verify_doi_exists(doi: str) -> Tuple[bool, str]:
    """
    Verify if a DOI exists by checking DOI.org resolution.

    Args:
        doi: The DOI to verify

    Returns:
        Tuple of (exists: bool, error_message: str)
    """
    if not doi:
        return False, "Empty DOI"

    # Validate DOI format (should start with 10. followed by prefix)
    if not doi.startswith('10.'):
        return False, f"Invalid DOI format (must start with '10.'): {doi}"

    # Check DOI structure
    if '/' not in doi:
        return False, f"Invalid DOI structure (missing '/'): {doi}"

    try:
        doi_url = f"https://doi.org/{doi}"
        # Use HEAD request for faster validation
        response = safe_request(doi_url, method='HEAD')

        if response is None:
            return False, "DOI resolution failed (network error)"

        status_code = response.status_code

        if status_code == 200 or status_code == 302:
            return True, ""
        elif status_code == 404:
            return False, f"DOI not found in DOI.org database (HTTP 404)"
        elif status_code == 403:
            return False, f"Access forbidden to DOI resource (HTTP 403)"
        else:
            return False, f"DOI resolution returned HTTP {status_code}"

    except Exception as e:
        return False, f"DOI verification error: {str(e)}"

def identify_publisher(doi: str) -> Optional[str]:
    """Identify publisher from DOI prefix."""
    for prefix, publisher in DOI_PUBLISHERS.items():
        if doi.startswith(prefix):
            return publisher
    return None

def fetch_bibtex_from_ieee(doi: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch BibTeX from IEEE Xplore.

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    try:
        # IEEE Xplore citation download URL
        # First, find the article number from DOI
        article_match = re.search(r'10\.1109/([^/]+)/(\d+)', doi)
        if not article_match:
            article_match = re.search(r'10\.1109/[^.]+\.(\d+)', doi)

        if not article_match:
            return None, "Cannot extract article number from DOI format"

        # Try to access the DOI URL to get the article number
        doi_url = f"https://doi.org/{doi}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = safe_request(doi_url, headers=headers, allow_redirects=True)
        if not response:
            return None, "DOI resolution failed (network error or timeout)"

        if response.status_code == 404:
            return None, f"DOI not found (HTTP 404) at {doi_url}"
        elif response.status_code != 200:
            return None, f"DOI resolution failed with HTTP {response.status_code}"

        # Extract article number from redirected URL
        article_num_match = re.search(r'/document/(\d+)', response.url)
        if not article_num_match:
            return None, f"Cannot extract article number from redirected URL: {response.url}"

        article_num = article_num_match.group(1)

        # IEEE citation export URL
        cite_url = f"https://ieeexplore.ieee.org/xpl/downloadCitations"

        # POST request to get BibTeX
        data = {
            'recordIds': article_num,
            'citations-format': 'citation-abstract',
            'download-format': 'download-bibtex'
        }

        response = safe_request(cite_url, method='POST', headers=headers, data=data)

        if not response:
            return None, "IEEE citation download API failed (network error)"

        if response.status_code == 404:
            return None, f"IEEE citation API returned 404 (article {article_num} not found)"
        elif response.status_code == 403:
            return None, "IEEE citation API returned 403 (access forbidden - may require authentication)"
        elif response.status_code != 200:
            return None, f"IEEE citation API failed with HTTP {response.status_code}"

        if response.text:
            return response.text, None
        else:
            return None, "IEEE returned empty response"

    except Exception as e:
        return None, f"IEEE fetch exception: {str(e)}"

def fetch_bibtex_from_ieee_selenium(doi: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch BibTeX from IEEE Xplore using Selenium (fallback method).

    This method simulates a real browser to bypass API restrictions.

    Args:
        doi: IEEE DOI

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    try:
        # Import Selenium only when needed
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import TimeoutException, NoSuchElementException
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
        except ImportError:
            return None, "Selenium packages not installed (pip install selenium webdriver-manager)"

        print(f"  Using Selenium browser automation...")

        # Set up headless Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Navigate to DOI
            doi_url = f"https://doi.org/{doi}"
            driver.get(doi_url)

            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Check if we're on IEEE Xplore
            if 'ieeexplore.ieee.org' not in driver.current_url:
                return None, f"DOI did not resolve to IEEE Xplore (got: {driver.current_url})"

            # Try to find and click the "Cite This" button
            try:
                cite_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cite This')]"))
                )
                cite_button.click()
                time.sleep(1)  # Wait for modal to open
            except TimeoutException:
                # Try alternative selectors
                try:
                    cite_button = driver.find_element(By.CLASS_NAME, "cite-this-btn")
                    cite_button.click()
                    time.sleep(1)
                except NoSuchElementException:
                    return None, "Could not find 'Cite This' button on IEEE page"

            # Find and click BibTeX tab
            try:
                bibtex_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'BibTeX')]"))
                )
                bibtex_tab.click()
                time.sleep(0.5)
            except TimeoutException:
                return None, "Could not find BibTeX tab in citation modal"

            # Extract BibTeX text
            try:
                bibtex_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "citation-text"))
                )
                bibtex_text = bibtex_element.text

                if bibtex_text:
                    return bibtex_text, None
                else:
                    return None, "BibTeX element found but empty"

            except TimeoutException:
                # Try alternative selectors
                try:
                    bibtex_element = driver.find_element(By.TAG_NAME, "pre")
                    bibtex_text = bibtex_element.text
                    if bibtex_text and bibtex_text.startswith('@'):
                        return bibtex_text, None
                except NoSuchElementException:
                    pass

                return None, "Could not extract BibTeX text from page"

        finally:
            # Always close the browser
            driver.quit()

    except ImportError:
        return None, "Selenium not installed"
    except Exception as e:
        return None, f"Selenium fetch exception: {str(e)}"

def fetch_bibtex_from_acm(doi: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch BibTeX from ACM Digital Library.

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    try:
        doi_url = f"https://doi.org/{doi}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Get the ACM article page
        response = safe_request(doi_url, headers=headers, allow_redirects=True)
        if not response:
            return None, "DOI resolution failed (network error or timeout)"

        if response.status_code == 404:
            return None, f"DOI not found (HTTP 404) at {doi_url}"
        elif response.status_code != 200:
            return None, f"DOI resolution failed with HTTP {response.status_code}"

        # Extract article ID from URL
        article_match = re.search(r'/doi/(?:abs/|full/)?10\.1145/(\d+)', response.url)
        if not article_match:
            return None, f"Cannot extract ACM article ID from URL: {response.url}"

        article_id = article_match.group(1)

        # ACM BibTeX export URL
        bibtex_url = f"https://dl.acm.org/doi/{doi}/bibtex"

        response = safe_request(bibtex_url, headers=headers)

        if not response:
            return None, "ACM BibTeX API failed (network error)"

        if response.status_code == 404:
            return None, f"ACM BibTeX page not found (HTTP 404)"
        elif response.status_code == 403:
            return None, "ACM returned 403 (access forbidden - may require authentication)"
        elif response.status_code != 200:
            return None, f"ACM BibTeX API failed with HTTP {response.status_code}"

        # Parse HTML to extract BibTeX
        soup = BeautifulSoup(response.text, 'html.parser')
        pre_tag = soup.find('pre') or soup.find('div', class_='citation')

        if pre_tag:
            return pre_tag.get_text(), None
        else:
            return None, "BibTeX content not found in ACM page HTML"

    except Exception as e:
        return None, f"ACM fetch exception: {str(e)}"

def fetch_bibtex_from_arxiv(doi: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch BibTeX from arXiv.

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    try:
        # Extract arXiv ID from DOI
        arxiv_match = re.search(r'10\.48550/arXiv\.(.+)', doi)
        if not arxiv_match:
            return None, "Cannot extract arXiv ID from DOI"

        arxiv_id = arxiv_match.group(1)

        # arXiv API URL
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

        response = safe_request(api_url)
        if not response:
            return None, "arXiv API request failed (network error or timeout)"

        if response.status_code == 404:
            return None, f"arXiv article not found (HTTP 404)"
        elif response.status_code != 200:
            return None, f"arXiv API failed with HTTP {response.status_code}"

        # Parse XML response
        soup = BeautifulSoup(response.text, 'xml')
        entry = soup.find('entry')

        if not entry:
            return None, "No entry found in arXiv API response"

        # Extract information
        title_tag = entry.find('title')
        if not title_tag:
            return None, "Title not found in arXiv response"

        title = title_tag.get_text().strip().replace('\n', ' ')
        authors = [author.find('name').get_text() for author in entry.find_all('author')]

        published_tag = entry.find('published')
        if not published_tag:
            return None, "Publication date not found in arXiv response"

        published = published_tag.get_text()[:4]  # Year

        summary_tag = entry.find('summary')
        summary = summary_tag.get_text().strip().replace('\n', ' ') if summary_tag else ""

        # Format as BibTeX
        author_str = ' and '.join(authors)
        bibtex_id = f"arxiv{arxiv_id.replace('.', '_')}"

        bibtex = f"""@article{{{bibtex_id},
  title={{{title}}},
  author={{{author_str}}},
  journal={{arXiv preprint arXiv:{arxiv_id}}},
  year={{{published}}},
  doi={{{doi}}},
  abstract={{{summary}}}
}}"""

        return bibtex, None

    except Exception as e:
        return None, f"arXiv fetch exception: {str(e)}"

def fetch_bibtex_from_crossref(doi: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch BibTeX from CrossRef API (fallback).

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    try:
        url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; BibTeXCompleter/1.0; mailto:user@example.com)'
        }

        response = safe_request(url, headers=headers)

        if not response:
            return None, "CrossRef API request failed (network error or timeout)"

        if response.status_code == 404:
            return None, f"DOI not found in CrossRef database (HTTP 404)"
        elif response.status_code == 403:
            return None, "CrossRef returned 403 (access forbidden)"
        elif response.status_code != 200:
            return None, f"CrossRef API failed with HTTP {response.status_code}"

        if response.text:
            return response.text, None
        else:
            return None, "CrossRef returned empty response"

    except Exception as e:
        return None, f"CrossRef fetch exception: {str(e)}"

def fetch_bibtex_from_scholar(title: str, author: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch BibTeX from Google Scholar as fallback.

    Args:
        title: Paper title to search for
        author: Optional author name for more precise matching

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    try:
        # Import scholarly only when needed to avoid dependency issues
        try:
            from scholarly import scholarly
        except ImportError:
            return None, "scholarly package not installed (pip install scholarly)"

        # Build search query
        search_query = title
        if author:
            search_query = f"{title} {author}"

        print(f"  Searching Google Scholar for: {title[:50]}...")

        # Search for publication
        search_results = scholarly.search_pubs(search_query)

        # Get first result
        try:
            first_result = next(search_results)
        except StopIteration:
            return None, f"No results found on Google Scholar for title: {title[:50]}"

        # Check title similarity (basic check)
        result_title = first_result.get('bib', {}).get('title', '')
        if not result_title:
            return None, "Google Scholar result missing title"

        # Simple similarity check - titles should have significant overlap
        title_words = set(title.lower().split())
        result_words = set(result_title.lower().split())
        overlap = len(title_words & result_words)
        min_len = min(len(title_words), len(result_words))

        if min_len > 0 and overlap / min_len < 0.5:
            return None, f"Google Scholar result title mismatch (overlap: {overlap}/{min_len})"

        # Extract bibliographic info
        bib = first_result.get('bib', {})
        pub_year = bib.get('pub_year', 'Unknown')
        authors = bib.get('author', [])
        venue = bib.get('venue', bib.get('journal', 'Unknown'))
        abstract = bib.get('abstract', '')

        # Try to get more complete info if available
        try:
            filled_result = scholarly.fill(first_result)
            bib = filled_result.get('bib', bib)
        except:
            pass  # Use original if fill fails

        # Generate BibTeX entry
        # Determine entry type
        entry_type = 'article'
        if 'conference' in venue.lower() or 'proceedings' in venue.lower():
            entry_type = 'inproceedings'

        # Generate citation key
        first_author = authors[0].split()[-1] if authors else "unknown"
        cite_key = f"{first_author.lower()}{pub_year}{title.split()[0].lower() if title.split() else 'paper'}"

        # Format authors
        author_str = ' and '.join(authors) if authors else 'Unknown'

        # Build BibTeX
        bibtex_lines = [f"@{entry_type}{{{cite_key},"]
        bibtex_lines.append(f"  title={{{result_title}}},")
        bibtex_lines.append(f"  author={{{author_str}}},")

        if entry_type == 'article':
            bibtex_lines.append(f"  journal={{{venue}}},")
        else:
            bibtex_lines.append(f"  booktitle={{{venue}}},")

        bibtex_lines.append(f"  year={{{pub_year}}},")

        if abstract:
            # Truncate long abstracts
            if len(abstract) > 500:
                abstract = abstract[:497] + "..."
            bibtex_lines.append(f"  abstract={{{abstract}}},")

        # Add URL if available
        if 'pub_url' in first_result:
            bibtex_lines.append(f"  url={{{first_result['pub_url']}}},")

        bibtex_lines.append("}")
        bibtex = "\n".join(bibtex_lines)

        return bibtex, None

    except ImportError:
        return None, "scholarly package not installed"
    except Exception as e:
        return None, f"Google Scholar fetch exception: {str(e)}"

def fetch_complete_bibtex(doi: str, publisher: Optional[str] = None,
                          title: Optional[str] = None, author: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch complete BibTeX entry from the appropriate source.

    Args:
        doi: DOI of the publication
        publisher: Publisher name (auto-detected if not provided)
        title: Paper title (for Google Scholar fallback)
        author: Author name (for Google Scholar fallback)

    Returns:
        Tuple of (bibtex: Optional[str], error_message: Optional[str])
    """
    # Check cache first
    cached = get_cached_bibtex(doi)
    if cached:
        return cached, None

    if not publisher:
        publisher = identify_publisher(doi)

    print(f"Fetching from {publisher or 'CrossRef'} for DOI: {doi}")

    bibtex = None
    error_msg = None

    # Try publisher-specific scraper first
    if publisher == 'IEEE':
        bibtex, error_msg = fetch_bibtex_from_ieee(doi)
        if bibtex:
            cache_bibtex(doi, bibtex)
            return bibtex, None
        else:
            print(f"  ✗ IEEE error: {error_msg}")
            # Try Selenium as fallback for IEEE
            print(f"  Trying IEEE Selenium fallback...")
            bibtex, selenium_error = fetch_bibtex_from_ieee_selenium(doi)
            if bibtex:
                cache_bibtex(doi, bibtex)
                return bibtex, None
            else:
                print(f"  ✗ IEEE Selenium error: {selenium_error}")
                error_msg = f"IEEE API: {error_msg}; IEEE Selenium: {selenium_error}"
    elif publisher == 'ACM':
        bibtex, error_msg = fetch_bibtex_from_acm(doi)
        if bibtex:
            cache_bibtex(doi, bibtex)
            return bibtex, None
        else:
            print(f"  ✗ ACM error: {error_msg}")
    elif publisher == 'arXiv':
        bibtex, error_msg = fetch_bibtex_from_arxiv(doi)
        if bibtex:
            cache_bibtex(doi, bibtex)
            return bibtex, None
        else:
            print(f"  ✗ arXiv error: {error_msg}")

    # Fallback to CrossRef for any publisher
    print(f"Trying CrossRef as fallback...")
    bibtex, crossref_error = fetch_bibtex_from_crossref(doi)

    if bibtex:
        cache_bibtex(doi, bibtex)
        return bibtex, None
    else:
        print(f"  ✗ CrossRef error: {crossref_error}")

    # Final fallback to Google Scholar if title is available
    if title:
        print(f"Trying Google Scholar as final fallback...")
        # Add 2-second delay for Google Scholar rate limiting
        time.sleep(2)
        bibtex, scholar_error = fetch_bibtex_from_scholar(title, author)

        if bibtex:
            cache_bibtex(doi, bibtex)
            return bibtex, None
        else:
            print(f"  ✗ Google Scholar error: {scholar_error}")
            # Return combined error message
            final_error = f"{publisher} failed: {error_msg}; CrossRef failed: {crossref_error}; Scholar failed: {scholar_error}" if error_msg else f"CrossRef failed: {crossref_error}; Scholar failed: {scholar_error}"
            return None, final_error
    else:
        # No title available for Scholar fallback
        final_error = f"{publisher} failed: {error_msg}; CrossRef fallback failed: {crossref_error}" if error_msg else crossref_error
        return None, final_error

def parse_bibtex_string(bibtex_str: str) -> Optional[Dict]:
    """Parse a BibTeX string and return the first entry as a dictionary."""
    try:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bib_db = bibtexparser.loads(bibtex_str, parser=parser)

        if bib_db.entries:
            return bib_db.entries[0]
        return None
    except Exception as e:
        print(f"Error parsing BibTeX: {e}")
        return None

def validate_fetched_bibtex(original_entry: Dict, fetched_entry: Dict) -> Tuple[bool, str]:
    """
    Validate that fetched BibTeX matches the original entry.

    Args:
        original_entry: Original BibTeX entry
        fetched_entry: Fetched BibTeX entry to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Extract title from both entries
    orig_title = original_entry.get('title', '').lower().strip()
    fetched_title = fetched_entry.get('title', '').lower().strip()

    if not fetched_title:
        return False, "Fetched entry missing title"

    # If original has title, check similarity
    if orig_title:
        # Remove common punctuation and extra spaces
        import string
        orig_clean = orig_title.translate(str.maketrans('', '', string.punctuation)).split()
        fetched_clean = fetched_title.translate(str.maketrans('', '', string.punctuation)).split()

        # Calculate word overlap
        orig_words = set(orig_clean)
        fetched_words = set(fetched_clean)
        overlap = len(orig_words & fetched_words)
        min_len = min(len(orig_words), len(fetched_words))

        if min_len == 0:
            return False, "Title validation failed (empty title)"

        similarity = overlap / min_len

        if similarity < 0.6:  # Require at least 60% word overlap
            return False, f"Title mismatch (similarity: {similarity:.1%})"

    # Check year consistency if both have year
    orig_year = original_entry.get('year', '')
    fetched_year = fetched_entry.get('year', '')

    if orig_year and fetched_year:
        try:
            if abs(int(orig_year) - int(fetched_year)) > 1:  # Allow 1 year difference
                return False, f"Year mismatch (original: {orig_year}, fetched: {fetched_year})"
        except ValueError:
            pass  # Ignore if year is not a number

    # Check DOI match if both have DOI
    orig_doi = original_entry.get('doi', '').lower().strip()
    fetched_doi = fetched_entry.get('doi', '').lower().strip()

    if orig_doi and fetched_doi:
        # Normalize DOIs
        orig_doi = orig_doi.replace('https://', '').replace('http://', '').replace('dx.doi.org/', '').replace('doi.org/', '')
        fetched_doi = fetched_doi.replace('https://', '').replace('http://', '').replace('dx.doi.org/', '').replace('doi.org/', '')

        if orig_doi != fetched_doi:
            return False, f"DOI mismatch (original: {orig_doi}, fetched: {fetched_doi})"

    # All checks passed
    return True, ""

def check_completeness(entry: Dict) -> Tuple[List[str], List[str]]:
    """Check which important fields are present and missing."""
    present = []
    missing = []

    # Check entry type specific fields
    entry_type = entry.get('ENTRYTYPE', 'article')

    for field in IMPORTANT_FIELDS:
        # Skip journal for inproceedings, skip booktitle for articles
        if entry_type == 'inproceedings' and field == 'journal':
            continue
        if entry_type == 'article' and field == 'booktitle':
            continue

        if field in entry and entry[field] and entry[field].strip():
            present.append(field)
        else:
            missing.append(field)

    return present, missing

def merge_bibtex_entries(original: Dict, fetched: Dict, preserve_original: bool = True) -> Dict:
    """Merge fetched BibTeX data into original entry."""
    merged = original.copy()

    # Always update with fetched data for missing fields
    for key, value in fetched.items():
        if key == 'ID':
            continue  # Preserve original ID

        # Add missing fields
        if key not in merged or not merged[key] or not merged[key].strip():
            merged[key] = value
        # Update incomplete fields (if fetched has more info)
        elif not preserve_original and len(str(value)) > len(str(merged[key])):
            merged[key] = value

    return merged

def complete_bibtex_file(input_file: str, output_file: str, interactive: bool = True):
    """Complete BibTeX entries by fetching from official sources."""
    # Initialize cache and failed DOI log
    init_cache()
    init_failed_doi_log()

    # Load input file
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    total_entries = len(bib_database.entries)
    completed_count = 0
    failed_entries = []
    cache_hits = 0
    doi_validation_failures = 0

    print(f"Processing {total_entries} entries...\n")

    for i, entry in enumerate(bib_database.entries):
        entry_id = entry.get('ID', 'Unknown ID')
        print(f"[{i+1}/{total_entries}] Processing: {entry_id}")

        # Check current completeness
        present, missing = check_completeness(entry)

        if not missing:
            print(f"  ✓ Already complete (all important fields present)\n")
            continue

        print(f"  Missing fields: {', '.join(missing)}")

        # Extract DOI
        doi = extract_doi(entry)

        if not doi:
            print(f"  ✗ No DOI found")
            log_failed_doi(doi or "N/A", entry_id, None, "No DOI found in entry")
            if interactive:
                response = input(f"  Enter DOI manually (or press Enter to skip): ").strip()
                if response:
                    doi = response
                else:
                    failed_entries.append(entry_id)
                    print()
                    continue
            else:
                failed_entries.append(entry_id)
                print()
                continue

        # Apply DOI correction if available
        corrected_doi, was_corrected, correction_msg = apply_doi_correction(doi)

        if was_corrected:
            if corrected_doi is None:
                # DOI is marked as invalid or pending
                print(f"  ⚠️  {correction_msg}")
                if interactive:
                    response = input(f"  Try fetching with original DOI anyway? (y/n): ").strip().lower()
                    if response != 'y':
                        failed_entries.append(entry_id)
                        print()
                        continue
                else:
                    # In non-interactive mode, skip invalid DOIs
                    failed_entries.append(entry_id)
                    print()
                    continue
            else:
                # DOI was corrected
                print(f"  ✓ {correction_msg}")
                doi = corrected_doi

        # Validate DOI exists
        print(f"  Validating DOI: {doi}")
        doi_valid, doi_error = verify_doi_exists(doi)

        if not doi_valid:
            print(f"  ✗ DOI validation failed: {doi_error}")
            doi_validation_failures += 1
            log_failed_doi(doi, entry_id, identify_publisher(doi), f"DOI validation failed: {doi_error}")
            if interactive:
                response = input(f"  Try fetching anyway? (y/n): ").strip().lower()
                if response != 'y':
                    failed_entries.append(entry_id)
                    print()
                    continue
            else:
                failed_entries.append(entry_id)
                print()
                continue
        else:
            print(f"  ✓ DOI validated successfully")

        # Check if cached (before fetching)
        was_cached = get_cached_bibtex(doi) is not None

        # Extract title and author for potential Google Scholar fallback
        entry_title = entry.get('title', '').strip()
        entry_author = entry.get('author', '').split(' and ')[0] if 'author' in entry else None

        # Fetch complete BibTeX
        publisher = identify_publisher(doi)
        fetched_bibtex, fetch_error = fetch_complete_bibtex(doi, publisher, entry_title, entry_author)

        if not fetched_bibtex:
            error_msg = fetch_error or "Unknown error"
            print(f"  ✗ Failed to fetch from source: {error_msg}")
            log_failed_doi(doi, entry_id, publisher, error_msg)
            if interactive:
                response = input(f"  Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    failed_entries.append(entry_id)
                    print()
                    continue
            else:
                failed_entries.append(entry_id)
                print()
                continue

        # Parse fetched BibTeX
        fetched_entry = parse_bibtex_string(fetched_bibtex)

        if not fetched_entry:
            error_msg = "Failed to parse fetched BibTeX"
            print(f"  ✗ {error_msg}")
            log_failed_doi(doi, entry_id, publisher, error_msg)
            failed_entries.append(entry_id)
            print()
            continue

        # Validate fetched BibTeX against original
        is_valid, validation_error = validate_fetched_bibtex(entry, fetched_entry)

        if not is_valid:
            print(f"  ⚠️  Warning: Validation failed - {validation_error}")
            if interactive:
                response = input(f"  Use fetched data anyway? (y/n): ").strip().lower()
                if response != 'y':
                    log_failed_doi(doi, entry_id, publisher, f"Validation failed: {validation_error}")
                    failed_entries.append(entry_id)
                    print()
                    continue
            else:
                # In non-interactive mode, skip entries that fail validation
                print(f"  ✗ Skipping due to validation failure")
                log_failed_doi(doi, entry_id, publisher, f"Validation failed: {validation_error}")
                failed_entries.append(entry_id)
                print()
                continue
        else:
            print(f"  ✓ Fetched BibTeX validated successfully")

        # Merge entries
        merged_entry = merge_bibtex_entries(entry, fetched_entry)
        bib_database.entries[i] = merged_entry

        # Check new completeness
        new_present, new_missing = check_completeness(merged_entry)
        fields_added = len(new_present) - len(present)

        print(f"  ✓ Completed! Added {fields_added} field(s)")
        if new_missing:
            print(f"  Still missing: {', '.join(new_missing)}")

        if was_cached:
            cache_hits += 1

        completed_count += 1
        print()

        # Adaptive rate limiting: shorter delay for cached responses
        if was_cached:
            time.sleep(RATE_LIMIT_CACHE_DELAY)
        else:
            time.sleep(RATE_LIMIT_DELAY)

    # Write output file
    with open(output_file, 'w', encoding='utf-8') as output:
        bibtexparser.dump(bib_database, output)

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total entries: {total_entries}")
    print(f"  Completed: {completed_count}")
    print(f"  Failed: {len(failed_entries)}")
    print(f"  DOI validation failures: {doi_validation_failures}")
    print(f"  Cache hits: {cache_hits}")
    if failed_entries:
        print(f"  Failed IDs: {', '.join(failed_entries)}")
    print(f"\nFailed DOI log saved to: {get_failed_doi_log_path()}")
    print(f"Output saved to: {output_file}")

if __name__ == '__main__':
    input_file = 'test_input.bib'
    output_file = 'test_completed_output.bib'

    complete_bibtex_file(input_file, output_file, interactive=False)
