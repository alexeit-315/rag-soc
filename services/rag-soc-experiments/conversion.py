from fastapi import FastAPI, Header, Request, Response
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging
import time
import uuid

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================

# Базовая конфигурация логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Создаём логгер для сервиса
logger = logging.getLogger("experimentation-service")

# ============================================
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# ============================================

app = FastAPI(
    title="Experimentation Service",
    description="Сервис для тестирования и дообучения моделей",
    version="1.0.0",
    docs_url="/api/v1/experiments/docs",
    redoc_url="/api/v1/experiments/redoc",
    openapi_url="/api/v1/experiments/openapi.json"
)


# ============================================
# MIDDLEWARE ДЛЯ МОНИТОРИНГА
# ============================================

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """
    Middleware для логирования всех запросов и мониторинга времени выполнения
    """
    # Генерируем уникальный ID для каждого запроса (трейсинг)
    request_id = str(uuid.uuid4())[:8]
    
    # Засекаем время начала
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"[{request_id}] → {request.method} {request.url.path}")
    
    # Обрабатываем запрос
    try:
        response = await call_next(request)
        
        # Считаем время выполнения
        process_time = time.time() - start_time
        
        # Добавляем заголовки для мониторинга
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Логируем ответ
        logger.info(
            f"[{request_id}] ← {response.status_code} | "
            f"duration: {process_time:.4f}s | "
            f"size: {len(response.body) if hasattr(response, 'body') else 0}B"
        )
        
        return response
        
    except Exception as e:
        # Логируем ошибку
        logger.error(f"[{request_id}] ✗ Error: {str(e)}")
        raise


# ============================================
# МОДЕЛИ ДАННЫХ
# ============================================

class RunExperimentRequest(BaseModel):
    experiment_name: str
    model_id: str
    documents: List[str]
    test_data: List[Dict[str, str]]

class DetectLanguageRequest(BaseModel):
    documents: List[str]

class DetectLanguageResponse(BaseModel):
    detected_language: str
    recommended_models: List[Dict[str, str]]

class ExportResponse(BaseModel):
    experiment_id: str
    metadata: Dict
    results: Dict
    exported_at: str

# ============================================
# API ЭНДПОИНТЫ
# ============================================

@app.post("/api/v1/experiments/detect-language", response_model=DetectLanguageResponse)
async def detect_language(
    request: DetectLanguageRequest,
    user_id: str = Header(..., alias="X-User-Id")
):
    """
    Определение языка документов и подсказка наиболее подходящих моделей
    Требование №1: Многоязычность
    """
    logger.info(f"User {user_id} запросил определение языка для {len(request.documents)} документов")
    
    # Заглушка: в реальности здесь будет вызов сервиса определения языка
    detected_language = "unknown"
    recommended_models = [
            {"model_id": "multilingual-e5", "description": "Поддерживает 100+ языков (рекомендуется при неизвестном языке)"}
        ]
    
    logger.info(f"Определён язык: {detected_language}, рекомендовано {len(recommended_models)} моделей")
    
    return {
        "detected_language": detected_language,
        "recommended_models": recommended_models
    }

@app.post("/api/v1/experiments/run")
async def run_experiment(
    request: RunExperimentRequest,
    user_id: str = Header(..., alias="X-User-Id")
):
    """Запуск эксперимента"""
    logger.info(f"User {user_id} запустил эксперимент: {request.experiment_name}")
    logger.debug(f"Документов получено: {len(request.documents)}")
    logger.debug(f"Тестовых данных: {len(request.test_data)}")
    
    return {
        "experiment_id": "exp_001",
        "status": "completed",
        "results": {
            "vector_search": {"f1": 0.87, "confidence": 0.92},
            "hybrid_search": {"f1": 0.92, "confidence": 0.95}
        },
        "metadata": {
            "experiment_name": request.experiment_name,
            "model_id": request.model_id,
            "user_id": user_id
        }
    }


@app.get("/api/v1/experiments/")
async def list_experiments(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Header(..., alias="X-User-Id")
):
    """Список экспериментов"""
    logger.info(f"User {user_id} запросил список экспериментов (skip={skip}, limit={limit})")
    
    return {
        "total": 3,
        "skip": skip,
        "limit": limit,
        "experiments": [
            {
                "experiment_id": "exp_001",
                "experiment_name": "Тест модели A",
                "model_id": "rubert-base",
                "status": "completed",
                "created_at": "2026-03-30T10:00:00"
            },
            {
                "experiment_id": "exp_002",
                "experiment_name": "Тест модели B",
                "model_id": "multilingual-e5",
                "status": "completed",
                "created_at": "2026-03-29T15:30:00"
            }
        ]
    }


@app.get("/api/v1/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """Детали эксперимента"""
    logger.info(f"User {user_id} запросил эксперимент {experiment_id}")
    
    return {
        "experiment_id": experiment_id,
        "metadata": {
            "experiment_name": "Тест модели A",
            "model_id": "rubert-base",
            "user_id": user_id,
            "created_at": "2026-03-30T10:00:00"
        },
        "results": {
            "vector_search": {"f1": 0.87, "confidence": 0.92},
            "hybrid_search": {"f1": 0.92, "confidence": 0.95}
        }
    }


@app.post("/api/v1/experiments/{experiment_id}/rerun")
async def rerun_experiment(
    experiment_id: str,
    user_id: str = Header(..., alias="X-User-Id")
):
    """Перезапуск эксперимента"""
    logger.info(f"User {user_id} перезапускает эксперимент {experiment_id}")
    
    return {
        "original_experiment_id": experiment_id,
        "new_experiment_id": f"{experiment_id}_rerun_001",
        "status": "completed",
        "results": {
            "vector_search": {"f1": 0.88, "confidence": 0.93},
            "hybrid_search": {"f1": 0.93, "confidence": 0.96}
        }
    }

@app.get("/api/v1/experiments/{experiment_id}/export")
async def export_experiment(
    experiment_id: str,
    format: str = "json",
    user_id: str = Header(..., alias="X-User-Id")
):
    """
    Экспорт результатов эксперимента в JSON или CSV формате
    Требование №3: поддержка экспорта в структурированном формате
    """
    logger.info(f"User {user_id} экспортирует эксперимент {experiment_id} в формате {format}")
    
    export_data = {
        "experiment_id": experiment_id,
        "metadata": {
            "experiment_name": "Тест модели A" if experiment_id == "exp_001" else "Тест модели B",
            "model_id": "rubert-base" if experiment_id == "exp_001" else "multilingual-e5",
            "user_id": user_id,
            "created_at": "2026-03-30T10:00:00" if experiment_id == "exp_001" else "2026-03-29T15:30:00"
        },
        "results": {
            "vector_search": {"f1": 0.87, "confidence": 0.92},
            "hybrid_search": {"f1": 0.92, "confidence": 0.95}
        },
        "exported_at": datetime.now().isoformat()
    }
    
    if format.lower() == "csv":
        # Заглушка для CSV
        csv_content = (
            "experiment_id,experiment_name,model_id,vector_f1,vector_confidence,hybrid_f1,hybrid_confidence\n"
            f"{export_data['experiment_id']},{export_data['metadata']['experiment_name']},"
            f"{export_data['metadata']['model_id']},0.87,0.92,0.92,0.95"
        )
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={experiment_id}.csv"}
        )
    
    # По умолчанию JSON
    return export_data

