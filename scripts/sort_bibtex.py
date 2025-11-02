import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from operator import itemgetter

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

if __name__ == '__main__':
    input_file = 'input.bib'
    output_file = 'sorted_output.bib'
    sort_bibtex_file(input_file, output_file)
    print(f'Sorted BibTeX file saved as {output_file}')
