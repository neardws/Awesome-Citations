import sys
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from collections import Counter
from tabulate import tabulate
from operator import itemgetter

from awesome_citations.scripts.complete_bibtex import complete_bibtex_file

def remove_duplicates(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Remove duplicates based on the reference name
    bib_database.entries = {entry['ID']: entry for entry in bib_database.entries}.values()

    # Write the deduplicated entries to a new BibTeX file
    with open(output_file, 'w', encoding='utf-8') as deduplicated_bibtex_file:
        bibtexparser.dump(bib_database, deduplicated_bibtex_file)

def sort_bibtex_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Sort the entries by reference name
    bib_database.entries = sorted(bib_database.entries, key=itemgetter('ID'))

    # Write the sorted entries to a new BibTeX file
    with open(output_file, 'w', encoding='utf-8') as sorted_bibtex_file:
        bibtexparser.dump(bib_database, sorted_bibtex_file)

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
    sorted_data = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    print(f"\n{title}:")
    print(tabulate(sorted_data, headers=headers, tablefmt='grid'))

if __name__ == '__main__':
    input_file = 'refs.bib'
    sorted_file = 'sorted_output.bib'
    deduplicated_file = 'deduplicated_output.bib'
    sort_bibtex_file(input_file, sorted_file)
    remove_duplicates(sorted_file, deduplicated_file)
    print(f'Deduplicated BibTeX file saved as {deduplicated_file}')
    type_counter, year_counter, publication_counter = analyze_bibtex_file(deduplicated_file)

    # Print reference types table
    print_table(type_counter, 'Reference Types', ['Type', 'Count'])

    # Print publication years table sorted by newest order
    year_counter = {int(k): v for k, v in year_counter.items() if k != 'Unknown'}
    year_counter = dict(sorted(year_counter.items(), key=lambda x: x[0], reverse=True))
    print_table(year_counter, 'Publication Years', ['Year', 'Count'])

    # Print publications table sorted by numbers order
    publication_counter = dict(sorted(publication_counter.items(), key=lambda x: x[1], reverse=True))
    print_table(publication_counter, 'Publications', ['Publication', 'Count'])

