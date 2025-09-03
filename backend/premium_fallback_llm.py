"""
Premium Fallback LLM System
Automatically switches from premium ChatGPT to free models when rate limited
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PremiumFallbackLLM:
    """LLM with premium to free model fallback system"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Model hierarchy: Premium → Standard → Free
        self.model_hierarchy = [
            {
                "name": "gpt-4",
                "tier": "premium",
                "cost_per_1k": 0.03,
                "description": "GPT-4 (Premium)"
            },
            {
                "name": "gpt-4-turbo-preview", 
                "tier": "premium",
                "cost_per_1k": 0.01,
                "description": "GPT-4 Turbo (Premium)"
            },
            {
                "name": "gpt-3.5-turbo",
                "tier": "standard", 
                "cost_per_1k": 0.002,
                "description": "GPT-3.5 Turbo (Standard)"
            },
            {
                "name": "gpt-3.5-turbo-16k",
                "tier": "free",
                "cost_per_1k": 0.002,
                "description": "GPT-3.5 Turbo 16K (Free tier compatible)"
            }
        ]
        
        self.current_model_index = 0
        self.rate_limit_tracker = {}
        self.client = None
        
        if self.api_key:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
    
    def get_current_model(self) -> Dict[str, Any]:
        """Get current model information"""
        if self.current_model_index < len(self.model_hierarchy):
            return self.model_hierarchy[self.current_model_index]
        return self.model_hierarchy[-1]  # Fallback to last model
    
    def fallback_to_next_model(self) -> Optional[Dict[str, Any]]:
        """Fallback to next model in hierarchy"""
        if self.current_model_index < len(self.model_hierarchy) - 1:
            self.current_model_index += 1
            new_model = self.get_current_model()
            logger.info(f"Falling back to: {new_model['description']}")
            return new_model
        else:
            logger.warning("No more models to fallback to")
            return None
    
    def reset_to_premium(self):
        """Reset to premium model (call this periodically)"""
        self.current_model_index = 0
        logger.info("Reset to premium model")
    
    async def generate_answer(self, question: str, sources: List[Dict] = None, language: str = "auto", max_retries: int = 3) -> Dict[str, Any]:
        """Generate answer with premium fallback system"""
        
        sources = sources or []
        
        for attempt in range(max_retries):
            try:
                current_model = self.get_current_model()
                
                # Try current model
                result = await self._call_openai_api(question, sources, language, current_model)
                
                if result["success"]:
                    # Add model info to response
                    result["model_used"] = current_model["description"]
                    result["tier"] = current_model["tier"]
                    return result
                
                # Handle rate limit
                elif result["error_type"] == "rate_limit":
                    logger.warning(f"Rate limit hit for {current_model['description']}")
                    
                    # Try to fallback
                    next_model = self.fallback_to_next_model()
                    if next_model:
                        logger.info(f"Falling back to {next_model['description']}")
                        continue  # Try next model
                    else:
                        # All models exhausted
                        return await self._create_rate_limit_response(question)
                
                # Handle other errors
                else:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return await self._create_error_response(question, result["error"])
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return await self._create_error_response(question, str(e))
        
        # If all attempts failed
        return await self._create_fallback_response(question)
    
    async def _call_openai_api(self, question: str, sources: List[Dict], language: str, model_info: Dict) -> Dict[str, Any]:
        """Make API call to OpenAI with specific model"""
        
        if not self.client:
            return {
                "success": False,
                "error_type": "no_api_key",
                "error": "OpenAI API key not configured"
            }
        
        try:
            # Create context from sources
            context = ""
            if sources:
                context = "\n\nRelevant legal sources:\n"
                for i, source in enumerate(sources[:3], 1):
                    context += f"{i}. {source.get('text', '')[:500]}...\n"
            
            # Create prompt
            prompt = f"""You are an expert Indian legal research assistant. Answer the legal question based on the provided sources and your knowledge of Indian law.

Question: {question}

Context: {context}

Please provide a comprehensive answer covering:
1. Relevant legal provisions
2. Case law if applicable  
3. Practical implications
4. Citations to sources

Answer in {language if language != 'auto' else 'English'}:"""
            
            # API payload
            payload = {
                "model": model_info["name"],
                "messages": [
                    {"role": "system", "content": "You are an expert Indian legal research assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
                "temperature": 0.3
            }
            
            # Make API call
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=120.0
            )
            
            if response.status_code == 200:
                data = response.json()
                answer_text = data["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "text": answer_text,
                    "language_detected": language,
                    "model": model_info["name"],
                    "usage": data.get("usage", {})
                }
            
            elif response.status_code == 429:
                # Rate limit exceeded
                return {
                    "success": False,
                    "error_type": "rate_limit",
                    "error": "Rate limit exceeded",
                    "retry_after": response.headers.get("retry-after", 60)
                }
            
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                return {
                    "success": False,
                    "error_type": "api_error",
                    "error": error_data.get("error", {}).get("message", "Unknown API error"),
                    "status_code": response.status_code
                }
                
        except httpx.TimeoutException:
            return {
                "success": False,
                "error_type": "timeout",
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": "network_error", 
                "error": str(e)
            }
    
    async def _create_rate_limit_response(self, question: str) -> Dict[str, Any]:
        """Create response when all models are rate limited"""
        return {
            "text": f"""🚨 **All ChatGPT Models Temporarily Rate Limited**

Your question: "{question}"

**What happened:**
• Your premium ChatGPT subscription hit rate limits
• All fallback models also rate limited
• This is temporary and will reset automatically

**Immediate Solutions:**
1. ⏰ **Wait 1 hour** - Rate limits reset automatically
2. 💰 **Add more credits** - https://platform.openai.com/account/billing
3. 🔧 **Use offline mode** - Local AI models (no API limits)

**Offline Mode Available:**
I can switch to local legal AI models that don't use OpenAI API.
This provides basic legal research without any rate limits.

**Your Options:**
• Wait for rate limits to reset
• Use offline mode for immediate response
• Add billing to increase limits

Would you like me to switch to offline mode for unlimited usage?""",
            "language_detected": "en",
            "model_used": "Rate Limited",
            "tier": "fallback"
        }
    
    async def _create_error_response(self, question: str, error: str) -> Dict[str, Any]:
        """Create response for API errors"""
        return {
            "text": f"""❌ **API Error**

Your question: "{question}"

**Error:** {error}

**Solutions:**
1. Check your internet connection
2. Verify OpenAI API key is valid
3. Try again in a few minutes
4. Use offline mode as backup

**Offline Mode:**
Switch to local AI models for immediate response without API dependency.""",
            "language_detected": "en",
            "model_used": "Error",
            "tier": "error"
        }
    
    async def _create_fallback_response(self, question: str) -> Dict[str, Any]:
        """Create basic fallback response"""
        
        # Basic legal knowledge responses
        question_lower = question.lower()
        
        if "section 302" in question_lower or "murder" in question_lower:
            answer = """**Section 302 - Murder (IPC)**

Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.

**Key Elements:**
• Intention to cause death
• Knowledge that act is likely to cause death  
• Actual causing of death

**Punishment:** Death penalty OR Life imprisonment + Fine

**Note:** This is a basic response. For comprehensive analysis, ensure API connectivity or use offline mode."""

        elif "bail" in question_lower:
            answer = """**Bail Provisions (CrPC)**

"Bail is the rule, jail is the exception"

**Types of Bail:**
• Regular bail (Sections 437-439)
• Anticipatory bail (Section 438)
• Interim bail (temporary)

**Factors for Bail:**
• Nature of offense
• Severity of punishment
• Character of accused
• Flight risk

**Note:** For detailed bail analysis, use full AI mode when available."""

        else:
            answer = f"""**Basic Legal Information**

Your question: "{question}"

**Available in Basic Mode:**
• IPC sections and criminal law basics
• Bail and procedure information
• Constitutional law fundamentals
• Evidence Act provisions

**For Comprehensive Analysis:**
• Ensure ChatGPT API is working
• Use offline mode with local models
• Upload relevant legal documents

**Current Status:** Running in basic fallback mode due to API limitations."""

        return {
            "text": answer,
            "language_detected": "en",
            "model_used": "Basic Fallback",
            "tier": "fallback"
        }

# Global instance
premium_fallback_llm = PremiumFallbackLLM()