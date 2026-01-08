"""
Awesome Citations - A comprehensive BibTeX bibliography management toolkit.

This package provides tools for:
- Completing incomplete BibTeX entries from multiple sources (IEEE, ACM, arXiv, CrossRef, etc.)
- Standardizing field formatting (titles, authors, journals, pages)
- Replacing arXiv preprints with published versions
- Generating PDF bibliographies in multiple citation styles
- Analyzing bibliography statistics
"""

__version__ = "0.1.0"
__author__ = "neardws"

from awesome_citations.scripts.workflow_complete import workflow_complete_bibtex
from awesome_citations.scripts.complete_bibtex import fetch_complete_bibtex
from awesome_citations.scripts.format_bibtex import standardize_entry
from awesome_citations.scripts.analyze_bibtex import analyze_bibtex_file
from awesome_citations.scripts.sort_bibtex import sort_bibtex_file as sort_bibtex
from awesome_citations.scripts.generate_pdf import generate_pdf_from_bibtex

__all__ = [
    "workflow_complete_bibtex",
    "fetch_complete_bibtex",
    "standardize_entry",
    "analyze_bibtex_file",
    "sort_bibtex",
    "generate_pdf_from_bibtex",
    "__version__",
]
