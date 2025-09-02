"""
LLM integration for legal question answering and judgment generation
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
import asyncio

from utils.textnorm import is_devanagari_text

logger = logging.getLogger(__name__)

class LegalLLM:
    """LLM interface for legal AI tasks"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None
    
    async def initialize(self):
        """Initialize LLM client"""
        if not self.api_key:
            logger.warning("OpenAI API key not provided - LLM features will be limited")
            return
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        logger.info("LLM client initialized")
    
    async def generate_answer(
        self, 
        question: str, 
        sources: List[Dict[str, Any]], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate grounded answer with bracket citations"""
        try:
            if not self.client:
                return {
                    "text": "LLM not available. Please configure OpenAI API key.",
                    "language_detected": "en"
                }
            
            # Detect language
            detected_lang = self._detect_language(question, language)
            
            # Prepare context from sources
            context = self._prepare_context(sources)
            
            # Create prompt
            prompt = self._create_qa_prompt(question, context, detected_lang)
            
            # Generate response
            response = await self._call_llm(prompt)
            
            return {
                "text": response,
                "language_detected": detected_lang
            }
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return {
                "text": f"Error generating answer: {str(e)}",
                "language_detected": "en"
            }
    
    async def generate_summary(
        self, 
        content: str, 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate structured legal document summary"""
        try:
            if not self.client:
                return self._fallback_summary()
            
            detected_lang = self._detect_language(content, language)
            prompt = self._create_summary_prompt(content, detected_lang)
            
            response = await self._call_llm(prompt)
            
            # Parse structured response
            try:
                summary_data = json.loads(response)
                summary_data["language_detected"] = detected_lang
                return summary_data
            except json.JSONDecodeError:
                # Fallback to basic parsing
                return self._parse_summary_fallback(response, detected_lang)
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return self._fallback_summary()
    
    async def generate_judgment(
        self,
        case_facts: str,
        legal_issues: List[str],
        relevant_sources: List[Dict[str, Any]],
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate structured legal judgment"""
        try:
            if not self.client:
                return self._fallback_judgment()
            
            detected_lang = self._detect_language(case_facts, language)
            context = self._prepare_context(relevant_sources)
            
            prompt = self._create_judgment_prompt(
                case_facts, legal_issues, context, detected_lang
            )
            
            response = await self._call_llm(prompt, max_tokens=3000)
            
            # Parse structured response
            try:
                judgment_data = json.loads(response)
                return judgment_data
            except json.JSONDecodeError:
                return self._parse_judgment_fallback(response)
            
        except Exception as e:
            logger.error(f"Failed to generate judgment: {e}")
            return self._fallback_judgment()
    
    def _detect_language(self, text: str, language: str) -> str:
        """Detect or validate language setting"""
        if language in ["en", "hi"]:
            return language
        
        # Auto-detect based on script
        if is_devanagari_text(text):
            return "hi"
        else:
            return "en"
    
    def _prepare_context(self, sources: List[Dict[str, Any]]) -> str:
        """Prepare context string from source chunks"""
        if not sources:
            return ""
        
        context_parts = []
        for i, source in enumerate(sources, 1):
            filename = source.get("filename", "Unknown")
            text = source.get("text", "")
            
            context_parts.append(f"[{i}] {filename}: {text[:500]}...")
        
        return "\n\n".join(context_parts)
    
    def _create_qa_prompt(self, question: str, context: str, language: str) -> str:
        """Create prompt for question answering"""
        if language == "hi":
            return f"""आप एक भारतीय कानूनी विशेषज्ञ हैं। दिए गए संदर्भ के आधार पर प्रश्न का उत्तर दें।

संदर्भ:
{context}

प्रश्न: {question}

निर्देश:
- केवल दिए गए संदर्भ का उपयोग करें
- उत्तर में [1], [2] आदि के रूप में उद्धरण शामिल करें
- सटीक और संक्षिप्त उत्तर दें
- यदि जानकारी उपलब्ध नहीं है तो स्पष्ट रूप से बताएं

उत्तर:"""
        else:
            return f"""You are an Indian legal expert. Answer the question based on the provided context.

Context:
{context}

Question: {question}

Instructions:
- Use only the provided context
- Include citations as [1], [2], etc. in your answer
- Provide accurate and concise responses
- If information is not available, clearly state so

Answer:"""
    
    def _create_summary_prompt(self, content: str, language: str) -> str:
        """Create prompt for document summarization"""
        if language == "hi":
            prompt = f"""निम्नलिखित कानूनी दस्तावेज़ का संरचित सारांश बनाएं:

{content[:2000]}

कृपया निम्नलिखित JSON प्रारूप में उत्तर दें:
{{
    "facts": "मुख्य तथ्य",
    "issues": ["कानूनी मुद्दे की सूची"],
    "arguments": "पक्षों के तर्क",
    "holding": "न्यायालय का निर्णय",
    "relief": "राहत/आदेश"
}}"""
        else:
            prompt = f"""Provide a structured summary of the following legal document:

{content[:2000]}

Please respond in the following JSON format:
{{
    "facts": "Key facts of the case",
    "issues": ["List of legal issues"],
    "arguments": "Arguments presented by parties",
    "holding": "Court's decision/holding",
    "relief": "Relief granted/orders issued"
}}"""
        
        return prompt
    
    def _create_judgment_prompt(
        self,
        case_facts: str,
        legal_issues: List[str],
        context: str,
        language: str
    ) -> str:
        """Create prompt for judgment generation"""
        issues_str = "\n".join(f"- {issue}" for issue in legal_issues)
        
        if language == "hi":
            prompt = f"""आप एक भारतीय न्यायाधीश हैं। निम्नलिखित मामले के लिए संरचित निर्णय तैयार करें:

मामले के तथ्य:
{case_facts}

कानूनी मुद्दे:
{issues_str}

संबंधित कानूनी संदर्भ:
{context}

कृपया निम्नलिखित JSON संरचना में निर्णय प्रदान करें:"""
        else:
            prompt = f"""You are an Indian judge. Draft a structured judgment for the following case:

Case Facts:
{case_facts}

Legal Issues:
{issues_str}

Relevant Legal Context:
{context}

Please provide the judgment in the following JSON structure:"""
        
        # Add JSON schema
        schema = """{
    "metadata": {
        "case_type": "civil/criminal/constitutional",
        "jurisdiction": "Supreme Court/High Court/District Court",
        "date": "YYYY-MM-DD"
    },
    "framing": "Brief framing of the case and jurisdiction",
    "points_for_determination": ["List of legal points to be determined"],
    "applicable_law": {
        "constitutional": ["Relevant constitutional provisions"],
        "statutes": ["Applicable statutes"],
        "rules_regulations": ["Relevant rules and regulations"],
        "precedents": ["Key precedent cases"]
    },
    "arguments": {
        "petitioner": "Petitioner's main arguments",
        "respondent": "Respondent's main arguments"
    },
    "court_analysis": [
        {
            "issue": "Legal issue being analyzed",
            "analysis": "Court's reasoning",
            "citations": ["Relevant case law and statutes"]
        }
    ],
    "findings": ["Court's key findings"],
    "relief": {
        "final_order": "Final order of the court",
        "directions": ["Specific directions issued"],
        "costs": "Cost orders if any"
    },
    "prediction": {
        "likely_outcome": "Most probable outcome",
        "probabilities": {
            "favor_petitioner": 0.0,
            "favor_respondent": 0.0,
            "partial_relief": 0.0
        },
        "drivers": ["Key factors influencing the outcome"]
    },
    "limitations": ["Limitations of this analysis"]
}"""
        
        return prompt + "\n\n" + schema
    
    async def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make API call to LLM"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _fallback_summary(self) -> Dict[str, Any]:
        """Fallback summary when LLM is unavailable"""
        return {
            "facts": "LLM not available for summarization",
            "issues": ["Unable to extract issues"],
            "arguments": "Arguments analysis unavailable",
            "holding": "Holding analysis unavailable", 
            "relief": "Relief details unavailable",
            "language_detected": "en"
        }
    
    def _fallback_judgment(self) -> Dict[str, Any]:
        """Fallback judgment when LLM is unavailable"""
        return {
            "metadata": {"case_type": "unknown", "jurisdiction": "unknown", "date": ""},
            "framing": "Judgment generation unavailable - LLM not configured",
            "points_for_determination": ["Unable to determine without LLM"],
            "applicable_law": {"constitutional": [], "statutes": [], "rules_regulations": [], "precedents": []},
            "arguments": {"petitioner": "Unavailable", "respondent": "Unavailable"},
            "court_analysis": [],
            "findings": ["LLM required for analysis"],
            "relief": {"final_order": "Unable to generate", "directions": [], "costs": ""},
            "prediction": {"likely_outcome": "Unknown", "probabilities": {}, "drivers": []},
            "limitations": ["LLM not available for judgment generation"]
        }
    
    def _parse_summary_fallback(self, response: str, language: str) -> Dict[str, Any]:
        """Parse summary response when JSON parsing fails"""
        return {
            "facts": response[:200] + "..." if len(response) > 200 else response,
            "issues": ["Unable to parse structured response"],
            "arguments": "See full response",
            "holding": "Unable to extract",
            "relief": "Unable to extract",
            "language_detected": language
        }
    
    def _parse_judgment_fallback(self, response: str) -> Dict[str, Any]:
        """Parse judgment response when JSON parsing fails"""
        fallback = self._fallback_judgment()
        fallback["framing"] = response[:300] + "..." if len(response) > 300 else response
        return fallback