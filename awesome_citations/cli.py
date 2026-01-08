#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line interface for Awesome Citations.

Usage:
    awesome-citations process <input.bib> [--output output.bib] [--config config.json]
    awesome-citations complete <input.bib> [--output output.bib]
    awesome-citations format <input.bib> <output.bib> [--config config.json]
    awesome-citations sort <input.bib> [--output output.bib]
    awesome-citations analyze <input.bib>
    awesome-citations pdf <input.bib> <output.pdf> [--style ieee]
"""

import argparse
import sys
import os


def get_default_config_path():
    """Get default config.json path."""
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(pkg_dir), 'config.json')
    if os.path.exists(config_path):
        return config_path
    return os.path.join(os.getcwd(), 'config.json')


def cmd_process(args):
    """Run complete workflow."""
    from awesome_citations.scripts.workflow_complete import workflow_complete_bibtex
    
    output = args.output
    if not output:
        base = os.path.splitext(args.input)[0]
        output = f"{base}_completed.bib"
    
    config = args.config if args.config else get_default_config_path()
    workflow_complete_bibtex(args.input, output, config)


def cmd_complete(args):
    """Complete BibTeX entries."""
    from awesome_citations.scripts.complete_bibtex import main as complete_main
    
    output = args.output
    if not output:
        base = os.path.splitext(args.input)[0]
        output = f"{base}_completed.bib"
    
    sys.argv = ['complete_bibtex', args.input, output]
    complete_main()


def cmd_format(args):
    """Format BibTeX entries."""
    from awesome_citations.scripts.format_bibtex import main as format_main
    
    config = args.config if args.config else get_default_config_path()
    sys.argv = ['format_bibtex', args.input, args.output, config]
    format_main()


def cmd_sort(args):
    """Sort BibTeX entries."""
    from awesome_citations.scripts.sort_bibtex import sort_bibtex
    
    output = args.output
    if not output:
        base = os.path.splitext(args.input)[0]
        output = f"{base}_sorted.bib"
    
    sort_bibtex(args.input, output)
    print(f"Sorted BibTeX saved to: {output}")


def cmd_analyze(args):
    """Analyze BibTeX file."""
    from awesome_citations.scripts.analyze_bibtex import analyze_bibtex_file, print_table
    type_counter, year_counter, publication_counter = analyze_bibtex_file(args.input)
    
    print_table(type_counter, 'Reference Types', ['Type', 'Count'])
    
    year_counter_int = {int(k): v for k, v in year_counter.items() if k != 'Unknown'}
    year_counter_sorted = dict(sorted(year_counter_int.items(), key=lambda x: x[0], reverse=True))
    print_table(year_counter_sorted, 'Publication Years', ['Year', 'Count'])
    
    publication_counter_sorted = dict(sorted(publication_counter.items(), key=lambda x: x[1], reverse=True))
    print_table(publication_counter_sorted, 'Publications', ['Publication', 'Count'])


def cmd_pdf(args):
    """Generate PDF bibliography."""
    from awesome_citations.scripts.generate_pdf import generate_pdf_from_bibtex, check_latex_installation
    
    if not check_latex_installation():
        print("Error: LaTeX (pdflatex and biber) is required for PDF generation.")
        sys.exit(1)
    
    config = {}
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    generate_pdf_from_bibtex(
        args.input,
        args.output,
        style=args.style,
        document_title=config.get('pdf_output', {}).get('document_title', 'References')
    )
    print(f"PDF generated: {args.output}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog='awesome-citations',
        description='Awesome Citations - A comprehensive BibTeX bibliography management toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  awesome-citations process refs.bib
  awesome-citations process refs.bib --output completed.bib --config config.json
  awesome-citations analyze refs.bib
  awesome-citations pdf refs.bib bibliography.pdf --style ieee
        """
    )
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # process command
    p_process = subparsers.add_parser('process', help='Run complete workflow (recommended)')
    p_process.add_argument('input', help='Input BibTeX file')
    p_process.add_argument('--output', '-o', help='Output BibTeX file')
    p_process.add_argument('--config', '-c', help='Configuration JSON file')
    p_process.set_defaults(func=cmd_process)
    
    # complete command
    p_complete = subparsers.add_parser('complete', help='Complete missing BibTeX fields')
    p_complete.add_argument('input', help='Input BibTeX file')
    p_complete.add_argument('--output', '-o', help='Output BibTeX file')
    p_complete.set_defaults(func=cmd_complete)
    
    # format command
    p_format = subparsers.add_parser('format', help='Standardize BibTeX formatting')
    p_format.add_argument('input', help='Input BibTeX file')
    p_format.add_argument('output', help='Output BibTeX file')
    p_format.add_argument('--config', '-c', help='Configuration JSON file')
    p_format.set_defaults(func=cmd_format)
    
    # sort command
    p_sort = subparsers.add_parser('sort', help='Sort BibTeX entries by ID')
    p_sort.add_argument('input', help='Input BibTeX file')
    p_sort.add_argument('--output', '-o', help='Output BibTeX file')
    p_sort.set_defaults(func=cmd_sort)
    
    # analyze command
    p_analyze = subparsers.add_parser('analyze', help='Analyze BibTeX statistics')
    p_analyze.add_argument('input', help='Input BibTeX file')
    p_analyze.set_defaults(func=cmd_analyze)
    
    # pdf command
    p_pdf = subparsers.add_parser('pdf', help='Generate PDF bibliography')
    p_pdf.add_argument('input', help='Input BibTeX file')
    p_pdf.add_argument('output', help='Output PDF file')
    p_pdf.add_argument('--style', '-s', default='ieee',
                       choices=['ieee', 'acm', 'apa', 'gb7714'],
                       help='Citation style (default: ieee)')
    p_pdf.add_argument('--config', '-c', help='Configuration JSON file')
    p_pdf.set_defaults(func=cmd_pdf)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
