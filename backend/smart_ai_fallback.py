"""
Smart AI Fallback System for InLegalDesk
Automatically switches from premium ChatGPT to free/default models when rate limited
Ensures uninterrupted service with graceful degradation
"""
import os
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class AIModelTier(Enum):
    """AI model tiers in order of preference"""
    PREMIUM = "premium"          # GPT-4, GPT-4-turbo (best quality)
    STANDARD = "standard"        # GPT-3.5-turbo (good quality)
    FREE = "free"               # Free tier models
    LOCAL_ADVANCED = "local_advanced"  # Local transformers models
    LOCAL_BASIC = "local_basic"        # Basic local processing
    FALLBACK = "fallback"              # Simple rule-based responses

class SmartAIFallback:
    """Smart AI system with automatic fallback when rate limited"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.current_tier = AIModelTier.PREMIUM
        self.rate_limit_reset_times = {}
        self.consecutive_failures = {}
        self.fallback_enabled = True
        
        # Model configurations
        self.model_configs = {
            AIModelTier.PREMIUM: {
                "models": ["gpt-4o", "gpt-4-turbo-preview", "gpt-4"],
                "max_tokens": 4000,
                "temperature": 0.1,
                "cost_per_1k": 0.03,
                "quality": "excellent"
            },
            AIModelTier.STANDARD: {
                "models": ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                "max_tokens": 2000,
                "temperature": 0.1,
                "cost_per_1k": 0.002,
                "quality": "very good"
            },
            AIModelTier.FREE: {
                "models": ["gpt-3.5-turbo"],
                "max_tokens": 1000,
                "temperature": 0.2,
                "cost_per_1k": 0.002,
                "quality": "good"
            },
            AIModelTier.LOCAL_ADVANCED: {
                "models": ["local_transformers"],
                "max_tokens": 1500,
                "temperature": 0.1,
                "cost_per_1k": 0.0,
                "quality": "good"
            },
            AIModelTier.LOCAL_BASIC: {
                "models": ["local_basic"],
                "max_tokens": 1000,
                "temperature": 0.2,
                "cost_per_1k": 0.0,
                "quality": "basic"
            },
            AIModelTier.FALLBACK: {
                "models": ["rule_based"],
                "max_tokens": 500,
                "temperature": 0.0,
                "cost_per_1k": 0.0,
                "quality": "basic"
            }
        }
        
        self.client = None
        if self.api_key:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
    
    async def generate_response(self, question: str, context: str = "", max_retries: int = 3) -> Dict[str, Any]:
        """Generate response with smart fallback system"""
        
        # Try each tier until one succeeds
        for tier in [AIModelTier.PREMIUM, AIModelTier.STANDARD, AIModelTier.FREE, 
                     AIModelTier.LOCAL_ADVANCED, AIModelTier.LOCAL_BASIC, AIModelTier.FALLBACK]:
            
            # Check if this tier is available and not rate limited
            if not self._is_tier_available(tier):
                logger.info(f"Skipping {tier.value} - not available or rate limited")
                continue
            
            try:
                logger.info(f"Attempting response with {tier.value} tier")
                response = await self._generate_with_tier(tier, question, context)
                
                if response:
                    # Reset failure count on success
                    self.consecutive_failures[tier] = 0
                    response["ai_tier_used"] = tier.value
                    response["quality_level"] = self.model_configs[tier]["quality"]
                    return response
                    
            except Exception as e:
                logger.warning(f"{tier.value} tier failed: {e}")
                await self._handle_tier_failure(tier, e)
                continue
        
        # If all tiers fail, return basic error response
        return self._create_emergency_response(question)
    
    def _is_tier_available(self, tier: AIModelTier) -> bool:
        """Check if a tier is available and not rate limited"""
        
        # Check if tier is rate limited
        if tier in self.rate_limit_reset_times:
            reset_time = self.rate_limit_reset_times[tier]
            if datetime.now() < reset_time:
                return False
        
        # Check tier-specific availability
        if tier in [AIModelTier.PREMIUM, AIModelTier.STANDARD, AIModelTier.FREE]:
            return self.api_key is not None
        
        elif tier == AIModelTier.LOCAL_ADVANCED:
            try:
                import torch
                import transformers
                return True
            except ImportError:
                return False
        
        elif tier in [AIModelTier.LOCAL_BASIC, AIModelTier.FALLBACK]:
            return True  # Always available
        
        return False
    
    async def _generate_with_tier(self, tier: AIModelTier, question: str, context: str) -> Optional[Dict[str, Any]]:
        """Generate response using specific tier"""
        
        if tier in [AIModelTier.PREMIUM, AIModelTier.STANDARD, AIModelTier.FREE]:
            return await self._generate_with_openai(tier, question, context)
        
        elif tier == AIModelTier.LOCAL_ADVANCED:
            return await self._generate_with_local_models(question, context)
        
        elif tier == AIModelTier.LOCAL_BASIC:
            return self._generate_with_basic_local(question, context)
        
        elif tier == AIModelTier.FALLBACK:
            return self._generate_with_fallback(question, context)
        
        return None
    
    async def _generate_with_openai(self, tier: AIModelTier, question: str, context: str) -> Optional[Dict[str, Any]]:
        """Generate response using OpenAI API with tier-specific settings"""
        
        if not self.client:
            return None
        
        config = self.model_configs[tier]
        model = config["models"][0]  # Use first model in tier
        
        # Create system prompt based on tier
        if tier == AIModelTier.PREMIUM:
            system_prompt = """You are an expert Indian legal research assistant with access to comprehensive legal databases. Provide detailed, accurate legal analysis with proper citations and case law references."""
        elif tier == AIModelTier.STANDARD:
            system_prompt = """You are an Indian legal research assistant. Provide accurate legal information with relevant citations."""
        else:  # FREE
            system_prompt = """You are a legal assistant for Indian law. Provide helpful legal information."""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }
        
        try:
            response = await self.client.post(
                f"{os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}/chat/completions",
                json=payload,
                timeout=120.0
            )
            
            if response.status_code == 200:
                data = response.json()
                answer_text = data["choices"][0]["message"]["content"]
                
                return {
                    "answer": answer_text,
                    "model_used": model,
                    "tier": tier.value,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                }
            
            elif response.status_code == 429:  # Rate limit
                logger.warning(f"Rate limit hit for {tier.value} tier")
                await self._handle_rate_limit(tier, response)
                return None
            
            elif response.status_code == 401:  # Invalid API key
                logger.error("Invalid API key")
                return None
            
            else:
                logger.warning(f"OpenAI API error {response.status_code}: {response.text}")
                return None
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout for {tier.value} tier")
            return None
        except Exception as e:
            logger.error(f"OpenAI API error for {tier.value}: {e}")
            return None
    
    async def _generate_with_local_models(self, question: str, context: str) -> Optional[Dict[str, Any]]:
        """Generate response using local transformer models"""
        
        try:
            # Try to use hybrid AI system
            from hybrid_legal_ai import create_hybrid_legal_ai
            
            hybrid_ai = create_hybrid_legal_ai()
            if hybrid_ai:
                result = await hybrid_ai.process_legal_query(question, context)
                
                return {
                    "answer": result.get("response", "Local model response generated"),
                    "model_used": "local_transformers",
                    "tier": "local_advanced",
                    "confidence": result.get("confidence", 0.7)
                }
        
        except Exception as e:
            logger.warning(f"Local advanced models failed: {e}")
        
        return None
    
    def _generate_with_basic_local(self, question: str, context: str) -> Dict[str, Any]:
        """Generate response using basic local processing"""
        
        # Simple keyword-based responses for common legal queries
        question_lower = question.lower()
        
        basic_responses = {
            "section 302": {
                "answer": "**Section 302 IPC - Murder**\n\nSection 302 of the Indian Penal Code deals with the punishment for murder. According to this section, whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.\n\n**Key Elements:**\n• Intention to cause death\n• Knowledge that the act is likely to cause death\n• Actual causation of death\n\n**Note**: This is a basic response. For detailed analysis, please wait for API rate limits to reset or add credits to your OpenAI account.",
                "confidence": 0.8
            },
            "section 420": {
                "answer": "**Section 420 IPC - Cheating**\n\nSection 420 of the Indian Penal Code deals with cheating and dishonestly inducing delivery of property. The punishment is imprisonment for a term which may extend to seven years, or with fine, or with both.\n\n**Elements:**\n• Cheating (as defined in Section 415)\n• Dishonestly inducing delivery of property\n• Intention to deceive\n\n**Note**: This is a basic response. For comprehensive analysis, please wait for API rate limits to reset.",
                "confidence": 0.8
            },
            "bail": {
                "answer": "**Bail Provisions in Indian Law**\n\nBail is governed primarily by the Code of Criminal Procedure (CrPC), particularly Sections 436-450. The general principle is 'bail is the rule, jail is the exception.'\n\n**Types of Bail:**\n• Regular bail (Section 437)\n• Anticipatory bail (Section 438)\n• Default bail (Section 167)\n\n**Note**: This is a basic response. For detailed case law and specific situations, please wait for API rate limits to reset.",
                "confidence": 0.7
            }
        }
        
        # Find best matching response
        best_match = None
        for keyword, response_data in basic_responses.items():
            if keyword in question_lower:
                best_match = response_data
                break
        
        if best_match:
            return {
                "answer": best_match["answer"],
                "model_used": "local_basic",
                "tier": "local_basic", 
                "confidence": best_match["confidence"]
            }
        
        # Generic response
        return {
            "answer": f"**Legal Query Response (Basic Mode)**\n\nYour question: {question}\n\nI'm currently operating in basic mode due to API rate limits. For comprehensive legal analysis, please:\n\n1. ⏰ Wait for rate limits to reset (usually 15-60 minutes)\n2. 💰 Add credits to your OpenAI account\n3. 🔧 Check your usage at https://platform.openai.com/usage\n\nFor immediate assistance with common legal topics (IPC sections, bail, evidence), please rephrase your question with specific section numbers or legal concepts.",
            "model_used": "local_basic",
            "tier": "local_basic",
            "confidence": 0.5
        }
    
    def _generate_with_fallback(self, question: str, context: str) -> Dict[str, Any]:
        """Generate basic fallback response"""
        
        return {
            "answer": f"**InLegalDesk - Basic Response Mode**\n\nI'm currently in fallback mode due to temporary API limitations.\n\n**Your Question**: {question}\n\n**Basic Guidance**: For comprehensive legal research on Indian law topics, please:\n\n• Wait for premium AI to become available\n• Check your OpenAI account status\n• Use offline legal research resources\n• Contact legal professionals for urgent matters\n\n**Available**: Basic legal information and guidance\n**Limited**: Advanced AI analysis and case law research",
            "model_used": "fallback",
            "tier": "fallback",
            "confidence": 0.3
        }
    
    async def _handle_rate_limit(self, tier: AIModelTier, response: httpx.Response):
        """Handle rate limit for specific tier"""
        
        # Parse rate limit headers
        retry_after = 60  # Default
        if "retry-after" in response.headers:
            retry_after = int(response.headers["retry-after"])
        elif "x-ratelimit-reset" in response.headers:
            retry_after = int(response.headers["x-ratelimit-reset"]) - int(time.time())
        
        # Set reset time for this tier
        self.rate_limit_reset_times[tier] = datetime.now() + timedelta(seconds=retry_after)
        
        logger.warning(f"{tier.value} tier rate limited for {retry_after} seconds")
    
    async def _handle_tier_failure(self, tier: AIModelTier, error: Exception):
        """Handle failure for specific tier"""
        
        if tier not in self.consecutive_failures:
            self.consecutive_failures[tier] = 0
        
        self.consecutive_failures[tier] += 1
        
        # If too many consecutive failures, disable tier temporarily
        if self.consecutive_failures[tier] >= 3:
            self.rate_limit_reset_times[tier] = datetime.now() + timedelta(minutes=10)
            logger.warning(f"Temporarily disabling {tier.value} due to consecutive failures")
    
    def _create_emergency_response(self, question: str) -> Dict[str, Any]:
        """Create emergency response when all tiers fail"""
        
        return {
            "answer": f"**Emergency Response Mode**\n\nAll AI systems are temporarily unavailable. Your question was: {question}\n\n**Immediate Actions**:\n1. Wait 15-30 minutes for rate limits to reset\n2. Check OpenAI account status and billing\n3. Use manual legal research resources\n4. Contact legal professionals for urgent matters\n\n**System Status**: All AI tiers temporarily unavailable\n**Recommendation**: Try again in 30 minutes or add OpenAI credits",
            "model_used": "emergency",
            "tier": "emergency",
            "confidence": 0.1,
            "status": "all_systems_unavailable"
        }
    
    def get_current_tier_info(self) -> Dict[str, Any]:
        """Get information about current AI tier"""
        
        available_tiers = []
        for tier in AIModelTier:
            if self._is_tier_available(tier):
                available_tiers.append({
                    "tier": tier.value,
                    "quality": self.model_configs[tier]["quality"],
                    "cost": self.model_configs[tier]["cost_per_1k"],
                    "models": self.model_configs[tier]["models"]
                })
        
        return {
            "current_tier": self.current_tier.value,
            "available_tiers": available_tiers,
            "rate_limited_tiers": [
                tier.value for tier, reset_time in self.rate_limit_reset_times.items()
                if datetime.now() < reset_time
            ],
            "fallback_enabled": self.fallback_enabled
        }
    
    async def test_api_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity and determine available tiers"""
        
        results = {}
        
        if not self.api_key:
            return {"error": "No API key configured"}
        
        # Test each OpenAI tier
        for tier in [AIModelTier.PREMIUM, AIModelTier.STANDARD, AIModelTier.FREE]:
            config = self.model_configs[tier]
            model = config["models"][0]
            
            try:
                # Minimal test request
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                
                response = await self.client.post(
                    f"{os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}/chat/completions",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    results[tier.value] = {"status": "available", "model": model}
                elif response.status_code == 429:
                    results[tier.value] = {"status": "rate_limited", "model": model}
                else:
                    results[tier.value] = {"status": "error", "code": response.status_code}
                    
            except Exception as e:
                results[tier.value] = {"status": "failed", "error": str(e)}
        
        return results

# Global smart fallback instance
smart_ai = SmartAIFallback()

async def get_ai_response_with_fallback(question: str, context: str = "") -> Dict[str, Any]:
    """Get AI response with automatic fallback system"""
    return await smart_ai.generate_response(question, context)

def get_ai_tier_status() -> Dict[str, Any]:
    """Get current AI tier status"""
    return smart_ai.get_current_tier_info()

async def test_all_ai_tiers() -> Dict[str, Any]:
    """Test all AI tiers and return availability"""
    return await smart_ai.test_api_connectivity()