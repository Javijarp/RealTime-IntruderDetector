# Stage 1: Build the Spring Boot backend
FROM gradle:8.14-jdk21 as builder

WORKDIR /build

# Copy the entire project
COPY . .

# Build the application
RUN gradle build -x test

# Stage 2: Runtime image
FROM eclipse-temurin:21-jdk-alpine

WORKDIR /app

# Copy the built JAR from builder stage
COPY --from=builder /build/build/libs/*.jar /app/

EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "/app/security-backend-0.0.1-SNAPSHOT.jar"]
