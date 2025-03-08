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
from .database import engine, get_db
from .db_models import Base, PANVerification, ReversePennyDrop, Payment
from sqlalchemy.orm import Session
import json
import uuid
# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

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
async def verify_pan(request: PANVerificationRequest, settings=Depends(get_settings), db: Session = Depends(get_db)):
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
                    try:
                        # Transform camelCase to snake_case for response
                        transformed_data = {
                            "status": "success",
                            "data": {
                                "aadhaar_seeding_status": response_data.get("data", {}).get("aadhaarSeedingStatus", 
                                                                                          response_data.get("data", {}).get("aadhaar_seeding_status")),
                                "category": response_data.get("data", {}).get("category", "Unknown"),
                                "full_name": response_data.get("data", {}).get("fullName", 
                                                                             response_data.get("data", {}).get("full_name", "Unknown")),
                                "first_name": response_data.get("data", {}).get("firstName", 
                                                                              response_data.get("data", {}).get("first_name")),
                                "middle_name": response_data.get("data", {}).get("middleName", 
                                                                               response_data.get("data", {}).get("middle_name")),
                                "last_name": response_data.get("data", {}).get("lastName", 
                                                                             response_data.get("data", {}).get("last_name"))
                            },
                            "message": response_data.get("message", "PAN verification completed"),
                            "trace_id": response_data.get("traceId", response_data.get("trace_id", ""))
                        }
                        
                        # Store the verification result in the database
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name=transformed_data["data"]["full_name"],
                            category=transformed_data["data"]["category"],
                            aadhaar_seeding_status=transformed_data["data"]["aadhaar_seeding_status"],
                            first_name=transformed_data["data"]["first_name"],
                            middle_name=transformed_data["data"]["middle_name"],
                            last_name=transformed_data["data"]["last_name"],
                            status=transformed_data["status"],
                            message=transformed_data["message"],
                            trace_id=transformed_data["trace_id"]
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        # Log the error but don't fail the request
                        print(f"Error storing PAN verification in database: {str(db_error)}")
                        print(f"Response data: {response_data}")
                    
                    # Return the transformed data to match the response model
                    return transformed_data
                elif response.status_code == 400:
                    # Store failed verification
                    try:
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name="",
                            category="",
                            status="failed",
                            message=response_data.get("message", "Bad request"),
                            trace_id=response_data.get("trace_id", response_data.get("traceId", ""))
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing failed PAN verification: {str(db_error)}")
                    
                    raise HTTPException(status_code=400, detail=response_data.get("message", "Bad request"))
                elif response.status_code == 404:
                    # Store not found verification
                    try:
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name="",
                            category="",
                            status="not_found",
                            message=response_data.get("message", "PAN not found"),
                            trace_id=response_data.get("trace_id", response_data.get("traceId", ""))
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing not found PAN verification: {str(db_error)}")
                    
                    raise HTTPException(status_code=404, detail=response_data.get("message", "PAN not found"))
                else:
                    # Store error verification
                    try:
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name="",
                            category="",
                            status="error",
                            message="Error from Setu API",
                            trace_id=response_data.get("trace_id", response_data.get("traceId", ""))
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing error PAN verification: {str(db_error)}")
                    
                    raise HTTPException(status_code=response.status_code, detail="Error from Setu API")
            except httpx.RequestError as e:
                # Store connection error verification
                try:
                    db_verification = PANVerification(
                        pan=request.pan,
                        full_name="",
                        category="",
                        status="connection_error",
                        message=f"Error communicating with Setu API: {str(e)}",
                        trace_id=""
                    )
                    db.add(db_verification)
                    db.commit()
                except Exception as db_error:
                    print(f"Error storing connection error PAN verification: {str(db_error)}")
                
                raise HTTPException(status_code=500, detail=f"Error communicating with Setu API: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in verify_pan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/api/rpd/create_request", response_model=ReversePennyDropResponse)
async def create_reverse_penny_drop(request: ReversePennyDropRequest, settings=Depends(get_settings), db: Session = Depends(get_db)):
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
                try:
                    # Transform camelCase to snake_case for database and response
                    transformed_data = {
                        "id": response_data.get("id", ""),
                        "short_url": response_data.get("shortURL", response_data.get("shortUrl", "")),
                        "status": response_data.get("status", ""),
                        "trace_id": response_data.get("traceId", response_data.get("trace_id", "")),
                        "upi_bill_id": response_data.get("upiBillID", response_data.get("upiBillId", "")),
                        "upi_link": response_data.get("upiLink", ""),
                        "valid_upto": response_data.get("validUpto", "")
                    }
                    
                    # Store the reverse penny drop request in the database
                    db_rpd = ReversePennyDrop(
                        id=transformed_data["id"],
                        short_url=transformed_data["short_url"],
                        status=transformed_data["status"],
                        trace_id=transformed_data["trace_id"],
                        upi_bill_id=transformed_data["upi_bill_id"],
                        upi_link=transformed_data["upi_link"],
                        valid_upto=transformed_data["valid_upto"]
                    )
                    db.add(db_rpd)
                    db.commit()
                except Exception as db_error:
                    # Log the error but don't fail the request
                    print(f"Error storing reverse penny drop in database: {str(db_error)}")
                    print(f"Response data: {response_data}")
                
                # Return the transformed data to match the response model
                return transformed_data
            else:
                # Try to store the failed request
                try:
                    error_message = response_data.get("error", {}).get("message", "Error from Setu API")
                    db_rpd = ReversePennyDrop(
                        id=response_data.get("id", f"error_{uuid.uuid4()}"),
                        short_url="",
                        status="ERROR",
                        trace_id=response_data.get("trace_id", ""),
                        upi_bill_id="",
                        upi_link="",
                        valid_upto=""
                    )
                    db.add(db_rpd)
                    db.commit()
                except Exception as db_error:
                    print(f"Error storing failed reverse penny drop: {str(db_error)}")
                
                error_message = response_data.get("error", {}).get("message", "Error from Setu API")
                raise HTTPException(status_code=response.status_code, detail=error_message)
                
        except httpx.RequestError as e:
            # Try to store the connection error
            try:
                db_rpd = ReversePennyDrop(
                    id=f"connection_error_{uuid.uuid4()}",
                    short_url="",
                    status="CONNECTION_ERROR",
                    trace_id="",
                    upi_bill_id="",
                    upi_link="",
                    valid_upto=""
                )
                db.add(db_rpd)
                db.commit()
            except Exception as db_error:
                print(f"Error storing connection error reverse penny drop: {str(db_error)}")
            
            raise HTTPException(status_code=500, detail=f"Error communicating with Setu API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in create_reverse_penny_drop: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/api/rpd/mock-payment", response_model=MockPaymentResponse)
async def mock_payment(request: MockPaymentRequest, settings=Depends(get_settings), db: Session = Depends(get_db)):
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
            print(response_data)
            # Handle different response statuses
            if response.status_code == 200:
                try:
                    # Transform camelCase to snake_case for response
                    transformed_data = {
                        "success": response_data.get("success", True),
                        "trace_id": response_data.get("traceId", response_data.get("trace_id", ""))
                    }
                    
                    # Store the payment in the database
                    db_payment = Payment(
                        request_id=request.request_id,
                        payment_status=request.payment_status,
                        trace_id=transformed_data["trace_id"]
                    )
                    db.add(db_payment)
                    db.commit()
                    
                    # Update the status of the reverse penny drop
                    rpd = db.query(ReversePennyDrop).filter(ReversePennyDrop.id == request.request_id).first()
                    if rpd:
                        rpd.status = "SUCCESS" if request.payment_status else "EXPIRED"
                        db.commit()
                except Exception as db_error:
                    # Log the error but don't fail the request
                    print(f"Error storing payment in database: {str(db_error)}")
                
                # Return the transformed data to match the response model
                return transformed_data
            else:
                # Try to store the failed payment
                try:
                    db_payment = Payment(
                        request_id=request.request_id,
                        payment_status=False,
                        trace_id=response_data.get("trace_id", "")
                    )
                    db.add(db_payment)
                    db.commit()
                except Exception as db_error:
                    print(f"Error storing failed payment: {str(db_error)}")
                
                error_message = response_data.get("error", {}).get("message", "Error from Setu API")
                raise HTTPException(status_code=response.status_code, detail=error_message)
        except httpx.RequestError as e:
            # Try to store the connection error
            try:
                db_payment = Payment(
                    request_id=request.request_id,
                    payment_status=False,
                    trace_id=""
                )
                db.add(db_payment)
                db.commit()
            except Exception as db_error:
                print(f"Error storing connection error payment: {str(db_error)}")
            
            raise HTTPException(status_code=500, detail=f"Error communicating with Setu API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in mock_payment: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Add new endpoints for database queries

@app.get("/api/pan/history")
async def get_pan_verification_history(db: Session = Depends(get_db)):
    """
    Get history of PAN verifications
    """
    verifications = db.query(PANVerification).all()
    return verifications

@app.get("/api/rpd/history")
async def get_reverse_penny_drop_history(db: Session = Depends(get_db)):
    """
    Get history of reverse penny drop requests
    """
    rpds = db.query(ReversePennyDrop).all()
    return rpds

@app.get("/api/payments/history")
async def get_payment_history(db: Session = Depends(get_db)):
    """
    Get history of payments
    """
    payments = db.query(Payment).all()
    return payments

@app.get("/api/admin/metrics")
async def get_admin_metrics(db: Session = Depends(get_db)):
    """
    Get admin metrics for the dashboard
    """
    try:
        # Get total KYC attempted (PAN verifications)
        total_kyc_attempted = db.query(PANVerification).count()
        
        # Get total KYC successful (PAN verifications with status 'success')
        total_kyc_successful = db.query(PANVerification).filter(PANVerification.status == "success").count()
        
        # Get total KYC failed
        total_kyc_failed = total_kyc_attempted - total_kyc_successful
        
        # Get total KYC failed due to PAN
        # This is a simplification - in a real app, you'd have more detailed failure reasons
        total_kyc_failed_due_to_pan = db.query(PANVerification).filter(
            PANVerification.status != "success"
        ).count()
        
        # For bank account failures, we'll use the reverse penny drop data
        # Get total RPD attempts
        total_rpd_attempted = db.query(ReversePennyDrop).count()
        
        # Get total RPD successful
        total_rpd_successful = db.query(ReversePennyDrop).filter(
            ReversePennyDrop.status == "SUCCESS"
        ).count()
        
        # Get total RPD failed
        total_rpd_failed = total_rpd_attempted - total_rpd_successful
        
        # For simplification, we'll assume:
        # - If only PAN failed, it's counted in total_kyc_failed_due_to_pan
        # - If only Bank Account failed, it's counted in total_rpd_failed
        # - If both failed, we'll estimate based on the data
        
        # This is a simplified calculation - in a real app, you'd track these metrics more precisely
        total_kyc_failed_due_to_bank = total_rpd_failed
        
        # Estimate failures due to both - this is just an example approach
        # In a real app, you'd track this explicitly
        total_kyc_failed_due_to_both = min(total_kyc_failed_due_to_pan, total_kyc_failed_due_to_bank) // 2
        
        # Adjust individual failure counts to account for the "both" category
        total_kyc_failed_due_to_pan -= total_kyc_failed_due_to_both
        total_kyc_failed_due_to_bank -= total_kyc_failed_due_to_both
        
        return {
            "totalKycAttempted": total_kyc_attempted,
            "totalKycSuccessful": total_kyc_successful,
            "totalKycFailed": total_kyc_failed,
            "totalKycFailedDueToPan": total_kyc_failed_due_to_pan,
            "totalKycFailedDueToBankAccount": total_kyc_failed_due_to_bank,
            "totalKycFailedDueToBoth": total_kyc_failed_due_to_both
        }
    except Exception as e:
        # Log the error
        print(f"Error calculating metrics: {str(e)}")
        # Return zeros for all metrics
        return {
            "totalKycAttempted": 0,
            "totalKycSuccessful": 0,
            "totalKycFailed": 0,
            "totalKycFailedDueToPan": 0,
            "totalKycFailedDueToBankAccount": 0,
            "totalKycFailedDueToBoth": 0
        }
