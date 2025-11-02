# Examples

This directory contains sample files to help you get started with Awesome Citations.

## Files

- `sample_input.bib` - Example BibTeX file with various entry types
- `sample_config.json` - Example configuration file

## Quick Start

### 1. Run the complete workflow

```bash
cd /path/to/Awesome-Citations
python3 scripts/workflow_complete.py examples/sample_input.bib --output output/result.bib
```

This will:
- Sort and deduplicate entries
- Complete missing fields
- Standardize formatting
- Generate change log
- Generate PDF (if LaTeX installed)

### 2. Use custom configuration

```bash
python3 scripts/workflow_complete.py examples/sample_input.bib \
  --output output/result.bib \
  --config examples/sample_config.json
```

## Output Location

All output files will be saved to the `output/` directory:
- `output/result.bib` - Processed BibTeX file
- `output/result_changes.md` - Change log
- `output/result.pdf` - PDF bibliography

## More Examples

See the main [README.md](../README.md) and [docs/WORKFLOW_GUIDE.md](../docs/WORKFLOW_GUIDE.md) for more usage examples.
