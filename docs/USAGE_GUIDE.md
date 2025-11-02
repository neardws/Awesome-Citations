# Enhanced BibTeX Completion Tool - Usage Guide

## 📋 Overview

This enhanced BibTeX completion tool provides comprehensive bibliography management including:

- **Multi-source data fetching**: IEEE Xplore, ACM Digital Library, arXiv, CrossRef, DBLP
- **arXiv published version detection**: Automatically finds and replaces preprints with published versions
- **Field standardization**: Title Case formatting, journal name normalization, author formatting
- **PDF generation**: Create formatted reference lists in multiple citation styles (IEEE, ACM, APA, GB/T 7714)
- **Parallel processing**: Fast processing for large bibliography files
- **Detailed change logging**: Track all modifications with comprehensive reports

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For PDF generation, install LaTeX:
# MacOS
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install texlive-full

# Windows
# Download from https://miktex.org/download
```

### 2. Basic Usage

```bash
# Complete and format a BibTeX file
python enhanced_complete.py input.bib completed_output.bib config.json
```

This single command will:
1. ✅ Complete missing fields from official sources
2. 🔄 Replace arXiv preprints with published versions
3. 📝 Format titles to Title Case with protected acronyms
4. 📚 Normalize journal/conference names
5. 📄 Generate a formatted PDF bibliography
6. 📊 Create a detailed change log (Markdown format)

## 📁 Project Structure

```
Awesome-Citations/
├── enhanced_complete.py      # Main enhanced completion script
├── format_bibtex.py          # Field standardization module
├── generate_pdf.py           # PDF generation module
├── complete_bibtex.py        # Original completion functions
├── config.json               # Configuration file
├── requirements.txt          # Python dependencies
│
├── utils/
│   ├── arxiv_detector.py     # arXiv published version detector
│   ├── multi_source_merger.py# Multi-source data merger
│   ├── title_formatter.py    # Title formatting utilities
│   └── change_logger.py      # Change tracking and logging
│
├── data/
│   ├── journal_abbr.json     # Journal abbreviation mappings
│   ├── protected_words.json  # Acronyms and proper nouns
│   ├── small_words.json      # Articles, prepositions, etc.
│   └── chinese_journals.json # Chinese journal configurations
│
└── templates/
    ├── ieee_template.tex     # IEEE citation style
    ├── acm_template.tex      # ACM citation style
    ├── apa_template.tex      # APA citation style
    └── gb7714_template.tex   # GB/T 7714 (Chinese standard)
```

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "citation_style": "ieee",              // PDF citation style
  "title_format": "titlecase",           // titlecase, sentencecase, preserve
  "journal_format": "abbreviation",      // abbreviation, full, both
  "author_format": "first_last",         // first_last, last_first
  "page_format": "double_dash",          // double_dash, single_dash
  "arxiv_handling": "replace_with_published",  // Auto-replace arXiv
  "merge_multiple_sources": true,        // Fetch from multiple sources
  "parallel_processing": true,           // Enable parallel processing
  "max_workers": 5,                      // Concurrent requests
  "request_delay": 1.0,                  // Delay between requests (seconds)

  "pdf_output": {
    "enabled": true,
    "document_title": "参考文献列表 / References",
    "sort_by": "author",
    "font_size": "11pt"
  },

  "logging": {
    "enabled": true,
    "output_file": "changes_log.md",
    "verbose": true
  }
}
```

## 📖 Usage Examples

### Example 1: Basic Completion

```bash
# Complete a simple BibTeX file
python enhanced_complete.py my_refs.bib
```

**Output files**:
- `completed_output.bib` - Completed BibTeX file
- `completed_output.pdf` - Formatted reference list PDF
- `changes_log.md` - Detailed change log

### Example 2: Format Only (No Completion)

```bash
# Just format existing complete entries
python format_bibtex.py input.bib formatted_output.bib config.json
```

### Example 3: PDF Generation Only

```bash
# Generate PDF from existing BibTeX
python generate_pdf.py input.bib references.pdf ieee config.json

# Available styles: ieee, acm, apa, gb7714
python generate_pdf.py input.bib refs_acm.pdf acm
python generate_pdf.py input.bib refs_cn.pdf gb7714
```

### Example 4: Custom Configuration

```bash
# Use custom config file
python enhanced_complete.py input.bib output.bib my_custom_config.json
```

## 🎯 Key Features

### 1. arXiv Published Version Detection

Automatically detects arXiv preprints and searches for published versions:

```
Original entry:
  @article{vaswani2017,
    title={Attention Is All You Need},
    author={Vaswani, Ashish and others},
    journal={arXiv preprint arXiv:1706.03762},
    year={2017}
  }

After processing:
  @inproceedings{vaswani2017,
    title={Attention Is All You Need},
    author={Vaswani, Ashish and others},
    booktitle={Advances in Neural Information Processing Systems},
    pages={5998--6008},
    year={2017},
    doi={10.5555/3295222.3295349}
  }
```

**Detection methods**:
- Semantic Scholar API (most reliable for arXiv)
- DBLP API (excellent for CS papers)
- CrossRef API (comprehensive coverage)

### 2. Multi-Source Data Merging

Fetches data from multiple sources and intelligently merges:

```python
# Sources checked (in priority order):
1. DOI official source (IEEE/ACM/Springer)
2. DBLP (for CS papers)
3. CrossRef (universal fallback)

# Merge strategy:
- Choose longest/most complete field values
- Preserve original entry ID
- Track data source for each field
```

### 3. Field Standardization

**Title Formatting** (Title Case):
```
Input:  "a survey on deep learning for natural language processing"
Output: "A Survey on Deep Learning for Natural Language Processing"

Input:  "IoT-based smart home using LoRa and WiFi"
Output: "{IoT}-Based Smart Home Using {LoRa} and {WiFi}"
         ↑ Protected acronyms in braces for LaTeX
```

**Journal Normalization**:
```
Input:  "IEEE Transactions on Pattern Analysis and Machine Intelligence"
Output: "IEEE Trans. Pattern Anal. Mach. Intell."  (abbreviation mode)

Input:  "IEEE Trans. PAMI"
Output: "IEEE Transactions on Pattern Analysis and Machine Intelligence"  (full mode)
```

**Page Formatting**:
```
Input:  "100-110" or "100–110"
Output: "100--110"  (double dash for LaTeX)
```

### 4. PDF Generation

Generates beautifully formatted reference lists:

```bash
# IEEE style (numeric citations)
python generate_pdf.py refs.bib ieee_refs.pdf ieee

# ACM style
python generate_pdf.py refs.bib acm_refs.pdf acm

# APA style (author-year)
python generate_pdf.py refs.bib apa_refs.pdf apa

# Chinese GB/T 7714 standard
python generate_pdf.py refs.bib cn_refs.pdf gb7714
```

### 5. Change Logging

Generates detailed Markdown reports:

```markdown
# BibTeX Processing Change Log

## Summary Statistics
- Total entries processed: 50
- Entries modified: 35
- arXiv entries replaced: 5
- Fields added: 127
- Titles formatted: 48

## Detailed Changes by Entry

### `smith2023deep`
- ✅ **Added field** `doi`
  - **Value**: `10.1109/TPAMI.2023.123456`
  - **Source**: IEEE Xplore
- 📝 **Formatted title** (titlecase)
  - **Old**: `a deep learning approach`
  - **New**: `A Deep Learning Approach`

### `vaswani2017attention`
- 🔄 **Replaced arXiv preprint with published version**
  - **arXiv ID**: 1706.03762
  - **Published DOI**: 10.5555/3295222.3295349
  - **Source**: Semantic Scholar
```

## 🔧 Advanced Configuration

### Custom Protected Words

Edit `data/protected_words.json`:

```json
{
  "acronyms": ["IoT", "API", "CNN", "LSTM", "WiFi", "5G"],
  "organizations": ["IEEE", "ACM", "NASA"],
  "proper_nouns": ["TensorFlow", "PyTorch", "Linux"]
}
```

### Custom Journal Abbreviations

Edit `data/journal_abbr.json`:

```json
{
  "IEEE Transactions on ...": "IEEE Trans. ...",
  "Your Custom Journal Name": "YourJournal"
}
```

### Chinese Journal Support

Edit `data/chinese_journals.json` for Chinese publication formats:

```json
{
  "major_journals": {
    "计算机学报": {
      "english_name": "Chinese Journal of Computers",
      "issn": "0254-4164"
    }
  }
}
```

## 📊 Performance

- **Sequential processing**: ~2-3 seconds per entry
- **Parallel processing** (5 workers): ~0.5-1 second per entry
- **Large files** (1000+ entries): Use `parallel_processing: true`

**Rate limiting**: Built-in 1-second delay between requests to respect API limits.

## ⚠️ Troubleshooting

### Problem: LaTeX compilation fails

**Solution**:
```bash
# Verify LaTeX installation
pdflatex --version
biber --version

# Install missing LaTeX packages
tlmgr install biblatex biber
```

### Problem: API rate limiting

**Solution**: Increase `request_delay` in config:
```json
{
  "request_delay": 2.0  // Increase to 2 seconds
}
```

### Problem: arXiv replacement not working

**Possible causes**:
- No published version exists yet
- Title mismatch in search
- API timeout

**Check** `changes_log.md` for detailed error messages.

## 📝 Tips and Best Practices

1. **Backup your original BibTeX file** before processing
2. **Review `changes_log.md`** to verify modifications
3. **Test with a small subset** before processing large files
4. **Use parallel processing** for files with 50+ entries
5. **Check PDF output** to ensure formatting matches your requirements
6. **Customize protected words** for your specific field

## 🤝 Contributing

To add new features:

1. **New data source**: Add fetch function in `complete_bibtex.py`
2. **New citation style**: Add template in `templates/`
3. **New field formatter**: Extend `format_bibtex.py`

## 📄 License

See LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check this documentation
2. Review `changes_log.md` for error details
3. Open an issue on GitHub

---

**Happy citing! 📚✨**
