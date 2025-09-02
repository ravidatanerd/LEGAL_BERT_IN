"""
Legal LLM integration for Q&A, summarization, and judgment generation
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import openai
from loguru import logger

class LegalLLM:
    """Legal LLM for various legal tasks"""
    
    def __init__(self):
        self.client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Initialize OpenAI client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found")
                return
            
            self.client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
            
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    async def generate_answer(self, question: str, context: List[Dict[str, Any]], 
                            language: str = "auto") -> Dict[str, Any]:
        """Generate grounded answer with citations"""
        try:
            if not self.client:
                raise RuntimeError("OpenAI client not initialized")
            
            # Prepare context with citations
            context_text = self._prepare_context_with_citations(context)
            
            # Create prompt based on language
            if language == "hi" or (language == "auto" and self._is_hindi_query(question)):
                prompt = self._create_hindi_qa_prompt(question, context_text)
            else:
                prompt = self._create_english_qa_prompt(question, context_text)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Indian legal researcher and advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            answer_text = response.choices[0].message.content.strip()
            
            # Extract citations from response
            citations = self._extract_citations(answer_text)
            
            return {
                "text": answer_text,
                "citations": citations,
                "language": language,
                "context_used": len(context)
            }
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise
    
    async def generate_summary(self, document: Dict[str, Any], 
                             language: str = "auto") -> Dict[str, Any]:
        """Generate structured summary of legal document"""
        try:
            if not self.client:
                raise RuntimeError("OpenAI client not initialized")
            
            document_text = document.get('text', '')
            if not document_text:
                raise ValueError("Document text is empty")
            
            # Create summary prompt
            if language == "hi":
                prompt = self._create_hindi_summary_prompt(document_text)
            else:
                prompt = self._create_english_summary_prompt(document_text)
            
            # Generate summary
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert legal document analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Parse structured summary
            structured_summary = self._parse_structured_summary(summary_text)
            
            return {
                "summary": structured_summary,
                "language": language,
                "document_id": document.get('document_id', ''),
                "text_length": len(document_text)
            }
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise
    
    async def generate_judgment(self, facts: str, issues: List[str], 
                              context: List[Dict[str, Any]], 
                              language: str = "auto",
                              court_type: str = "high_court") -> Dict[str, Any]:
        """Generate structured legal judgment"""
        try:
            if not self.client:
                raise RuntimeError("OpenAI client not initialized")
            
            # Prepare context
            context_text = self._prepare_context_for_judgment(context)
            
            # Create judgment prompt
            if language == "hi":
                prompt = self._create_hindi_judgment_prompt(facts, issues, context_text, court_type)
            else:
                prompt = self._create_english_judgment_prompt(facts, issues, context_text, court_type)
            
            # Generate judgment
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Indian legal judge with deep knowledge of Indian law."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.2
            )
            
            judgment_text = response.choices[0].message.content.strip()
            
            # Parse structured judgment
            structured_judgment = self._parse_structured_judgment(judgment_text)
            
            return {
                "judgment": structured_judgment,
                "language": language,
                "court_type": court_type,
                "sources_used": len(context)
            }
            
        except Exception as e:
            logger.error(f"Judgment generation failed: {e}")
            raise
    
    def _prepare_context_with_citations(self, context: List[Dict[str, Any]]) -> str:
        """Prepare context with numbered citations"""
        context_parts = []
        
        for i, item in enumerate(context, 1):
            chunk_id = item.get('chunk_id', f'chunk_{i}')
            text = item.get('text', '')
            metadata = item.get('metadata', {})
            
            # Create citation
            source_file = metadata.get('source_file', 'Unknown')
            page_num = metadata.get('page_number', '')
            
            citation = f"[{i}] {source_file}"
            if page_num:
                citation += f", p.{page_num}"
            
            context_parts.append(f"{citation}\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _prepare_context_for_judgment(self, context: List[Dict[str, Any]]) -> str:
        """Prepare context for judgment generation"""
        context_parts = []
        
        for item in context:
            text = item.get('text', '')
            metadata = item.get('metadata', {})
            
            # Add source information
            source_info = metadata.get('source_file', 'Unknown')
            if 'section' in metadata:
                source_info += f" (Section {metadata['section']})"
            
            context_parts.append(f"Source: {source_info}\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _create_english_qa_prompt(self, question: str, context: str) -> str:
        """Create English Q&A prompt"""
        return f"""Based on the following legal documents and precedents, please provide a comprehensive answer to the question. Use numbered citations [1], [2], etc. to reference specific sources.

Question: {question}

Legal Context:
{context}

Please provide:
1. A direct answer to the question
2. Relevant legal principles and precedents
3. Proper citations using [n] format
4. Any important caveats or limitations

Answer:"""
    
    def _create_hindi_qa_prompt(self, question: str, context: str) -> str:
        """Create Hindi Q&A prompt"""
        return f"""निम्नलिखित कानूनी दस्तावेजों और नजीरों के आधार पर, कृपया प्रश्न का व्यापक उत्तर दें। विशिष्ट स्रोतों का संदर्भ देने के लिए क्रमांकित उद्धरण [1], [2], आदि का उपयोग करें।

प्रश्न: {question}

कानूनी संदर्भ:
{context}

कृपया प्रदान करें:
1. प्रश्न का प्रत्यक्ष उत्तर
2. प्रासंगिक कानूनी सिद्धांत और नजीरें
3. [n] प्रारूप का उपयोग करके उचित उद्धरण
4. कोई महत्वपूर्ण चेतावनी या सीमाएं

उत्तर:"""
    
    def _create_english_summary_prompt(self, document_text: str) -> str:
        """Create English summary prompt"""
        return f"""Please provide a structured summary of the following legal document in the following format:

**Facts:**
[Key factual information]

**Issues:**
[Legal issues raised]

**Arguments:**
[Key arguments presented]

**Holding:**
[Court's decision]

**Relief:**
[Relief granted or denied]

Document:
{document_text}

Summary:"""
    
    def _create_hindi_summary_prompt(self, document_text: str) -> str:
        """Create Hindi summary prompt"""
        return f"""कृपया निम्नलिखित कानूनी दस्तावेज का संरचित सारांश निम्नलिखित प्रारूप में प्रदान करें:

**तथ्य:**
[मुख्य तथ्यात्मक जानकारी]

**मुद्दे:**
[उठाए गए कानूनी मुद्दे]

**तर्क:**
[प्रस्तुत किए गए मुख्य तर्क]

**निर्णय:**
[न्यायालय का निर्णय]

**राहत:**
[प्रदान की गई या नकारी गई राहत]

दस्तावेज:
{document_text}

सारांश:"""
    
    def _create_english_judgment_prompt(self, facts: str, issues: List[str], 
                                      context: str, court_type: str) -> str:
        """Create English judgment prompt"""
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        
        return f"""Generate a comprehensive legal judgment in JSON format based on the following information. The judgment should follow Indian legal standards and precedents.

Case Facts:
{facts}

Legal Issues:
{issues_text}

Relevant Legal Context:
{context}

Court Type: {court_type}

Please generate a judgment in the following JSON structure:
{{
    "metadata": {{
        "court": "{court_type}",
        "case_number": "Generated case number",
        "date": "Current date",
        "judge": "Hon'ble Justice"
    }},
    "framing": "Brief case framing",
    "points_for_determination": ["Issue 1", "Issue 2", ...],
    "applicable_law": {{
        "constitutional": ["Relevant constitutional provisions"],
        "statutes": ["Relevant statutes"],
        "rules_regulations": ["Relevant rules"],
        "precedents": ["Relevant case law"]
    }},
    "arguments": {{
        "petitioner": ["Petitioner's arguments"],
        "respondent": ["Respondent's arguments"]
    }},
    "court_analysis": [
        {{
            "issue": "Issue description",
            "analysis": "Detailed legal analysis",
            "citations": ["Relevant citations"]
        }}
    ],
    "findings": ["Court's findings on each issue"],
    "relief": {{
        "final_order": "Final order text",
        "directions": ["Specific directions"],
        "costs": "Cost order"
    }},
    "prediction": {{
        "likely_outcome": "Predicted outcome",
        "probabilities": {{"success": 0.8, "failure": 0.2}},
        "drivers": ["Key factors driving the decision"]
    }},
    "limitations": ["Any limitations or caveats"]
}}

Judgment:"""
    
    def _create_hindi_judgment_prompt(self, facts: str, issues: List[str], 
                                    context: str, court_type: str) -> str:
        """Create Hindi judgment prompt"""
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        
        return f"""निम्नलिखित जानकारी के आधार पर JSON प्रारूप में एक व्यापक कानूनी निर्णय उत्पन्न करें। निर्णय भारतीय कानूनी मानकों और नजीरों का पालन करना चाहिए।

मामले के तथ्य:
{facts}

कानूनी मुद्दे:
{issues_text}

प्रासंगिक कानूनी संदर्भ:
{context}

न्यायालय प्रकार: {court_type}

कृपया निम्नलिखित JSON संरचना में निर्णय उत्पन्न करें:
[Same JSON structure as English version but with Hindi content]

निर्णय:"""
    
    def _parse_structured_summary(self, summary_text: str) -> Dict[str, Any]:
        """Parse structured summary from LLM response"""
        try:
            # Try to extract structured sections
            sections = {
                "facts": "",
                "issues": [],
                "arguments": [],
                "holding": "",
                "relief": ""
            }
            
            # Simple parsing - can be improved
            lines = summary_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('**Facts:**') or line.startswith('**तथ्य:**'):
                    current_section = 'facts'
                elif line.startswith('**Issues:**') or line.startswith('**मुद्दे:**'):
                    current_section = 'issues'
                elif line.startswith('**Arguments:**') or line.startswith('**तर्क:**'):
                    current_section = 'arguments'
                elif line.startswith('**Holding:**') or line.startswith('**निर्णय:**'):
                    current_section = 'holding'
                elif line.startswith('**Relief:**') or line.startswith('**राहत:**'):
                    current_section = 'relief'
                elif line.startswith('**') and line.endswith('**'):
                    current_section = None
                elif current_section:
                    if current_section in ['issues', 'arguments']:
                        if line.startswith('- '):
                            sections[current_section].append(line[2:])
                    else:
                        sections[current_section] += line + ' '
            
            # Clean up text
            for key in ['facts', 'holding', 'relief']:
                sections[key] = sections[key].strip()
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to parse structured summary: {e}")
            return {"raw_summary": summary_text}
    
    def _parse_structured_judgment(self, judgment_text: str) -> Dict[str, Any]:
        """Parse structured judgment from LLM response"""
        try:
            # Try to parse as JSON first
            if judgment_text.strip().startswith('{'):
                return json.loads(judgment_text)
            
            # Fallback to text parsing
            return {
                "raw_judgment": judgment_text,
                "parsing_error": "Could not parse as JSON"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse judgment JSON: {e}")
            return {
                "raw_judgment": judgment_text,
                "parsing_error": str(e)
            }
    
    def _extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations from text"""
        import re
        
        citations = []
        citation_pattern = r'\[(\d+)\]'
        
        matches = re.finditer(citation_pattern, text)
        for match in matches:
            citation_num = int(match.group(1))
            citations.append({
                "number": citation_num,
                "position": match.start(),
                "text": match.group(0)
            })
        
        return citations
    
    def _is_hindi_query(self, query: str) -> bool:
        """Check if query contains Hindi text"""
        # Simple check for Devanagari script
        devanagari_chars = sum(1 for c in query if '\u0900' <= c <= '\u097F')
        return devanagari_chars > len(query) * 0.3