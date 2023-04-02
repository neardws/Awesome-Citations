# Awesome Citations

Awesome Citations is a Python project that helps you analyze and sort your BibTeX files. With this project, you can easily sort your BibTeX references, find the proportion of references under different types, years, and publications, and output the results as tables.

## Features

- Sort BibTeX files by reference names (IDs)
- Analyze the proportion of references by:
- Reference types (e.g., articles, books, conferences)
- Publication years
- Publications (e.g., journals, conferences)

## Dependencies

- bibtexparser

- tabulate

## Installation

To install the required libraries, run the following command:

```bash     
pip install bibtexparser tabulate     
```

## Usage


1. Sort a BibTeX file by reference names:

- Edit `sort_bibtex.py` and replace `input.bib` and `sorted_output.bib` with the names of your input and output files.
- Run the script:
```bash
python sort_bibtex.py
```

2. Analyze a BibTeX file:

- Edit `analyze_bibtex.py` and replace `input.bib` with the name of your BibTeX file.
- Run the script:
```bash
python analyze_bibtex.py
```

This script will output three tables for reference types, publication years (sorted by newest order), and publications (sorted by numbers order).

## Acknowledgment

Special thanks to ChatGPT by OpenAI for providing valuable assistance in the development of this project.

## License

[GNU General Public License v3.0](LICENSE)