"""
Enhanced Circuit Breaker Pattern Implementation
Provides fault tolerance and resilience for service calls
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
import functools

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures before opening
    success_threshold: int = 3          # Number of successes to close from half-open
    timeout: int = 60                   # Time in seconds to wait before trying half-open
    expected_exception: type = Exception  # Exception type to count as failures
    max_failures: int = 100             # Maximum failures before permanent open

class CircuitBreaker:
    """Enhanced circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
        
        # Metrics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.circuit_opens = 0
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.total_calls += 1
            
            # Check if circuit should be opened
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker {self.name} attempting reset to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    self.failed_calls += 1
                    raise CircuitBreakerOpenException(f"Circuit breaker {self.name} is OPEN")
            
            # Execute the function
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                await self._on_success()
                return result
                
            except self.config.expected_exception as e:
                await self._on_failure()
                raise e
            except Exception as e:
                # Unexpected exception - don't count as failure
                logger.warning(f"Unexpected exception in circuit breaker {self.name}: {e}")
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset from OPEN to HALF_OPEN"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.config.timeout
    
    async def _on_success(self):
        """Handle successful call"""
        self.successful_calls += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(f"Circuit breaker {self.name} closed after {self.success_count} successes")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed call"""
        self.failed_calls += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed in half-open state, go back to open
            logger.warning(f"Circuit breaker {self.name} opened again after failure in HALF_OPEN state")
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")
                self.state = CircuitState.OPEN
                self.circuit_opens += 1
        
        # Check for permanent open
        if self.failure_count >= self.config.max_failures:
            logger.error(f"Circuit breaker {self.name} permanently opened after {self.failure_count} failures")
            self.state = CircuitState.OPEN
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        success_rate = (self.successful_calls / self.total_calls * 100) if self.total_calls > 0 else 0
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round(success_rate, 2),
            "failure_count": self.failure_count,
            "circuit_opens": self.circuit_opens,
            "last_failure_time": self.last_failure_time
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.name} manually reset")

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker pattern"""
    def decorator(func):
        breaker = CircuitBreaker(name, config)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        # Add circuit breaker instance to function
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator

# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create circuit breaker by name"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]

def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all circuit breakers"""
    return _circuit_breakers.copy()

def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    for breaker in _circuit_breakers.values():
        breaker.reset()
    logger.info("All circuit breakers reset")

# Pre-configured circuit breakers for common use cases
def create_http_circuit_breaker(name: str) -> CircuitBreaker:
    """Create circuit breaker for HTTP calls"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=30,
        expected_exception=Exception
    )
    return get_circuit_breaker(name, config)

def create_database_circuit_breaker(name: str) -> CircuitBreaker:
    """Create circuit breaker for database calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=60,
        expected_exception=Exception
    )
    return get_circuit_breaker(name, config)