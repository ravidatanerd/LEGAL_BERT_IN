"""
Text normalization utilities for mixed Hindi/English legal documents
"""

import re
import unicodedata
from typing import str
from loguru import logger

class TextNormalizer:
    """Text normalization for mixed Hindi/English legal documents"""
    
    def __init__(self):
        # Unicode categories to remove
        self.remove_categories = {
            'Cf',  # Format characters
            'Cc',  # Control characters
            'Co',  # Private use
            'Cs',  # Surrogates
        }
        
        # Specific characters to remove
        self.remove_chars = {
            '\u200B',  # Zero width space
            '\u200C',  # Zero width non-joiner
            '\u200D',  # Zero width joiner
            '\u2060',  # Word joiner
            '\uFEFF',  # Byte order mark
            '\u00A0',  # Non-breaking space
        }
    
    def normalize(self, text: str) -> str:
        """Normalize text for legal document processing"""
        if not text:
            return ""
        
        try:
            # Step 1: Unicode NFC normalization
            text = unicodedata.normalize('NFC', text)
            
            # Step 2: Remove unwanted Unicode categories
            text = self._remove_unicode_categories(text)
            
            # Step 3: Remove specific problematic characters
            text = self._remove_specific_chars(text)
            
            # Step 4: Clean whitespace
            text = self._clean_whitespace(text)
            
            # Step 5: Fix common OCR errors
            text = self._fix_ocr_errors(text)
            
            # Step 6: Normalize mixed script text
            text = self._normalize_mixed_script(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Text normalization failed: {e}")
            return text  # Return original text if normalization fails
    
    def _remove_unicode_categories(self, text: str) -> str:
        """Remove unwanted Unicode categories"""
        result = []
        for char in text:
            if unicodedata.category(char) not in self.remove_categories:
                result.append(char)
        return ''.join(result)
    
    def _remove_specific_chars(self, text: str) -> str:
        """Remove specific problematic characters"""
        for char in self.remove_chars:
            text = text.replace(char, '')
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean and normalize whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        # Remove empty lines at start and end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        
        return '\n'.join(lines)
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors in legal documents"""
        # Common OCR substitutions
        ocr_fixes = {
            # Numbers and letters
            '0': 'O',  # Zero to O (context dependent, but common in legal text)
            '1': 'l',  # One to lowercase l (context dependent)
            '5': 'S',  # Five to S (context dependent)
            
            # Legal specific
            '§': 'Section',
            '¶': 'Paragraph',
            '†': 'Footnote',
            '‡': 'Footnote',
            
            # Punctuation
            '"': '"',  # Straight quotes to curly quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # En dash to hyphen
            '—': '-',  # Em dash to hyphen
        }
        
        # Apply fixes (be careful with context-dependent ones)
        for wrong, correct in ocr_fixes.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _normalize_mixed_script(self, text: str) -> str:
        """Normalize mixed Hindi/English text"""
        # This is a simplified approach - in production, you might want
        # more sophisticated script detection and normalization
        
        # Ensure proper spacing around script boundaries
        # Hindi (Devanagari) script range: U+0900-U+097F
        devanagari_pattern = r'[\u0900-\u097F]+'
        
        # Add space before Hindi text if preceded by English
        text = re.sub(r'([a-zA-Z])([\u0900-\u097F])', r'\1 \2', text)
        
        # Add space after Hindi text if followed by English
        text = re.sub(r'([\u0900-\u097F])([a-zA-Z])', r'\1 \2', text)
        
        return text
    
    def extract_script_info(self, text: str) -> dict:
        """Extract information about scripts used in text"""
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len([c for c in text if c.isalpha()])
        
        return {
            'devanagari_ratio': devanagari_chars / max(total_chars, 1),
            'latin_ratio': latin_chars / max(total_chars, 1),
            'is_mixed_script': devanagari_chars > 0 and latin_chars > 0,
            'primary_script': 'devanagari' if devanagari_chars > latin_chars else 'latin'
        }
    
    def split_by_script(self, text: str) -> list:
        """Split text by script boundaries"""
        # Find script boundaries
        boundaries = []
        prev_script = None
        
        for i, char in enumerate(text):
            if char.isalpha():
                if '\u0900' <= char <= '\u097F':
                    current_script = 'devanagari'
                else:
                    current_script = 'latin'
                
                if prev_script and prev_script != current_script:
                    boundaries.append(i)
                prev_script = current_script
        
        # Split text at boundaries
        if not boundaries:
            return [text]
        
        parts = []
        start = 0
        for boundary in boundaries:
            parts.append(text[start:boundary])
            start = boundary
        parts.append(text[start:])
        
        return [part.strip() for part in parts if part.strip()]