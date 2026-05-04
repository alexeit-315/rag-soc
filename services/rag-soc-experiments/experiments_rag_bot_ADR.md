## ADR Experimentation Service 


### **Функциональные требования**

Верхнеуровневые Use Cases.

| **№** | **Действующие лица или системы** | **Use Case** | **Описание** |
|:-----:|:--------------------------------|:-------------|:-------------|
| UC1 | ML Engineer, API Gateway, Experimentation Service, SQL Database | Проведение тестирования моделей на предоставленных данных | 1. ML Engineer авторизуется через API Gateway;<br/>2. ML Engineer загружает документы в папку через API Gateway;<br/>3. API Gateway отправляет webhook в Experimentation Service с метаданными (путь к папке);<br/>4. Experimentation Service читает данные из папки, обрабатывает и удаляет;<br/>5. Experimentation Service сохраняет метаданные эксперимента в SQL БД;<br/>6. Experimentation Service выдает ML Engineer Quality test оценки запрошенных моделей, дообученных на предоставленных данных. |

---

### **Нефункциональные требования**

Нефункциональные и архитектурно значимые требования.

| **№** | **Требование** |
|:-----:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Многоязычность. Система должна подсказывать пользователю наиболее подходящие для работы модели на основе языка, используемого в предоставленных документах. |
| 2 | Система должна указывать степень уверенности в ответе (confidence). |
| 3 | Система должна поддерживать экспорт результатов обработки в структурированном формате (JSON/CSV). |
| 4 | Система должна поддерживать настраиваемые стратегии чанкинга (size, overlap, semantic chunking). |
| 5 | Система должна предоставлять возможность выбирать модель для дообучения. |
| 6 | Система должна предоставлять информационные данные для анализа результатов обучения, реализуя раздельно и в комбинации гибридный и контекстный поиск для полноты картины. |
| 7 | Система должна предоставлять возможность перепровести эксперимент. |
| 8 | Система должна иметь сопровождающую документацию. |
| 9 | Система должна выдавать пользователю только те результаты экспериментов, к которым у него есть доступ. |

---

### **Решение**

#### Механизм передачи данных

1. ML Engineer через API Gateway загружает данные запроса в папку (Object Storage / NFS)
2. API Gateway отправляет webhook в Experimentation Service с метаданными (путь к папке, experiment_id, user_id)
3. Experimentation Service читает данные из папки
4. Experimentation Service обрабатывает данные
5. Experimentation Service удаляет данные из папки

#### Webhook от API Gateway

```json
{
  "experiment_id": "exp_20260422_001",
  "data_path": "/data/experiments/exp_20260422_001/",
  "timestamp": "2026-04-22T10:00:00Z",
  "user_id": "ml_engineer@company.com"
}
```

#### JSON схема запроса (хранится в папке как request.json)

```json
{
  "experiment_name": "Сравнение эмбеддеров на финансовых документах",
  "documents": ["документ1.pdf", "документ2.pdf"],
  "test_data": [
    {"query": "вопрос 1", "expected_answer": "ответ 1"},
    {"query": "вопрос 2", "expected_answer": "ответ 2"}
  ],
  "language": "ru",
  "model_id": "rubert-base",
  "chunking_config": {
    "strategy": "semantic",
    "size": 512,
    "overlap": 50
  },
  "search_modes": ["vector_only", "hybrid"]
}
```

#### Описание полей запроса

| Поле | Тип | Описание | Связанное требование |
|------|-----|----------|---------------------|
| experiment_name | string | Название эксперимента | |
| documents | array | Список документов для дообучения | |
| test_data | array | Тестовая выборка с ожидаемыми ответами | |
| language | string | Язык документов (ru/en/cn) | №1 |
| model_id | string | Выбранная модель для дообучения | №5 |
| chunking_config.strategy | string | Стратегия чанкинга (simple/semantic) | №4 |
| chunking_config.size | int | Размер чанка | №4 |
| chunking_config.overlap | int | Перекрытие между чанками | №4 |
| search_modes | array | Режимы поиска (vector_only / hybrid) | №6 |

#### Детектирование языка и подсказка моделей (требование №1)

Перед основным запросом ML Engineer может отправить документы для определения языка(???):

```
ML Engineer → API Gateway → Experimentation Service (документы)
Experimentation Service → ML Engineer (наиболее подходящие модели)
ML Engineer → API Gateway → Experimentation Service (необходимые параметры с выбранной моделью)
```

#### Формат ответа (требования №2, №3, №6)

```json
{
  "experiment_id": "exp_20260422_001",
  "status": "completed",
  "results": {
    "vector_only": {
      "f1": 0.87,
      "precision": 0.85,
      "recall": 0.89,
      "confidence": 0.92
    },
    "hybrid": {
      "f1": 0.92,
      "precision": 0.91,
      "recall": 0.93,
      "confidence": 0.95
    }
  },
  "metadata": {
    "experiment_name": "Сравнение эмбеддеров на финансовых документах",
    "model_id": "rubert-base",
    "chunking_strategy": "semantic",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "documents_count": 2,
    "user_id": "ml_engineer@company.com",
    "created_at": "2026-04-22T10:00:00Z"
  },
  "export_urls": {
    "json": "/api/v1/experiments/exp_20260422_001/export?format=json",
    "csv": "/api/v1/experiments/exp_20260422_001/export?format=csv"
  }
}
```

#### Вызовы API в RAG Orchestrator (Data Plane)

Experimentation Service вызывает RAG Orchestrator (Data Plane) для выполнения RAG пайплайна:

```json
POST /api/v1/rag/execute
{
  "experiment_id": "exp_20260422_001",
  "queries": [...],  // из test_data
  "documents": [...],  // из запроса
  "model_id": "rubert-base",
  "chunking_config": {
    "strategy": "semantic",
    "size": 512,
    "overlap": 50
  },
  "search_modes": ["vector_only", "hybrid"]
}
```

RAG Orchestrator (Data Plane) в свою очередь обращается к:
- **Search Service** (гибридный поиск: semantic + BM25)
- **Reranker** (переранжирование)
- **Generator** (генерация ответа через Inference Gateway)
- **Vector DB** (хранение и поиск эмбеддингов)

#### Вызовы API в Vector DB

Experimentation Service вызывает Vector DB для сохранения индексов:

```json
PUT /collections/exp_20260422_001/points
{
  "points": [
    {
      "id": "chunk_001",
      "vector": [0.1, 0.2, ...],
      "payload": {
        "text": "содержимое чанка",
        "metadata": {
          "source": "document1.pdf",
          "chunk_index": 0
        }
      }
    }
  ]
}
```

#### Эндпоинты Experimentation Service

| Метод | Эндпоинт | Описание | Требования |
|-------|----------|----------|------------|
| POST | `/api/v1/experiments/detect-language` | Определение языка и подсказка моделей | №1 |
| POST | `/api/v1/experiments/run` | Запуск эксперимента (webhook + данные из папки) | UC1 |
| GET | `/api/v1/experiments/` | Список своих экспериментов | №9 |
| GET | `/api/v1/experiments/{id}` | Детали своего эксперимента | №9 |
| POST | `/api/v1/experiments/{id}/rerun` | Перезапуск своего эксперимента | №7 |
| GET | `/api/v1/experiments/{id}/export` | Экспорт результатов (JSON/CSV) | №3 |

#### Хранение метаданных (SQL БД)

| Поле | Тип | Описание |
|------|-----|----------|
| experiment_id | string (PK) | Уникальный идентификатор |
| user_id | string | Владелец эксперимента |
| experiment_name | string | Название |
| model_id | string | Использованная модель |
| chunking_strategy | string | Стратегия чанкинга |
| chunking_size | int | Размер чанка |
| chunking_overlap | int | Перекрытие |
| documents_count | int | Количество документов |
| status | string | completed / failed / running |
| results_vector_only | json | Результаты vector_only поиска |
| results_hybrid | json | Результаты hybrid поиска |
| created_at | timestamp | Дата создания |
| updated_at | timestamp | Дата обновления |

#### Схема последовательности вызовов

```
1. ML Engineer → API Gateway (загрузка данных в папку)
2. API Gateway → Experimentation Service (webhook)
3. Experimentation Service → Object Storage (чтение request.json из папки)
4. Experimentation Service → SQL БД (сохранение метаданных)
5. Experimentation Service → RAG Orchestrator (выполнение RAG пайплайна)
   RAG Orchestrator → Vector DB (поиск/сохранение эмбеддингов)
   RAG Orchestrator → Search Service (гибридный поиск)
   RAG Orchestrator → Reranker (переранжирование)
   RAG Orchestrator → Generator (генерация ответа)
6. Experimentation Service → SQL БД (сохранение результатов)
7. Experimentation Service → Object Storage (удаление папки с данными)
8. Experimentation Service → ML Engineer (возврат результатов)
```

---

### **Недостатки, ограничения, риски**

| № | Описание |
|:--:|:---------|
| 1 | Зависимость от Object Storage. При недоступности хранилища эксперимент не может быть выполнен. |
| 2 | Webhook требует тонкой настройки. |

---

### **Swagger**

Документация API доступна по адресу:
```
http://localhost:8001/api/v1/experiments/docs
```

## API Experimentation Service (через webhook)

### Базовый URL
```
http://localhost:8001/api/v1/experiments
```

---

### 1. Запуск эксперимента (через webhook)

| Параметр | Значение |
|----------|----------|
| **Метод** | `POST` |
| **Эндпоинт** | `/run` |
| **Полный URL** | `http://localhost:8001/api/v1/experiments/run` |
| **Заголовок** | `X-User-Id: string` |

**Webhook от API Gateway:**
```json
{
  "experiment_id": "exp_20260422_001",
  "data_path": "/data/experiments/exp_20260422_001/",
  "timestamp": "2026-04-22T10:00:00Z",
  "user_id": "ml_engineer@company.com"
}
```

**После получения webhook Experimentation Service:**
1. Читает `request.json` из папки `data_path`
2. Обрабатывает эксперимент
3. Удаляет папку с данными

**Структура `request.json` в папке:**
```json
{
  "experiment_name": "Сравнение эмбеддеров на финансовых документах",
  "documents": ["документ1.pdf", "документ2.pdf"],
  "test_data": [
    {"query": "вопрос 1", "expected_answer": "ответ 1"},
    {"query": "вопрос 2", "expected_answer": "ответ 2"}
  ],
  "language": "ru",
  "model_id": "rubert-base",
  "chunking_config": {
    "strategy": "semantic",
    "size": 512,
    "overlap": 50
  },
  "search_modes": ["vector_only", "hybrid"]
}
```

**Response:**
```json
{
  "experiment_id": "exp_001",
  "status": "completed",
  "results": {
    "vector_search": {"f1": 0.87, "confidence": 0.92},
    "hybrid_search": {"f1": 0.92, "confidence": 0.95}
  },
  "metadata": {
    "experiment_name": "string",
    "model_id": "string",
    "user_id": "string"
  }
}
```

---

### 2. Список экспериментов

| Параметр | Значение |
|----------|----------|
| **Метод** | `GET` |
| **Эндпоинт** | `/` |
| **Полный URL** | `http://localhost:8001/api/v1/experiments/` |
| **Заголовок** | `X-User-Id: string` |
| **Query параметры** | `skip` (int, default: 0), `limit` (int, default: 20) |

**Response:**
```json
{
  "total": 3,
  "skip": 0,
  "limit": 20,
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
```

---

### 3. Детали эксперимента

| Параметр | Значение |
|----------|----------|
| **Метод** | `GET` |
| **Эндпоинт** | `/{experiment_id}` |
| **Полный URL** | `http://localhost:8001/api/v1/experiments/{experiment_id}` |
| **Заголовок** | `X-User-Id: string` |

**Response:**
```json
{
  "experiment_id": "exp_001",
  "metadata": {
    "experiment_name": "Тест модели A",
    "model_id": "rubert-base",
    "user_id": "string",
    "created_at": "2026-03-30T10:00:00"
  },
  "results": {
    "vector_search": {"f1": 0.87, "confidence": 0.92},
    "hybrid_search": {"f1": 0.92, "confidence": 0.95}
  }
}
```

---

### 4. Перезапуск эксперимента

| Параметр | Значение |
|----------|----------|
| **Метод** | `POST` |
| **Эндпоинт** | `/{experiment_id}/rerun` |
| **Полный URL** | `http://localhost:8001/api/v1/experiments/{experiment_id}/rerun` |
| **Заголовок** | `X-User-Id: string` |

**Response:**
```json
{
  "original_experiment_id": "exp_001",
  "new_experiment_id": "exp_001_rerun_001",
  "status": "completed",
  "results": {
    "vector_search": {"f1": 0.88, "confidence": 0.93},
    "hybrid_search": {"f1": 0.93, "confidence": 0.96}
  }
}
```

---

### 5. Health check

| Параметр | Значение |
|----------|----------|
| **Метод** | `GET` |
| **Эндпоинт** | `/health` |
| **Полный URL** | `http://localhost:8002/health` |

**Response:**
```json
{"status": "alive"}
```

---

### 6. Ready check

| Параметр | Значение |
|----------|----------|
| **Метод** | `GET` |
| **Эндпоинт** | `/ready` |
| **Полный URL** | `http://localhost:8002/ready` |

**Response (200):**
```json
{
  "ready": true,
  "checks": {
    "database": {"ready": true, "error": null},
    "model": {"ready": true, "error": null},
    "kafka": {"ready": true, "error": null}
  }
}
```

---

## Сводная таблица

| Сервис | Метод | Эндпоинт | Порт | Примечание |
|--------|-------|----------|------|------------|
| Conversion | POST | `/api/v1/experiments/run` | 8001 | Webhook + данные из папки |
| Conversion | GET | `/api/v1/experiments/` | 8001 | Список экспериментов |
| Conversion | GET | `/api/v1/experiments/{experiment_id}` | 8001 | Детали эксперимента |
| Conversion | POST | `/api/v1/experiments/{experiment_id}/rerun` | 8001 | Перезапуск |
| System | GET | `/health` | 8002 | Liveness probe |
| System | GET | `/ready` | 8002 | Readiness probe |

curl.exe http://localhost:8001/api/v1/experiments/ -H "X-User-Id: test"

curl.exe http://localhost:8002/health