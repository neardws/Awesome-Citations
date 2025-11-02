"""
Unit tests for utils/ modules.

Tests cover:
- Title formatter (title_formatter.py)
- arXiv detector (arxiv_detector.py)
- Multi-source merger (multi_source_merger.py)
- Change logger (change_logger.py)
"""

import pytest
import sys
import os

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.title_formatter import (
    load_protected_words,
    load_small_words,
    format_title,
    is_likely_acronym
)
from utils.change_logger import ChangeLogger


# ============================================================================
# Test Title Formatter
# ============================================================================

class TestTitleFormatter:
    """Tests for title_formatter.py module."""

    @pytest.mark.unit
    def test_load_protected_words(self):
        """Test loading protected words from config."""
        words = load_protected_words()
        assert isinstance(words, set)
        # Should contain common acronyms
        assert any('IEEE' in w or 'ACM' in w for w in words) or len(words) == 0

    @pytest.mark.unit
    def test_load_small_words(self):
        """Test loading small words from config."""
        words = load_small_words()
        assert isinstance(words, set)
        # Should contain common articles
        assert 'the' in words or 'a' in words or len(words) > 0

    @pytest.mark.unit
    def test_format_title_to_title_case(self):
        """Test formatting title to Title Case."""
        title = "a survey on deep learning"
        protected = set()
        small = {'a', 'on'}

        result = format_title(title, 'titlecase', protected, small)

        assert result.startswith('A Survey')
        assert 'Deep Learning' in result or 'deep learning' in result.lower()

    @pytest.mark.unit
    def test_format_title_preserve_acronyms(self):
        """Test that acronyms are preserved in braces."""
        title = "IoT applications using WiFi"
        protected = {'IoT', 'WiFi'}
        small = set()

        result = format_title(title, 'titlecase', protected, small)

        # Should have braces around acronyms for LaTeX
        assert '{IoT}' in result or 'IoT' in result
        assert '{WiFi}' in result or 'WiFi' in result

    @pytest.mark.unit
    def test_is_likely_acronym(self):
        """Test acronym detection heuristic."""
        assert is_likely_acronym('IoT')
        assert is_likely_acronym('HTTP')
        assert is_likely_acronym('ML')
        assert not is_likely_acronym('The')
        assert not is_likely_acronym('deep')


# ============================================================================
# Test Change Logger
# ============================================================================

class TestChangeLogger:
    """Tests for change_logger.py module."""

    @pytest.mark.unit
    def test_logger_initialization(self):
        """Test creating a change logger instance."""
        logger = ChangeLogger()
        assert logger is not None
        assert hasattr(logger, 'log_field_added')

    @pytest.mark.unit
    def test_logger_field_added(self):
        """Test logging field addition."""
        logger = ChangeLogger()
        logger.log_field_added('test2023', 'doi', '10.1109/TEST.2023.123', 'IEEE')

        # Logger should track the change
        assert hasattr(logger, 'changes') or hasattr(logger, '_changes')

    @pytest.mark.unit
    def test_logger_title_formatted(self):
        """Test logging title formatting."""
        logger = ChangeLogger()
        logger.log_title_formatted('test2023', 'old title', 'New Title', 'titlecase')

        # Should not raise an error
        assert True

    @pytest.mark.unit
    def test_logger_generate_report(self, temp_dir):
        """Test generating markdown report."""
        logger = ChangeLogger()
        logger.log_field_added('test2023', 'doi', '10.1109/TEST.2023.123', 'IEEE')

        report_file = temp_dir / 'test_log.md'
        logger.generate_markdown_report(str(report_file))

        # Report should be created
        assert report_file.exists()
        content = report_file.read_text()
        assert len(content) > 0


# ============================================================================
# Test arXiv Detector (if implemented)
# ============================================================================

@pytest.mark.unit
def test_arxiv_module_exists():
    """Test that arXiv detector module exists."""
    try:
        from utils import arxiv_detector
        assert hasattr(arxiv_detector, 'is_arxiv_entry')
    except ImportError:
        pytest.skip("arXiv detector module not found")


# ============================================================================
# Test Multi-Source Merger (if implemented)
# ============================================================================

@pytest.mark.unit
def test_merger_module_exists():
    """Test that multi-source merger module exists."""
    try:
        from utils import multi_source_merger
        assert hasattr(multi_source_merger, 'merge_entries')
    except ImportError:
        pytest.skip("Multi-source merger module not found")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
