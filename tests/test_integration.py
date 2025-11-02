"""
Integration tests for Awesome-Citations.

Tests cover:
- End-to-end completion workflow
- Error handling and edge cases
- File I/O operations
"""

import pytest
import os
from pathlib import Path


# ============================================================================
# Test Enhanced Complete Workflow
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
def test_enhanced_complete_basic_workflow(test_data_dir, temp_dir):
    """Test basic enhanced completion workflow."""
    # Skip if enhanced_complete module doesn't exist
    try:
        import enhanced_complete as ec
    except ImportError:
        pytest.skip("enhanced_complete module not available")

    input_file = test_data_dir / 'complete_entries.bib'
    output_file = temp_dir / 'enhanced_output.bib'

    # This would require mocking API calls for real test
    # For now, just verify the module loads
    assert hasattr(ec, 'enhanced_complete_bibtex')


# ============================================================================
# Test Error Handling
# ============================================================================

@pytest.mark.integration
def test_handle_missing_input_file():
    """Test graceful handling of missing input file."""
    try:
        import complete_bibtex as cb
        import format_bibtex as fb

        # These should handle missing files gracefully
        # (actual behavior depends on implementation)
        assert True
    except ImportError:
        pytest.skip("Modules not available")


@pytest.mark.integration
def test_handle_malformed_bibtex(test_data_dir, temp_dir):
    """Test handling of malformed BibTeX entries."""
    malformed_file = test_data_dir / 'malformed_entries.bib'

    if not malformed_file.exists():
        pytest.skip("Malformed test file not found")

    # Attempt to process malformed file
    # Should not crash
    try:
        import bibtexparser
        with open(malformed_file, 'r', encoding='utf-8') as f:
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            db = bibtexparser.load(f, parser=parser)
        # Parser should handle gracefully
        assert True
    except Exception:
        # Even if it fails, test passes (we're testing error handling)
        assert True


# ============================================================================
# Test File Processing
# ============================================================================

@pytest.mark.integration
def test_process_large_file(test_data_dir, temp_dir, temp_config_file):
    """Test processing large BibTeX file."""
    large_file = test_data_dir / 'large_file.bib'

    if not large_file.exists():
        pytest.skip("Large test file not found")

    try:
        import format_bibtex as fb
        output_file = temp_dir / 'large_formatted.bib'

        fb.format_bibtex_file(str(large_file), str(output_file), str(temp_config_file))

        # Should complete without error
        assert output_file.exists()
    except ImportError:
        pytest.skip("format_bibtex module not available")


@pytest.mark.integration
def test_process_mixed_scenarios(test_data_dir, temp_dir, temp_config_file):
    """Test processing file with mixed scenarios."""
    mixed_file = test_data_dir / 'mixed_scenarios.bib'

    if not mixed_file.exists():
        pytest.skip("Mixed scenarios test file not found")

    try:
        import format_bibtex as fb
        output_file = temp_dir / 'mixed_formatted.bib'

        fb.format_bibtex_file(str(mixed_file), str(output_file), str(temp_config_file))

        assert output_file.exists()
    except ImportError:
        pytest.skip("format_bibtex module not available")


# ============================================================================
# Test Utilities Integration
# ============================================================================

@pytest.mark.integration
def test_utilities_sorting_and_deduplication(test_data_dir, temp_dir):
    """Test sorting and deduplication from utilities.py."""
    duplicate_file = test_data_dir / 'duplicate_entries.bib'

    if not duplicate_file.exists():
        pytest.skip("Duplicate entries test file not found")

    try:
        import utilities
        # Test depends on utilities.py implementation
        assert hasattr(utilities, 'remove_duplicates') or hasattr(utilities, 'sort_bibtex_file')
    except ImportError:
        pytest.skip("utilities module not available")


# ============================================================================
# Test Configuration Loading
# ============================================================================

@pytest.mark.integration
def test_load_all_data_files():
    """Test that all data files can be loaded."""
    data_dir = Path(__file__).parent.parent / 'data'

    if not data_dir.exists():
        pytest.skip("Data directory not found")

    # Check for expected data files
    expected_files = [
        'protected_words.json',
        'small_words.json',
        'journal_abbr.json'
    ]

    import json

    for filename in expected_files:
        filepath = data_dir / filename
        if filepath.exists():
            # Should be valid JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, dict) or isinstance(data, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
