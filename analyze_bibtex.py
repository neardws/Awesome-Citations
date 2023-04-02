import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from collections import Counter
from tabulate import tabulate

def analyze_bibtex_file(input_file):
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Analyze reference types
    type_counter = Counter(entry['ENTRYTYPE'] for entry in bib_database.entries)

    # Analyze publication years
    year_counter = Counter(entry.get('year', 'Unknown') for entry in bib_database.entries)

    # Analyze publications (journals, conferences, etc.)
    publication_counter = Counter(entry.get('journal', entry.get('booktitle', 'Unknown')) for entry in bib_database.entries)

    return type_counter, year_counter, publication_counter

def print_table(counter, title, headers):
    sorted_data = sorted(counter.items())
    print(f"\n{title}:")
    print(tabulate(sorted_data, headers=headers, tablefmt='grid'))

if __name__ == '__main__':
    input_file = 'input.bib'
    type_counter, year_counter, publication_counter = analyze_bibtex_file(input_file)

    # Print reference types table
    print_table(type_counter, 'Reference Types', ['Type', 'Count'])

    # Print publication years table sorted by newest order
    year_counter = {int(k): v for k, v in year_counter.items() if k != 'Unknown'}
    year_counter = dict(sorted(year_counter.items(), key=lambda x: x[0], reverse=True))
    print_table(year_counter, 'Publication Years', ['Year', 'Count'])

    # Print publications table sorted by numbers order
    publication_counter = dict(sorted(publication_counter.items(), key=lambda x: x[1], reverse=True))
    print_table(publication_counter, 'Publications', ['Publication', 'Count'])
