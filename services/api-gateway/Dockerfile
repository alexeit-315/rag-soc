# Используем официальный образ OpenJDK 17
FROM openjdk:17-jdk-slim

# Устанавливаем working directory в контейнере
WORKDIR /app

# Копируем jar файл с конкретным именем
COPY build/libs/API_Gateway-0.0.1-SNAPSHOT.jar app.jar

# Экспортируем порт, на котором будет работать API Gateway
EXPOSE 8080

# Устанавливаем environment variables
ENV JAVA_OPTS="-Xmx512m -Xms256m -Djava.security.egd=file:/dev/./urandom"

# Запускаем приложение
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# Альтернативный способ запуска:
# ENTRYPOINT ["java", "-jar", "/app/app.jar"]