# HDX Converter

A modular tool for converting HDX documentation to multiple formats (TXT, MD, JSON) with comprehensive metadata extraction.

## Features

- Extracts content from HDX (HTML) files
- Preserves internal links and navigation
- Generates structured metadata in JSON format (schema 1.2)
- Converts to multiple formats: TXT, Markdown, HTML backup
- Validates metadata completeness
- Handles images and tables
- Provides detailed statistics and reporting
- Modular architecture for easy extension

## Установка

### Создание и активация виртуального окружения
```bash
# Перейдите в директорию проекта
cd /path/to/rag-soc-core/services/rag-soc-converter

# Создание виртуального окружения
python3 -m venv venv_converter

# Активация виртуального окружения
# Для Windows (GitBash):
. venv_converter/Scripts/activate
```

### Установка зависимостей
```bash
# Убедитесь, что виртуальное окружение активировано
# В командной строке должно быть (venv_converter)

# Установка зависимостей
pip install fastapi uvicorn kafka-python prometheus-client

# Для работы с S3 (если нужно)
pip install boto3

# Если есть файл requirements.txt (рекомендованный способ)
pip install -r requirements.txt

pip install -e .
```

### Проверка установки
```bash
# Проверка установленных пакетов
pip list | grep -E "fastapi|uvicorn|kafka|prometheus"

# Ожидаемый вывод:
# fastapi              0.104.0
# kafka-python         2.0.2
# prometheus-client    0.19.0
# uvicorn              0.24.0
```

### Сборка контейнера
```bash
# Создание директорий для данных
mkdir -p /tmp/converter_input /tmp/converter_output

# Сборка образа
docker build -t rag-soc-converter:1.0.8 .
```

## Запуск API сервера

### Вариант 1: Минимальный запуск (без Kafka)
```bash
# Из корневой директории проекта
python -m hdx_converter.cli api --host 0.0.0.0 --port 8080
```

### Вариант 2: С указанием уровня логирования
```bash
# DEBUG режим для отладки
python -m hdx_converter.cli api --host 0.0.0.0 --port 8080 --log-level 3
```

### Вариант 3: С включенной Kafka интеграцией
```bash
# С локальным Kafka
python -m hdx_converter.cli api \
  --host 0.0.0.0 \
  --port 8080 \
  --kafka-enabled \
  --kafka-bootstrap-servers localhost:9092 \
  --log-level 3
```

### Вариант 4: В docker с выключенной Kafka
```bash
# Запуск контейнера
docker run -d \
  --name rag-soc-converter \
  -p 8080:8080 \
  -v /tmp/converter_input:/data/input:ro \
  -v /tmp/converter_output:/data/output \
  -e KAFKA_ENABLED=false \
  rag-soc-converter:1.0.8

# Просмотр логов
docker logs rag-soc-converter

# Остановка
docker stop rag-soc-converter 2>/dev/null || true

# Удаление
docker rm rag-soc-converter 2>/dev/null || true
docker rmi rag-soc-converter:1.0.8 2>/dev/null || true
```

### Вариант 5: Через docker compose c выключенной Kafka (рекомендованный способ)
```bash
# Запуск в фоне
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart
```

## Ручное развертывание в тестовой среде (Kubernetes)


### **Шаг 1. Клонирование репозитория на сервер**

```bash
cd ~
git clone https://github.com/alexeit-315/rag-soc-core.git
cd rag-soc-core
```

Убедитесь, что Dockerfile находится в подкаталоге `rag-soc-converter`:

```bash
ls -la services/rag-soc-converter/
```

Должен быть файл `Dockerfile`.

---

### **Шаг 2. Сборка Docker-образа локально**

Перейдите в директорию с Dockerfile и соберите образ:

```bash
cd services/rag-soc-converter
docker build -t rag-soc-converter:test .
```

Процесс займет несколько минут (будет скачиваться Python-образ и зависимости из `requirements.txt`).

После сборки проверьте:

```bash
docker images | grep rag-soc-converter
```

---

### **Шаг 3. Загрузка образа в kind-кластер**

**Важно:** чтобы узнать имя текущего кластера:

```bash
kind get clusters
```

kind не использует Docker-демон напрямую для запуска pods. Образ нужно загрузить в kind (для кластера rag-test):

```bash
kind load docker-image rag-soc-converter:test --name rag-test
```

---

### **Шаг 4. Создание PV и PVC**

#### 💾 4.1. PV (kind-aware local disk)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: converter-pv
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  storageClassName: local-hdd
  persistentVolumeReclaimPolicy: Retain
  local:
    path: /mnt/data/converter
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - rag-test-worker
EOF
```

#### 💾 4.2 Создание каталога на ноде (kind-aware local disk)
```bash
kubectl run --restart=Never --image=busybox converter-dir -n data-infra --overrides='
{
  "spec": {
    "nodeName": "rag-test-worker",
    "containers": [{
      "name": "creator",
      "image": "busybox",
      "command": ["sh", "-c", "mkdir -p /mnt/data/converter && chmod 777 /mnt/data/converter && echo done"]
    }],
    "restartPolicy": "Never"
  }
}'
```

#### 💾 4.3 Создание каталога на хосте

```bash
# Создание директории на хосте для Converter
sudo mkdir -p /mnt/data/k8s-storage/converter
sudo chmod 777 /mnt/data/k8s-storage/converter
```

---

#### 💾 4.4 Создание файла `converter-pvc.yaml`:

```bash
cat <<EOF > converter-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rag-converter-storage
  namespace: data-plane
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-hdd
  resources:
    requests:
      storage: 100Gi
  volumeName: converter-pv
EOF
```

Применение:

```bash
kubectl apply -f converter-pvc.yaml
```

Проверка:

```bash
kubectl get pv
kubectl get pvc -n data-plane
```

Статус должен быть `Bound`.

---

### **Шаг 5. Создание Deployment для сервиса**

Создайте файл `converter-deployment.yaml` с двумя вариантами параметризации (выберите один — я покажу оба):

#### **Вариант А: через аргументы командной строки (без args, запускаем по умолчанию)**

```bash
cat <<EOF > converter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-soc-converter
  namespace: data-plane
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rag-soc-converter
  template:
    metadata:
      labels:
        app: rag-soc-converter
    spec:
      nodeSelector:
        kubernetes.io/hostname: rag-test-worker
      tolerations:
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      containers:
      - name: converter
        image: rag-soc-converter:test
        imagePullPolicy: IfNotPresent
        # Не передаем args — используем CMD из Dockerfile
        # Dockerfile CMD: ["hdx-converter-api", "--host", "0.0.0.0", "--port", "8080"]
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1"
            memory: "2Gi"
        volumeMounts:
        - name: storage
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: rag-converter-storage
EOF
```
#### **Вариант Б: через переменные окружения (env)**

Если сервис поддерживает env-переменные (например, `CONVERTER_HOST`, `CONVERTER_PORT`), используйте этот вариант:

```bash
cat <<EOF > converter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-soc-converter
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rag-soc-converter
  template:
    metadata:
      labels:
        app: rag-soc-converter
    spec:
      nodeSelector:
        kubernetes.io/hostname: rag-test-worker
      containers:
      - name: converter
        image: rag-soc-converter:test
        imagePullPolicy: IfNotPresent
        env:
        - name: CONVERTER_HOST
          value: "0.0.0.0"
        - name: CONVERTER_PORT
          value: "8080"
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1"
            memory: "2Gi"
        volumeMounts:
        - name: storage
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: rag-converter-storage
EOF
```

**Примените выбранный вариант:**

```bash
kubectl apply -f converter-deployment.yaml
```

---

### **Шаг 6. Создание Service для доступа с хоста и по сети**

Создайте файл `service.yaml` (NodePort для доступа с хоста):

```bash
cat <<EOF > converter-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-soc-converter-svc
  namespace: data-plane
spec:
  type: NodePort
  selector:
    app: rag-soc-converter
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30081
    protocol: TCP
EOF
```

Примените:

```bash
kubectl apply -f converter-service.yaml
```

---

### **Шаг 7. Проверка состояния развертывания**

```bash
kubectl get pods -n data-plane
kubectl get deployments -n data-plane
kubectl get svc -n data-plane
kubectl get pvc -n data-plane
```

Дождитесь, пока pod перейдет в статус `Running`:

```bash
kubectl wait --for=condition=ready pod -l app=rag-soc-converter --timeout=120s
```

---

### **Шаг 8. Проверка работоспособности сервиса**

#### **Проверка через localhost (с хоста)**

```bash
curl -v http://localhost:30080/health
```

Ожидаемый ответ: HTTP 200, JSON `{"status": "healthy", "version": "1.0.0", "components": {}}`

```bash
curl -v http://localhost:30080/ready
```

Ожидаемый ответ: HTTP 200, JSON `{"ready": true, "checks": {...}}` или `503`, если зависимости не готовы (в тестовой среде без Kafka/S3 это нормально).

#### **Проверка метрик**

```bash
curl http://localhost:30080/metrics
```

Должен вернуться текст в формате Prometheus.

#### **Проверка API конвертации (опционально)**

```bash
curl -X POST http://localhost:30080/convert \
  -H "Content-Type: application/json" \
  -d '{"source_uri": "file:///data/test.hdx", "log_level": 2}'
```

Ожидается HTTP 202 и `job_id`.

---

### **Шаг 9. Просмотр логов (при необходимости)**

```bash
kubectl logs -l app=rag-soc-converter -n data-plane --tail=50
```

---

## **Итог**

Сервис `rag-soc-converter` должен быть:
- Запущен в существующем kind-кластере
- Доступен по адресу `http://<IP_сервера>:30080` или `http://localhost:30080`
- С PVC 100 ГБ
- С лимитами CPU 1, RAM 2 ГБ
- С liveness и readiness probes

---

**Если на каком-то шаге возникает ошибка — остановитесь, скопируйте вывод терминала и покажите мне.**



## Тестирование

### Проверка работоспособности

В другом терминале выполните проверку

```bash
# Проверка health
curl http://localhost:8080/health

# Ожидаемый ответ:
# {"status":"healthy","version":"1.0.0","components":{}}

# Проверка ready
curl http://localhost:8080/ready

# Ожидаемый ответ:
# {"ready":true,"checks":{"object_storage":true,"kafka":true}}

# Проверка OpenAPI документации
# Откройте в браузере: http://localhost:8080/docs
```

### Тестирование API

#### Запуск конвертации

```bash
# Создайте тестовый HDX файл или используйте существующий
# Запустите конвертацию
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source_uri": "../../source/HiSecEngine_USG6000F_V600R024C10_04_en_AEP01098.hdx",
    "output_uri": "../../../../output",
    "log_level": 2
  }'
```

Ожидаемый вывод:

``` json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "source_uri": "/path/to/your/test.hdx",
  "output_uri": "/path/to/output",
  "created_at": "2024-03-27T10:00:00Z"
}
```


#### Проверка статуса задачи

```bash
# Замените JOB_ID на полученный из предыдущего ответа
curl http://localhost:8080/api/v1/convert/JOB_ID/status
```

#### Получение списка задач

```bash
# Все задачи
curl http://localhost:8080/api/v1/convert

# Только завершенные
curl "http://localhost:8080/api/v1/convert?status=completed"

# С пагинацией
curl "http://localhost:8080/api/v1/convert?limit=10&offset=0"
```


