# Face Recognition System

This project is a comprehensive Face Recognition application that integrates an edge detection module, a backend service built with Spring Boot, and a frontend interface developed with React. The system is designed to capture, process, and display detection events in real-time.

## Project Structure

```
face-recognition-system
├── backend                # Spring Boot backend service
│   ├── src
│   │   ├── main
│   │   │   ├── java
│   │   │   │   └── com
│   │   │   │       └── unibe
│   │   │   │           ├── controller        # Handles HTTP requests
│   │   │   │           ├── service           # Business logic
│   │   │   │           ├── model             # Data models
│   │   │   │           ├── repository         # Database access
│   │   │   │           └── Application.java   # Main entry point
│   │   │   └── resources
│   │   │       ├── application.properties      # Configuration settings
│   │   │       └── logback.xml                # Logging configuration
│   │   └── test
│   │       └── java
│   │           └── com
│   │               └── unibe
│   │                   └── service             # Unit tests
│   ├── pom.xml                                 # Maven configuration
│   └── README.md                               # Backend documentation
├── frontend               # React frontend application
│   ├── public
│   │   └── index.html                           # Main HTML file
│   ├── src
│   │   ├── components                           # React components
│   │   ├── pages                                # Page components
│   │   ├── services                             # API service functions
│   │   ├── styles                               # CSS styles
│   │   ├── App.tsx                              # Main application component
│   │   └── main.tsx                             # Entry point for React app
│   ├── package.json                             # npm configuration
│   ├── tsconfig.json                           # TypeScript configuration
│   └── README.md                               # Frontend documentation
├── edge-module           # Edge detection module
│   ├── src
│   │   ├── edge_module.py                       # Main logic for edge detection
│   │   ├── config.py                            # Configuration settings
│   │   ├── yolo_inference.py                    # YOLO inference functions
│   │   ├── buffer.py                            # Local buffer implementation
│   │   └── utils.py                             # Utility functions
│   ├── requirements.txt                          # Python dependencies
│   └── README.md                                # Edge module documentation
├── integration            # Integration setup
│   ├── docker-compose.yml                         # Docker Compose configuration
│   ├── .env                                       # Environment variables
│   └── README.md                                  # Integration documentation
```

## Getting Started

### Prerequisites

- Java 11 or higher
- Maven
- Node.js and npm
- Python 3.6 or higher
- Docker (for integration)

### Setup Instructions

1. **Backend Setup**
   - Navigate to the `backend` directory.
   - Run `mvn clean install` to build the project.
   - Configure the `application.properties` file for your database settings.
   - Start the Spring Boot application using `mvn spring-boot:run`.

2. **Frontend Setup**
   - Navigate to the `frontend` directory.
   - Run `npm install` to install dependencies.
   - Start the React application using `npm start`.

3. **Edge Module Setup**
   - Navigate to the `edge-module` directory.
   - Install required Python packages using `pip install -r requirements.txt`.
   - Run the edge detection module.

4. **Integration with Docker**
   - Navigate to the `integration` directory.
   - Create a `.env` file with necessary environment variables.
   - Run `docker-compose up` to start all services.

## Usage

- Access the frontend application at `http://localhost:3000`.
- The backend API can be accessed at `http://localhost:8080/api`.
- The edge detection module will process video feeds and send detection events to the backend.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.