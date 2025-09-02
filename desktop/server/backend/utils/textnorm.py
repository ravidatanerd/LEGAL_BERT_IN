"""
Text normalization utilities for mixed Hindi/English content
"""
import unicodedata
import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Zero-width characters to remove
ZERO_WIDTH_CHARS = [
    '\u200c',  # ZWNJ (Zero Width Non-Joiner)
    '\u200d',  # ZWJ (Zero Width Joiner)
    '\u200b',  # ZWSP (Zero Width Space)
    '\u2060',  # WJ (Word Joiner)
    '\ufeff',  # BOM (Byte Order Mark)
]

# Non-breaking spaces to normalize
NON_BREAKING_SPACES = [
    '\u00a0',  # Non-breaking space
    '\u2007',  # Figure space
    '\u2009',  # Thin space
    '\u202f',  # Narrow no-break space
]

def normalize_text(text: str) -> str:
    """
    Normalize text for mixed Hindi/English content
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text safe for embedding and search
    """
    if not text:
        return ""
    
    try:
        # Unicode NFC normalization
        normalized = unicodedata.normalize('NFC', text)
        
        # Remove zero-width characters
        for char in ZERO_WIDTH_CHARS:
            normalized = normalized.replace(char, '')
        
        # Normalize non-breaking spaces to regular spaces
        for char in NON_BREAKING_SPACES:
            normalized = normalized.replace(char, ' ')
        
        # Clean up multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove excessive newlines but preserve paragraph breaks
        normalized = re.sub(r'\n\s*\n\s*\n+', '\n\n', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
        
    except Exception as e:
        logger.error(f"Text normalization failed: {e}")
        return text  # Return original text if normalization fails

def is_devanagari_text(text: str) -> bool:
    """
    Check if text contains Devanagari script
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains Devanagari characters
    """
    if not text:
        return False
    
    # Devanagari Unicode range: U+0900-U+097F
    devanagari_chars = sum(1 for char in text if 0x0900 <= ord(char) <= 0x097F)
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return False
    
    # Consider it Devanagari if >20% of alphabetic characters are Devanagari
    return (devanagari_chars / total_chars) > 0.2

def split_mixed_script_query(query: str) -> Dict[str, str]:
    """
    Split mixed Hindi/English query into separate components
    
    Args:
        query: Mixed script query
        
    Returns:
        Dict with 'devanagari' and 'other' components
    """
    if not query:
        return {"devanagari": "", "other": ""}
    
    # Simple approach: extract Devanagari and non-Devanagari parts
    devanagari_chars = []
    other_chars = []
    
    for char in query:
        if 0x0900 <= ord(char) <= 0x097F:
            devanagari_chars.append(char)
        else:
            other_chars.append(char)
    
    devanagari_text = ''.join(devanagari_chars).strip()
    other_text = ''.join(other_chars).strip()
    
    # Clean up the separated texts
    devanagari_text = re.sub(r'\s+', ' ', devanagari_text)
    other_text = re.sub(r'\s+', ' ', other_text)
    
    return {
        "devanagari": devanagari_text,
        "other": other_text
    }