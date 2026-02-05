# Face Recognition System Integration

This document provides instructions for setting up and running the Face Recognition application using Docker. The application consists of three main components: the backend service, the frontend application, and the edge detection module. Each component is designed to work together seamlessly to provide real-time face recognition capabilities.

## Project Structure

The project is organized as follows:

```
face-recognition-system
├── backend                # Spring Boot backend service
├── frontend               # React frontend application
├── edge-module            # Edge detection module
└── integration            # Docker integration setup
```

## Prerequisites

Before you begin, ensure you have the following installed:

- Docker
- Docker Compose

## Setup Instructions

1. **Clone the Repository**

   Clone the repository to your local machine:

   ```bash
   git clone <repository-url>
   cd face-recognition-system
   ```

2. **Configure Environment Variables**

   Update the `.env` file in the `integration` directory with the necessary environment variables, such as database connection details and any other configuration required for your setup.

3. **Build and Run the Application**

   Navigate to the `integration` directory and use Docker Compose to build and run the application:

   ```bash
   cd integration
   docker-compose up --build
   ```

   This command will start all services defined in the `docker-compose.yml` file, including the backend, frontend, and edge detection module.

4. **Access the Application**

   Once the services are running, you can access the frontend application in your web browser at:

   ```
   http://localhost:3000
   ```

   The backend API will be available at:

   ```
   http://localhost:8080/api
   ```

## Stopping the Application

To stop the application, you can use the following command in the `integration` directory:

```bash
docker-compose down
```

This will stop and remove all running containers.

## Troubleshooting

- Ensure that Docker is running and that you have sufficient permissions to run Docker commands.
- Check the logs of individual services for any errors. You can view logs using:

  ```bash
  docker-compose logs <service-name>
  ```

## Conclusion

This integration setup allows you to run the Face Recognition application in a containerized environment, making it easier to manage dependencies and configurations. For further details on each component, refer to their respective README files in the `backend`, `frontend`, and `edge-module` directories.