from fastapi import FastAPI, Response
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

app = FastAPI()

# ---- Вспомогательные функции для проверки зависимостей ----
async def check_database() -> tuple[bool, str]:
    """
    Проверяет, что SQL БД доступна.
    """
    try:
        # Тут проверка соединения с PostgreSQL :р
        return True, "ok"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False, str(e)

async def check_model() -> tuple[bool, str]:
    """
    Проверяет, что ML модель загружена и готова.
    """
    try:
        # Тут проверка соединения с моделью :р
        return True, "ok"
    except Exception as e:
        logger.error(f"Model check failed: {e}")
        return False, str(e)

async def check_kafka() -> tuple[bool, str]:
    """
    Проверяет, что Kafka доступна.
    """
    try:
        # Тут проверка соединения с Kafka :р
        return True, "ok"
    except Exception as e:
        logger.error(f"Kafka check failed: {e}")
        return False, str(e)

# ---- Эндпоинты для проверок ----
@app.get("/health")
async def health():
    """
    Liveness probe - проверяет, что процесс жив.
    """
    return {"status": "alive"}


class CachedChecker:
    """Кэширует результаты проверок на определённое время"""
    
    def __init__(self, ttl_seconds: int = 10):
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, tuple[bool, str, datetime]] = {}
    
    async def check(self, name: str, check_func) -> tuple[bool, str]:
        """Возвращает кэшированный результат, если он ещё свежий"""
        now = datetime.now()
        
        if name in self._cache:
            result, error, timestamp = self._cache[name]
            if now - timestamp < self.ttl:
                return result, error
        
        # Выполняем реальную проверку
        result, error = await check_func()
        self._cache[name] = (result, error, now)
        return result, error

# Создаём проверяльщик с TTL 10 секунд
checker = CachedChecker(ttl_seconds=10)

@app.get("/ready")
async def ready(response: Response):
    """
    Readiness probe с кэшированием результатов на 10 секунд.
    """
    db_ok, db_error = await checker.check("database", check_database)
    model_ok, model_error = await checker.check("model", check_model)
    kafka_ok, kafka_error = await checker.check("kafka", check_kafka)
    
    checks = {
        "database": {"ready": db_ok, "error": db_error if not db_ok else None},
        "model": {"ready": model_ok, "error": model_error if not model_ok else None},
        "kafka": {"ready": kafka_ok, "error": kafka_error if not kafka_ok else None}
    }
    
    ready = all([db_ok, model_ok, kafka_ok])

    status_code = 200 if ready else 503
    
    return Response(
        content=f'{{"ready": {str(ready).lower()}, "checks": {_format_checks(checks)}}}',
        status_code=status_code,
        media_type="application/json"
    )
    
def _format_checks(checks: Dict[str, dict]) -> str:
    """Форматирование checks для JSON ответа."""
    items = []
    for k, v in checks.items():
        items.append(f'"{k}": {{"ready": {str(v["ready"]).lower()}, "error": {v["error"] if v["error"] else "null"}}}')
    return "{" + ", ".join(items) + "}"