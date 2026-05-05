package com.example.api_gateway.model

enum class JobStatus {
    pending,//Ожидает начала обработки
    processing,//В процессе обработки
    completed,//Успешно завершена
    failed,//Завершена с ошибкой
    cancelled//Отменена пользователем
}