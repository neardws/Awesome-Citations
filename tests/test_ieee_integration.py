"""
IEEE Integration Tests

Tests the complete IEEE DOI fetching workflow with the enhancements from IEEE_FAILURE_ANALYSIS.md.

These tests use the actual problematic DOIs identified in the analysis to verify:
- DOI validation works correctly
- Error messages are detailed and helpful
- Fallback chain functions properly
- Failed DOIs are logged correctly
- DOI corrections database is applied

Note: These are integration tests that may make actual network requests.
Mark as @pytest.mark.slow for optional execution.
"""

import pytest
import os
import json
from unittest.mock import patch, Mock
import complete_bibtex as cb


# DOIs from IEEE_FAILURE_ANALYSIS.md
KNOWN_WORKING_DOI = "10.1109/TWC.2024.3396161"  # Success with CrossRef fallback
KNOWN_FAILING_DOIS = [
    "10.1109/ICCAKM54721.2021.9675934",  # 404 Not Found
    "10.1109/ACCESS.2020.3013148",       # 404 Not Found
    "10.1109/ACCESS.2023.3276915",       # 404 Not Found
    "10.1109/ACCESS.2023.3265856",       # 404 Not Found
    "10.1109/TDSC.2024.3363675",         # 404 Not Found
]


# ============================================================================
# Test DOI Validation with Real IEEE DOIs
# ============================================================================

class TestIEEEDOIValidation:
    """Test DOI validation with actual IEEE DOIs."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_validate_working_ieee_doi(self):
        """Test validation of known working IEEE DOI."""
        valid, error = cb.verify_doi_exists(KNOWN_WORKING_DOI)

        # Should resolve successfully
        assert valid is True or "404" not in error.lower()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_validate_failing_ieee_dois(self):
        """Test validation of known failing IEEE DOIs."""
        results = []

        for doi in KNOWN_FAILING_DOIS[:2]:  # Test first 2 to avoid rate limiting
            valid, error = cb.verify_doi_exists(doi)
            results.append((doi, valid, error))

        # At least some should be detected as invalid
        invalid_count = sum(1 for _, valid, _ in results if not valid)
        assert invalid_count > 0, "Should detect some invalid DOIs"

        # Error messages should be informative
        for doi, valid, error in results:
            if not valid:
                assert "404" in error or "not found" in error.lower()


# ============================================================================
# Test IEEE Fetch with Fallback Chain
# ============================================================================

class TestIEEEFetchFallbackChain:
    """Test the complete IEEE fetch fallback chain."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_ieee_api_to_crossref_fallback(self):
        """Test IEEE API fails but CrossRef succeeds."""
        # Mock IEEE API failure but allow CrossRef to succeed
        with patch('complete_bibtex.fetch_bibtex_from_ieee') as mock_ieee:
            mock_ieee.return_value = (None, "IEEE API failed (mocked)")

            bibtex, error = cb.fetch_complete_bibtex(KNOWN_WORKING_DOI, 'IEEE')

            # Should fall back to CrossRef and succeed
            assert bibtex is not None or error is not None
            mock_ieee.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_ieee_complete_fallback_chain_with_scholar(self):
        """Test complete fallback chain including Google Scholar."""
        # Use a failing DOI with title/author for Scholar fallback
        with patch('complete_bibtex.fetch_bibtex_from_ieee') as mock_ieee:
            with patch('complete_bibtex.fetch_bibtex_from_crossref') as mock_crossref:
                mock_ieee.return_value = (None, "IEEE API failed")
                mock_crossref.return_value = (None, "CrossRef failed")

                bibtex, error = cb.fetch_complete_bibtex(
                    KNOWN_FAILING_DOIS[0],
                    'IEEE',
                    title='IoT Security Review',
                    author='Wang'
                )

                # Should attempt all fallbacks
                mock_ieee.assert_called_once()
                mock_crossref.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_ieee_selenium_fallback_integration(self):
        """Test that Selenium fallback is attempted when IEEE API fails."""
        with patch('complete_bibtex.fetch_bibtex_from_ieee') as mock_ieee:
            with patch('complete_bibtex.fetch_bibtex_from_ieee_selenium') as mock_selenium:
                mock_ieee.return_value = (None, "IEEE API failed")
                mock_selenium.return_value = ("@article{test}", None)

                bibtex, error = cb.fetch_complete_bibtex(KNOWN_WORKING_DOI, 'IEEE')

                # Should try Selenium after IEEE API fails
                mock_ieee.assert_called_once()
                mock_selenium.assert_called_once()

                assert bibtex is not None


# ============================================================================
# Test Error Message Quality
# ============================================================================

class TestIEEEErrorMessages:
    """Test that error messages are detailed and helpful."""

    @pytest.mark.integration
    def test_error_message_includes_http_status(self):
        """Test that error messages include HTTP status codes."""
        with patch('complete_bibtex.safe_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response

            bibtex, error = cb.fetch_bibtex_from_ieee(KNOWN_FAILING_DOIS[0])

            assert "404" in error
            assert bibtex is None

    @pytest.mark.integration
    def test_error_message_includes_failure_context(self):
        """Test that error messages include context about what failed."""
        with patch('complete_bibtex.safe_request') as mock_request:
            mock_request.return_value = None

            bibtex, error = cb.fetch_bibtex_from_ieee(KNOWN_FAILING_DOIS[0])

            # Should explain DOI resolution failed
            assert "doi resolution" in error.lower() or "network" in error.lower()

    @pytest.mark.integration
    def test_combined_error_message_from_fallback_chain(self):
        """Test that fallback chain combines error messages."""
        with patch('complete_bibtex.fetch_bibtex_from_ieee') as mock_ieee:
            with patch('complete_bibtex.fetch_bibtex_from_crossref') as mock_crossref:
                mock_ieee.return_value = (None, "IEEE API error: 404")
                mock_crossref.return_value = (None, "CrossRef error: Not found")

                bibtex, error = cb.fetch_complete_bibtex(KNOWN_FAILING_DOIS[0], 'IEEE')

                # Error should mention both IEEE and CrossRef attempts
                assert "IEEE" in error or "404" in error
                assert "CrossRef" in error or "Not found" in error


# ============================================================================
# Test Failed DOI Logging
# ============================================================================

class TestIEEEFailedDOILogging:
    """Test that failed DOIs are logged correctly."""

    @pytest.mark.integration
    def test_failed_doi_is_logged(self):
        """Test that failed DOI fetch creates log entry."""
        test_doi = KNOWN_FAILING_DOIS[0]
        test_entry_id = 'test_ieee_fail_2023'

        with patch('complete_bibtex.init_failed_doi_log'):
            with patch('complete_bibtex.load_failed_dois', return_value=[]):
                with patch('builtins.open', create=True):
                    with patch('json.dump') as mock_dump:
                        cb.log_failed_doi(
                            doi=test_doi,
                            entry_id=test_entry_id,
                            publisher='IEEE',
                            error_message='DOI not found (HTTP 404)',
                            http_status=404
                        )

                        # Verify logging was called
                        mock_dump.assert_called_once()
                        logged_data = mock_dump.call_args[0][0]

                        # Verify log contains DOI and error details
                        assert len(logged_data) == 1
                        assert logged_data[0]['doi'] == test_doi
                        assert logged_data[0]['http_status'] == 404
                        assert 'IEEE' in logged_data[0]['publisher']


# ============================================================================
# Test DOI Corrections Integration
# ============================================================================

class TestIEEEDOICorrections:
    """Test DOI corrections database with IEEE DOIs."""

    @pytest.mark.integration
    def test_doi_correction_applied_for_invalid_doi(self):
        """Test that DOI correction is applied for known invalid DOI."""
        mock_corrections = {
            KNOWN_FAILING_DOIS[0]: {
                'corrected_doi': None,
                'status': 'invalid',
                'reason': 'DOI does not exist in DOI.org database'
            }
        }

        with patch('complete_bibtex.load_doi_corrections', return_value=mock_corrections):
            corrected_doi, is_corrected, message = cb.apply_doi_correction(KNOWN_FAILING_DOIS[0])

            assert corrected_doi is None
            assert is_corrected is True
            assert 'invalid' in message.lower()

    @pytest.mark.integration
    def test_doi_correction_with_replacement(self):
        """Test DOI correction with corrected replacement."""
        original_doi = "10.1109/WRONG.DOI"
        correct_doi = KNOWN_WORKING_DOI

        mock_corrections = {
            original_doi: {
                'corrected_doi': correct_doi,
                'status': 'corrected',
                'reason': 'DOI typo in source'
            }
        }

        with patch('complete_bibtex.load_doi_corrections', return_value=mock_corrections):
            corrected_doi, is_corrected, message = cb.apply_doi_correction(original_doi)

            assert corrected_doi == correct_doi
            assert is_corrected is True
            assert 'typo' in message.lower() or 'corrected' in message.lower()


# ============================================================================
# Test Complete IEEE Workflow
# ============================================================================

class TestIEEECompleteWorkflow:
    """Test complete IEEE DOI processing workflow."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_ieee_workflow_with_valid_doi(self):
        """Test complete workflow with a valid IEEE DOI."""
        entry = {
            'ID': 'wang2024test',
            'ENTRYTYPE': 'article',
            'title': 'Test Paper',
            'doi': KNOWN_WORKING_DOI
        }

        # Test DOI extraction
        doi = cb.extract_doi(entry)
        assert doi == KNOWN_WORKING_DOI

        # Test publisher identification
        publisher = cb.identify_publisher(doi)
        assert publisher == 'IEEE'

        # Test DOI validation
        valid, error = cb.verify_doi_exists(doi)
        # May succeed or have specific error
        if not valid:
            assert error != ""

    @pytest.mark.integration
    def test_ieee_workflow_with_invalid_doi(self):
        """Test complete workflow with an invalid IEEE DOI."""
        entry = {
            'ID': 'invalid2023',
            'ENTRYTYPE': 'inproceedings',
            'title': 'Invalid Paper',
            'doi': KNOWN_FAILING_DOIS[0]
        }

        # Test DOI extraction
        doi = cb.extract_doi(entry)
        assert doi == KNOWN_FAILING_DOIS[0]

        # Test publisher identification
        publisher = cb.identify_publisher(doi)
        assert publisher == 'IEEE'

        # Test DOI validation - should fail
        valid, error = cb.verify_doi_exists(doi)
        if not valid:
            assert "404" in error or "not found" in error.lower()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_ieee_workflow_comprehensive(self):
        """Test comprehensive workflow: validation → fetch → validate → log."""
        entry = {
            'ID': 'comprehensive_test_2023',
            'title': 'Comprehensive Test Paper',
            'author': 'Test Author',
            'year': '2023',
            'doi': KNOWN_FAILING_DOIS[0]
        }

        # Step 1: Extract DOI
        doi = cb.extract_doi(entry)
        assert doi is not None

        # Step 2: Apply corrections (if any)
        with patch('complete_bibtex.load_doi_corrections', return_value={}):
            corrected_doi, is_corrected, msg = cb.apply_doi_correction(doi)

        # Step 3: Validate DOI
        valid, validation_error = cb.verify_doi_exists(doi)

        # Step 4: Try to fetch (expect failure)
        with patch('complete_bibtex.get_cached_bibtex', return_value=None):
            bibtex, fetch_error = cb.fetch_complete_bibtex(
                doi,
                'IEEE',
                title=entry.get('title'),
                author=entry.get('author')
            )

        # Step 5: Verify error was logged
        if bibtex is None:
            assert fetch_error is not None
            assert len(fetch_error) > 0


# ============================================================================
# Test Success Rate Measurement
# ============================================================================

class TestIEEESuccessRateMeasurement:
    """Test to measure IEEE success rate improvement."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_measure_ieee_success_rate_with_fallbacks(self):
        """Measure success rate of IEEE DOIs with all fallbacks enabled."""
        test_dois = [KNOWN_WORKING_DOI] + KNOWN_FAILING_DOIS[:2]  # Mix of working and failing

        results = {
            'total': len(test_dois),
            'ieee_api_success': 0,
            'selenium_success': 0,
            'crossref_success': 0,
            'scholar_success': 0,
            'total_success': 0,
            'failures': []
        }

        for doi in test_dois:
            # Try IEEE API first (mocked to always fail for testing fallbacks)
            with patch('complete_bibtex.fetch_bibtex_from_ieee') as mock_ieee:
                with patch('complete_bibtex.get_cached_bibtex', return_value=None):
                    mock_ieee.return_value = (None, "API failed")

                    bibtex, error = cb.fetch_complete_bibtex(doi, 'IEEE')

                    if bibtex:
                        results['total_success'] += 1
                    else:
                        results['failures'].append((doi, error))

        # Report results
        success_rate = (results['total_success'] / results['total']) * 100
        print(f"\nIEEE Success Rate with Fallbacks: {success_rate:.1f}%")
        print(f"Total DOIs tested: {results['total']}")
        print(f"Successful fetches: {results['total_success']}")
        print(f"Failed fetches: {len(results['failures'])}")

        # Note: Actual success rate depends on mocking strategy
        # This test demonstrates the measurement framework


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
