#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Title Formatter for BibTeX

This module formats BibTeX titles to Title Case with proper protection
of acronyms, proper nouns, and special terms.
"""

import re
import json
import os
from typing import List, Set


def load_protected_words(config_path: str = None) -> Set[str]:
    """
    Load protected words from configuration file.

    Args:
        config_path: Path to protected_words.json

    Returns:
        Set of protected words
    """
    if config_path is None:
        # Default path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, 'data', 'protected_words.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        protected = set()
        protected.update(data.get('acronyms', []))
        protected.update(data.get('organizations', []))
        protected.update(data.get('proper_nouns', []))

        return protected
    except Exception as e:
        print(f"Warning: Failed to load protected words: {e}")
        return set()


def load_small_words(config_path: str = None) -> Set[str]:
    """
    Load small words (articles, prepositions, conjunctions) from configuration.

    Args:
        config_path: Path to small_words.json

    Returns:
        Set of small words that should be lowercase (unless first/last word)
    """
    if config_path is None:
        # Default path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, 'data', 'small_words.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        small = set()
        small.update(data.get('articles', []))
        small.update(data.get('conjunctions', []))
        small.update(data.get('prepositions', []))

        return small
    except Exception as e:
        print(f"Warning: Failed to load small words: {e}")
        # Default small words
        return {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
                'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'from', 'with'}


def extract_protected_parts(title: str, protected_words: Set[str]) -> List[tuple]:
    """
    Extract parts of the title that should be protected (wrapped in braces).

    Args:
        title: Title string
        protected_words: Set of words to protect

    Returns:
        List of tuples (start_pos, end_pos, word) for protected parts
    """
    protected_parts = []

    # Find all protected words in the title (case-insensitive match)
    for word in protected_words:
        # Match whole word only
        pattern = r'\b' + re.escape(word) + r'\b'
        for match in re.finditer(pattern, title, re.IGNORECASE):
            # Keep the original case from the title
            protected_parts.append((match.start(), match.end(), match.group()))

    # Also find words already in braces - they should remain protected
    for match in re.finditer(r'\{([^}]+)\}', title):
        protected_parts.append((match.start(), match.end(), match.group()))

    # Sort by position
    protected_parts.sort(key=lambda x: x[0])

    return protected_parts


def is_likely_acronym(word: str) -> bool:
    """
    Heuristically determine if a word is likely an acronym.

    Args:
        word: Word to check

    Returns:
        True if word appears to be an acronym
    """
    # All uppercase and 2-6 characters
    if word.isupper() and 2 <= len(word) <= 6:
        return True

    # Mixed case but follows pattern like "IoT" or "LoRa"
    if len(word) >= 2 and word[0].isupper() and any(c.isupper() for c in word[1:]):
        # Check if it has internal capitals (camelCase pattern)
        if sum(1 for c in word if c.isupper()) >= 2:
            return True

    return False


def to_title_case(title: str, protected_words: Set[str] = None, small_words: Set[str] = None) -> str:
    """
    Convert title to Title Case with proper protection of special terms.

    Title Case rules:
    - First and last words are always capitalized
    - Major words (nouns, verbs, adjectives, adverbs) are capitalized
    - Minor words (articles, prepositions, conjunctions) are lowercase unless first/last
    - Protected words (acronyms, proper nouns) maintain their original case
    - Protected words are wrapped in braces for LaTeX

    Args:
        title: Title string to format
        protected_words: Set of words to protect (loaded from config if None)
        small_words: Set of small words to keep lowercase (loaded from config if None)

    Returns:
        Formatted title string with braces around protected words
    """
    if protected_words is None:
        protected_words = load_protected_words()

    if small_words is None:
        small_words = load_small_words()

    # Remove existing braces for processing
    clean_title = re.sub(r'[{}]', '', title)

    # Find protected parts before processing
    protected_parts = extract_protected_parts(clean_title, protected_words)

    # Split into words, preserving punctuation
    # This regex keeps punctuation attached to words
    words = re.findall(r"[\w'-]+|[^\w\s]", clean_title)

    formatted_words = []
    word_positions = []
    current_pos = 0

    for i, word in enumerate(words):
        # Find the position of this word in the original title
        word_pos = clean_title.find(word, current_pos)
        word_positions.append((word_pos, word_pos + len(word)))
        current_pos = word_pos + len(word)

        # Check if this word should be protected
        is_protected = False
        for start, end, protected_text in protected_parts:
            if start <= word_pos < end:
                is_protected = True
                break

        # Skip punctuation
        if not re.match(r"[\w'-]+", word):
            formatted_words.append(word)
            continue

        # Check if word is likely an acronym
        if is_likely_acronym(word):
            formatted_words.append('{' + word + '}')
            continue

        # Apply Title Case rules
        if is_protected:
            # Keep original case and add braces
            formatted_words.append('{' + word + '}')
        elif i == 0 or i == len(words) - 1:
            # First and last words always capitalized
            formatted_words.append(word.capitalize())
        elif word.lower() in small_words:
            # Small words stay lowercase
            formatted_words.append(word.lower())
        else:
            # Major words get capitalized
            formatted_words.append(word.capitalize())

    # Join words, handling spacing around punctuation
    result = []
    for i, word in enumerate(formatted_words):
        if i == 0:
            result.append(word)
        elif word in ',:;.!?)]\'"' or (i > 0 and formatted_words[i-1] in '(["\'{'):
            result.append(word)
        else:
            result.append(' ' + word)

    return ''.join(result)


def format_title_sentence_case(title: str, protected_words: Set[str] = None) -> str:
    """
    Convert title to sentence case (only first word and proper nouns capitalized).

    Args:
        title: Title string to format
        protected_words: Set of words to protect

    Returns:
        Formatted title string
    """
    if protected_words is None:
        protected_words = load_protected_words()

    # Remove existing braces
    clean_title = re.sub(r'[{}]', '', title)

    # Find protected parts
    protected_parts = extract_protected_parts(clean_title, protected_words)

    # Convert to lowercase first
    result = clean_title.lower()

    # Capitalize first letter
    if result:
        result = result[0].upper() + result[1:]

    # Capitalize after sentence-ending punctuation
    result = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)

    # Protect special words
    for start, end, word in protected_parts:
        if not word.startswith('{'):
            result = result[:start] + '{' + word + '}' + result[end:]

    return result


def preserve_with_protection(title: str, protected_words: Set[str] = None) -> str:
    """
    Keep original title case but add braces around protected words.

    Args:
        title: Title string
        protected_words: Set of words to protect

    Returns:
        Title with braces around protected words
    """
    if protected_words is None:
        protected_words = load_protected_words()

    # If already has braces around protected words, return as-is
    if '{' in title:
        return title

    result = title

    # Sort protected words by length (longest first) to avoid partial matches
    sorted_protected = sorted(protected_words, key=len, reverse=True)

    for word in sorted_protected:
        # Match whole word only, case-insensitive
        pattern = r'\b(' + re.escape(word) + r')\b'
        result = re.sub(pattern, r'{\1}', result, flags=re.IGNORECASE)

    return result


def format_title(title: str, format_type: str = 'titlecase',
                 protected_words: Set[str] = None, small_words: Set[str] = None) -> str:
    """
    Format a title according to the specified format type.

    Args:
        title: Title string to format
        format_type: One of 'titlecase', 'sentencecase', or 'preserve'
        protected_words: Set of words to protect
        small_words: Set of small words to keep lowercase

    Returns:
        Formatted title string
    """
    if not title or not title.strip():
        return title

    format_type = format_type.lower()

    if format_type == 'titlecase':
        return to_title_case(title, protected_words, small_words)
    elif format_type == 'sentencecase':
        return format_title_sentence_case(title, protected_words)
    elif format_type == 'preserve':
        return preserve_with_protection(title, protected_words)
    else:
        raise ValueError(f"Unknown format type: {format_type}")


if __name__ == "__main__":
    # Test the formatter
    test_titles = [
        "a survey on deep learning for natural language processing",
        "IoT-based Smart Home System Using LoRa Technology",
        "The IEEE 802.11 Standard for WiFi Communications",
        "Attention is all you need",
        "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "End-to-end learning for the semantic web using RDF and neural networks",
        "An introduction to machine learning with TensorFlow and PyTorch"
    ]

    print("Testing Title Formatter")
    print("=" * 80)

    for title in test_titles:
        print(f"\nOriginal: {title}")
        print(f"Title Case: {format_title(title, 'titlecase')}")
        print(f"Sentence Case: {format_title(title, 'sentencecase')}")
        print(f"Preserve: {format_title(title, 'preserve')}")
