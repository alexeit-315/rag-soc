package com.example.api_gateway.model

enum class HealthStatus {
    healthy,// Все компоненты работают
    degraded,// Часть компонентов недоступна, но сервис работает
    unhealthy// Сервис не может обрабатывать запросы
}