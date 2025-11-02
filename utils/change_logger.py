#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Change Logger for BibTeX Processing

This module tracks and logs all changes made to BibTeX entries during
the completion and formatting process.
"""

from typing import Dict, List, Optional
from datetime import datetime
import re


class ChangeLogger:
    """
    Tracks changes made to BibTeX entries and generates detailed reports.
    """

    def __init__(self):
        self.changes = []
        self.stats = {
            'total_entries': 0,
            'entries_modified': 0,
            'arxiv_replaced': 0,
            'fields_added': 0,
            'fields_updated': 0,
            'titles_formatted': 0,
            'journals_normalized': 0,
            'errors': 0
        }

    def log_entry_processed(self, entry_id: str):
        """Log that an entry was processed."""
        self.stats['total_entries'] += 1

    def log_field_added(self, entry_id: str, field_name: str, new_value: str, source: str = ''):
        """
        Log that a new field was added to an entry.

        Args:
            entry_id: Entry ID
            field_name: Name of the field added
            new_value: Value of the new field
            source: Data source (e.g., 'IEEE', 'CrossRef', 'DBLP')
        """
        self.changes.append({
            'entry_id': entry_id,
            'change_type': 'field_added',
            'field': field_name,
            'old_value': None,
            'new_value': new_value,
            'source': source
        })
        self.stats['fields_added'] += 1

    def log_field_updated(self, entry_id: str, field_name: str, old_value: str, new_value: str, reason: str = ''):
        """
        Log that a field was updated.

        Args:
            entry_id: Entry ID
            field_name: Name of the field updated
            old_value: Original value
            new_value: New value
            reason: Reason for update (e.g., 'formatting', 'normalization')
        """
        self.changes.append({
            'entry_id': entry_id,
            'change_type': 'field_updated',
            'field': field_name,
            'old_value': old_value,
            'new_value': new_value,
            'reason': reason
        })
        self.stats['fields_updated'] += 1

    def log_arxiv_replacement(self, entry_id: str, arxiv_id: str, doi: str, source: str = ''):
        """
        Log that an arXiv entry was replaced with published version.

        Args:
            entry_id: Entry ID
            arxiv_id: Original arXiv ID
            doi: DOI of published version
            source: Source of published version
        """
        self.changes.append({
            'entry_id': entry_id,
            'change_type': 'arxiv_replaced',
            'arxiv_id': arxiv_id,
            'doi': doi,
            'source': source
        })
        self.stats['arxiv_replaced'] += 1

    def log_title_formatted(self, entry_id: str, old_title: str, new_title: str, format_type: str):
        """
        Log that a title was formatted.

        Args:
            entry_id: Entry ID
            old_title: Original title
            new_title: Formatted title
            format_type: Type of formatting applied
        """
        self.changes.append({
            'entry_id': entry_id,
            'change_type': 'title_formatted',
            'field': 'title',
            'old_value': old_title,
            'new_value': new_title,
            'format_type': format_type
        })
        self.stats['titles_formatted'] += 1

    def log_journal_normalized(self, entry_id: str, old_journal: str, new_journal: str, format_type: str):
        """
        Log that a journal/conference name was normalized.

        Args:
            entry_id: Entry ID
            old_journal: Original journal name
            new_journal: Normalized journal name
            format_type: 'abbreviation' or 'full'
        """
        self.changes.append({
            'entry_id': entry_id,
            'change_type': 'journal_normalized',
            'field': 'journal',
            'old_value': old_journal,
            'new_value': new_journal,
            'format_type': format_type
        })
        self.stats['journals_normalized'] += 1

    def log_error(self, entry_id: str, error_message: str):
        """
        Log an error that occurred during processing.

        Args:
            entry_id: Entry ID
            error_message: Error description
        """
        self.changes.append({
            'entry_id': entry_id,
            'change_type': 'error',
            'error': error_message
        })
        self.stats['errors'] += 1

    def get_entry_changes(self, entry_id: str) -> List[Dict]:
        """
        Get all changes for a specific entry.

        Args:
            entry_id: Entry ID

        Returns:
            List of change records for the entry
        """
        return [c for c in self.changes if c['entry_id'] == entry_id]

    def get_modified_entries(self) -> List[str]:
        """Get list of all entry IDs that were modified."""
        modified = set()
        for change in self.changes:
            if change['change_type'] != 'error':
                modified.add(change['entry_id'])
        return sorted(list(modified))

    def generate_markdown_report(self, output_file: str = 'changes_log.md'):
        """
        Generate a detailed Markdown report of all changes.

        Args:
            output_file: Path to output Markdown file
        """
        modified_entries = self.get_modified_entries()
        self.stats['entries_modified'] = len(modified_entries)

        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("# BibTeX Processing Change Log\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Summary Statistics
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total entries processed**: {self.stats['total_entries']}\n")
            f.write(f"- **Entries modified**: {self.stats['entries_modified']}\n")
            f.write(f"- **arXiv entries replaced**: {self.stats['arxiv_replaced']}\n")
            f.write(f"- **Fields added**: {self.stats['fields_added']}\n")
            f.write(f"- **Fields updated**: {self.stats['fields_updated']}\n")
            f.write(f"- **Titles formatted**: {self.stats['titles_formatted']}\n")
            f.write(f"- **Journals normalized**: {self.stats['journals_normalized']}\n")
            f.write(f"- **Errors encountered**: {self.stats['errors']}\n\n")

            # Change Type Summary
            change_types = {}
            for change in self.changes:
                ct = change['change_type']
                change_types[ct] = change_types.get(ct, 0) + 1

            f.write("## Changes by Type\n\n")
            for ct, count in sorted(change_types.items(), key=lambda x: -x[1]):
                f.write(f"- **{ct.replace('_', ' ').title()}**: {count}\n")
            f.write("\n")

            # Detailed Changes by Entry
            f.write("## Detailed Changes by Entry\n\n")

            for entry_id in modified_entries:
                entry_changes = self.get_entry_changes(entry_id)

                f.write(f"### `{entry_id}`\n\n")

                for change in entry_changes:
                    ct = change['change_type']

                    if ct == 'field_added':
                        f.write(f"- ✅ **Added field** `{change['field']}`\n")
                        f.write(f"  - **Value**: {self._format_value(change['new_value'])}\n")
                        if change.get('source'):
                            f.write(f"  - **Source**: {change['source']}\n")

                    elif ct == 'field_updated':
                        f.write(f"- 🔄 **Updated field** `{change['field']}`\n")
                        f.write(f"  - **Old**: {self._format_value(change['old_value'])}\n")
                        f.write(f"  - **New**: {self._format_value(change['new_value'])}\n")
                        if change.get('reason'):
                            f.write(f"  - **Reason**: {change['reason']}\n")

                    elif ct == 'arxiv_replaced':
                        f.write(f"- 🔄 **Replaced arXiv preprint with published version**\n")
                        f.write(f"  - **arXiv ID**: {change['arxiv_id']}\n")
                        f.write(f"  - **Published DOI**: {change['doi']}\n")
                        if change.get('source'):
                            f.write(f"  - **Source**: {change['source']}\n")

                    elif ct == 'title_formatted':
                        f.write(f"- 📝 **Formatted title** ({change.get('format_type', 'unknown')})\n")
                        f.write(f"  - **Old**: {self._format_value(change['old_value'])}\n")
                        f.write(f"  - **New**: {self._format_value(change['new_value'])}\n")

                    elif ct == 'journal_normalized':
                        f.write(f"- 📚 **Normalized journal name** ({change.get('format_type', 'unknown')})\n")
                        f.write(f"  - **Old**: {self._format_value(change['old_value'])}\n")
                        f.write(f"  - **New**: {self._format_value(change['new_value'])}\n")

                    elif ct == 'error':
                        f.write(f"- ❌ **Error**: {change['error']}\n")

                f.write("\n")

            # Errors Section
            if self.stats['errors'] > 0:
                f.write("## Errors\n\n")
                errors = [c for c in self.changes if c['change_type'] == 'error']
                for error in errors:
                    f.write(f"- **{error['entry_id']}**: {error['error']}\n")
                f.write("\n")

            # Footer
            f.write("---\n\n")
            f.write("*Generated by BibTeX Completion and Formatting Tool*\n")

        print(f"\n📄 Change log saved to: {output_file}")

    def _format_value(self, value: Optional[str], max_length: int = 100) -> str:
        """
        Format a value for display in the report.

        Args:
            value: Value to format
            max_length: Maximum length before truncation

        Returns:
            Formatted value string
        """
        if value is None:
            return "*None*"

        value = str(value).strip()

        if not value:
            return "*Empty*"

        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value)

        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length] + "..."

        # Escape markdown special characters
        value = value.replace('|', '\\|')

        return f"`{value}`"

    def print_summary(self):
        """Print a summary of changes to console."""
        modified = len(self.get_modified_entries())
        self.stats['entries_modified'] = modified

        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total entries processed:  {self.stats['total_entries']}")
        print(f"Entries modified:         {self.stats['entries_modified']}")
        print(f"arXiv entries replaced:   {self.stats['arxiv_replaced']}")
        print(f"Fields added:             {self.stats['fields_added']}")
        print(f"Fields updated:           {self.stats['fields_updated']}")
        print(f"Titles formatted:         {self.stats['titles_formatted']}")
        print(f"Journals normalized:      {self.stats['journals_normalized']}")
        print(f"Errors:                   {self.stats['errors']}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    # Test the logger
    logger = ChangeLogger()

    # Simulate some changes
    logger.log_entry_processed('smith2023')
    logger.log_field_added('smith2023', 'doi', '10.1109/test.2023.123456', 'IEEE Xplore')
    logger.log_field_added('smith2023', 'volume', '10', 'IEEE Xplore')
    logger.log_title_formatted('smith2023',
                              'a survey on machine learning',
                              'A Survey on Machine Learning',
                              'titlecase')

    logger.log_entry_processed('doe2022')
    logger.log_arxiv_replacement('doe2022', '2201.12345', '10.1145/3514567.890123', 'Semantic Scholar')

    logger.log_entry_processed('jones2024')
    logger.log_journal_normalized('jones2024',
                                  'IEEE Transactions on Pattern Analysis and Machine Intelligence',
                                  'IEEE Trans. Pattern Anal. Mach. Intell.',
                                  'abbreviation')

    logger.log_error('brown2023', 'Failed to fetch data from CrossRef API')

    # Print summary
    logger.print_summary()

    # Generate report
    logger.generate_markdown_report('test_changes_log.md')
    print("Test report generated: test_changes_log.md")
