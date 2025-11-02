"""
Pytest configuration and shared fixtures for Awesome-Citations test suite.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return the test data directory."""
    return project_root / "tests" / "test_data"


@pytest.fixture(scope="session")
def fixtures_dir(project_root):
    """Return the fixtures directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture(scope="session")
def config_file(project_root):
    """Return the path to config.json."""
    return project_root / "config.json"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_config():
    """Return a sample configuration dictionary."""
    return {
        "citation_style": "ieee",
        "title_format": "titlecase",
        "journal_format": "abbreviation",
        "author_format": "first_last",
        "page_format": "double_dash",
        "arxiv_handling": "replace_with_published",
        "merge_multiple_sources": True,
        "parallel_processing": False,  # Disable for predictable testing
        "max_workers": 2,
        "request_delay": 1.0,
        "pdf_output": {
            "enabled": True,
            "document_title": "Test References",
            "sort_by": "author",
            "font_size": "11pt"
        },
        "logging": {
            "enabled": True,
            "output_file": "test_changes_log.md",
            "verbose": True
        }
    }


@pytest.fixture
def temp_config_file(temp_dir, sample_config):
    """Create a temporary config file for testing."""
    config_path = temp_dir / "test_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2)
    return config_path


@pytest.fixture
def sample_bibtex_entry():
    """Return a sample BibTeX entry as a dictionary."""
    return {
        'ID': 'smith2023deep',
        'ENTRYTYPE': 'article',
        'title': 'A Deep Learning Approach for Image Recognition',
        'author': 'Smith, John and Doe, Jane',
        'year': '2023',
        'journal': 'IEEE Transactions on Pattern Analysis and Machine Intelligence',
        'volume': '45',
        'number': '3',
        'pages': '123-135',
        'doi': '10.1109/TPAMI.2023.1234567'
    }


@pytest.fixture
def incomplete_bibtex_entry():
    """Return an incomplete BibTeX entry missing important fields."""
    return {
        'ID': 'johnson2022ml',
        'ENTRYTYPE': 'article',
        'title': 'machine learning in healthcare',
        'author': 'Johnson, Alice',
        'year': '2022',
        'doi': '10.1145/3491234.5678901'
    }


@pytest.fixture
def arxiv_bibtex_entry():
    """Return a BibTeX entry for an arXiv preprint."""
    return {
        'ID': 'vaswani2017attention',
        'ENTRYTYPE': 'article',
        'title': 'Attention Is All You Need',
        'author': 'Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, Lukasz and Polosukhin, Illia',
        'year': '2017',
        'journal': 'arXiv preprint arXiv:1706.03762',
        'eprint': '1706.03762',
        'archivePrefix': 'arXiv'
    }


@pytest.fixture
def create_temp_bib_file(temp_dir):
    """Factory fixture to create temporary BibTeX files."""
    def _create_file(entries, filename="test.bib"):
        """
        Create a BibTeX file from a list of entry dictionaries.

        Args:
            entries: List of entry dictionaries
            filename: Name of the output file

        Returns:
            Path to the created file
        """
        db = BibDatabase()
        db.entries = entries

        writer = BibTexWriter()
        writer.indent = '  '
        writer.order_entries_by = 'id'

        filepath = temp_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(writer.write(db))

        return filepath

    return _create_file


@pytest.fixture
def load_bibtex_file():
    """Factory fixture to load and parse BibTeX files."""
    def _load_file(filepath):
        """
        Load and parse a BibTeX file.

        Args:
            filepath: Path to the BibTeX file

        Returns:
            BibDatabase object
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            parser.customization = bibtexparser.customization.convert_to_unicode
            return bibtexparser.load(f, parser=parser)

    return _load_file


@pytest.fixture
def assert_bibtex_field():
    """Helper fixture for asserting BibTeX field values."""
    def _assert_field(entry, field, expected_value, message=None):
        """
        Assert that a BibTeX entry has a specific field value.

        Args:
            entry: BibTeX entry dictionary
            field: Field name to check
            expected_value: Expected value
            message: Optional custom assertion message
        """
        assert field in entry, f"Field '{field}' not found in entry '{entry.get('ID', 'unknown')}'"
        actual_value = entry[field]
        if message:
            assert actual_value == expected_value, message
        else:
            assert actual_value == expected_value, \
                f"Field '{field}' in entry '{entry['ID']}': expected '{expected_value}', got '{actual_value}'"

    return _assert_field


@pytest.fixture
def check_file_exists():
    """Helper fixture to check if files exist."""
    def _check(filepath, should_exist=True):
        """
        Check if a file exists.

        Args:
            filepath: Path to check
            should_exist: Whether the file should exist (default True)
        """
        exists = Path(filepath).exists()
        if should_exist:
            assert exists, f"Expected file does not exist: {filepath}"
        else:
            assert not exists, f"File should not exist: {filepath}"

    return _check


@pytest.fixture(scope="session")
def api_rate_limiter():
    """
    Rate limiter for API tests to respect service limits.
    Ensures 1 second delay between API calls.
    """
    import time
    last_call_time = {'time': 0}

    def _wait():
        current_time = time.time()
        elapsed = current_time - last_call_time['time']
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        last_call_time['time'] = time.time()

    return _wait


@pytest.fixture
def mock_api_response():
    """Factory fixture for creating mock API responses."""
    def _create_response(status_code=200, content="", json_data=None):
        """
        Create a mock response object.

        Args:
            status_code: HTTP status code
            content: Response content as string
            json_data: JSON data to return

        Returns:
            Mock response object
        """
        class MockResponse:
            def __init__(self, status_code, content, json_data):
                self.status_code = status_code
                self.content = content
                self._json_data = json_data
                self.text = content

            def json(self):
                return self._json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise Exception(f"HTTP Error {self.status_code}")

        return MockResponse(status_code, content, json_data)

    return _create_response


# Pytest hooks for custom test behavior

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "requires_latex: mark test as requiring LaTeX installation"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network connectivity"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add 'api' marker to tests with 'api' in name
        if 'api' in item.nodeid.lower():
            item.add_marker(pytest.mark.api)

        # Add 'slow' marker to integration tests
        if 'integration' in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)

        # Add 'pdf' marker to PDF generation tests
        if 'pdf' in item.nodeid.lower() or 'generate_pdf' in item.nodeid.lower():
            item.add_marker(pytest.mark.pdf)
