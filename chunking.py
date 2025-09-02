"""
Document chunking system for legal documents
"""

import re
from typing import List, Dict, Any, Optional
from loguru import logger

class DocumentChunker:
    """Chunk legal documents for optimal retrieval"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 min_chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Legal document patterns
        self.section_patterns = [
            r'^Section\s+\d+[\.:]?\s*',
            r'^Article\s+\d+[\.:]?\s*',
            r'^Rule\s+\d+[\.:]?\s*',
            r'^Chapter\s+\d+[\.:]?\s*',
            r'^Part\s+\d+[\.:]?\s*',
            r'^Schedule\s+\d+[\.:]?\s*',
            r'^Appendix\s+\d+[\.:]?\s*',
        ]
        
        self.case_patterns = [
            r'^In\s+the\s+matter\s+of',
            r'^In\s+re:',
            r'^State\s+vs\.?\s+',
            r'^Union\s+of\s+India\s+vs\.?\s+',
            r'^Petitioner\s+vs\.?\s+',
            r'^Appellant\s+vs\.?\s+',
        ]
    
    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk a legal document into optimal segments"""
        try:
            if not text or not text.strip():
                return []
            
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Detect document type and choose chunking strategy
            doc_type = self._detect_document_type(processed_text)
            
            if doc_type == "statute":
                chunks = self._chunk_statute(processed_text, metadata)
            elif doc_type == "judgment":
                chunks = self._chunk_judgment(processed_text, metadata)
            elif doc_type == "case_law":
                chunks = self._chunk_case_law(processed_text, metadata)
            else:
                chunks = self._chunk_generic(processed_text, metadata)
            
            # Post-process chunks
            chunks = self._postprocess_chunks(chunks, metadata)
            
            logger.info(f"Created {len(chunks)} chunks for document type: {doc_type}")
            return chunks
            
        except Exception as e:
            logger.error(f"Document chunking failed: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for chunking"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper sentence boundaries
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\2', text)
        
        # Split into lines for better structure detection
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _detect_document_type(self, text: str) -> str:
        """Detect the type of legal document"""
        text_lower = text.lower()
        
        # Check for statute patterns
        statute_indicators = [
            'act', 'section', 'article', 'rule', 'regulation',
            'schedule', 'appendix', 'chapter', 'part'
        ]
        
        # Check for judgment patterns
        judgment_indicators = [
            'judgment', 'order', 'decree', 'petition', 'appeal',
            'writ petition', 'criminal appeal', 'civil appeal'
        ]
        
        # Check for case law patterns
        case_indicators = [
            'vs.', 'versus', 'petitioner', 'respondent', 'appellant',
            'in the matter of', 'state vs', 'union of india vs'
        ]
        
        statute_score = sum(1 for indicator in statute_indicators if indicator in text_lower)
        judgment_score = sum(1 for indicator in judgment_indicators if indicator in text_lower)
        case_score = sum(1 for indicator in case_indicators if indicator in text_lower)
        
        if statute_score > judgment_score and statute_score > case_score:
            return "statute"
        elif judgment_score > case_score:
            return "judgment"
        elif case_score > 0:
            return "case_law"
        else:
            return "generic"
    
    def _chunk_statute(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk statute documents by sections"""
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new section
            is_section_header = any(re.match(pattern, line, re.IGNORECASE) 
                                  for pattern in self.section_patterns)
            
            if is_section_header:
                # Save previous chunk if it exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            chunk_text, metadata, current_section
                        ))
                
                # Start new chunk
                current_chunk = [line]
                current_section = self._extract_section_number(line)
            else:
                current_chunk.append(line)
                
                # Check if chunk is getting too large
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text) > self.chunk_size:
                    # Split at sentence boundary
                    sentences = self._split_at_sentence_boundary(chunk_text)
                    if len(sentences) > 1:
                        # Save first part
                        chunks.append(self._create_chunk(
                            sentences[0], metadata, current_section
                        ))
                        # Continue with remaining text
                        current_chunk = [sentences[1]]
                    else:
                        # Force split
                        mid_point = len(chunk_text) // 2
                        split_point = self._find_split_point(chunk_text, mid_point)
                        chunks.append(self._create_chunk(
                            chunk_text[:split_point], metadata, current_section
                        ))
                        current_chunk = [chunk_text[split_point:]]
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    chunk_text, metadata, current_section
                ))
        
        return chunks
    
    def _chunk_judgment(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk judgment documents by logical sections"""
        chunks = []
        
        # Split by major sections
        sections = self._split_judgment_sections(text)
        
        for section_name, section_text in sections.items():
            if len(section_text) <= self.chunk_size:
                chunks.append(self._create_chunk(
                    section_text, metadata, section_name
                ))
            else:
                # Further split large sections
                sub_chunks = self._chunk_by_paragraphs(section_text, metadata, section_name)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_case_law(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk case law documents"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = []
        for paragraph in paragraphs:
            current_chunk.append(paragraph)
            chunk_text = '\n\n'.join(current_chunk)
            
            if len(chunk_text) > self.chunk_size:
                if len(current_chunk) > 1:
                    # Save all but last paragraph
                    chunks.append(self._create_chunk(
                        '\n\n'.join(current_chunk[:-1]), metadata
                    ))
                    current_chunk = [current_chunk[-1]]
                else:
                    # Single large paragraph - split it
                    sub_chunks = self._chunk_by_sentences(paragraph, metadata)
                    chunks.extend(sub_chunks[:-1])  # All but last
                    current_chunk = [sub_chunks[-1]['text']] if sub_chunks else []
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(chunk_text, metadata))
        
        return chunks
    
    def _chunk_generic(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic chunking strategy"""
        chunks = []
        
        # Split by paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = []
        for paragraph in paragraphs:
            current_chunk.append(paragraph)
            chunk_text = '\n\n'.join(current_chunk)
            
            if len(chunk_text) > self.chunk_size:
                if len(current_chunk) > 1:
                    chunks.append(self._create_chunk(
                        '\n\n'.join(current_chunk[:-1]), metadata
                    ))
                    current_chunk = [current_chunk[-1]]
                else:
                    # Split large paragraph
                    mid_point = len(chunk_text) // 2
                    split_point = self._find_split_point(chunk_text, mid_point)
                    chunks.append(self._create_chunk(
                        chunk_text[:split_point], metadata
                    ))
                    current_chunk = [chunk_text[split_point:]]
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(chunk_text, metadata))
        
        return chunks
    
    def _split_judgment_sections(self, text: str) -> Dict[str, str]:
        """Split judgment into logical sections"""
        sections = {}
        
        # Common judgment sections
        section_patterns = {
            'facts': r'(?:facts?|background|case\s+history)',
            'issues': r'(?:issues?|questions?|points?\s+for\s+determination)',
            'arguments': r'(?:arguments?|contentions?|submissions?)',
            'analysis': r'(?:analysis|reasoning|discussion)',
            'holding': r'(?:holding|decision|conclusion)',
            'relief': r'(?:relief|order|directions?)'
        }
        
        current_section = 'introduction'
        current_text = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new section
            new_section = None
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    new_section = section_name
                    break
            
            if new_section and new_section != current_section:
                # Save current section
                if current_text:
                    sections[current_section] = '\n'.join(current_text)
                
                # Start new section
                current_section = new_section
                current_text = [line]
            else:
                current_text.append(line)
        
        # Save final section
        if current_text:
            sections[current_section] = '\n'.join(current_text)
        
        return sections
    
    def _chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any], 
                           section_name: str) -> List[Dict[str, Any]]:
        """Chunk text by paragraphs"""
        chunks = []
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = []
        for paragraph in paragraphs:
            current_chunk.append(paragraph)
            chunk_text = '\n\n'.join(current_chunk)
            
            if len(chunk_text) > self.chunk_size:
                if len(current_chunk) > 1:
                    chunks.append(self._create_chunk(
                        '\n\n'.join(current_chunk[:-1]), metadata, section_name
                    ))
                    current_chunk = [current_chunk[-1]]
                else:
                    # Split large paragraph
                    mid_point = len(chunk_text) // 2
                    split_point = self._find_split_point(chunk_text, mid_point)
                    chunks.append(self._create_chunk(
                        chunk_text[:split_point], metadata, section_name
                    ))
                    current_chunk = [chunk_text[split_point:]]
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    chunk_text, metadata, section_name
                ))
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text by sentences"""
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        
        current_chunk = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            current_chunk.append(sentence)
            chunk_text = '. '.join(current_chunk)
            
            if len(chunk_text) > self.chunk_size:
                if len(current_chunk) > 1:
                    chunks.append(self._create_chunk(
                        '. '.join(current_chunk[:-1]) + '.', metadata
                    ))
                    current_chunk = [current_chunk[-1]]
                else:
                    # Single long sentence - force split
                    mid_point = len(chunk_text) // 2
                    split_point = self._find_split_point(chunk_text, mid_point)
                    chunks.append(self._create_chunk(
                        chunk_text[:split_point], metadata
                    ))
                    current_chunk = [chunk_text[split_point:]]
        
        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(chunk_text, metadata))
        
        return chunks
    
    def _create_chunk(self, text: str, metadata: Dict[str, Any], 
                     section: Optional[str] = None) -> Dict[str, Any]:
        """Create a chunk with metadata"""
        chunk = {
            'text': text,
            'length': len(text),
            'word_count': len(text.split()),
            'metadata': metadata.copy(),
            'section': section,
            'chunk_type': self._classify_chunk_type(text)
        }
        
        # Add chunk-specific metadata
        chunk['metadata']['chunk_length'] = len(text)
        chunk['metadata']['chunk_word_count'] = len(text.split())
        if section:
            chunk['metadata']['section'] = section
        
        return chunk
    
    def _classify_chunk_type(self, text: str) -> str:
        """Classify the type of chunk content"""
        text_lower = text.lower()
        
        if any(pattern in text_lower for pattern in ['section', 'article', 'rule']):
            return 'statutory_provision'
        elif any(pattern in text_lower for pattern in ['judgment', 'order', 'decree']):
            return 'judicial_decision'
        elif any(pattern in text_lower for pattern in ['facts', 'background']):
            return 'factual_content'
        elif any(pattern in text_lower for pattern in ['analysis', 'reasoning']):
            return 'legal_analysis'
        elif any(pattern in text_lower for pattern in ['argument', 'contention']):
            return 'legal_argument'
        else:
            return 'general_content'
    
    def _extract_section_number(self, line: str) -> Optional[str]:
        """Extract section number from line"""
        for pattern in self.section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _split_at_sentence_boundary(self, text: str) -> List[str]:
        """Split text at sentence boundary"""
        sentences = re.split(r'([.!?]+)', text)
        if len(sentences) <= 2:
            return [text]
        
        # Reconstruct sentences with punctuation
        result = []
        current = ""
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            
            current += sentence
            if len(current) > self.chunk_size // 2:
                result.append(current)
                current = ""
        
        if current:
            result.append(current)
        
        return result if result else [text]
    
    def _find_split_point(self, text: str, preferred_point: int) -> int:
        """Find a good split point near the preferred point"""
        # Look for sentence boundaries
        for i in range(preferred_point, min(preferred_point + 100, len(text))):
            if text[i] in '.!?':
                return i + 1
        
        # Look backwards
        for i in range(preferred_point, max(preferred_point - 100, 0), -1):
            if text[i] in '.!?':
                return i + 1
        
        # Fall back to word boundary
        for i in range(preferred_point, min(preferred_point + 50, len(text))):
            if text[i] == ' ':
                return i
        
        return preferred_point
    
    def _postprocess_chunks(self, chunks: List[Dict[str, Any]], 
                          metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Post-process chunks for quality"""
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Add chunk index
            chunk['chunk_index'] = i
            
            # Add overlap with previous chunk if needed
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk['text'][-self.chunk_overlap:]
                chunk['overlap_with_previous'] = overlap_text
            
            # Validate chunk quality
            if self._is_valid_chunk(chunk):
                processed_chunks.append(chunk)
            else:
                logger.warning(f"Skipping invalid chunk {i}: {chunk.get('text', '')[:100]}...")
        
        return processed_chunks
    
    def _is_valid_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Validate chunk quality"""
        text = chunk.get('text', '')
        
        # Check minimum length
        if len(text) < self.min_chunk_size:
            return False
        
        # Check for meaningful content
        words = text.split()
        if len(words) < 10:
            return False
        
        # Check alphanumeric ratio
        alnum_chars = sum(1 for c in text if c.isalnum())
        if alnum_chars / max(len(text), 1) < 0.3:
            return False
        
        return True