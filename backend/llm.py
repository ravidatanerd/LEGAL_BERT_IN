"""
LLM integration for legal question answering and judgment generation
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
import asyncio

from utils.textnorm import is_devanagari_text
from hybrid_legal_ai import HybridLegalAI, create_hybrid_legal_ai
from smart_ai_fallback import get_ai_response_with_fallback, get_ai_tier_status

logger = logging.getLogger(__name__)

class LegalLLM:
    """Enhanced LLM interface with hybrid BERT+GPT capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None
        self.hybrid_ai: Optional[HybridLegalAI] = None
        self.use_hybrid = os.getenv("ENABLE_HYBRID_AI", "true").lower() == "true"
    
    async def initialize(self):
        """Initialize LLM client and hybrid AI system"""
        if self.api_key:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            logger.info("LLM client initialized")
        else:
            logger.warning("OpenAI API key not provided - using hybrid fallback mode")
        
        # Initialize hybrid AI system
        if self.use_hybrid:
            try:
                self.hybrid_ai = await create_hybrid_legal_ai()
                logger.info("Hybrid BERT+GPT system initialized")
            except Exception as e:
                logger.warning(f"Hybrid AI initialization failed, using basic mode: {e}")
                self.hybrid_ai = None
    
    async def generate_answer(
        self, 
        question: str, 
        sources: List[Dict[str, Any]], 
        language: str = "auto"
    ) -> Dict[str, Any]:
        """Generate grounded answer using hybrid BERT+GPT system"""
        try:
            # Use hybrid AI system if available
            if self.hybrid_ai:
                logger.info("Using hybrid BERT+GPT system for enhanced legal analysis")
                
                # Perform hybrid analysis and generation
                hybrid_result = await self.hybrid_ai.analyze_and_generate(
                    query=question,
                    sources=sources,
                    generation_type="answer",
                    language=language
                )
                
                # Format hybrid response
                response_text = self._format_hybrid_response(hybrid_result, sources)
                
                return {
                    "text": response_text,
                    "language_detected": hybrid_result.contextual_understanding.get("language", "en"),
                    "hybrid_analysis": {
                        "confidence_score": hybrid_result.confidence_score,
                        "hybrid_score": hybrid_result.hybrid_score,
                        "legal_reasoning": hybrid_result.legal_reasoning,
                        "contextual_understanding": {
                            "context_type": hybrid_result.contextual_understanding.get("context_type"),
                            "legal_concepts": hybrid_result.contextual_understanding.get("legal_concepts", []),
                            "complexity_score": hybrid_result.contextual_understanding.get("complexity_score", 0)
                        }
                    },
                    "enhanced_citations": hybrid_result.citations
                }
            
            # Use smart fallback system for rate limit handling
            else:
                logger.info("Using smart AI fallback system with rate limit handling")
                
                # Prepare context from sources
                context = self._prepare_context(sources)
                
                # Use smart fallback system
                fallback_response = await get_ai_response_with_fallback(question, context)
                
                # Add tier information to response
                tier_info = get_ai_tier_status()
                
                # Format response based on tier used
                if fallback_response.get("tier") in ["premium", "standard", "free"]:
                    response_text = fallback_response["answer"]
                    if sources:
                        response_text += "\n\n**Sources:**\n"
                        for i, source in enumerate(sources[:3], 1):
                            response_text += f"[{i}] {source.get('filename', 'Unknown')} (Score: {source.get('combined_score', 0):.2f})\n"
                else:
                    # Local or fallback tier
                    response_text = fallback_response["answer"]
                    if fallback_response.get("tier") == "rate_limited_fallback":
                        response_text += f"\n\n**Note**: Using {fallback_response.get('tier', 'fallback')} mode due to API rate limits. Premium ChatGPT will be available again shortly."
                
                return {
                    "text": response_text,
                    "language_detected": self._detect_language(question, language),
                    "ai_tier_used": fallback_response.get("tier", "unknown"),
                    "model_used": fallback_response.get("model_used", "unknown"),
                    "quality_level": fallback_response.get("quality_level", "basic"),
                    "rate_limit_info": tier_info.get("rate_limited_tiers", [])
                }
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return {
                "text": f"Error generating answer: {str(e)}",
                "language_detected": "en"
            }
    
    def _format_hybrid_response(self, hybrid_result: Any, sources: List[Dict[str, Any]]) -> str:
        """Format hybrid analysis result into readable response"""
        
        response_parts = []
        
        # Add main generated response
        response_parts.append(hybrid_result.generated_response)
        
        # Add legal reasoning section
        if hybrid_result.legal_reasoning:
            response_parts.append("\n\n**Legal Analysis:**")
            for i, reasoning in enumerate(hybrid_result.legal_reasoning, 1):
                response_parts.append(f"{i}. {reasoning}")
        
        # Add contextual insights
        context = hybrid_result.contextual_understanding
        if context.get("legal_concepts"):
            response_parts.append(f"\n\n**Legal Concepts Identified:** {', '.join(context['legal_concepts'][:5])}")
        
        # Add confidence and hybrid scoring
        response_parts.append(f"\n\n**Analysis Quality:**")
        response_parts.append(f"- Contextual Understanding: {hybrid_result.confidence_score:.2f}")
        response_parts.append(f"- Hybrid Model Score: {hybrid_result.hybrid_score:.2f}")
        response_parts.append(f"- Legal Complexity: {context.get('complexity_score', 0):.2f}")
        
        # Add enhanced citations
        if hybrid_result.citations:
            response_parts.append(f"\n\n**Sources:**")
            for citation in hybrid_result.citations[:3]:  # Top 3 sources
                response_parts.append(f"[{citation['index']}] {citation['filename']} (Relevance: {citation['relevance_score']:.2f})")
        
        return "\n".join(response_parts)
    
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
        """Generate structured legal judgment using hybrid system"""
        try:
            # Use hybrid AI for enhanced judgment generation
            if self.hybrid_ai:
                logger.info("Using hybrid BERT+GPT system for judgment generation")
                
                # Combine case facts and legal issues for analysis
                combined_input = f"Case Facts: {case_facts}\n\nLegal Issues: {'; '.join(legal_issues)}"
                
                # Perform hybrid analysis
                hybrid_result = await self.hybrid_ai.analyze_and_generate(
                    query=combined_input,
                    sources=relevant_sources,
                    generation_type="judgment",
                    language=language
                )
                
                # Create enhanced judgment structure
                judgment_data = self._create_enhanced_judgment_structure(
                    hybrid_result, case_facts, legal_issues, relevant_sources
                )
                
                return judgment_data
            
            # Fallback to basic LLM
            elif self.client:
                logger.info("Using basic LLM for judgment generation")
                detected_lang = self._detect_language(case_facts, language)
                context = self._prepare_context(relevant_sources)
                
                prompt = self._create_judgment_prompt(
                    case_facts, legal_issues, context, detected_lang
                )
                
                response = await self._call_llm(prompt, max_tokens=3000)
                
                try:
                    judgment_data = json.loads(response)
                    return judgment_data
                except json.JSONDecodeError:
                    return self._parse_judgment_fallback(response)
            
            else:
                return self._fallback_judgment()
            
        except Exception as e:
            logger.error(f"Failed to generate judgment: {e}")
            return self._fallback_judgment()
    
    def _create_enhanced_judgment_structure(
        self,
        hybrid_result: Any,
        case_facts: str,
        legal_issues: List[str],
        relevant_sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create enhanced judgment structure using hybrid analysis"""
        
        context = hybrid_result.contextual_understanding
        
        # Extract legal concepts and entities for judgment
        legal_concepts = context.get("legal_concepts", [])
        legal_entities = context.get("legal_entities", [])
        context_type = context.get("context_type", "general_legal")
        
        # Determine applicable law based on concepts
        applicable_law = self._extract_applicable_law_from_concepts(legal_concepts, legal_entities)
        
        # Create enhanced judgment structure
        judgment = {
            "metadata": {
                "case_type": self._determine_case_type(legal_concepts),
                "jurisdiction": "High Court",  # Default
                "date": "2024-01-01",
                "hybrid_analysis": {
                    "confidence_score": hybrid_result.confidence_score,
                    "hybrid_score": hybrid_result.hybrid_score,
                    "context_type": context_type,
                    "complexity_score": context.get("complexity_score", 0)
                }
            },
            "framing": hybrid_result.generated_response,
            "points_for_determination": legal_issues,
            "applicable_law": applicable_law,
            "arguments": {
                "petitioner": "Arguments based on contextual analysis",
                "respondent": "Counter-arguments derived from legal reasoning"
            },
            "court_analysis": [
                {
                    "issue": issue,
                    "analysis": f"Based on hybrid BERT+GPT analysis: {reasoning}",
                    "citations": [source.get("filename", "Unknown") for source in relevant_sources[:2]]
                }
                for issue, reasoning in zip(legal_issues, hybrid_result.legal_reasoning)
            ],
            "findings": [
                f"Hybrid contextual analysis confidence: {hybrid_result.confidence_score:.2f}",
                f"Legal complexity assessment: {context.get('complexity_score', 0):.2f}",
                f"Identified {len(legal_concepts)} relevant legal concepts"
            ],
            "relief": {
                "final_order": "Order based on hybrid legal analysis",
                "directions": ["Direction derived from contextual understanding"],
                "costs": "Costs as per legal complexity assessment"
            },
            "prediction": {
                "likely_outcome": "Outcome predicted using hybrid model scoring",
                "probabilities": {
                    "favor_petitioner": 0.4 + (hybrid_result.hybrid_score * 0.2),
                    "favor_respondent": 0.4 + ((1 - hybrid_result.hybrid_score) * 0.2),
                    "partial_relief": 0.2
                },
                "drivers": [
                    f"Hybrid model confidence: {hybrid_result.confidence_score:.2f}",
                    f"Contextual understanding depth",
                    f"Legal concept analysis: {len(legal_concepts)} concepts"
                ]
            },
            "limitations": [
                "Analysis based on hybrid BERT+GPT model",
                "Requires verification by qualified legal professionals",
                "Contextual understanding may vary with case complexity"
            ],
            "hybrid_insights": {
                "model_strategy": hybrid_result.contextual_understanding.get("strategy", "hybrid"),
                "legal_reasoning_steps": hybrid_result.legal_reasoning,
                "enhanced_citations": hybrid_result.citations
            }
        }
        
        return judgment
    
    def _extract_applicable_law_from_concepts(self, legal_concepts: List[str], legal_entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract applicable law based on identified concepts and entities"""
        
        applicable_law = {
            "constitutional": [],
            "statutes": [],
            "rules_regulations": [],
            "precedents": []
        }
        
        # Map concepts to law categories
        for concept in legal_concepts:
            if "criminal_law" in concept:
                applicable_law["statutes"].append("Indian Penal Code, 1860")
                applicable_law["statutes"].append("Code of Criminal Procedure, 1973")
            elif "constitutional_law" in concept:
                applicable_law["constitutional"].append("Constitution of India")
            elif "procedural_law" in concept:
                applicable_law["statutes"].append("Code of Criminal Procedure, 1973")
                applicable_law["statutes"].append("Indian Evidence Act, 1872")
            elif "civil_law" in concept:
                applicable_law["statutes"].append("Indian Contract Act, 1872")
                applicable_law["statutes"].append("Transfer of Property Act, 1882")
        
        # Add from legal entities
        for entity in legal_entities:
            if entity.get("type") == "act_reference":
                act_name = entity.get("value", "")
                if act_name not in applicable_law["statutes"]:
                    applicable_law["statutes"].append(act_name)
        
        # Remove duplicates
        for category in applicable_law:
            applicable_law[category] = list(set(applicable_law[category]))
        
        return applicable_law
    
    def _determine_case_type(self, legal_concepts: List[str]) -> str:
        """Determine case type based on legal concepts"""
        
        if any("criminal_law" in concept for concept in legal_concepts):
            return "criminal"
        elif any("constitutional_law" in concept for concept in legal_concepts):
            return "constitutional"
        elif any("civil_law" in concept for concept in legal_concepts):
            return "civil"
        else:
            return "miscellaneous"
    
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
        """Make API call to LLM with security measures"""
        try:
            # Validate prompt length
            if len(prompt) > 50000:
                prompt = prompt[:50000] + "\n[Content truncated for safety]"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": min(max_tokens, 4000),  # Cap max tokens
                "temperature": 0.1
            }
            
            # Make request with timeout
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=120.0
            )
            
            if response.status_code == 401:
                raise Exception("Invalid API key - please check your credentials")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded - please try again later")
            elif response.status_code != 200:
                # Don't log full response for security
                raise Exception(f"LLM API error: {response.status_code}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Validate response content
            if len(content) > 100000:  # Sanity check
                logger.warning("Unusually long LLM response received")
                content = content[:100000] + "\n[Response truncated for safety]"
            
            return content
            
        except Exception as e:
            # Log error without exposing sensitive information
            error_msg = str(e)
            if "sk-" in error_msg:
                error_msg = re.sub(r'sk-[a-zA-Z0-9]+', 'sk-****', error_msg)
            
            logger.error(f"LLM API call failed: {error_msg}")
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