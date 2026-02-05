# Frontend README.md

# Face Recognition System - Frontend

This is the frontend part of the Face Recognition System, built using React and TypeScript. It provides a user interface for interacting with the backend services and displaying real-time detection events.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Components](#components)
- [Pages](#pages)
- [Services](#services)
- [Styles](#styles)
- [Contributing](#contributing)
- [License](#license)

## Installation

To get started with the frontend application, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/face-recognition-system.git
   cd face-recognition-system/frontend
   ```

2. Install the dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

4. Open your browser and navigate to `http://localhost:3000`.

## Usage

The frontend application allows users to:

- View a live feed from the edge detection module.
- Access a dashboard displaying the system's status.
- Review a log of detection events.
- Adjust application settings.

## Components

- **Dashboard**: Displays an overview of the system's status.
- **EventLog**: Shows a log of detection events.
- **LiveFeed**: Displays a live video feed from the edge detection module.

## Pages

- **Home**: The landing page of the application.
- **Settings**: Allows users to configure application settings.

## Services

The `services/api.ts` file contains functions for making API calls to the backend service, handling requests and responses.

## Styles

The `styles/App.css` file contains styles for the frontend application, ensuring a consistent look and feel.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.