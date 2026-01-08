#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Generation from BibTeX

This module generates formatted PDF bibliography from BibTeX files using LaTeX.
"""

import os
import subprocess
import shutil
import json
from typing import Optional
import tempfile


def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return {}


def check_latex_installation() -> bool:
    """
    Check if LaTeX (pdflatex and biber) is installed.

    Returns:
        True if LaTeX is available, False otherwise
    """
    try:
        # Check pdflatex
        result = subprocess.run(['pdflatex', '--version'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=5)
        if result.returncode != 0:
            return False

        # Check biber
        result = subprocess.run(['biber', '--version'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=5)
        if result.returncode != 0:
            return False

        return True

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def load_template(style: str, template_dir: str = 'templates') -> str:
    """
    Load LaTeX template for the specified style.

    Args:
        style: Citation style (ieee, acm, apa, gb7714, or custom)
        template_dir: Directory containing template files

    Returns:
        Template content as string
    """
    template_map = {
        'ieee': 'ieee_template.tex',
        'acm': 'acm_template.tex',
        'apa': 'apa_template.tex',
        'gb7714': 'gb7714_template.tex',
        'gb7714-2015': 'gb7714_template.tex'
    }

    template_file = template_map.get(style.lower())

    if not template_file:
        raise ValueError(f"Unknown style: {style}. Available: {list(template_map.keys())}")

    template_path = os.path.join(template_dir, template_file)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_tex_file(bib_file: str, output_tex: str, style: str,
                     document_title: str, template_dir: str = 'templates'):
    """
    Generate LaTeX file from template.

    Args:
        bib_file: Path to BibTeX file
        output_tex: Path to output .tex file
        style: Citation style
        document_title: Title for the document
        template_dir: Directory containing templates
    """
    # Load template
    template = load_template(style, template_dir)

    # Get absolute path for bib file (relative to tex file location)
    bib_file_abs = os.path.abspath(bib_file)

    # Fill in template
    content = template.format(
        bib_file=bib_file_abs,
        document_title=document_title
    )

    # Write tex file
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(content)


def compile_latex(tex_file: str, output_pdf: str, working_dir: Optional[str] = None) -> bool:
    """
    Compile LaTeX file to PDF.

    Args:
        tex_file: Path to .tex file
        output_pdf: Desired path for output PDF
        working_dir: Working directory for compilation

    Returns:
        True if compilation successful, False otherwise
    """
    if working_dir is None:
        working_dir = os.path.dirname(tex_file)

    tex_basename = os.path.basename(tex_file)
    tex_name_noext = os.path.splitext(tex_basename)[0]

    print(f"\n{'=' * 60}")
    print("LaTeX Compilation")
    print(f"{'=' * 60}\n")

    try:
        # First pdflatex run
        print("Running pdflatex (pass 1)...")
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_basename],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️  pdflatex (pass 1) returned error code {result.returncode}")
            print("Output:", result.stdout.decode('utf-8', errors='ignore')[-1000:])

        # Run biber
        print("Running biber...")
        result = subprocess.run(
            ['biber', tex_name_noext],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️  biber returned error code {result.returncode}")
            print("Output:", result.stdout.decode('utf-8', errors='ignore')[-1000:])

        # Second pdflatex run (to resolve references)
        print("Running pdflatex (pass 2)...")
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_basename],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️  pdflatex (pass 2) returned error code {result.returncode}")
            print("Output:", result.stdout.decode('utf-8', errors='ignore')[-1000:])

        # Third pdflatex run (to finalize)
        print("Running pdflatex (pass 3)...")
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_basename],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️  pdflatex (pass 3) returned error code {result.returncode}")
            print("Output:", result.stdout.decode('utf-8', errors='ignore')[-1000:])

        # Check if PDF was generated
        generated_pdf = os.path.join(working_dir, f"{tex_name_noext}.pdf")

        if not os.path.exists(generated_pdf):
            print("\n❌ PDF file was not generated")
            return False

        # Move PDF to desired location
        if os.path.abspath(generated_pdf) != os.path.abspath(output_pdf):
            shutil.copy2(generated_pdf, output_pdf)

        print(f"\n✓ PDF successfully generated: {output_pdf}\n")
        return True

    except subprocess.TimeoutExpired:
        print("\n❌ LaTeX compilation timed out")
        return False
    except Exception as e:
        print(f"\n❌ Error during compilation: {e}")
        return False


def cleanup_latex_files(tex_file: str):
    """
    Clean up auxiliary LaTeX files.

    Args:
        tex_file: Path to .tex file
    """
    base_name = os.path.splitext(tex_file)[0]
    extensions = ['.aux', '.log', '.bbl', '.bcf', '.blg', '.run.xml', '.out']

    for ext in extensions:
        aux_file = base_name + ext
        if os.path.exists(aux_file):
            try:
                os.remove(aux_file)
            except Exception as e:
                print(f"Warning: Failed to remove {aux_file}: {e}")


def generate_pdf_from_bibtex(bib_file: str, output_pdf: str = 'references.pdf',
                             style: str = 'ieee', config_path: str = 'config.json',
                             keep_tex: bool = False):
    """
    Generate PDF bibliography from BibTeX file.

    Args:
        bib_file: Path to input BibTeX file
        output_pdf: Path to output PDF file
        style: Citation style (ieee, acm, apa, gb7714)
        config_path: Path to configuration file
        keep_tex: Whether to keep intermediate .tex file
    """
    print(f"\n{'=' * 60}")
    print("PDF Generation from BibTeX")
    print(f"{'=' * 60}\n")

    # Check LaTeX installation
    print("Checking LaTeX installation...")
    if not check_latex_installation():
        print("❌ LaTeX is not installed or not in PATH")
        print("\nPlease install LaTeX:")
        print("  - MacOS: brew install --cask mactex")
        print("  - Ubuntu: sudo apt-get install texlive-full")
        print("  - Windows: https://miktex.org/download")
        return False

    print("✓ LaTeX installation found\n")

    # Load configuration
    config = load_config(config_path)
    pdf_config = config.get('pdf_output', {})

    # Override with config if available
    if 'document_title' in pdf_config:
        document_title = pdf_config['document_title']
    else:
        document_title = "参考文献列表 / References"

    # Create temporary directory for compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate .tex file
        tex_file = os.path.join(temp_dir, 'bibliography.tex')

        print(f"Generating LaTeX file...")
        print(f"  Style: {style}")
        print(f"  Title: {document_title}")

        try:
            generate_tex_file(bib_file, tex_file, style, document_title)
            print(f"✓ LaTeX file generated: {tex_file}\n")
        except Exception as e:
            print(f"❌ Failed to generate LaTeX file: {e}")
            return False

        # Compile to PDF
        success = compile_latex(tex_file, output_pdf, temp_dir)

        # Optionally save .tex file
        if keep_tex and success:
            output_tex = os.path.splitext(output_pdf)[0] + '.tex'
            shutil.copy2(tex_file, output_tex)
            print(f"LaTeX source saved to: {output_tex}")

    return success


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_pdf.py <bib_file> [output_pdf] [style] [config]")
        print("\nAvailable styles: ieee, acm, apa, gb7714")
        print("\nExample:")
        print("  python generate_pdf.py input.bib references.pdf ieee config.json")
        sys.exit(1)

    bib_file = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else 'references.pdf'
    style = sys.argv[3] if len(sys.argv) > 3 else 'ieee'
    config_file = sys.argv[4] if len(sys.argv) > 4 else 'config.json'

    success = generate_pdf_from_bibtex(bib_file, output_pdf, style, config_file, keep_tex=True)

    sys.exit(0 if success else 1)
