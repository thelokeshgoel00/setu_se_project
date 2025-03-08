# Setu API Integration UI

A React-based user interface for interacting with the Setu API Integration backend.

## Features

- PAN Verification
- Reverse Penny Drop for bank account verification
- Mock payment simulation for testing

## Tech Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Axios for API calls
- React Router for navigation

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm run dev
   ```

3. Build for production:
   ```
   npm run build
   ```

## Usage

Make sure the backend server is running on `http://localhost:8000` before starting the frontend application.

The frontend will be available at `http://localhost:5173` and will proxy API requests to the backend server.

## Pages

- **Home**: Overview of available features
- **PAN Verification**: Form to verify PAN numbers
- **Reverse Penny Drop**: Form to create reverse penny drop requests and simulate payments 