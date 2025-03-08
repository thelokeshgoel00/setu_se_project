# Setu API Integration

A FastAPI application that integrates with Setu APIs for PAN verification and reverse penny drop functionality.

## Setup

1. Clone this repository
2. Set up a virtual environment:
   ```
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with the following variables:
   ```
   SETU_CLIENT_ID=your_client_id
   SETU_CLIENT_SECRET=your_client_secret
   SETU_PRODUCT_INSTANCE_ID=your_product_instance_id
   SETU_BASE_URL=https://dg-sandbox.setu.co  # Use https://dg.setu.co for production
   ```

## Running the Application

Make sure your virtual environment is activated, then start the FastAPI server:

```
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Running with Docker

You can run the application using Docker, which packages everything needed to run the application in a container.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

### Running the Application with Docker

1. Make sure you have a `.env` file in the root directory with your Setu API credentials:
   ```
   SETU_CLIENT_ID=your_client_id
   SETU_CLIENT_SECRET=your_client_secret
   SETU_PRODUCT_INSTANCE_ID=your_product_instance_id
   SETU_BASE_URL=https://dg-sandbox.setu.co  # Use https://dg.setu.co for production
   ```

2. Build and start the Docker containers:
   ```
   docker-compose up -d
   ```

3. The application will be available at:
   - Backend API: `http://localhost:8000`
   - Frontend: `http://localhost:5173`
   - API Documentation: `http://localhost:8000/docs`

4. To stop the application:
   ```
   docker-compose down
   ```

### Building and Running Without Docker Compose

If you prefer to use Docker directly without Docker Compose:

1. Build the Docker image:
   ```
   docker build -t setu-api-app .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 -p 5173:5173 --env-file .env -d setu-api-app
   ```

3. To stop the container:
   ```
   docker stop <container_id>
   ```

## API Endpoints

### 1. Verify PAN

**Endpoint**: `POST /api/pan/verify`

**Request Body**:
```json
{
  "pan": "ABCDE1234A",
  "consent": "Y",
  "reason": "Verification for onboarding"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "aadhaar_seeding_status": "LINKED",
    "category": "Individual",
    "full_name": "John Doe",
    "first_name": "John",
    "middle_name": "Hartwell",
    "last_name": "Doe"
  },
  "message": "PAN is valid",
  "trace_id": "1-6346a91a-620cf6cc4f68d2e30316881e"
}
```

### 2. Create Reverse Penny Drop Request

**Endpoint**: `POST /api/bav/reverse-penny-drop`

**Request Body**:
```json
{
  "additional_data": {
    "customerId": "customer123",
    "purpose": "account_verification"
  },
  "redirection_config": {
    "redirect_url": "https://yourapp.com/callback",
    "timeout": 60
  }
}
```

**Response**:
```json
{
  "id": "rpd_123456789",
  "short_url": "https://setu.co/rpd/abc123",
  "status": "PENDING",
  "trace_id": "1-6346a91a-620cf6cc4f68d2e30316881e",
  "upi_bill_id": "bill123456",
  "upi_link": "upi://pay?pa=setu@axis&pn=Setu&am=1.00&tr=rpd_123456789",
  "valid_upto": "2023-12-31T23:59:59Z"
}
```

### 3. Mock Payment (Sandbox Only)

**Endpoint**: `POST /api/bav/reverse-penny-drop/{request_id}/mock-payment`

**Request Body**:
```json
{
  "payment_status": "successful"
}
```

**Response**:
```json
{
  "success": true,
  "trace_id": "1-6346a91a-620cf6cc4f68d2e30316881e"
}
```

## Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 