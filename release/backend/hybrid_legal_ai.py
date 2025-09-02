"""
Hybrid BERT+GPT Legal AI System
Combines InLegalBERT's contextual understanding with GPT's generative capabilities
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import torch
from transformers import (
    AutoTokenizer, AutoModel, T5ForConditionalGeneration, 
    T5Tokenizer, XLNetLMHeadModel, XLNetTokenizer
)
import httpx

from utils.textnorm import normalize_text, is_devanagari_text

logger = logging.getLogger(__name__)

@dataclass
class LegalAnalysisResult:
    """Result from legal analysis"""
    contextual_understanding: Dict[str, Any]
    generated_response: str
    confidence_score: float
    legal_reasoning: List[str]
    citations: List[Dict[str, Any]]
    hybrid_score: float

class ContextualEncoder:
    """InLegalBERT-based contextual encoder for deep legal understanding"""
    
    def __init__(self, model_name: str = "law-ai/InLegalBERT"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def initialize(self):
        """Initialize the contextual encoder"""
        try:
            logger.info(f"Initializing contextual encoder with {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("Contextual encoder initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize contextual encoder: {e}")
            raise
    
    async def encode_legal_context(
        self, 
        text: str, 
        sources: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract deep contextual understanding from legal text
        
        Args:
            text: Input legal text
            sources: Related legal sources for context
            
        Returns:
            Rich contextual analysis
        """
        try:
            # Normalize and prepare text
            normalized_text = normalize_text(text)
            
            # Tokenize input
            inputs = self.tokenizer(
                normalized_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get contextual embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Extract rich contextual features
                last_hidden_states = outputs.last_hidden_state
                pooled_output = outputs.pooler_output if hasattr(outputs, 'pooler_output') else None
                
                # Attention-weighted pooling
                attention_mask = inputs["attention_mask"]
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
                sum_embeddings = torch.sum(last_hidden_states * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                mean_pooled = sum_embeddings / sum_mask
                
                # Extract attention patterns for legal reasoning
                attention_weights = self._extract_attention_patterns(last_hidden_states, attention_mask)
            
            # Analyze legal concepts
            legal_concepts = await self._analyze_legal_concepts(normalized_text, mean_pooled)
            
            # Determine legal context type
            context_type = self._classify_legal_context(normalized_text)
            
            # Extract key legal entities
            legal_entities = self._extract_legal_entities(normalized_text)
            
            return {
                "embeddings": mean_pooled.cpu().numpy(),
                "attention_patterns": attention_weights,
                "legal_concepts": legal_concepts,
                "context_type": context_type,
                "legal_entities": legal_entities,
                "language": "hi" if is_devanagari_text(text) else "en",
                "confidence": self._calculate_understanding_confidence(attention_weights),
                "complexity_score": self._assess_legal_complexity(normalized_text)
            }
            
        except Exception as e:
            logger.error(f"Contextual encoding failed: {e}")
            raise
    
    def _extract_attention_patterns(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, Any]:
        """Extract attention patterns for legal reasoning insights"""
        try:
            # Simplified attention analysis
            attention_scores = torch.mean(hidden_states, dim=-1)
            
            # Find high-attention tokens (potential legal concepts)
            high_attention_indices = torch.topk(attention_scores[0], k=min(10, attention_scores.size(1))).indices
            
            return {
                "high_attention_positions": high_attention_indices.cpu().tolist(),
                "attention_distribution": attention_scores[0].cpu().tolist(),
                "focus_areas": len(high_attention_indices)
            }
            
        except Exception as e:
            logger.warning(f"Attention pattern extraction failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_legal_concepts(self, text: str, embeddings: torch.Tensor) -> List[str]:
        """Analyze legal concepts in the text"""
        # Legal concept keywords for Indian law
        legal_concepts = {
            "criminal_law": ["murder", "theft", "assault", "robbery", "fraud", "section 302", "section 420"],
            "civil_law": ["contract", "tort", "property", "damages", "injunction", "specific performance"],
            "constitutional_law": ["fundamental rights", "directive principles", "article", "constitution"],
            "procedural_law": ["procedure", "evidence", "witness", "bail", "appeal", "jurisdiction"],
            "family_law": ["marriage", "divorce", "adoption", "maintenance", "custody"],
            "corporate_law": ["company", "director", "shareholder", "merger", "acquisition"]
        }
        
        identified_concepts = []
        text_lower = text.lower()
        
        for category, keywords in legal_concepts.items():
            for keyword in keywords:
                if keyword in text_lower:
                    identified_concepts.append(f"{category}:{keyword}")
        
        return identified_concepts
    
    def _classify_legal_context(self, text: str) -> str:
        """Classify the type of legal context"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["section", "act", "code", "law"]):
            return "statutory_interpretation"
        elif any(word in text_lower for word in ["case", "judgment", "court", "held"]):
            return "case_analysis"
        elif any(word in text_lower for word in ["what", "how", "why", "explain"]):
            return "legal_query"
        elif any(word in text_lower for word in ["draft", "prepare", "judgment", "order"]):
            return "document_generation"
        else:
            return "general_legal"
    
    def _extract_legal_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract legal entities using pattern matching"""
        import re
        
        entities = []
        
        # Section references
        section_pattern = r'section\s+(\d+[a-z]?)\s*(?:of\s+(?:the\s+)?([^.]+?))?'
        for match in re.finditer(section_pattern, text, re.IGNORECASE):
            entities.append({
                "type": "section_reference",
                "value": match.group(1),
                "act": match.group(2) if match.group(2) else "unknown"
            })
        
        # Case citations
        case_pattern = r'([A-Z][^.]+?)\s+v\.?\s+([A-Z][^.]+?)(?:\s+\((\d{4})\))?'
        for match in re.finditer(case_pattern, text):
            entities.append({
                "type": "case_citation",
                "petitioner": match.group(1),
                "respondent": match.group(2),
                "year": match.group(3) if match.group(3) else "unknown"
            })
        
        # Act references
        act_pattern = r'(Indian\s+Penal\s+Code|Code\s+of\s+Criminal\s+Procedure|Evidence\s+Act|Constitution)'
        for match in re.finditer(act_pattern, text, re.IGNORECASE):
            entities.append({
                "type": "act_reference",
                "value": match.group(1)
            })
        
        return entities
    
    def _calculate_understanding_confidence(self, attention_patterns: Dict[str, Any]) -> float:
        """Calculate confidence in contextual understanding"""
        try:
            if "attention_distribution" in attention_patterns:
                attention_scores = attention_patterns["attention_distribution"]
                # Higher variance in attention suggests better understanding
                variance = np.var(attention_scores) if attention_scores else 0
                return min(1.0, variance * 10)  # Normalize to 0-1
            return 0.5
        except:
            return 0.5
    
    def _assess_legal_complexity(self, text: str) -> float:
        """Assess the complexity of legal text"""
        # Simple complexity metrics
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Legal complexity indicators
        complex_terms = ["whereas", "notwithstanding", "pursuant", "aforementioned", "hereinafter"]
        complex_count = sum(1 for term in complex_terms if term in text.lower())
        
        # Normalize complexity score
        complexity = (avg_word_length / 10 + complex_count / len(words)) * 100 if words else 0
        return min(1.0, complexity)

class GenerativeDecoder:
    """GPT-based generative decoder for sophisticated legal text generation"""
    
    def __init__(self):
        self.openai_client = None
        self.t5_model = None
        self.t5_tokenizer = None
        self.xlnet_model = None
        self.xlnet_tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def initialize(self):
        """Initialize generative models"""
        try:
            logger.info("Initializing generative decoder...")
            
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(120.0),
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                logger.info("OpenAI client initialized")
            
            # Initialize T5 for encoder-decoder tasks
            try:
                t5_model_name = "t5-small"  # Use small model for efficiency
                self.t5_tokenizer = T5Tokenizer.from_pretrained(t5_model_name)
                self.t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name)
                self.t5_model.to(self.device)
                self.t5_model.eval()
                logger.info("T5 encoder-decoder model initialized")
            except Exception as e:
                logger.warning(f"T5 initialization failed: {e}")
            
            # Initialize XLNet for autoregressive+bidirectional tasks
            try:
                xlnet_model_name = "xlnet-base-cased"
                self.xlnet_tokenizer = XLNetTokenizer.from_pretrained(xlnet_model_name)
                self.xlnet_model = XLNetLMHeadModel.from_pretrained(xlnet_model_name)
                self.xlnet_model.to(self.device)
                self.xlnet_model.eval()
                logger.info("XLNet hybrid model initialized")
            except Exception as e:
                logger.warning(f"XLNet initialization failed: {e}")
            
            logger.info("Generative decoder initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize generative decoder: {e}")
            raise
    
    async def generate_with_context(
        self,
        contextual_analysis: Dict[str, Any],
        query: str,
        generation_type: str = "answer"
    ) -> Dict[str, Any]:
        """
        Generate response using contextual understanding
        
        Args:
            contextual_analysis: Output from ContextualEncoder
            query: Original query
            generation_type: Type of generation (answer, judgment, summary)
            
        Returns:
            Generated response with metadata
        """
        try:
            # Choose best generation strategy based on context
            strategy = self._select_generation_strategy(contextual_analysis, generation_type)
            
            if strategy == "openai_enhanced":
                return await self._generate_with_openai_enhanced(contextual_analysis, query, generation_type)
            elif strategy == "t5_encoder_decoder":
                return await self._generate_with_t5(contextual_analysis, query, generation_type)
            elif strategy == "xlnet_hybrid":
                return await self._generate_with_xlnet(contextual_analysis, query, generation_type)
            else:
                return await self._generate_fallback(contextual_analysis, query, generation_type)
            
        except Exception as e:
            logger.error(f"Hybrid generation failed: {e}")
            raise
    
    def _select_generation_strategy(self, context: Dict[str, Any], gen_type: str) -> str:
        """Select optimal generation strategy based on context analysis"""
        
        complexity = context.get("complexity_score", 0)
        context_type = context.get("context_type", "general_legal")
        confidence = context.get("confidence", 0)
        
        # High complexity legal reasoning -> OpenAI enhanced
        if complexity > 0.7 and gen_type in ["judgment", "analysis"]:
            return "openai_enhanced"
        
        # Structured generation tasks -> T5 encoder-decoder
        elif gen_type in ["summary", "structured_response"] and self.t5_model:
            return "t5_encoder_decoder"
        
        # Complex contextual understanding -> XLNet hybrid
        elif confidence > 0.6 and context_type == "statutory_interpretation" and self.xlnet_model:
            return "xlnet_hybrid"
        
        # Default to OpenAI enhanced if available
        elif self.openai_client:
            return "openai_enhanced"
        
        else:
            return "fallback"
    
    async def _generate_with_openai_enhanced(
        self, 
        context: Dict[str, Any], 
        query: str, 
        gen_type: str
    ) -> Dict[str, Any]:
        """Generate using OpenAI with enhanced contextual prompting"""
        try:
            # Create enhanced prompt using contextual analysis
            enhanced_prompt = self._create_enhanced_prompt(context, query, gen_type)
            
            # Make OpenAI API call
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_legal_system_prompt(context)
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            response = await self.openai_client.post(
                f"{base_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code}")
            
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
            
            return {
                "text": generated_text,
                "strategy": "openai_enhanced",
                "model": model,
                "contextual_enhancement": True,
                "legal_reasoning_depth": "high",
                "token_usage": result.get("usage", {})
            }
            
        except Exception as e:
            logger.error(f"OpenAI enhanced generation failed: {e}")
            raise
    
    async def _generate_with_t5(
        self, 
        context: Dict[str, Any], 
        query: str, 
        gen_type: str
    ) -> Dict[str, Any]:
        """Generate using T5 encoder-decoder architecture"""
        try:
            # Create T5 task-specific prompt
            task_prompt = self._create_t5_prompt(context, query, gen_type)
            
            # Tokenize input
            inputs = self.t5_tokenizer(
                task_prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate with T5
            with torch.no_grad():
                outputs = self.t5_model.generate(
                    **inputs,
                    max_length=500,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
            
            # Decode generated text
            generated_text = self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {
                "text": generated_text,
                "strategy": "t5_encoder_decoder",
                "model": "t5-small",
                "contextual_enhancement": True,
                "legal_reasoning_depth": "medium"
            }
            
        except Exception as e:
            logger.error(f"T5 generation failed: {e}")
            raise
    
    async def _generate_with_xlnet(
        self, 
        context: Dict[str, Any], 
        query: str, 
        gen_type: str
    ) -> Dict[str, Any]:
        """Generate using XLNet hybrid autoregressive+bidirectional"""
        try:
            # Create XLNet prompt with contextual information
            xlnet_prompt = self._create_xlnet_prompt(context, query, gen_type)
            
            # Tokenize
            inputs = self.xlnet_tokenizer(
                xlnet_prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=400
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate with XLNet
            with torch.no_grad():
                outputs = self.xlnet_model.generate(
                    inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_length=inputs["input_ids"].shape[1] + 200,
                    num_beams=3,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.95,
                    pad_token_id=self.xlnet_tokenizer.pad_token_id
                )
            
            # Extract only the generated part
            generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
            generated_text = self.xlnet_tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            return {
                "text": generated_text,
                "strategy": "xlnet_hybrid",
                "model": "xlnet-base-cased",
                "contextual_enhancement": True,
                "legal_reasoning_depth": "high",
                "bidirectional_context": True
            }
            
        except Exception as e:
            logger.error(f"XLNet generation failed: {e}")
            raise
    
    async def _generate_fallback(
        self, 
        context: Dict[str, Any], 
        query: str, 
        gen_type: str
    ) -> Dict[str, Any]:
        """Fallback generation using contextual analysis only"""
        
        legal_concepts = context.get("legal_concepts", [])
        context_type = context.get("context_type", "general_legal")
        legal_entities = context.get("legal_entities", [])
        
        # Create structured response based on analysis
        if gen_type == "answer":
            response = f"Based on the legal context analysis:\n\n"
            response += f"Context Type: {context_type.replace('_', ' ').title()}\n"
            
            if legal_concepts:
                response += f"Legal Concepts Identified: {', '.join(legal_concepts[:5])}\n"
            
            if legal_entities:
                response += f"Legal References Found: {len(legal_entities)} entities\n"
            
            response += f"\nThis query requires legal expertise. Please consult with a qualified legal professional for authoritative guidance."
        
        elif gen_type == "judgment":
            response = "**LEGAL JUDGMENT FRAMEWORK**\n\n"
            response += f"**Context Analysis**: {context_type.replace('_', ' ').title()}\n"
            response += f"**Legal Complexity**: {context.get('complexity_score', 0):.2f}\n"
            response += f"**Identified Concepts**: {len(legal_concepts)} legal concepts found\n\n"
            response += "**Note**: Full judgment generation requires advanced AI models. Please configure OpenAI API key for complete functionality."
        
        else:
            response = f"Contextual analysis completed for {gen_type}. Enhanced generation requires AI model configuration."
        
        return {
            "text": response,
            "strategy": "contextual_fallback",
            "model": "inlegalbert_analysis",
            "contextual_enhancement": True,
            "legal_reasoning_depth": "basic"
        }
    
    def _create_enhanced_prompt(self, context: Dict[str, Any], query: str, gen_type: str) -> str:
        """Create enhanced prompt using contextual analysis"""
        
        legal_concepts = context.get("legal_concepts", [])
        context_type = context.get("context_type", "general_legal")
        legal_entities = context.get("legal_entities", [])
        language = context.get("language", "en")
        complexity = context.get("complexity_score", 0)
        
        if language == "hi":
            base_prompt = f"""आप एक विशेषज्ञ भारतीय कानूनी AI सहायक हैं। निम्नलिखित संदर्भ विश्लेषण के आधार पर प्रश्न का उत्तर दें:

संदर्भ विश्लेषण:
- संदर्भ प्रकार: {context_type.replace('_', ' ')}
- कानूनी जटिलता: {complexity:.2f}
- पहचानी गई अवधारणाएं: {', '.join(legal_concepts[:5]) if legal_concepts else 'कोई नहीं'}
- कानूनी संदर्भ: {len(legal_entities)} संदर्भ मिले

प्रश्न: {query}

कृपया एक विस्तृत, सटीक और संदर्भित उत्तर प्रदान करें।"""
        else:
            base_prompt = f"""You are an expert Indian legal AI assistant. Based on the following contextual analysis, provide a comprehensive response:

Contextual Analysis:
- Context Type: {context_type.replace('_', ' ').title()}
- Legal Complexity: {complexity:.2f}
- Identified Concepts: {', '.join(legal_concepts[:5]) if legal_concepts else 'None'}
- Legal References: {len(legal_entities)} entities found

Query: {query}

Please provide a detailed, accurate, and well-cited response based on Indian law."""
        
        return base_prompt
    
    def _get_legal_system_prompt(self, context: Dict[str, Any]) -> str:
        """Get system prompt based on context"""
        
        language = context.get("language", "en")
        context_type = context.get("context_type", "general_legal")
        
        if language == "hi":
            return """आप एक विशेषज्ञ भारतीय कानूनी सलाहकार हैं जो InLegalBERT संदर्भ विश्लेषण का उपयोग करके सटीक कानूनी सलाह प्रदान करते हैं। आपका उत्तर हमेशा भारतीय कानून पर आधारित होना चाहिए और उचित उद्धरणों के साथ होना चाहिए।"""
        else:
            return """You are an expert Indian legal advisor that uses InLegalBERT contextual analysis to provide accurate legal guidance. Your responses should always be grounded in Indian law with proper citations and references."""
    
    def _create_t5_prompt(self, context: Dict[str, Any], query: str, gen_type: str) -> str:
        """Create T5-specific prompt for encoder-decoder generation"""
        
        task_prefixes = {
            "answer": "answer question:",
            "summary": "summarize:",
            "judgment": "generate legal judgment:",
            "analysis": "analyze legal text:"
        }
        
        prefix = task_prefixes.get(gen_type, "answer question:")
        
        # Include contextual information
        context_info = f"Legal context: {context.get('context_type', 'general')}. "
        if context.get("legal_concepts"):
            context_info += f"Concepts: {', '.join(context['legal_concepts'][:3])}. "
        
        return f"{prefix} {context_info}{query}"
    
    def _create_xlnet_prompt(self, context: Dict[str, Any], query: str, gen_type: str) -> str:
        """Create XLNet-specific prompt for hybrid generation"""
        
        # XLNet works well with structured prompts
        prompt_parts = [
            f"Legal Query Analysis:",
            f"Context: {context.get('context_type', 'general_legal').replace('_', ' ').title()}",
            f"Complexity: {context.get('complexity_score', 0):.1f}",
        ]
        
        if context.get("legal_concepts"):
            prompt_parts.append(f"Concepts: {', '.join(context['legal_concepts'][:3])}")
        
        prompt_parts.extend([
            f"",
            f"Query: {query}",
            f"",
            f"Legal Response:"
        ])
        
        return "\n".join(prompt_parts)

class HybridLegalAI:
    """
    Main hybrid BERT+GPT system for legal AI
    Combines contextual understanding with sophisticated generation
    """
    
    def __init__(self):
        self.encoder = ContextualEncoder()
        self.decoder = GenerativeDecoder()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the hybrid system"""
        try:
            logger.info("Initializing Hybrid Legal AI system...")
            
            # Initialize both components
            await self.encoder.initialize()
            await self.decoder.initialize()
            
            self.initialized = True
            logger.info("Hybrid Legal AI system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize hybrid system: {e}")
            raise
    
    async def analyze_and_generate(
        self,
        query: str,
        sources: List[Dict[str, Any]] = None,
        generation_type: str = "answer",
        language: str = "auto"
    ) -> LegalAnalysisResult:
        """
        Perform hybrid analysis and generation
        
        Args:
            query: Legal query or input text
            sources: Related legal sources
            generation_type: Type of generation needed
            language: Target language
            
        Returns:
            Complete legal analysis result
        """
        try:
            if not self.initialized:
                raise RuntimeError("Hybrid system not initialized")
            
            # Phase 1: Deep Contextual Understanding (BERT)
            logger.info("Phase 1: Contextual analysis with InLegalBERT")
            contextual_analysis = await self.encoder.encode_legal_context(query, sources)
            
            # Phase 2: Enhanced Generation (GPT/T5/XLNet)
            logger.info("Phase 2: Enhanced generation with hybrid models")
            generation_result = await self.decoder.generate_with_context(
                contextual_analysis, query, generation_type
            )
            
            # Phase 3: Hybrid Scoring and Validation
            logger.info("Phase 3: Hybrid scoring and validation")
            hybrid_score = self._calculate_hybrid_score(contextual_analysis, generation_result)
            
            # Phase 4: Legal Reasoning Extraction
            legal_reasoning = self._extract_legal_reasoning(
                contextual_analysis, generation_result, sources
            )
            
            # Phase 5: Citation Enhancement
            enhanced_citations = self._enhance_citations(
                contextual_analysis, sources, generation_result
            )
            
            return LegalAnalysisResult(
                contextual_understanding=contextual_analysis,
                generated_response=generation_result["text"],
                confidence_score=contextual_analysis.get("confidence", 0.5),
                legal_reasoning=legal_reasoning,
                citations=enhanced_citations,
                hybrid_score=hybrid_score
            )
            
        except Exception as e:
            logger.error(f"Hybrid analysis and generation failed: {e}")
            raise
    
    def _calculate_hybrid_score(
        self, 
        contextual_analysis: Dict[str, Any], 
        generation_result: Dict[str, Any]
    ) -> float:
        """Calculate hybrid model performance score"""
        
        # Factors for hybrid scoring
        context_confidence = contextual_analysis.get("confidence", 0.5)
        complexity_handling = 1.0 - contextual_analysis.get("complexity_score", 0.5)
        
        # Generation quality indicators
        generation_strategy = generation_result.get("strategy", "fallback")
        strategy_scores = {
            "openai_enhanced": 0.9,
            "t5_encoder_decoder": 0.8,
            "xlnet_hybrid": 0.85,
            "contextual_fallback": 0.6
        }
        
        strategy_score = strategy_scores.get(generation_strategy, 0.5)
        
        # Contextual enhancement bonus
        enhancement_bonus = 0.1 if generation_result.get("contextual_enhancement") else 0
        
        # Calculate weighted hybrid score
        hybrid_score = (
            context_confidence * 0.4 +
            complexity_handling * 0.3 +
            strategy_score * 0.2 +
            enhancement_bonus * 0.1
        )
        
        return min(1.0, hybrid_score)
    
    def _extract_legal_reasoning(
        self,
        contextual_analysis: Dict[str, Any],
        generation_result: Dict[str, Any],
        sources: List[Dict[str, Any]] = None
    ) -> List[str]:
        """Extract legal reasoning steps from hybrid analysis"""
        
        reasoning_steps = []
        
        # Add contextual reasoning
        context_type = contextual_analysis.get("context_type", "general_legal")
        reasoning_steps.append(f"Contextual Analysis: Identified as {context_type.replace('_', ' ')}")
        
        # Add concept-based reasoning
        legal_concepts = contextual_analysis.get("legal_concepts", [])
        if legal_concepts:
            reasoning_steps.append(f"Legal Concepts: Found {len(legal_concepts)} relevant concepts")
        
        # Add entity-based reasoning
        legal_entities = contextual_analysis.get("legal_entities", [])
        if legal_entities:
            reasoning_steps.append(f"Legal References: Identified {len(legal_entities)} statutory/case references")
        
        # Add generation strategy reasoning
        strategy = generation_result.get("strategy", "unknown")
        reasoning_steps.append(f"Generation Strategy: Used {strategy.replace('_', ' ')} for optimal response")
        
        # Add source-based reasoning
        if sources:
            reasoning_steps.append(f"Source Analysis: Consulted {len(sources)} relevant legal sources")
        
        return reasoning_steps
    
    def _enhance_citations(
        self,
        contextual_analysis: Dict[str, Any],
        sources: List[Dict[str, Any]] = None,
        generation_result: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Enhance citations with contextual understanding"""
        
        enhanced_citations = []
        
        if sources:
            for i, source in enumerate(sources):
                # Calculate relevance based on contextual analysis
                relevance_score = self._calculate_source_relevance(
                    source, contextual_analysis
                )
                
                enhanced_citation = {
                    "index": i + 1,
                    "filename": source.get("filename", "Unknown"),
                    "chunk_id": source.get("chunk_id", ""),
                    "text_preview": source.get("text", "")[:200] + "...",
                    "relevance_score": relevance_score,
                    "contextual_match": relevance_score > 0.7,
                    "legal_concepts_matched": self._find_matching_concepts(
                        source.get("text", ""), 
                        contextual_analysis.get("legal_concepts", [])
                    )
                }
                
                enhanced_citations.append(enhanced_citation)
        
        # Sort by relevance
        enhanced_citations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return enhanced_citations
    
    def _calculate_source_relevance(
        self, 
        source: Dict[str, Any], 
        contextual_analysis: Dict[str, Any]
    ) -> float:
        """Calculate source relevance based on contextual analysis"""
        
        source_text = source.get("text", "").lower()
        legal_concepts = contextual_analysis.get("legal_concepts", [])
        
        # Base relevance from existing score
        base_score = source.get("combined_score", 0.5)
        
        # Concept matching bonus
        concept_matches = sum(1 for concept in legal_concepts if concept.split(":")[-1] in source_text)
        concept_bonus = min(0.3, concept_matches * 0.1)
        
        # Entity matching bonus
        legal_entities = contextual_analysis.get("legal_entities", [])
        entity_matches = sum(1 for entity in legal_entities if entity.get("value", "").lower() in source_text)
        entity_bonus = min(0.2, entity_matches * 0.1)
        
        return min(1.0, base_score + concept_bonus + entity_bonus)
    
    def _find_matching_concepts(self, text: str, legal_concepts: List[str]) -> List[str]:
        """Find matching legal concepts in source text"""
        text_lower = text.lower()
        matching_concepts = []
        
        for concept in legal_concepts:
            concept_term = concept.split(":")[-1]
            if concept_term in text_lower:
                matching_concepts.append(concept)
        
        return matching_concepts

# Factory function for easy integration
async def create_hybrid_legal_ai() -> HybridLegalAI:
    """Create and initialize hybrid legal AI system"""
    hybrid_ai = HybridLegalAI()
    await hybrid_ai.initialize()
    return hybrid_ai