"""
Unit tests for complete_bibtex.py module.

Tests cover:
- DOI extraction from various fields
- Publisher identification from DOI prefixes
- BibTeX fetching from IEEE, ACM, arXiv, CrossRef
- Entry completeness checking
- Entry merging logic
- DOI validation (NEW)
- Multi-source validation (NEW)
- Error handling and propagation (NEW)
- DOI corrections database (NEW)
- Failed DOI logging (NEW)
"""

import pytest
import os
import json
from unittest.mock import patch, Mock, MagicMock
import complete_bibtex as cb


# ============================================================================
# Test DOI Extraction
# ============================================================================

class TestExtractDOI:
    """Tests for extract_doi() function."""

    @pytest.mark.unit
    def test_extract_doi_from_doi_field(self):
        """Test extracting DOI from doi field."""
        entry = {'doi': '10.1109/TPAMI.2023.1234567'}
        assert cb.extract_doi(entry) == '10.1109/TPAMI.2023.1234567'

    @pytest.mark.unit
    def test_extract_doi_with_url_prefix(self):
        """Test extracting DOI with https://doi.org/ prefix."""
        entry = {'doi': 'https://doi.org/10.1145/3456789'}
        assert cb.extract_doi(entry) == '10.1145/3456789'

    @pytest.mark.unit
    def test_extract_doi_with_dx_prefix(self):
        """Test extracting DOI with https://dx.doi.org/ prefix."""
        entry = {'doi': 'https://dx.doi.org/10.1016/j.cell.2023.01.001'}
        assert cb.extract_doi(entry) == '10.1016/j.cell.2023.01.001'

    @pytest.mark.unit
    def test_extract_doi_from_url_field(self):
        """Test extracting DOI from URL field."""
        entry = {'url': 'https://doi.org/10.1109/CVPR.2023.00123'}
        assert cb.extract_doi(entry) == '10.1109/CVPR.2023.00123'

    @pytest.mark.unit
    def test_extract_doi_no_doi_present(self):
        """Test extracting DOI when no DOI is present."""
        entry = {'title': 'Some Paper', 'author': 'John Smith'}
        assert cb.extract_doi(entry) is None

    @pytest.mark.unit
    def test_extract_doi_empty_doi_field(self):
        """Test extracting DOI from empty doi field."""
        entry = {'doi': ''}
        assert cb.extract_doi(entry) is None

    @pytest.mark.unit
    def test_extract_doi_whitespace_trimming(self):
        """Test that DOI extraction trims whitespace."""
        entry = {'doi': '  10.1109/TPAMI.2023.1234567  '}
        assert cb.extract_doi(entry) == '10.1109/TPAMI.2023.1234567'


# ============================================================================
# Test Publisher Identification
# ============================================================================

class TestIdentifyPublisher:
    """Tests for identify_publisher() function."""

    @pytest.mark.unit
    def test_identify_ieee_publisher(self):
        """Test identifying IEEE from DOI prefix."""
        assert cb.identify_publisher('10.1109/TPAMI.2023.1234567') == 'IEEE'

    @pytest.mark.unit
    def test_identify_acm_publisher(self):
        """Test identifying ACM from DOI prefix."""
        assert cb.identify_publisher('10.1145/3456789.0123456') == 'ACM'

    @pytest.mark.unit
    def test_identify_springer_publisher(self):
        """Test identifying Springer from DOI prefix."""
        assert cb.identify_publisher('10.1007/s10994-023-6789-0') == 'Springer'

    @pytest.mark.unit
    def test_identify_elsevier_publisher(self):
        """Test identifying Elsevier from DOI prefix."""
        assert cb.identify_publisher('10.1016/j.cell.2023.01.001') == 'Elsevier'

    @pytest.mark.unit
    def test_identify_arxiv_publisher(self):
        """Test identifying arXiv from DOI prefix."""
        assert cb.identify_publisher('10.48550/arXiv.1706.03762') == 'arXiv'

    @pytest.mark.unit
    def test_identify_unknown_publisher(self):
        """Test identifying unknown publisher returns None."""
        assert cb.identify_publisher('10.9999/unknown.2023.123') is None


# ============================================================================
# Test Entry Completeness Checking
# ============================================================================

class TestCheckCompleteness:
    """Tests for check_completeness() function."""

    @pytest.mark.unit
    def test_complete_article_entry(self):
        """Test checking completeness of a complete article."""
        entry = {
            'ENTRYTYPE': 'article',
            'ID': 'test2023',
            'author': 'Smith, John',
            'title': 'Test Paper',
            'year': '2023',
            'journal': 'Test Journal',
            'volume': '10',
            'number': '3',
            'pages': '123-135',
            'publisher': 'IEEE',
            'doi': '10.1109/TEST.2023.123'
        }
        present, missing = cb.check_completeness(entry)

        # Should have most fields present (booktitle not applicable for article)
        assert 'author' in present
        assert 'title' in present
        assert 'journal' in present
        assert 'booktitle' not in present  # Not checked for articles
        assert 'booktitle' not in missing  # Not checked for articles
        assert len(missing) == 0 or all(f != 'booktitle' for f in missing)

    @pytest.mark.unit
    def test_incomplete_article_missing_pages(self):
        """Test checking article missing pages field."""
        entry = {
            'ENTRYTYPE': 'article',
            'ID': 'test2023',
            'author': 'Smith, John',
            'title': 'Test Paper',
            'year': '2023',
            'journal': 'Test Journal'
        }
        present, missing = cb.check_completeness(entry)

        assert 'pages' in missing
        assert 'volume' in missing
        assert 'number' in missing

    @pytest.mark.unit
    def test_complete_inproceedings_entry(self):
        """Test checking completeness of a complete conference paper."""
        entry = {
            'ENTRYTYPE': 'inproceedings',
            'ID': 'test2023',
            'author': 'Smith, John',
            'title': 'Test Paper',
            'year': '2023',
            'booktitle': 'Test Conference',
            'pages': '123-135',
            'publisher': 'IEEE',
            'doi': '10.1109/TEST.2023.123'
        }
        present, missing = cb.check_completeness(entry)

        assert 'booktitle' in present
        assert 'journal' not in present  # Not applicable for inproceedings
        assert 'journal' not in missing  # Not checked for inproceedings

    @pytest.mark.unit
    def test_entry_with_empty_fields(self):
        """Test that empty string fields are counted as missing."""
        entry = {
            'ENTRYTYPE': 'article',
            'author': '',
            'title': 'Test Paper',
            'year': '2023',
            'journal': '   '  # Whitespace only
        }
        present, missing = cb.check_completeness(entry)

        assert 'author' in missing
        assert 'journal' in missing
        assert 'title' in present


# ============================================================================
# Test BibTeX Parsing
# ============================================================================

class TestParseBibtexString:
    """Tests for parse_bibtex_string() function."""

    @pytest.mark.unit
    def test_parse_valid_bibtex(self):
        """Test parsing valid BibTeX string."""
        bibtex_str = """@article{test2023,
          title={Test Paper},
          author={Smith, John},
          year={2023},
          journal={Test Journal}
        }"""

        entry = cb.parse_bibtex_string(bibtex_str)

        assert entry is not None
        assert entry['ID'] == 'test2023'
        assert entry['title'] == 'Test Paper'
        assert entry['author'] == 'Smith, John'

    @pytest.mark.unit
    def test_parse_invalid_bibtex(self):
        """Test parsing invalid BibTeX string."""
        bibtex_str = "This is not valid BibTeX"
        entry = cb.parse_bibtex_string(bibtex_str)
        assert entry is None

    @pytest.mark.unit
    def test_parse_empty_bibtex(self):
        """Test parsing empty BibTeX string."""
        entry = cb.parse_bibtex_string("")
        assert entry is None


# ============================================================================
# Test Entry Merging
# ============================================================================

class TestMergeBibtexEntries:
    """Tests for merge_bibtex_entries() function."""

    @pytest.mark.unit
    def test_merge_preserves_original_id(self):
        """Test that merging preserves the original entry ID."""
        original = {'ID': 'original2023', 'title': 'Original Title'}
        fetched = {'ID': 'fetched2023', 'title': 'Fetched Title', 'author': 'Smith, John'}

        merged = cb.merge_bibtex_entries(original, fetched)

        assert merged['ID'] == 'original2023'

    @pytest.mark.unit
    def test_merge_adds_missing_fields(self):
        """Test that merging adds missing fields from fetched entry."""
        original = {'ID': 'test2023', 'title': 'Test Paper'}
        fetched = {'ID': 'test2023', 'author': 'Smith, John', 'year': '2023', 'journal': 'Test Journal'}

        merged = cb.merge_bibtex_entries(original, fetched)

        assert merged['author'] == 'Smith, John'
        assert merged['year'] == '2023'
        assert merged['journal'] == 'Test Journal'

    @pytest.mark.unit
    def test_merge_preserves_existing_fields(self):
        """Test that merging preserves original non-empty fields by default."""
        original = {'ID': 'test2023', 'title': 'Original Title', 'author': 'Original Author'}
        fetched = {'ID': 'test2023', 'title': 'Fetched Title', 'author': 'Fetched Author'}

        merged = cb.merge_bibtex_entries(original, fetched, preserve_original=True)

        assert merged['title'] == 'Original Title'
        assert merged['author'] == 'Original Author'

    @pytest.mark.unit
    def test_merge_replaces_empty_fields(self):
        """Test that merging replaces empty fields."""
        original = {'ID': 'test2023', 'title': '', 'author': '   '}
        fetched = {'ID': 'test2023', 'title': 'Fetched Title', 'author': 'Fetched Author'}

        merged = cb.merge_bibtex_entries(original, fetched)

        assert merged['title'] == 'Fetched Title'
        assert merged['author'] == 'Fetched Author'

    @pytest.mark.unit
    def test_merge_without_preserve_chooses_longer(self):
        """Test that merging without preserve_original chooses longer values."""
        original = {'ID': 'test2023', 'title': 'Short'}
        fetched = {'ID': 'test2023', 'title': 'Much Longer Title'}

        merged = cb.merge_bibtex_entries(original, fetched, preserve_original=False)

        assert merged['title'] == 'Much Longer Title'


# ============================================================================
# Test API Fetch Functions (with mocking)
# ============================================================================

class TestFetchFunctions:
    """Tests for API fetch functions with mocked responses."""

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.requests.get')
    @patch('complete_bibtex.requests.post')
    def test_fetch_from_ieee_success(self, mock_post, mock_get):
        """Test successful fetch from IEEE."""
        # Mock the DOI redirect
        mock_response_get = Mock()
        mock_response_get.status_code = 200
        mock_response_get.url = 'https://ieeexplore.ieee.org/document/1234567'
        mock_get.return_value = mock_response_get

        # Mock the BibTeX download
        mock_response_post = Mock()
        mock_response_post.status_code = 200
        mock_response_post.text = '@article{test, title={Test Paper}}'
        mock_post.return_value = mock_response_post

        doi = '10.1109/TPAMI.2023.1234567'
        result = cb.fetch_bibtex_from_ieee(doi)

        assert result is not None
        assert 'Test Paper' in result

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.requests.get')
    def test_fetch_from_ieee_failure(self, mock_get):
        """Test failed fetch from IEEE."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        doi = '10.1109/INVALID.2023.999999'
        result = cb.fetch_bibtex_from_ieee(doi)

        assert result is None

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.requests.get')
    def test_fetch_from_acm_success(self, mock_get):
        """Test successful fetch from ACM."""
        # Mock the DOI redirect
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.url = 'https://dl.acm.org/doi/10.1145/3456789'

        # Mock the BibTeX page
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.text = '<pre>@article{test, title={Test Paper}}</pre>'

        mock_get.side_effect = [mock_response1, mock_response2]

        doi = '10.1145/3456789.0123456'
        result = cb.fetch_bibtex_from_acm(doi)

        assert result is not None
        assert 'Test Paper' in result

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.requests.get')
    def test_fetch_from_crossref_success(self, mock_get):
        """Test successful fetch from CrossRef."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '@article{test2023, title={Test Paper}}'
        mock_get.return_value = mock_response

        doi = '10.1038/s41467-023-12345-6'
        result = cb.fetch_bibtex_from_crossref(doi)

        assert result is not None
        assert '@article' in result

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.requests.get')
    def test_fetch_from_arxiv_success(self, mock_get):
        """Test successful fetch from arXiv."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Test arXiv Paper</title>
            <author><name>John Smith</name></author>
            <author><name>Jane Doe</name></author>
            <published>2023-01-15</published>
            <summary>This is a test abstract.</summary>
          </entry>
        </feed>'''
        mock_get.return_value = mock_response

        doi = '10.48550/arXiv.2301.12345'
        result = cb.fetch_bibtex_from_arxiv(doi)

        assert result is not None
        assert 'Test arXiv Paper' in result
        assert 'John Smith' in result

    @pytest.mark.unit
    @pytest.mark.api
    def test_fetch_from_arxiv_invalid_doi(self):
        """Test fetch from arXiv with invalid DOI format."""
        doi = '10.1109/NOTARXIV.2023.123'
        result = cb.fetch_bibtex_from_arxiv(doi)

        assert result is None


# ============================================================================
# Test Complete Fetch Function
# ============================================================================

class TestFetchCompleteBibtex:
    """Tests for fetch_complete_bibtex() function."""

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.fetch_bibtex_from_ieee')
    def test_fetch_complete_ieee(self, mock_ieee):
        """Test fetching complete BibTeX for IEEE paper."""
        mock_ieee.return_value = '@article{test, title={Test Paper}}'

        doi = '10.1109/TPAMI.2023.1234567'
        result = cb.fetch_complete_bibtex(doi, 'IEEE')

        assert result is not None
        mock_ieee.assert_called_once_with(doi)

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.fetch_bibtex_from_acm')
    def test_fetch_complete_acm(self, mock_acm):
        """Test fetching complete BibTeX for ACM paper."""
        mock_acm.return_value = '@article{test, title={Test Paper}}'

        doi = '10.1145/3456789.0123456'
        result = cb.fetch_complete_bibtex(doi, 'ACM')

        assert result is not None
        mock_acm.assert_called_once_with(doi)

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.fetch_bibtex_from_ieee')
    @patch('complete_bibtex.fetch_bibtex_from_crossref')
    def test_fetch_complete_fallback_to_crossref(self, mock_crossref, mock_ieee):
        """Test fallback to CrossRef when publisher-specific fetch fails."""
        mock_ieee.return_value = None
        mock_crossref.return_value = '@article{test, title={Test Paper}}'

        doi = '10.1109/TPAMI.2023.1234567'
        result = cb.fetch_complete_bibtex(doi, 'IEEE')

        assert result is not None
        mock_ieee.assert_called_once()
        mock_crossref.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.api
    @patch('complete_bibtex.identify_publisher')
    @patch('complete_bibtex.fetch_bibtex_from_crossref')
    def test_fetch_complete_auto_identify_publisher(self, mock_crossref, mock_identify):
        """Test automatic publisher identification."""
        mock_identify.return_value = 'Springer'
        mock_crossref.return_value = '@article{test, title={Test Paper}}'

        doi = '10.1007/s10994-023-6789-0'
        result = cb.fetch_complete_bibtex(doi)

        assert result is not None
        mock_identify.assert_called_once_with(doi)


# ============================================================================
# Test Integration (File Processing)
# ============================================================================

class TestCompleteBibtexFile:
    """Integration tests for complete_bibtex_file() function."""

    @pytest.mark.integration
    def test_complete_file_basic(self, test_data_dir, temp_dir, create_temp_bib_file):
        """Test basic file completion workflow."""
        # Create a simple test file
        entries = [
            {
                'ID': 'test2023',
                'ENTRYTYPE': 'article',
                'title': 'Test Paper',
                'author': 'Smith, John',
                'year': '2023',
                'doi': '10.1109/TEST.2023.123'
            }
        ]

        input_file = create_temp_bib_file(entries, 'input_test.bib')
        output_file = temp_dir / 'output_test.bib'

        # Mock the fetch function to avoid real API calls
        with patch('complete_bibtex.fetch_complete_bibtex') as mock_fetch:
            mock_fetch.return_value = '''@article{test2023,
              title={Test Paper},
              author={Smith, John},
              year={2023},
              journal={Test Journal},
              volume={10},
              pages={123-135},
              doi={10.1109/TEST.2023.123}
            }'''

            cb.complete_bibtex_file(str(input_file), str(output_file), interactive=False)

        # Verify output file exists
        assert output_file.exists()

    @pytest.mark.integration
    def test_complete_file_with_missing_doi(self, temp_dir, create_temp_bib_file):
        """Test file completion with entries missing DOI."""
        entries = [
            {
                'ID': 'test2023',
                'ENTRYTYPE': 'article',
                'title': 'Test Paper Without DOI',
                'author': 'Smith, John',
                'year': '2023'
            }
        ]

        input_file = create_temp_bib_file(entries, 'no_doi_test.bib')
        output_file = temp_dir / 'no_doi_output.bib'

        # Should handle missing DOI gracefully in non-interactive mode
        cb.complete_bibtex_file(str(input_file), str(output_file), interactive=False)

        assert output_file.exists()


# ============================================================================
# Test DOI Validation (NEW)
# ============================================================================

class TestVerifyDOIExists:
    """Tests for verify_doi_exists() function."""

    @pytest.mark.unit
    def test_verify_valid_doi_format(self):
        """Test verifying DOI with valid format."""
        with patch('complete_bibtex.safe_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            valid, error = cb.verify_doi_exists('10.1109/TPAMI.2023.1234567')

            assert valid is True
            assert error == ""

    @pytest.mark.unit
    def test_verify_doi_not_found(self):
        """Test verifying DOI that doesn't exist (404)."""
        with patch('complete_bibtex.safe_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response

            valid, error = cb.verify_doi_exists('10.1109/INVALID.2023.999')

            assert valid is False
            assert "404" in error

    @pytest.mark.unit
    def test_verify_doi_forbidden(self):
        """Test verifying DOI that returns 403."""
        with patch('complete_bibtex.safe_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.return_value = mock_response

            valid, error = cb.verify_doi_exists('10.1109/RESTRICTED.2023.123')

            assert valid is False
            assert "403" in error

    @pytest.mark.unit
    def test_verify_doi_invalid_format(self):
        """Test verifying DOI with invalid format (doesn't start with 10.)."""
        valid, error = cb.verify_doi_exists('99.1109/INVALID')

        assert valid is False
        assert "Invalid DOI format" in error

    @pytest.mark.unit
    def test_verify_doi_missing_slash(self):
        """Test verifying DOI missing slash separator."""
        valid, error = cb.verify_doi_exists('10.1109INVALID')

        assert valid is False
        assert "missing '/'" in error

    @pytest.mark.unit
    def test_verify_doi_empty(self):
        """Test verifying empty DOI."""
        valid, error = cb.verify_doi_exists('')

        assert valid is False
        assert "Empty DOI" in error

    @pytest.mark.unit
    def test_verify_doi_network_error(self):
        """Test verifying DOI with network error."""
        with patch('complete_bibtex.safe_request') as mock_request:
            mock_request.return_value = None

            valid, error = cb.verify_doi_exists('10.1109/TEST.2023.123')

            assert valid is False
            assert "network error" in error.lower()


# ============================================================================
# Test Multi-Source Validation (NEW)
# ============================================================================

class TestValidateFetchedBibtex:
    """Tests for validate_fetched_bibtex() function."""

    @pytest.mark.unit
    def test_validate_matching_titles(self):
        """Test validation with matching titles."""
        original = {
            'title': 'Deep Learning for Computer Vision',
            'year': '2023'
        }
        fetched = {
            'title': 'Deep Learning for Computer Vision',
            'year': '2023'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is True
        assert error == ""

    @pytest.mark.unit
    def test_validate_similar_titles(self):
        """Test validation with similar but not identical titles."""
        original = {
            'title': 'Deep Learning for Computer Vision Applications',
        }
        fetched = {
            'title': 'Deep Learning for Computer Vision',
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is True  # Should pass with >60% overlap

    @pytest.mark.unit
    def test_validate_title_mismatch(self):
        """Test validation with completely different titles."""
        original = {
            'title': 'Machine Learning Algorithms',
        }
        fetched = {
            'title': 'Natural Language Processing Techniques',
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is False
        assert "Title mismatch" in error

    @pytest.mark.unit
    def test_validate_year_match(self):
        """Test validation with matching years."""
        original = {
            'title': 'Test Paper',
            'year': '2023'
        }
        fetched = {
            'title': 'Test Paper',
            'year': '2023'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is True

    @pytest.mark.unit
    def test_validate_year_one_off(self):
        """Test validation with year difference of 1 (should pass)."""
        original = {
            'title': 'Test Paper',
            'year': '2023'
        }
        fetched = {
            'title': 'Test Paper',
            'year': '2024'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is True  # ±1 year tolerance

    @pytest.mark.unit
    def test_validate_year_mismatch(self):
        """Test validation with year difference > 1."""
        original = {
            'title': 'Test Paper',
            'year': '2020'
        }
        fetched = {
            'title': 'Test Paper',
            'year': '2023'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is False
        assert "Year mismatch" in error

    @pytest.mark.unit
    def test_validate_doi_match(self):
        """Test validation with matching DOIs."""
        original = {
            'title': 'Test Paper',
            'doi': '10.1109/TEST.2023.123'
        }
        fetched = {
            'title': 'Test Paper',
            'doi': '10.1109/TEST.2023.123'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is True

    @pytest.mark.unit
    def test_validate_doi_normalized_match(self):
        """Test validation with normalized DOI matching."""
        original = {
            'title': 'Test Paper',
            'doi': 'https://doi.org/10.1109/TEST.2023.123'
        }
        fetched = {
            'title': 'Test Paper',
            'doi': '10.1109/TEST.2023.123'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is True

    @pytest.mark.unit
    def test_validate_doi_mismatch(self):
        """Test validation with different DOIs."""
        original = {
            'title': 'Test Paper',
            'doi': '10.1109/TEST.2023.123'
        }
        fetched = {
            'title': 'Test Paper',
            'doi': '10.1109/TEST.2023.999'
        }

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is False
        assert "DOI mismatch" in error

    @pytest.mark.unit
    def test_validate_missing_title_in_fetched(self):
        """Test validation when fetched entry has no title."""
        original = {'title': 'Test Paper'}
        fetched = {'author': 'John Smith'}

        valid, error = cb.validate_fetched_bibtex(original, fetched)

        assert valid is False
        assert "missing title" in error.lower()


# ============================================================================
# Test DOI Corrections Database (NEW)
# ============================================================================

class TestDOICorrections:
    """Tests for DOI corrections functionality."""

    @pytest.mark.unit
    def test_load_doi_corrections_file_not_exists(self):
        """Test loading corrections when file doesn't exist."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False

            corrections = cb.load_doi_corrections()

            assert corrections == {}

    @pytest.mark.unit
    def test_load_doi_corrections_valid_file(self):
        """Test loading corrections from valid JSON file."""
        mock_data = {
            'corrections': [
                {
                    'original_doi': '10.1109/INVALID.DOI',
                    'corrected_doi': '10.1109/CORRECT.DOI',
                    'status': 'corrected'
                },
                {
                    'original_doi': '10.1109/NONEXISTENT.DOI',
                    'corrected_doi': None,
                    'status': 'invalid'
                }
            ]
        }

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_data)
                with patch('json.load', return_value=mock_data):
                    corrections = cb.load_doi_corrections()

                    assert '10.1109/INVALID.DOI' in corrections
                    assert '10.1109/NONEXISTENT.DOI' in corrections

    @pytest.mark.unit
    def test_apply_doi_correction_not_in_database(self):
        """Test applying correction for DOI not in database."""
        with patch('complete_bibtex.load_doi_corrections', return_value={}):
            corrected_doi, is_corrected, message = cb.apply_doi_correction('10.1109/TEST.2023.123')

            assert corrected_doi == '10.1109/TEST.2023.123'
            assert is_corrected is False
            assert message == ""

    @pytest.mark.unit
    def test_apply_doi_correction_corrected_status(self):
        """Test applying correction with 'corrected' status."""
        mock_corrections = {
            '10.1109/WRONG.DOI': {
                'corrected_doi': '10.1109/RIGHT.DOI',
                'status': 'corrected',
                'reason': 'Typo'
            }
        }

        with patch('complete_bibtex.load_doi_corrections', return_value=mock_corrections):
            corrected_doi, is_corrected, message = cb.apply_doi_correction('10.1109/WRONG.DOI')

            assert corrected_doi == '10.1109/RIGHT.DOI'
            assert is_corrected is True
            assert 'Typo' in message

    @pytest.mark.unit
    def test_apply_doi_correction_invalid_status(self):
        """Test applying correction with 'invalid' status."""
        mock_corrections = {
            '10.1109/INVALID.DOI': {
                'corrected_doi': None,
                'status': 'invalid',
                'reason': 'Does not exist'
            }
        }

        with patch('complete_bibtex.load_doi_corrections', return_value=mock_corrections):
            corrected_doi, is_corrected, message = cb.apply_doi_correction('10.1109/INVALID.DOI')

            assert corrected_doi is None
            assert is_corrected is True
            assert 'invalid' in message.lower()

    @pytest.mark.unit
    def test_apply_doi_correction_pending_status(self):
        """Test applying correction with 'pending' status."""
        mock_corrections = {
            '10.1109/PENDING.DOI': {
                'corrected_doi': None,
                'status': 'pending',
                'reason': 'Needs research'
            }
        }

        with patch('complete_bibtex.load_doi_corrections', return_value=mock_corrections):
            corrected_doi, is_corrected, message = cb.apply_doi_correction('10.1109/PENDING.DOI')

            assert corrected_doi is None
            assert is_corrected is True
            assert 'pending' in message.lower()


# ============================================================================
# Test Error Handling and Propagation (NEW)
# ============================================================================

class TestErrorHandling:
    """Tests for enhanced error handling."""

    @pytest.mark.unit
    @patch('complete_bibtex.safe_request')
    def test_fetch_ieee_returns_error_tuple(self, mock_request):
        """Test that IEEE fetch returns (bibtex, error) tuple."""
        mock_request.return_value = None

        result = cb.fetch_bibtex_from_ieee('10.1109/TEST.2023.123')

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] is None  # bibtex
        assert result[1] is not None  # error message

    @pytest.mark.unit
    @patch('complete_bibtex.safe_request')
    def test_fetch_ieee_error_message_content(self, mock_request):
        """Test that IEEE fetch error message is descriptive."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        bibtex, error = cb.fetch_bibtex_from_ieee('10.1109/INVALID.2023.123')

        assert bibtex is None
        assert "404" in error
        assert "DOI not found" in error or "HTTP 404" in error

    @pytest.mark.unit
    @patch('complete_bibtex.safe_request')
    def test_fetch_crossref_returns_error_tuple(self, mock_request):
        """Test that CrossRef fetch returns (bibtex, error) tuple."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        result = cb.fetch_bibtex_from_crossref('10.1109/TEST.2023.123')

        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.unit
    @patch('complete_bibtex.safe_request')
    def test_fetch_acm_http_403_error(self, mock_request):
        """Test ACM fetch handles 403 Forbidden."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_request.return_value = mock_response

        bibtex, error = cb.fetch_bibtex_from_acm('10.1145/123456')

        assert bibtex is None
        assert "403" in error


# ============================================================================
# Test Failed DOI Logging (NEW)
# ============================================================================

class TestFailedDOILogging:
    """Tests for failed DOI logging functionality."""

    @pytest.mark.unit
    def test_log_failed_doi_creates_entry(self):
        """Test that log_failed_doi creates a log entry."""
        with patch('complete_bibtex.init_failed_doi_log'):
            with patch('complete_bibtex.load_failed_dois', return_value=[]):
                with patch('builtins.open', create=True) as mock_open:
                    with patch('json.dump') as mock_dump:
                        cb.log_failed_doi(
                            doi='10.1109/INVALID.2023.123',
                            entry_id='test2023',
                            publisher='IEEE',
                            error_message='DOI not found',
                            http_status=404
                        )

                        # Verify json.dump was called
                        mock_dump.assert_called_once()
                        call_args = mock_dump.call_args[0]
                        logged_data = call_args[0]

                        # Verify structure
                        assert len(logged_data) == 1
                        assert logged_data[0]['doi'] == '10.1109/INVALID.2023.123'
                        assert logged_data[0]['entry_id'] == 'test2023'
                        assert logged_data[0]['publisher'] == 'IEEE'
                        assert logged_data[0]['error_message'] == 'DOI not found'
                        assert logged_data[0]['http_status'] == 404
                        assert 'timestamp' in logged_data[0]


# ============================================================================
# Test Enhanced Fetch Functions (NEW)
# ============================================================================

class TestEnhancedFetchFunctions:
    """Tests for enhanced fetch functions with new features."""

    @pytest.mark.unit
    @patch('complete_bibtex.fetch_bibtex_from_ieee')
    @patch('complete_bibtex.fetch_bibtex_from_ieee_selenium')
    @patch('complete_bibtex.fetch_bibtex_from_crossref')
    @patch('complete_bibtex.get_cached_bibtex')
    @patch('complete_bibtex.cache_bibtex')
    def test_fetch_complete_ieee_with_selenium_fallback(self, mock_cache, mock_get_cache,
                                                         mock_crossref, mock_selenium, mock_ieee):
        """Test IEEE fetch with Selenium fallback."""
        mock_get_cache.return_value = None
        mock_ieee.return_value = (None, "API failed")
        mock_selenium.return_value = ("@article{test}", None)
        mock_crossref.return_value = (None, "CrossRef failed")

        bibtex, error = cb.fetch_complete_bibtex('10.1109/TEST.2023.123', 'IEEE')

        assert bibtex == "@article{test}"
        assert error is None
        mock_ieee.assert_called_once()
        mock_selenium.assert_called_once()

    @pytest.mark.unit
    @patch('complete_bibtex.fetch_bibtex_from_ieee')
    @patch('complete_bibtex.fetch_bibtex_from_crossref')
    @patch('complete_bibtex.fetch_bibtex_from_scholar')
    @patch('complete_bibtex.get_cached_bibtex')
    @patch('complete_bibtex.cache_bibtex')
    @patch('time.sleep')
    def test_fetch_complete_with_scholar_fallback(self, mock_sleep, mock_cache, mock_get_cache,
                                                   mock_scholar, mock_crossref, mock_ieee):
        """Test fetch with Google Scholar fallback."""
        mock_get_cache.return_value = None
        mock_ieee.return_value = (None, "IEEE failed")
        mock_crossref.return_value = (None, "CrossRef failed")
        mock_scholar.return_value = ("@article{scholar}", None)

        bibtex, error = cb.fetch_complete_bibtex(
            '10.1109/TEST.2023.123',
            'IEEE',
            title='Test Paper',
            author='John Smith'
        )

        assert bibtex == "@article{scholar}"
        assert error is None
        mock_scholar.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

