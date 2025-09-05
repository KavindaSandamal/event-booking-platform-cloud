import asyncio
import time
from typing import Callable, Any, Optional
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerConfig:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if not self.can_execute():
            raise Exception("Circuit breaker is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self.on_success()
            return result
        except self.config.expected_exception as e:
            self.on_failure()
            raise e

# Global circuit breaker instances
_circuit_breakers = {}

def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig()
        _circuit_breakers[name] = CircuitBreaker(config)
    return _circuit_breakers[name]

# Default circuit breaker configurations
def get_auth_circuit_breaker() -> CircuitBreaker:
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)
    return get_circuit_breaker("auth", config)

def get_payment_circuit_breaker() -> CircuitBreaker:
    config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
    return get_circuit_breaker("payment", config)

def get_booking_circuit_breaker() -> CircuitBreaker:
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)
    return get_circuit_breaker("booking", config)