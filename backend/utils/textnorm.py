"""
Text normalization utilities for mixed Hindi/English content
"""

import re
import unicodedata
from typing import str

def normalize_text(text: str) -> str:
    """
    Normalize text for mixed Hindi/English content
    - Unicode NFC normalization
    - Strip ZWJ/ZWNJ, non-breaking spaces
    - Clean whitespace
    """
    if not text:
        return ""
    
    # Unicode NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    # Remove ZWJ (Zero Width Joiner) and ZWNJ (Zero Width Non-Joiner)
    text = text.replace('\u200d', '')  # ZWJ
    text = text.replace('\u200c', '')  # ZWNJ
    
    # Remove non-breaking spaces and other problematic spaces
    text = text.replace('\u00a0', ' ')  # Non-breaking space
    text = text.replace('\u2000', ' ')  # En quad
    text = text.replace('\u2001', ' ')  # Em quad
    text = text.replace('\u2002', ' ')  # En space
    text = text.replace('\u2003', ' ')  # Em space
    text = text.replace('\u2004', ' ')  # Three-per-em space
    text = text.replace('\u2005', ' ')  # Four-per-em space
    text = text.replace('\u2006', ' ')  # Six-per-em space
    text = text.replace('\u2007', ' ')  # Figure space
    text = text.replace('\u2008', ' ')  # Punctuation space
    text = text.replace('\u2009', ' ')  # Thin space
    text = text.replace('\u200a', ' ')  # Hair space
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def split_mixed_script_query(query: str) -> tuple[str, str]:
    """
    Split mixed script query into Devanagari and other scripts
    Returns (devanagari_part, other_part)
    """
    devanagari_pattern = re.compile(r'[\u0900-\u097F]+')
    
    devanagari_parts = []
    other_parts = []
    
    # Split by Devanagari script
    parts = devanagari_pattern.split(query)
    devanagari_matches = devanagari_pattern.findall(query)
    
    for i, part in enumerate(parts):
        if part.strip():
            other_parts.append(part.strip())
        
        if i < len(devanagari_matches):
            devanagari_parts.append(devanagari_matches[i])
    
    devanagari_query = ' '.join(devanagari_parts).strip()
    other_query = ' '.join(other_parts).strip()
    
    return devanagari_query, other_query

def is_devanagari(text: str) -> bool:
    """Check if text contains Devanagari script"""
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    return bool(devanagari_pattern.search(text))

def get_text_confidence(text: str) -> float:
    """
    Calculate confidence score based on alphanumeric density
    Higher score for more alphanumeric content
    """
    if not text:
        return 0.0
    
    alnum_count = sum(1 for c in text if c.isalnum())
    total_count = len(text)
    
    if total_count == 0:
        return 0.0
    
    return alnum_count / total_count

def clean_citation_text(text: str) -> str:
    """Clean text for citation extraction"""
    if not text:
        return ""
    
    # Remove common citation patterns
    text = re.sub(r'\[.*?\]', '', text)  # Remove [1], [2], etc.
    text = re.sub(r'\(.*?\)', '', text)  # Remove (1), (2), etc.
    
    # Normalize
    text = normalize_text(text)
    
    return text