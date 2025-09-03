"""
OpenAI Rate Limit Handler for InLegalDesk
Handles rate limiting gracefully with fallbacks and retries
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OpenAIRateLimitHandler:
    """Handles OpenAI rate limiting with intelligent fallbacks"""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = None
        self.consecutive_failures = 0
        
        # Configuration
        self.max_requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
        self.retry_attempts = int(os.getenv("RETRY_ATTEMPTS", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "60"))
        self.enable_fallback = os.getenv("ENABLE_LOCAL_FALLBACK", "true").lower() == "true"
        
    async def handle_rate_limit_error(self, error_response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limit error with intelligent responses"""
        
        logger.warning("OpenAI rate limit exceeded")
        self.consecutive_failures += 1
        
        # Parse rate limit information
        retry_after = error_response.get("retry_after", 60)
        error_type = error_response.get("error", {}).get("type", "rate_limit_exceeded")
        
        # Calculate when to retry
        self.rate_limit_reset_time = datetime.now() + timedelta(seconds=retry_after)
        
        logger.info(f"Rate limit reset time: {self.rate_limit_reset_time}")
        
        # Provide user-friendly response
        response = {
            "status": "rate_limited",
            "message": self._create_rate_limit_message(retry_after),
            "retry_after": retry_after,
            "suggestions": self._get_rate_limit_suggestions(),
            "fallback_available": self.enable_fallback
        }
        
        return response
    
    def _create_rate_limit_message(self, retry_after: int) -> str:
        """Create user-friendly rate limit message"""
        
        if retry_after < 60:
            wait_time = f"{retry_after} seconds"
        elif retry_after < 3600:
            wait_time = f"{retry_after // 60} minutes"
        else:
            wait_time = f"{retry_after // 3600} hours"
        
        message = f"""
🚨 **OpenAI Rate Limit Exceeded**

Your ChatGPT API key is valid, but you've reached OpenAI's usage limits.

**Wait Time**: {wait_time}

**What this means**:
• Your API key is working correctly
• You've used up your allowed requests for this time period
• This is normal with free/low-tier OpenAI accounts

**Immediate Solutions**:
1. ⏰ Wait {wait_time} and try again
2. 💰 Add credits to your OpenAI account
3. 🔧 Use local models as fallback (see below)
4. 📊 Check usage at: https://platform.openai.com/usage
"""
        
        return message
    
    def _get_rate_limit_suggestions(self) -> list:
        """Get suggestions for handling rate limits"""
        return [
            "Add credits to your OpenAI account at https://platform.openai.com/account/billing",
            "Use VLM_PRESET=offline to avoid API calls entirely",
            "Set VLM_PRESET=balanced to use local models first",
            "Reduce OPENAI_MAX_TOKENS in configuration",
            "Enable local model fallbacks in settings",
            "Wait for the rate limit to reset automatically"
        ]
    
    def should_retry(self) -> bool:
        """Check if we should retry the request"""
        if self.rate_limit_reset_time is None:
            return True
        
        return datetime.now() >= self.rate_limit_reset_time
    
    def get_wait_time(self) -> int:
        """Get remaining wait time in seconds"""
        if self.rate_limit_reset_time is None:
            return 0
        
        remaining = (self.rate_limit_reset_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    async def wait_for_rate_limit_reset(self):
        """Wait for rate limit to reset"""
        wait_time = self.get_wait_time()
        if wait_time > 0:
            logger.info(f"Waiting {wait_time} seconds for rate limit reset")
            await asyncio.sleep(wait_time)
    
    def create_fallback_response(self, question: str) -> Dict[str, Any]:
        """Create fallback response when rate limited"""
        
        fallback_message = f"""
🤖 **Local AI Response** (OpenAI Rate Limited)

I'm currently rate-limited by OpenAI, but I can still help with basic legal information.

**Your Question**: {question}

**Basic Legal Guidance**:
For comprehensive analysis of your legal question, please:

1. ⏰ **Wait and retry** - OpenAI rate limit will reset automatically
2. 💰 **Add credits** - Visit https://platform.openai.com/account/billing
3. 🔧 **Use offline mode** - Set VLM_PRESET=offline for local-only processing
4. 📚 **Manual research** - Check legal databases and statutes directly

**Rate Limit Information**:
• Your API key is valid and working
• You've temporarily exceeded usage limits
• This is normal with free/trial accounts
• Adding billing removes most limitations

**Alternative**: Use the offline mode which provides legal research without API calls.
"""
        
        return {
            "answer": fallback_message,
            "sources": [
                {
                    "filename": "Rate Limit Handler",
                    "text": "Local fallback response due to OpenAI rate limiting",
                    "combined_score": 0.5
                }
            ],
            "language_detected": "en",
            "mode": "rate_limited_fallback"
        }

# Global rate limit handler
rate_limit_handler = OpenAIRateLimitHandler()

def handle_openai_error(error_response: Dict[str, Any], question: str = "") -> Dict[str, Any]:
    """Handle OpenAI API errors with appropriate responses"""
    
    error_type = error_response.get("error", {}).get("type", "unknown")
    
    if error_type == "rate_limit_exceeded" or "rate limit" in str(error_response).lower():
        return asyncio.run(rate_limit_handler.handle_rate_limit_error(error_response))
    
    elif error_type == "invalid_api_key":
        return {
            "status": "invalid_key",
            "message": "API key is invalid. Please check your OpenAI API key.",
            "suggestions": [
                "Verify your API key at https://platform.openai.com/api-keys",
                "Make sure the key starts with 'sk-' or 'sk-proj-'",
                "Check that the key hasn't been revoked",
                "Try regenerating a new API key"
            ]
        }
    
    elif error_type == "insufficient_quota":
        return {
            "status": "quota_exceeded",
            "message": "Your OpenAI account has insufficient quota.",
            "suggestions": [
                "Add credits at https://platform.openai.com/account/billing",
                "Check your usage at https://platform.openai.com/usage",
                "Consider upgrading your OpenAI plan",
                "Use local models as fallback"
            ]
        }
    
    else:
        return {
            "status": "api_error",
            "message": f"OpenAI API error: {error_type}",
            "suggestions": [
                "Check OpenAI status at https://status.openai.com",
                "Verify your internet connection",
                "Try again in a few minutes",
                "Use local models as fallback"
            ]
        }

if __name__ == "__main__":
    # Run as standalone troubleshooter
    check_openai_rate_limits()
    check_api_key_status()
    provide_rate_limit_solutions()