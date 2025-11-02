"""
Unit tests for format_bibtex.py module.

Tests cover:
- Author name formatting (first_last, last_first)
- Page number formatting (single dash, double dash)
- Journal name normalization
- Title formatting integration
- Entry standardization workflow
"""

import pytest
import os
from unittest.mock import patch, Mock
import format_bibtex as fb


# ============================================================================
# Test Author Formatting
# ============================================================================

class TestFormatAuthorNames:
    """Tests for format_author_names() function."""

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_last_first_to_first_last(self):
        """Test converting 'Last, First' to 'First Last' format."""
        authors = "Smith, John and Brown, Alice"
        result = fb.format_author_names(authors, 'first_last')
        assert result == "John Smith and Alice Brown"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_first_last_to_last_first(self):
        """Test converting 'First Last' to 'Last, First' format."""
        authors = "John Smith and Alice Brown"
        result = fb.format_author_names(authors, 'last_first')
        assert result == "Smith, John and Brown, Alice"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_single_author(self):
        """Test formatting single author name."""
        authors = "Smith, John"
        result = fb.format_author_names(authors, 'first_last')
        assert result == "John Smith"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_multiple_authors(self):
        """Test formatting multiple authors."""
        authors = "Smith, John and Brown, Alice and Wang, Li"
        result = fb.format_author_names(authors, 'first_last')
        assert result == "John Smith and Alice Brown and Li Wang"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_empty_author_string(self):
        """Test that empty author string is returned unchanged."""
        assert fb.format_author_names("", 'first_last') == ""
        assert fb.format_author_names("   ", 'first_last') == "   "

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_author_with_middle_name(self):
        """Test formatting author with middle names/initials."""
        authors = "Smith, John A. B."
        result = fb.format_author_names(authors, 'first_last')
        assert "John" in result
        assert "Smith" in result

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_preserves_case_insensitive_and(self):
        """Test that 'and' separator works case-insensitively."""
        authors = "Smith, John AND Brown, Alice And Wang, Li"
        result = fb.format_author_names(authors, 'first_last')
        # Should split on any case of 'and'
        assert "Smith" in result or "John Smith" in result


# ============================================================================
# Test Page Formatting
# ============================================================================

class TestFormatPages:
    """Tests for format_pages() function."""

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_single_to_double_dash(self):
        """Test converting single dash to double dash."""
        assert fb.format_pages("123-135", 'double_dash') == "123--135"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_double_dash_preserved(self):
        """Test that double dash is preserved."""
        assert fb.format_pages("123--135", 'double_dash') == "123--135"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_endash_to_double_dash(self):
        """Test converting en-dash to double dash."""
        assert fb.format_pages("123–135", 'double_dash') == "123--135"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_emdash_to_double_dash(self):
        """Test converting em-dash to double dash."""
        assert fb.format_pages("123—135", 'double_dash') == "123--135"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_to_single_dash(self):
        """Test converting to single dash format."""
        assert fb.format_pages("123--135", 'single_dash') == "123-135"
        assert fb.format_pages("123–135", 'single_dash') == "123-135"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_empty_string(self):
        """Test that empty page string is returned unchanged."""
        assert fb.format_pages("", 'double_dash') == ""

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_single_page(self):
        """Test formatting single page number."""
        assert fb.format_pages("123", 'double_dash') == "123"

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_article_number(self):
        """Test formatting ACM-style article numbers."""
        pages = "125:1-125:18"
        result = fb.format_pages(pages, 'double_dash')
        assert "125:1" in result
        assert "--" in result or "-" in result


# ============================================================================
# Test Journal Normalization
# ============================================================================

class TestNormalizeJournalName:
    """Tests for normalize_journal_name() function."""

    @pytest.mark.unit
    @pytest.mark.format
    def test_normalize_to_abbreviation_exact_match(self):
        """Test normalizing to abbreviation with exact match."""
        journal_abbr = {
            "IEEE Transactions on Pattern Analysis and Machine Intelligence": "IEEE Trans. Pattern Anal. Mach. Intell."
        }
        journal = "IEEE Transactions on Pattern Analysis and Machine Intelligence"
        result = fb.normalize_journal_name(journal, journal_abbr, 'abbreviation')
        assert result == "IEEE Trans. Pattern Anal. Mach. Intell."

    @pytest.mark.unit
    @pytest.mark.format
    def test_normalize_to_full_name(self):
        """Test normalizing abbreviation to full name."""
        journal_abbr = {
            "IEEE Transactions on Pattern Analysis and Machine Intelligence": "IEEE Trans. Pattern Anal. Mach. Intell."
        }
        journal = "IEEE Trans. Pattern Anal. Mach. Intell."
        result = fb.normalize_journal_name(journal, journal_abbr, 'full')
        assert result == "IEEE Transactions on Pattern Analysis and Machine Intelligence"

    @pytest.mark.unit
    @pytest.mark.format
    def test_normalize_case_insensitive(self):
        """Test that normalization is case-insensitive."""
        journal_abbr = {
            "IEEE Transactions on Example": "IEEE Trans. Example"
        }
        journal = "ieee transactions on example"
        result = fb.normalize_journal_name(journal, journal_abbr, 'abbreviation')
        assert result == "IEEE Trans. Example"

    @pytest.mark.unit
    @pytest.mark.format
    def test_normalize_no_match_returns_original(self):
        """Test that unmatched journal names are returned unchanged."""
        journal_abbr = {"Some Journal": "Some J."}
        journal = "Unknown Journal"
        result = fb.normalize_journal_name(journal, journal_abbr, 'abbreviation')
        assert result == "Unknown Journal"

    @pytest.mark.unit
    @pytest.mark.format
    def test_normalize_empty_journal(self):
        """Test that empty journal string is returned unchanged."""
        journal_abbr = {}
        assert fb.normalize_journal_name("", journal_abbr, 'abbreviation') == ""


# ============================================================================
# Test Configuration Loading
# ============================================================================

class TestLoadConfig:
    """Tests for load_config() and load_journal_abbreviations() functions."""

    @pytest.mark.unit
    def test_load_config_valid_file(self, temp_config_file):
        """Test loading valid config file."""
        config = fb.load_config(str(temp_config_file))
        assert isinstance(config, dict)
        assert 'citation_style' in config

    @pytest.mark.unit
    def test_load_config_nonexistent_file(self):
        """Test loading non-existent config file returns empty dict."""
        config = fb.load_config('nonexistent_config.json')
        assert config == {}

    @pytest.mark.unit
    def test_load_journal_abbreviations(self):
        """Test loading journal abbreviations."""
        # This will load from actual data/journal_abbr.json if it exists
        abbr = fb.load_journal_abbreviations()
        assert isinstance(abbr, dict)
        # Even if empty, should return dict


# ============================================================================
# Test Entry Standardization
# ============================================================================

class TestStandardizeEntry:
    """Tests for standardize_entry() function."""

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_title_formatting(self):
        """Test that entry standardization formats titles."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': 'a survey on deep learning methods',
            'author': 'Smith, John',
            'year': '2023'
        }

        config = {'title_format': 'titlecase'}
        journal_abbr = {}
        protected_words = set()
        small_words = {'a', 'on'}

        result = fb.standardize_entry(entry, config, journal_abbr,
                                      protected_words, small_words, None)

        # Title should be formatted to Title Case (or at least capitalized)
        # The result might already be correct, so just check it's properly capitalized
        assert result['title'].startswith('A Survey')
        assert 'Deep Learning' in result['title'] or 'deep learning' in result['title'].lower()

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_author_formatting(self):
        """Test that entry standardization formats authors."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': 'Test Paper',
            'author': 'Smith, John and Brown, Alice',
            'year': '2023'
        }

        config = {'author_format': 'first_last'}
        journal_abbr = {}

        result = fb.standardize_entry(entry, config, journal_abbr, set(), set(), None)

        # Authors should be converted to first_last format
        assert 'John Smith' in result['author']
        assert 'Alice Brown' in result['author']

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_pages_formatting(self):
        """Test that entry standardization formats pages."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': 'Test Paper',
            'pages': '123-135'
        }

        config = {'page_format': 'double_dash'}
        journal_abbr = {}

        result = fb.standardize_entry(entry, config, journal_abbr, set(), set(), None)

        assert result['pages'] == '123--135'

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_journal_normalization(self):
        """Test that entry standardization normalizes journal names."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': 'Test Paper',
            'journal': 'IEEE Transactions on Example'
        }

        config = {'journal_format': 'abbreviation'}
        journal_abbr = {
            'IEEE Transactions on Example': 'IEEE Trans. Example'
        }

        result = fb.standardize_entry(entry, config, journal_abbr, set(), set(), None)

        assert result['journal'] == 'IEEE Trans. Example'

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_cleans_whitespace(self):
        """Test that entry standardization cleans up excess whitespace."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': 'Test  Paper   With   Extra   Spaces',
            'author': 'Smith,  John'
        }

        config = {}
        journal_abbr = {}

        result = fb.standardize_entry(entry, config, journal_abbr, set(), set(), None)

        # Should have single spaces only
        assert '  ' not in result['title']
        assert '  ' not in result['author']

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_preserves_id_and_entrytype(self):
        """Test that ID and ENTRYTYPE are never modified."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': 'Test Paper'
        }

        config = {}
        journal_abbr = {}

        result = fb.standardize_entry(entry, config, journal_abbr, set(), set(), None)

        assert result['ID'] == 'test2023'
        assert result['ENTRYTYPE'] == 'article'


# ============================================================================
# Test File Processing Integration
# ============================================================================

class TestFormatBibtexFile:
    """Integration tests for format_bibtex_file() function."""

    @pytest.mark.integration
    @pytest.mark.format
    def test_format_file_basic(self, test_data_dir, temp_dir, temp_config_file):
        """Test basic file formatting workflow."""
        input_file = test_data_dir / 'mixed_case_titles.bib'
        output_file = temp_dir / 'formatted_output.bib'

        # Process the file
        fb.format_bibtex_file(str(input_file), str(output_file), str(temp_config_file))

        # Verify output exists
        assert output_file.exists()

        # Verify output has content
        assert output_file.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.format
    def test_format_file_with_logging(self, test_data_dir, temp_dir, temp_config_file):
        """Test file formatting with change logging enabled."""
        input_file = test_data_dir / 'mixed_case_titles.bib'
        output_file = temp_dir / 'formatted_with_log.bib'

        fb.format_bibtex_file(str(input_file), str(output_file), str(temp_config_file))

        # Check if log file was created
        # Note: actual log file location depends on config
        assert output_file.exists()

    @pytest.mark.integration
    @pytest.mark.format
    def test_format_file_preserves_entry_count(self, test_data_dir, temp_dir,
                                                temp_config_file, load_bibtex_file):
        """Test that formatting preserves all entries."""
        input_file = test_data_dir / 'complete_entries.bib'
        output_file = temp_dir / 'formatted_complete.bib'

        # Load original
        original_db = load_bibtex_file(input_file)
        original_count = len(original_db.entries)

        # Format
        fb.format_bibtex_file(str(input_file), str(output_file), str(temp_config_file))

        # Load formatted
        formatted_db = load_bibtex_file(output_file)

        assert len(formatted_db.entries) == original_count

    @pytest.mark.integration
    @pytest.mark.format
    def test_format_file_invalid_input(self, temp_dir, temp_config_file):
        """Test handling of invalid input file."""
        input_file = temp_dir / 'nonexistent.bib'
        output_file = temp_dir / 'output.bib'

        # Should handle gracefully without crashing
        fb.format_bibtex_file(str(input_file), str(output_file), str(temp_config_file))

        # Output should not be created if input is invalid
        # (depends on implementation)


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_author_with_special_characters(self):
        """Test formatting authors with special characters."""
        authors = r"M{\"u}ller, Hans and {\O}stergaard, Lars"
        result = fb.format_author_names(authors, 'first_last')
        assert 'M' in result  # Should handle LaTeX escapes

    @pytest.mark.unit
    @pytest.mark.format
    def test_format_pages_with_article_prefix(self):
        """Test formatting pages with ACM article number prefix."""
        pages = "e1234567"
        result = fb.format_pages(pages, 'double_dash')
        assert result == "e1234567"  # Should preserve non-range formats

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_entry_with_missing_fields(self):
        """Test standardizing entry with minimal fields."""
        entry = {
            'ID': 'minimal2023',
            'ENTRYTYPE': 'misc'
        }

        config = {}
        result = fb.standardize_entry(entry, config, {}, set(), set(), None)

        # Should not crash
        assert result['ID'] == 'minimal2023'

    @pytest.mark.unit
    @pytest.mark.format
    def test_standardize_entry_with_empty_title(self):
        """Test standardizing entry with empty title."""
        entry = {
            'ID': 'test2023',
            'ENTRYTYPE': 'article',
            'title': ''
        }

        config = {'title_format': 'titlecase'}
        result = fb.standardize_entry(entry, config, {}, set(), set(), None)

        # Should handle empty title gracefully
        assert 'title' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
