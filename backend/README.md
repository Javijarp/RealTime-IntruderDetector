# README for Backend Service

# Face Recognition System - Backend

This is the backend service for the Face Recognition System, built using Spring Boot. It handles HTTP requests related to detection events and provides the necessary business logic for processing these events.

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Configuration](#configuration)
- [Logging](#logging)
- [License](#license)

## Getting Started

To get started with the backend service, follow the instructions below to set up your development environment.

## Prerequisites

- Java 11 or higher
- Maven 3.6 or higher
- An IDE (e.g., IntelliJ IDEA, Eclipse) for Java development

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/face-recognition-system.git
   ```

2. Navigate to the backend directory:
   ```
   cd face-recognition-system/backend
   ```

3. Install the dependencies:
   ```
   mvn install
   ```

## Running the Application

To run the application, use the following command:
```
mvn spring-boot:run
```

The application will start on `http://localhost:8080`.

## API Endpoints

- **POST /api/events**: Create a new detection event.
- **GET /api/events**: Retrieve all detection events.

Refer to the `EventController.java` for more details on the API endpoints.

## Testing

Unit tests are located in the `src/test/java/com/unibe/service` directory. To run the tests, use the following command:
```
mvn test
```

## Configuration

Configuration properties can be found in `src/main/resources/application.properties`. Update the database connection settings as needed.

## Logging

Logging is configured using Logback. The configuration file is located at `src/main/resources/logback.xml`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.