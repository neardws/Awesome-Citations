# Test Suite Documentation

## Overview

This test suite provides comprehensive functional testing for the Awesome-Citations project based on the features documented in `USAGE_GUIDE.md`.

## Test Structure

```
tests/
├── conftest.py                 # Pytest fixtures and configuration
├── pytest.ini                  # Pytest configuration (in project root)
├── test_complete_bibtex.py     # Tests for BibTeX completion (complete_bibtex.py)
├── test_format_bibtex.py       # Tests for BibTeX formatting (format_bibtex.py)
├── test_utils.py               # Tests for utility modules
├── test_integration.py         # End-to-end integration tests
├── test_data/                  # Test input files (16 .bib files)
│   ├── incomplete_entries.bib
│   ├── arxiv_preprints.bib
│   ├── mixed_case_titles.bib
│   ├── journal_normalization.bib
│   ├── ieee_papers.bib
│   ├── acm_papers.bib
│   ├── crossref_papers.bib
│   ├── chinese_journals.bib
│   ├── complete_entries.bib
│   ├── duplicate_entries.bib
│   ├── malformed_entries.bib
│   ├── large_file.bib (50+ entries)
│   ├── page_formats.bib
│   ├── author_formats.bib
│   ├── edge_cases.bib
│   └── mixed_scenarios.bib
└── fixtures/                   # Expected outputs (if needed)
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **test_complete_bibtex.py**: 45+ tests
  - DOI extraction from various fields
  - Publisher identification from DOI prefixes
  - BibTeX fetching from IEEE, ACM, arXiv, CrossRef (mocked)
  - Entry completeness checking
  - Entry merging logic

- **test_format_bibtex.py**: 35+ tests
  - Author name formatting (first_last, last_first)
  - Page number formatting (single dash, double dash, en-dash, em-dash)
  - Journal name normalization
  - Title formatting integration
  - Entry standardization workflow

- **test_utils.py**: 15+ tests
  - Title formatter (Title Case, protected words, acronym detection)
  - Change logger (tracking modifications, generating reports)
  - arXiv detector (ID extraction, published version detection)
  - Multi-source merger (completeness scoring, field merging)

### Integration Tests (`@pytest.mark.integration`)
- **test_integration.py**: 10+ tests
  - End-to-end completion workflow
  - File I/O operations
  - Error handling with malformed entries
  - Large file processing (50+ entries)
  - Configuration loading

## Running Tests

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific test category
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m format -v
```

### Run Specific Test Files
```bash
# Test BibTeX completion
pytest tests/test_complete_bibtex.py -v

# Test BibTeX formatting
pytest tests/test_format_bibtex.py -v

# Test utilities
pytest tests/test_utils.py -v

# Test integration
pytest tests/test_integration.py -v
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests (uses real API calls, slow)
pytest -m api

# Run only format tests
pytest -m format

# Skip slow tests
pytest -m "not slow"
```

## Test Markers

- `unit`: Unit tests for individual functions/modules
- `integration`: End-to-end integration tests
- `api`: Tests that make real API calls (slow, requires network)
- `format`: Tests specifically for formatting functionality
- `complete`: Tests specifically for completion functionality
- `slow`: Tests that take significant time (large files, API calls)
- `pdf`: Tests for PDF generation (requires LaTeX)
- `arxiv`: Tests for arXiv detection functionality

## Test Data Files

### Input Files (16 files)

1. **incomplete_entries.bib** (8 entries)
   - Entries missing various fields (pages, journal, author, etc.)
   - Used for testing completion functionality

2. **arxiv_preprints.bib** (7 entries)
   - Well-known arXiv preprints that have published versions
   - Tests: vaswani2017attention, devlin2018bert, he2015resnet, etc.

3. **mixed_case_titles.bib** (10 entries)
   - Titles in various cases (lowercase, UPPERCASE, Mixed Case)
   - Contains acronyms (IoT, WiFi, CNN, LSTM, etc.)
   - Tests Title Case formatting with protected words

4. **journal_normalization.bib** (10 entries)
   - Various journal name formats
   - Tests abbreviation ↔ full name conversion

5. **ieee_papers.bib** (5 entries)
   - Valid IEEE papers with DOIs
   - Tests IEEE Xplore API integration

6. **acm_papers.bib** (5 entries)
   - Valid ACM papers with DOIs
   - Tests ACM Digital Library API integration

7. **crossref_papers.bib** (6 entries)
   - Papers from various publishers (Nature, Cell, Science, etc.)
   - Tests CrossRef API fallback

8. **chinese_journals.bib** (5 entries)
   - Chinese journal entries
   - Tests GB/T 7714 citation style

9. **complete_entries.bib** (5 entries)
   - Already complete entries
   - No modifications should be needed

10. **duplicate_entries.bib** (7 entries)
    - Exact and near-duplicates
    - Tests deduplication logic

11. **malformed_entries.bib** (10 entries)
    - Syntax errors, missing fields, invalid formats
    - Tests error handling

12. **large_file.bib** (50 entries)
    - Tests parallel processing performance
    - Tests scalability

13. **page_formats.bib** (8 entries)
    - Various page formats (123-135, 123--135, 123–135, 123—805)
    - Tests page format normalization

14. **author_formats.bib** (10 entries)
    - Various author name formats
    - Tests author name standardization

15. **edge_cases.bib** (15 entries)
    - Empty titles, very long titles, unicode characters
    - Math symbols, future years, missing years, etc.

16. **mixed_scenarios.bib** (15 entries)
    - Combination of multiple issues in one file
    - Real-world integration testing

## Fixtures (conftest.py)

### Session-Level Fixtures
- `project_root`: Project root directory
- `test_data_dir`: Test data directory path
- `fixtures_dir`: Expected output fixtures path
- `config_file`: Main configuration file path
- `api_rate_limiter`: Rate limiter for API tests

### Function-Level Fixtures
- `temp_dir`: Temporary directory for test outputs
- `sample_config`: Sample configuration dictionary
- `temp_config_file`: Temporary config file
- `sample_bibtex_entry`: Complete BibTeX entry
- `incomplete_bibtex_entry`: Incomplete entry
- `arxiv_bibtex_entry`: arXiv preprint entry
- `create_temp_bib_file`: Factory for creating temp BibTeX files
- `load_bibtex_file`: Factory for loading BibTeX files
- `assert_bibtex_field`: Helper for field assertions
- `check_file_exists`: Helper for file existence checks
- `mock_api_response`: Factory for mock API responses

## Expected Results

### Test Coverage Goals
- **Overall**: ≥90% code coverage
- **Core modules**:
  - `complete_bibtex.py`: ≥90%
  - `format_bibtex.py`: ≥90%
  - `utils/title_formatter.py`: ≥85%
  - `utils/change_logger.py`: ≥85%

### Expected Test Counts
- Total tests: 100+ individual test cases
- Unit tests: ~80 tests
- Integration tests: ~20 tests

### Test Execution Time
- Unit tests (without API): ~5-10 seconds
- Integration tests: ~2-5 minutes
- Full suite with API calls: ~10-15 minutes (due to rate limiting)

## Configuration

### pytest.ini
Located in project root, configures:
- Test discovery patterns
- Output formatting
- Test markers
- Coverage options
- Timeout settings (300s default)

### conftest.py
Provides:
- Shared fixtures across all tests
- Custom pytest hooks
- Helper functions for BibTeX manipulation

## API Testing

### Real API Calls
Tests marked with `@pytest.mark.api` make real API calls to:
- IEEE Xplore
- ACM Digital Library
- arXiv API
- CrossRef API
- Semantic Scholar API (for arXiv detection)
- DBLP API (for arXiv detection)

**Note**: Real API tests:
- Respect rate limits (1-second delays)
- May fail due to network issues
- May fail if APIs change
- Should be run sparingly in CI/CD

### Mocked API Tests
Most API tests use mocked responses for:
- Faster execution
- Predictable results
- Offline testing
- No rate limiting concerns

## Continuous Integration

### Recommended CI Configuration
```yaml
# Example GitHub Actions
- name: Install dependencies
  run: pip install -r requirements.txt

- name: Run unit tests
  run: pytest tests/ -m unit -v

- name: Run integration tests
  run: pytest tests/ -m "integration and not api" -v

- name: Generate coverage
  run: pytest tests/ --cov=. --cov-report=xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path includes project root

2. **API Test Failures**
   - Network connectivity required
   - Rate limiting may cause delays
   - Skip with: `pytest -m "not api"`

3. **PDF Generation Tests**
   - Requires LaTeX installation
   - Skip with: `pytest -m "not pdf"`

4. **Timeout Errors**
   - Increase timeout in pytest.ini
   - Check network connection for API tests

## Extending Tests

### Adding New Test Data
1. Create .bib file in `tests/test_data/`
2. Document purpose and expected behavior
3. Add corresponding test case

### Adding New Test Cases
1. Follow existing test structure
2. Use appropriate markers
3. Add docstrings explaining test purpose
4. Use fixtures from conftest.py

### Adding New Fixtures
1. Add to `tests/conftest.py`
2. Document purpose and usage
3. Consider scope (session, module, function)

## Maintenance

### Regular Updates
- Review test coverage reports
- Update test data as APIs evolve
- Add tests for new features
- Fix failing tests promptly

### Test Data Maintenance
- Keep test files small and focused
- Update DOIs if papers are updated
- Add new edge cases as discovered

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [USAGE_GUIDE.md](../USAGE_GUIDE.md) - Feature documentation
- [README.md](../README.md) - Project overview

---

**Last Updated**: 2025-11-01
**Test Suite Version**: 1.0.0
**Python Version**: 3.8+
