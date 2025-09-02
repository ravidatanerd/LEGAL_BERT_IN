"""
LLM service for legal research and judgment generation
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI
import asyncio

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service for legal tasks"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def generate_answer(
        self, 
        question: str, 
        context: List[Dict[str, Any]], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate grounded answer with citations"""
        try:
            # Prepare context with citations
            context_text = ""
            citations = []
            
            for i, result in enumerate(context, 1):
                chunk = result
                context_text += f"[{i}] {chunk['text']}\n\n"
                citations.append({
                    "id": i,
                    "text": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                    "document_id": chunk['document_id'],
                    "page_number": chunk['page_number'],
                    "confidence": chunk['confidence'],
                    "score": chunk.get('combined_score', 0.0)
                })
            
            # Determine language for response
            response_language = self._determine_language(question, language)
            
            # Create prompt
            system_prompt = self._get_qa_system_prompt(response_language)
            user_prompt = f"""Question: {question}

Context:
{context_text}

Please provide a comprehensive answer based on the context above. Use [n] citations to reference specific sources. Be precise and cite relevant legal provisions, cases, or statutes."""

            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.3
            )
            
            answer_text = response.choices[0].message.content.strip()
            
            return {
                "text": answer_text,
                "citations": citations,
                "language": response_language,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    async def generate_summary(
        self, 
        documents: List[Dict[str, Any]], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate structured summary of documents"""
        try:
            # Prepare document text
            document_text = ""
            for doc in documents:
                document_text += f"Document: {doc['document_id']}\n"
                for page_num, page_chunks in doc['pages'].items():
                    document_text += f"Page {page_num}:\n"
                    for chunk in page_chunks:
                        document_text += f"{chunk['text']}\n"
                document_text += "\n" + "="*50 + "\n\n"
            
            # Determine language
            response_language = self._determine_language(document_text, language)
            
            # Create prompt
            system_prompt = self._get_summary_system_prompt(response_language)
            user_prompt = f"""Please provide a structured summary of the following legal documents:

{document_text}

Provide a comprehensive summary with the following structure:
1. Facts
2. Issues
3. Arguments
4. Holding
5. Relief"""

            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.3
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            return {
                "summary": summary_text,
                "language": response_language,
                "document_count": len(documents),
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    async def generate_judgment(
        self, 
        case_facts: str, 
        issues: List[str], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate structured judgment"""
        try:
            # Determine language
            response_language = self._determine_language(case_facts, language)
            
            # Create prompt
            system_prompt = self._get_judgment_system_prompt(response_language)
            user_prompt = f"""Case Facts:
{case_facts}

Issues for Determination:
{chr(10).join(f"- {issue}" for issue in issues)}

Please generate a comprehensive judgment following the strict JSON schema provided in the system prompt."""

            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096,
                temperature=0.3
            )
            
            judgment_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                judgment_data = json.loads(judgment_text)
            except json.JSONDecodeError:
                # If not valid JSON, wrap in a basic structure
                judgment_data = {
                    "metadata": {
                        "case_title": "Generated Case",
                        "court": "High Court",
                        "date": "2024-01-01",
                        "case_number": "HC/2024/001"
                    },
                    "framing": case_facts,
                    "points_for_determination": issues,
                    "applicable_law": {
                        "constitutional": [],
                        "statutes": [],
                        "rules_regulations": [],
                        "precedents": []
                    },
                    "arguments": {
                        "petitioner": "",
                        "respondent": ""
                    },
                    "court_analysis": [],
                    "findings": [],
                    "relief": {
                        "final_order": "",
                        "directions": [],
                        "costs": ""
                    },
                    "prediction": {
                        "likely_outcome": "",
                        "probabilities": {},
                        "drivers": []
                    },
                    "limitations": [],
                    "raw_text": judgment_text
                }
            
            return {
                "judgment": judgment_data,
                "language": response_language,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating judgment: {e}")
            raise
    
    def _determine_language(self, text: str, language: str) -> str:
        """Determine response language"""
        if language == "auto":
            # Simple heuristic: if text contains Devanagari, use Hindi
            devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
            total_chars = len([c for c in text if c.isalpha()])
            
            if total_chars > 0 and devanagari_chars / total_chars > 0.1:
                return "hi"
            else:
                return "en"
        
        return language
    
    def _get_qa_system_prompt(self, language: str) -> str:
        """Get system prompt for QA based on language"""
        if language == "hi":
            return """आप एक अनुभवी भारतीय कानूनी शोधकर्ता हैं। आपको दिए गए संदर्भ के आधार पर सटीक और व्यापक उत्तर प्रदान करना है।

निर्देश:
1. केवल दिए गए संदर्भ का उपयोग करें
2. [n] संदर्भों का उपयोग करके स्रोतों का उल्लेख करें
3. कानूनी प्रावधानों, मामलों और कानूनों का सटीक उल्लेख करें
4. हिंदी में उत्तर दें"""
        else:
            return """You are an experienced Indian legal researcher. Provide accurate and comprehensive answers based on the given context.

Instructions:
1. Use only the provided context
2. Use [n] citations to reference sources
3. Cite specific legal provisions, cases, and statutes accurately
4. Be precise and authoritative in your response"""
    
    def _get_summary_system_prompt(self, language: str) -> str:
        """Get system prompt for summarization based on language"""
        if language == "hi":
            return """आप एक अनुभवी भारतीय कानूनी विश्लेषक हैं। दिए गए दस्तावेजों का संरचित सारांश तैयार करें।

संरचना:
1. तथ्य (Facts)
2. मुद्दे (Issues)  
3. तर्क (Arguments)
4. निर्णय (Holding)
5. राहत (Relief)

हिंदी में सारांश प्रदान करें।"""
        else:
            return """You are an experienced Indian legal analyst. Provide a structured summary of the given documents.

Structure:
1. Facts
2. Issues
3. Arguments
4. Holding
5. Relief

Provide the summary in English."""
    
    def _get_judgment_system_prompt(self, language: str) -> str:
        """Get system prompt for judgment generation based on language"""
        if language == "hi":
            return """आप एक अनुभवी भारतीय न्यायाधीश हैं। दिए गए मामले के लिए एक संरचित निर्णय तैयार करें।

JSON स्कीमा:
{
  "metadata": {
    "case_title": "मामले का शीर्षक",
    "court": "न्यायालय",
    "date": "तारीख",
    "case_number": "मामला संख्या"
  },
  "framing": "मामले का फ्रेमिंग",
  "points_for_determination": ["निर्धारण के बिंदु"],
  "applicable_law": {
    "constitutional": ["संवैधानिक प्रावधान"],
    "statutes": ["कानून"],
    "rules_regulations": ["नियम"],
    "precedents": ["पूर्व निर्णय"]
  },
  "arguments": {
    "petitioner": "याचिकाकर्ता के तर्क",
    "respondent": "प्रतिवादी के तर्क"
  },
  "court_analysis": [
    {
      "issue": "मुद्दा",
      "analysis": "विश्लेषण",
      "citations": ["संदर्भ"]
    }
  ],
  "findings": ["निष्कर्ष"],
  "relief": {
    "final_order": "अंतिम आदेश",
    "directions": ["निर्देश"],
    "costs": "लागत"
  },
  "prediction": {
    "likely_outcome": "संभावित परिणाम",
    "probabilities": {},
    "drivers": ["कारक"]
  },
  "limitations": ["सीमाएं"]
}

हिंदी में निर्णय प्रदान करें।"""
        else:
            return """You are an experienced Indian judge. Generate a structured judgment for the given case.

JSON Schema:
{
  "metadata": {
    "case_title": "Case Title",
    "court": "Court",
    "date": "Date",
    "case_number": "Case Number"
  },
  "framing": "Case Framing",
  "points_for_determination": ["Points for Determination"],
  "applicable_law": {
    "constitutional": ["Constitutional Provisions"],
    "statutes": ["Statutes"],
    "rules_regulations": ["Rules & Regulations"],
    "precedents": ["Precedents"]
  },
  "arguments": {
    "petitioner": "Petitioner's Arguments",
    "respondent": "Respondent's Arguments"
  },
  "court_analysis": [
    {
      "issue": "Issue",
      "analysis": "Analysis",
      "citations": ["Citations"]
    }
  ],
  "findings": ["Findings"],
  "relief": {
    "final_order": "Final Order",
    "directions": ["Directions"],
    "costs": "Costs"
  },
  "prediction": {
    "likely_outcome": "Likely Outcome",
    "probabilities": {},
    "drivers": ["Drivers"]
  },
  "limitations": ["Limitations"]
}

Provide the judgment in English."""