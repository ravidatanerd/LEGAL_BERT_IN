"""
Advanced rate limiting for the FastAPI backend
"""
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    window_size: int = 60  # seconds

class AdvancedRateLimiter:
    """Advanced rate limiter with multiple time windows"""
    
    def __init__(self):
        # Default rules for different endpoints
        self.rules = {
            "/ask": RateLimitRule(20, 100, 5),
            "/judgment": RateLimitRule(10, 50, 2),
            "/documents/upload": RateLimitRule(5, 20, 1),
            "/sources/add_statutes": RateLimitRule(2, 5, 1),
            "default": RateLimitRule(30, 150, 10)
        }
        
        # Request tracking
        self.requests = defaultdict(lambda: {
            "minute": deque(),
            "hour": deque(),
            "burst": deque()
        })
        
        # Blocked IPs
        self.blocked_ips = {}
        self.block_duration = 300  # 5 minutes
    
    def is_allowed(self, client_ip: str, endpoint: str) -> Dict[str, Any]:
        """
        Check if request is allowed
        
        Args:
            client_ip: Client IP address
            endpoint: API endpoint being accessed
            
        Returns:
            Dict with allowed status and details
        """
        current_time = time.time()
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip, current_time):
            return {
                "allowed": False,
                "reason": "IP temporarily blocked",
                "retry_after": self._get_block_remaining(client_ip, current_time)
            }
        
        # Get rule for endpoint
        rule = self._get_rule_for_endpoint(endpoint)
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Check rate limits
        client_requests = self.requests[client_ip]
        
        # Check burst limit (last 10 seconds)
        burst_count = len([t for t in client_requests["burst"] if current_time - t < 10])
        if burst_count >= rule.burst_limit:
            self._block_ip(client_ip, current_time, "burst_limit")
            return {
                "allowed": False,
                "reason": "Burst limit exceeded",
                "retry_after": 10
            }
        
        # Check minute limit
        minute_count = len(client_requests["minute"])
        if minute_count >= rule.requests_per_minute:
            return {
                "allowed": False,
                "reason": "Rate limit exceeded",
                "retry_after": 60
            }
        
        # Check hour limit
        hour_count = len(client_requests["hour"])
        if hour_count >= rule.requests_per_hour:
            return {
                "allowed": False,
                "reason": "Hourly limit exceeded",
                "retry_after": 3600
            }
        
        # Record this request
        client_requests["minute"].append(current_time)
        client_requests["hour"].append(current_time)
        client_requests["burst"].append(current_time)
        
        return {
            "allowed": True,
            "remaining": {
                "minute": rule.requests_per_minute - minute_count - 1,
                "hour": rule.requests_per_hour - hour_count - 1,
                "burst": rule.burst_limit - burst_count - 1
            }
        }
    
    def _get_rule_for_endpoint(self, endpoint: str) -> RateLimitRule:
        """Get rate limiting rule for endpoint"""
        # Find matching rule
        for pattern, rule in self.rules.items():
            if pattern in endpoint or pattern == "default":
                return rule
        
        return self.rules["default"]
    
    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Clean old request records"""
        client_requests = self.requests[client_ip]
        
        # Clean minute window
        while client_requests["minute"] and current_time - client_requests["minute"][0] > 60:
            client_requests["minute"].popleft()
        
        # Clean hour window
        while client_requests["hour"] and current_time - client_requests["hour"][0] > 3600:
            client_requests["hour"].popleft()
        
        # Clean burst window
        while client_requests["burst"] and current_time - client_requests["burst"][0] > 10:
            client_requests["burst"].popleft()
    
    def _is_ip_blocked(self, client_ip: str, current_time: float) -> bool:
        """Check if IP is currently blocked"""
        if client_ip in self.blocked_ips:
            block_time = self.blocked_ips[client_ip]
            if current_time - block_time < self.block_duration:
                return True
            else:
                # Unblock expired blocks
                del self.blocked_ips[client_ip]
        
        return False
    
    def _get_block_remaining(self, client_ip: str, current_time: float) -> int:
        """Get remaining block time for IP"""
        if client_ip in self.blocked_ips:
            block_time = self.blocked_ips[client_ip]
            remaining = self.block_duration - (current_time - block_time)
            return max(0, int(remaining))
        
        return 0
    
    def _block_ip(self, client_ip: str, current_time: float, reason: str):
        """Block an IP address"""
        self.blocked_ips[client_ip] = current_time
        logger.warning(f"IP {client_ip} blocked for {reason}")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using advanced rate limiter"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = AdvancedRateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        
        # Check rate limit
        limit_result = self.rate_limiter.is_allowed(client_ip, endpoint)
        
        if not limit_result["allowed"]:
            # Add rate limit headers
            headers = {
                "X-RateLimit-Reason": limit_result["reason"],
                "Retry-After": str(limit_result.get("retry_after", 60))
            }
            
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit_result['reason']}",
                headers=headers
            )
        
        # Add rate limit info to response headers
        response = await call_next(request)
        
        if "remaining" in limit_result:
            remaining = limit_result["remaining"]
            response.headers["X-RateLimit-Remaining-Minute"] = str(remaining.get("minute", 0))
            response.headers["X-RateLimit-Remaining-Hour"] = str(remaining.get("hour", 0))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"