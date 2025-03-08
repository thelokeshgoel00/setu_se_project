from fastapi import FastAPI, HTTPException, Depends

from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv
from .models import (
    PANVerificationRequest, PANVerificationResponse,
    ReversePennyDropRequest, ReversePennyDropResponse,
    MockPaymentRequest, MockPaymentResponse
)
from .config import get_settings
import json
# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Setu API Integration",
    description="API for verifying PAN and creating reverse penny drop requests using Setu API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173", "http://0.0.0.0:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to Setu API Integration. Visit /docs for API documentation."}

@app.post("/api/pan/verify", response_model=PANVerificationResponse)
async def verify_pan(request: PANVerificationRequest, settings=Depends(get_settings)):
    """
    Verify a PAN number using Setu API.
    
    - **pan**: PAN number to verify (e.g., ABCDE1234A)
    - **consent**: Must be 'Y' or 'y' to indicate consent
    - **reason**: Reason for verification (min 20 characters)
    """
    try:
        print(request)
        # Validate consent
        if request.consent.upper() != "Y":
            raise HTTPException(status_code=400, detail="Consent must be 'Y' to proceed with verification")
        
        # Validate reason length
        if len(request.reason) < 20:
            raise HTTPException(status_code=400, detail="Reason must be at least 20 characters long")
        
        # Prepare request to Setu API
        url = f"{settings.setu_base_url}/api/verify/pan"
        headers = {
            "x-client-id": settings.setu_client_id,
            "x-client-secret": settings.setu_client_secret,
            "x-product-instance-id": settings.setu_product_instance_pan_id,
            "Content-Type": "application/json"
        }
        payload = {
            "pan": request.pan,
            "consent": request.consent,
            "reason": request.reason
        }
        
        # Make request to Setu API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response_data = response.json()
                print(response_data)
                # Handle different response statuses
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "data": response_data.get("data", {}),
                        "message": response_data.get("message", "PAN is valid"),
                        "trace_id": response_data.get("traceId", "")
                    }
                elif response.status_code == 400:
                    raise HTTPException(status_code=400, detail=response_data.get("message", "Bad request"))
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail=response_data.get("message", "PAN not found"))
                else:
                    raise HTTPException(status_code=response.status_code, detail="Error from Setu API")
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Error communicating with Setu API: {str(e)}") 
    except Exception as e:
        raise e

@app.post("/api/rpd/create_request", response_model=ReversePennyDropResponse)
async def create_reverse_penny_drop(request: ReversePennyDropRequest, settings=Depends(get_settings)):
    """
    Create a reverse penny drop request using Setu API.
    
    This endpoint creates a reverse penny drop request which generates a UPI payment link.
    The user can make a small payment (usually ₹1) to verify their bank account.
    
    - **additional_data**: Optional additional information to include with the request
    - **redirection_config**: Optional configuration for redirect behavior after transaction
    """
    print("request",request)
    # Prepare request to Setu API
    url = f"{settings.setu_base_url}/api/verify/ban/reverse"
    headers = {
        "x-client-id": settings.setu_client_id,
        "x-client-secret": settings.setu_client_secret,
        "x-product-instance-id": settings.setu_product_instance_rpd_id,
        "Content-Type": "application/json"
    }
    
    # Prepare payload
    payload = {}
    # if request.additionalData:
    #     payload["additionalData"] = request.additionalData
    # if request.redirectionConfig:
    #     payload["redirectionConfig"] = {
    #         "redirectURL": request.redirectionConfig.redirectUrl,
    #         "timeout": request.redirectionConfig.timeout
    #     }
    
    # Make request to Setu API
    print(payload, url, headers)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()
            print(response_data)
            # Handle different response statuses
            if response.status_code == 201:
                return {
                    "id": response_data.get("id", ""),
                    "short_url": response_data.get("shortURL", ""),
                    "status": response_data.get("status", ""),
                    "trace_id": response_data.get("traceId", ""),
                    "upi_bill_id": response_data.get("upiBillID", ""),
                    "upi_link": response_data.get("upiLink", ""),
                    "valid_upto": response_data.get("validUpto", "")
                }
            else:
                error_message = response_data.get("error", {}).get("message", "Error from Setu API")
                raise HTTPException(status_code=response.status_code, detail=error_message)
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Setu API: {str(e)}")

@app.post("/api/rpd/mock-payment", response_model=MockPaymentResponse)
async def mock_payment(request: MockPaymentRequest, settings=Depends(get_settings)):
    """
    Mock a payment for a reverse penny drop request (sandbox only).
    
    This endpoint is only available in the sandbox environment and allows you to simulate
    a payment for testing purposes.
    
    - **request_id**: ID of the reverse penny drop request
    - **payment_status**: Status of the payment (successful or expired)
    """
    print(request)
    # Ensure we're in sandbox mode
    if "sandbox" not in settings.setu_base_url:
        raise HTTPException(status_code=400, detail="Mock payments are only available in sandbox mode")
    
    # Prepare request to Setu API
    url = f"{settings.setu_base_url}/api/verify/ban/reverse/mock_payment/{request.request_id}"
    headers = {
        "x-client-id": settings.setu_client_id,
        "x-client-secret": settings.setu_client_secret,
        "x-product-instance-id": settings.setu_product_instance_rpd_id,
        "Content-Type": "application/json"
    }
    payment_status = "successful" if request.payment_status else "expired"
    payload = {
        "paymentStatus": payment_status
    }
    
    # Make request to Setu API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            # Handle different response statuses
            if response.status_code == 200:
                return {
                    "success": True,
                    "trace_id": response_data.get("traceId", "")
                }
            else:
                error_message = response_data.get("error", {}).get("message", "Error from Setu API")
                raise HTTPException(status_code=response.status_code, detail=error_message)
                
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Setu API: {str(e)}")
