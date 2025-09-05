"""
Comprehensive Health Check System
Provides health monitoring for all services and dependencies
"""

import asyncio
import time
import logging
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
import redis
import psycopg2
from sqlalchemy import create_engine, text
import os

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: float
    details: Dict[str, Any] = None

class HealthChecker:
    """Comprehensive health checker for services and dependencies"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, Callable] = {}
        self.start_time = time.time()
        
    def add_check(self, name: str, check_func: Callable, critical: bool = True):
        """Add a health check function"""
        self.checks[name] = {
            'func': check_func,
            'critical': critical
        }
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        critical_failures = 0
        
        for name, check_info in self.checks.items():
            start_time = time.time()
            
            try:
                result = await check_info['func']()
                response_time = (time.time() - start_time) * 1000
                
                if isinstance(result, HealthCheckResult):
                    results[name] = result
                    if result.status == HealthStatus.UNHEALTHY and check_info['critical']:
                        critical_failures += 1
                        overall_status = HealthStatus.UNHEALTHY
                    elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                else:
                    # Simple boolean result
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    results[name] = HealthCheckResult(
                        name=name,
                        status=status,
                        message="Check completed" if result else "Check failed",
                        response_time_ms=response_time,
                        timestamp=time.time()
                    )
                    
                    if not result and check_info['critical']:
                        critical_failures += 1
                        overall_status = HealthStatus.UNHEALTHY
                        
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed with exception: {str(e)}",
                    response_time_ms=response_time,
                    timestamp=time.time()
                )
                
                if check_info['critical']:
                    critical_failures += 1
                    overall_status = HealthStatus.UNHEALTHY
                
                logger.error(f"Health check {name} failed: {e}")
        
        # Calculate overall health
        uptime = time.time() - self.start_time
        
        return {
            "service": self.service_name,
            "status": overall_status.value,
            "uptime_seconds": round(uptime, 2),
            "critical_failures": critical_failures,
            "total_checks": len(self.checks),
            "checks": {name: {
                "status": result.status.value,
                "message": result.message,
                "response_time_ms": round(result.response_time_ms, 2),
                "timestamp": result.timestamp,
                "details": result.details or {}
            } for name, result in results.items()},
            "timestamp": time.time()
        }

# Pre-built health check functions
class HealthChecks:
    """Collection of common health check functions"""
    
    @staticmethod
    async def check_database(database_url: str) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                # Test basic connectivity
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Test query performance
                query_start = time.time()
                conn.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
                query_time = (time.time() - query_start) * 1000
                
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    response_time_ms=response_time,
                    timestamp=time.time(),
                    details={
                        "query_time_ms": round(query_time, 2),
                        "connection_pool_size": engine.pool.size(),
                        "checked_out_connections": engine.pool.checkedout()
                    }
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    @staticmethod
    async def check_redis(redis_url: str) -> HealthCheckResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            client = redis.from_url(redis_url)
            
            # Test basic connectivity
            client.ping()
            
            # Test read/write performance
            test_key = f"health_check_{int(time.time())}"
            test_value = "test_value"
            
            write_start = time.time()
            client.set(test_key, test_value, ex=10)  # Expire in 10 seconds
            write_time = (time.time() - write_start) * 1000
            
            read_start = time.time()
            retrieved_value = client.get(test_key)
            read_time = (time.time() - read_start) * 1000
            
            # Clean up
            client.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if retrieved_value and retrieved_value.decode() == test_value:
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis connection and read/write successful",
                    response_time_ms=response_time,
                    timestamp=time.time(),
                    details={
                        "write_time_ms": round(write_time, 2),
                        "read_time_ms": round(read_time, 2),
                        "memory_usage": client.info().get('used_memory_human', 'unknown')
                    }
                )
            else:
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis read/write test failed",
                    response_time_ms=response_time,
                    timestamp=time.time()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    @staticmethod
    async def check_http_service(url: str, timeout: int = 5) -> HealthCheckResult:
        """Check HTTP service availability"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return HealthCheckResult(
                        name="http_service",
                        status=HealthStatus.HEALTHY,
                        message=f"HTTP service responded with status {response.status_code}",
                        response_time_ms=response_time,
                        timestamp=time.time(),
                        details={
                            "status_code": response.status_code,
                            "url": url
                        }
                    )
                else:
                    return HealthCheckResult(
                        name="http_service",
                        status=HealthStatus.DEGRADED,
                        message=f"HTTP service responded with status {response.status_code}",
                        response_time_ms=response_time,
                        timestamp=time.time(),
                        details={
                            "status_code": response.status_code,
                            "url": url
                        }
                    )
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="http_service",
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP service check failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    @staticmethod
    async def check_kafka(kafka_bootstrap_servers: str) -> HealthCheckResult:
        """Check Kafka connectivity"""
        start_time = time.time()
        
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                request_timeout_ms=5000
            )
            
            # Test connection by getting metadata
            metadata = producer.list_topics(timeout=5000)
            producer.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="kafka",
                status=HealthStatus.HEALTHY,
                message="Kafka connection successful",
                response_time_ms=response_time,
                timestamp=time.time(),
                details={
                    "bootstrap_servers": kafka_bootstrap_servers,
                    "topics_count": len(metadata)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="kafka",
                status=HealthStatus.UNHEALTHY,
                message=f"Kafka connection failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    @staticmethod
    async def check_disk_space(threshold_percent: float = 90.0) -> HealthCheckResult:
        """Check available disk space"""
        start_time = time.time()
        
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            
            response_time = (time.time() - start_time) * 1000
            
            if free_percent < (100 - threshold_percent):
                status = HealthStatus.UNHEALTHY
                message = f"Disk space critically low: {free_percent:.1f}% free"
            elif free_percent < (100 - threshold_percent + 10):
                status = HealthStatus.DEGRADED
                message = f"Disk space low: {free_percent:.1f}% free"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space adequate: {free_percent:.1f}% free"
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=time.time(),
                details={
                    "free_percent": round(free_percent, 2),
                    "free_bytes": free,
                    "total_bytes": total,
                    "threshold_percent": threshold_percent
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk space check failed: {str(e)}",
                response_time_ms=response_time,
                timestamp=time.time()
            )

# Global health checker instance
_health_checker: Optional[HealthChecker] = None

def get_health_checker(service_name: str = None) -> HealthChecker:
    """Get global health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(service_name or os.getenv('SERVICE_NAME', 'unknown'))
    return _health_checker

def setup_default_health_checks(service_name: str = None):
    """Setup default health checks for a service"""
    checker = get_health_checker(service_name)
    
    # Add database check if DATABASE_URL is available
    if os.getenv('DATABASE_URL'):
        checker.add_check(
            'database',
            lambda: HealthChecks.check_database(os.getenv('DATABASE_URL')),
            critical=True
        )
    
    # Add Redis check if REDIS_URL is available
    if os.getenv('REDIS_URL'):
        checker.add_check(
            'redis',
            lambda: HealthChecks.check_redis(os.getenv('REDIS_URL')),
            critical=True
        )
    
    # Add Kafka check if KAFKA_BOOTSTRAP_SERVERS is available
    if os.getenv('KAFKA_BOOTSTRAP_SERVERS'):
        checker.add_check(
            'kafka',
            lambda: HealthChecks.check_kafka(os.getenv('KAFKA_BOOTSTRAP_SERVERS')),
            critical=False
        )
    
    # Add disk space check
    checker.add_check(
        'disk_space',
        lambda: HealthChecks.check_disk_space(),
        critical=False
    )
    
    return checker
