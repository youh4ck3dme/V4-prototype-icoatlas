"""
Circuit Breaker pre externé registre (RÚZ, FS, ARES, KRS, ...).

Prenesené z backend_legacy_20251229_195800/services/circuit_breaker.py
(rovnaké stavy a prahy), doplnené o async volanie `acall` pre httpx.
"""
import logging
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger("uvicorn.error")


class CircuitState(Enum):
    CLOSED = "closed"        # požiadavky prechádzajú
    OPEN = "open"            # požiadavky sú blokované
    HALF_OPEN = "half_open"  # skúšobné požiadavky po recovery_timeout


class CircuitBreakerOpenError(Exception):
    """Circuit je otvorený, volanie sa neuskutočnilo."""


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60,
        expected_exception: type = Exception,
        name: str = "default",
        clock: Callable[[], float] = time.monotonic,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        self._clock = clock

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self.half_open_success_threshold = 2

    def _before_call(self) -> None:
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")

    def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        self._before_call()
        try:
            result = func(*args, **kwargs)
        except self.expected_exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    async def acall(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        self._before_call()
        try:
            result = await func(*args, **kwargs)
        except self.expected_exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return (self._clock() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker '%s' CLOSED (recovered)", self.name)
        else:
            self.failure_count = 0

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = self._clock()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning("Circuit breaker '%s' OPEN (failed in half-open)", self.name)
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker '%s' OPEN (threshold %s reached)", self.name, self.failure_count)

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    def reset(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name, **kwargs)
    return _breakers[name]


def get_all_breakers() -> Dict[str, Dict[str, Any]]:
    return {name: b.get_state() for name, b in _breakers.items()}


def reset_all_breakers() -> None:
    for b in _breakers.values():
        b.reset()
