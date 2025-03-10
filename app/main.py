from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv
from datetime import timedelta
from .models import (
    PANVerificationRequest, PANVerificationResponse,
    ReversePennyDropRequest, ReversePennyDropResponse,
    MockPaymentRequest, MockPaymentResponse,
    UserCreate, UserResponse, Token, UserRole,
    PANVerificationErrorResponse, ReversePennyDropErrorResponse
)
from .config import get_settings
from .database import engine, get_db
from .db_models import Base, PANVerification, ReversePennyDrop, Payment, User
from .auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_active_user, get_admin_user, get_member_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from sqlalchemy.orm import Session
import uuid
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
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

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.MEMBER  # Default role is member
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Get access token using username and password
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user

# Protected PAN verification endpoint (members only)
@app.post("/api/pan/verify", response_model=PANVerificationResponse, responses={400: {"model": PANVerificationErrorResponse}, 404: {"model": PANVerificationErrorResponse}, 500: {"model": PANVerificationErrorResponse}})
async def verify_pan(
    request: PANVerificationRequest, 
    current_user: User = Depends(get_member_user),
    settings=Depends(get_settings), 
    db: Session = Depends(get_db)
):
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
            # Return a custom error response
            error_response = PANVerificationErrorResponse(
                status="failed",
                message="Consent must be 'Y' to proceed with verification",
                trace_id=f"error_{uuid.uuid4()}"
            )
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder(error_response)
            )
        
        # Validate reason length
        if len(request.reason) < 20:
            # Return a custom error response
            error_response = PANVerificationErrorResponse(
                status="failed",
                message="Reason must be at least 20 characters long",
                trace_id=f"error_{uuid.uuid4()}"
            )
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder(error_response)
            )
        
        # Generate a unique trace_id for this verification flow
        flow_trace_id = f"flow_{uuid.uuid4()}"
        
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
            "reason": request.reason,
            "traceId": flow_trace_id  # Include our generated trace_id in the request
        }
        
        # Make request to Setu API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response_data = response.json()
                print(response_data)
                
                # Check if verification failed even with 200 status code
                if response.status_code == 200 and response_data.get("verification") == "failed":
                    # Store failed verification
                    try:
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name="",
                            category="",
                            status="failed",
                            message="PAN Verification Failed: " + response_data.get("message", "PAN not found"),
                            trace_id=flow_trace_id
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing failed PAN verification: {str(db_error)}")
                    
                    # Return a custom error response
                    error_response = PANVerificationErrorResponse(
                        status="failed",
                        message="PAN Verification Failed: " + response_data.get("message", "The provided PAN number was not found"),
                        trace_id=flow_trace_id
                    )
                    return JSONResponse(
                        status_code=404,
                        content=jsonable_encoder(error_response)
                    )
                
                # Handle different response statuses
                if response.status_code == 200:
                    try:
                        # Check if all required fields are present in the response
                        if not response_data.get("data", {}).get("fullName") and not response_data.get("data", {}).get("full_name"):
                            # Store failed verification
                            db_verification = PANVerification(
                                pan=request.pan,
                                full_name="",
                                category="",
                                status="failed",
                                message="PAN Verification Failed: Missing required data in response",
                                trace_id=flow_trace_id
                            )
                            db.add(db_verification)
                            db.commit()
                            
                            # Return a custom error response
                            error_response = PANVerificationErrorResponse(
                                status="failed",
                                message="PAN Verification Failed: The provided PAN information could not be verified",
                                trace_id=flow_trace_id
                            )
                            return JSONResponse(
                                status_code=400,
                                content=jsonable_encoder(error_response)
                            )
                        
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
                            "trace_id": flow_trace_id  # Use our generated trace_id instead of the one from the response
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
                            trace_id=flow_trace_id
                        )
                        db.add(db_verification)
                        db.commit()
                    except HTTPException:
                        # Re-raise HTTP exceptions
                        raise
                    except Exception as db_error:
                        # Log the error but don't fail the request
                        print(f"Error storing PAN verification in database: {str(db_error)}")
                        print(f"Response data: {response_data}")
                        
                        # If we can't store in the database, still return a proper error
                        error_response = PANVerificationErrorResponse(
                            status="error",
                            message="PAN Verification Failed: Error processing verification result",
                            trace_id=flow_trace_id
                        )
                        return JSONResponse(
                            status_code=500,
                            content=jsonable_encoder(error_response)
                        )
                    
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
                            message="PAN Verification Failed: " + response_data.get("message", "Bad request"),
                            trace_id=flow_trace_id
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing failed PAN verification: {str(db_error)}")
                    
                    # Return a custom error response
                    error_response = PANVerificationErrorResponse(
                        status="failed",
                        message="PAN Verification Failed: " + response_data.get("message", "The provided PAN information could not be verified"),
                        trace_id=flow_trace_id
                    )
                    return JSONResponse(
                        status_code=400,
                        content=jsonable_encoder(error_response)
                    )
                elif response.status_code == 404:
                    # Store not found verification
                    try:
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name="",
                            category="",
                            status="not_found",
                            message="PAN Verification Failed: " + response_data.get("message", "PAN not found"),
                            trace_id=flow_trace_id
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing not found PAN verification: {str(db_error)}")
                    
                    # Return a custom error response
                    error_response = PANVerificationErrorResponse(
                        status="not_found",
                        message="PAN Verification Failed: " + response_data.get("message", "The provided PAN number was not found"),
                        trace_id=flow_trace_id
                    )
                    return JSONResponse(
                        status_code=404,
                        content=jsonable_encoder(error_response)
                    )
                else:
                    # Store error verification
                    try:
                        db_verification = PANVerification(
                            pan=request.pan,
                            full_name="",
                            category="",
                            status="error",
                            message="PAN Verification Failed: Error from Setu API",
                            trace_id=flow_trace_id
                        )
                        db.add(db_verification)
                        db.commit()
                    except Exception as db_error:
                        print(f"Error storing error PAN verification: {str(db_error)}")
                    
                    # Return a custom error response
                    error_response = PANVerificationErrorResponse(
                        status="error",
                        message="PAN Verification Failed: Error from verification service",
                        trace_id=flow_trace_id
                    )
                    return JSONResponse(
                        status_code=response.status_code,
                        content=jsonable_encoder(error_response)
                    )
            except httpx.RequestError as e:
                # Store connection error verification
                try:
                    db_verification = PANVerification(
                        pan=request.pan,
                        full_name="",
                        category="",
                        status="connection_error",
                        message=f"PAN Verification Failed: Error communicating with Setu API: {str(e)}",
                        trace_id=flow_trace_id
                    )
                    db.add(db_verification)
                    db.commit()
                except Exception as db_error:
                    print(f"Error storing connection error PAN verification: {str(db_error)}")
                
                # Return a custom error response
                error_response = PANVerificationErrorResponse(
                    status="connection_error",
                    message="PAN Verification Failed: Error communicating with verification service",
                    trace_id=flow_trace_id
                )
                return JSONResponse(
                    status_code=500,
                    content=jsonable_encoder(error_response)
                )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Store unexpected error verification
        try:
            db_verification = PANVerification(
                pan=request.pan,
                full_name="",
                category="",
                status="error",
                message=f"PAN Verification Failed: Unexpected error: {str(e)}",
                trace_id=flow_trace_id if 'flow_trace_id' in locals() else f"error_{uuid.uuid4()}"
            )
            db.add(db_verification)
            db.commit()
        except Exception as db_error:
            print(f"Error storing unexpected error PAN verification: {str(db_error)}")
        
        print(f"Unexpected error in verify_pan: {str(e)}")
        # Return a custom error response
        error_response = PANVerificationErrorResponse(
            status="error",
            message="PAN Verification Failed: An unexpected error occurred during verification",
            trace_id=flow_trace_id if 'flow_trace_id' in locals() else f"error_{uuid.uuid4()}"
        )
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(error_response)
        )

@app.post("/api/rpd/create_request", response_model=ReversePennyDropResponse, responses={400: {"model": ReversePennyDropErrorResponse}, 404: {"model": ReversePennyDropErrorResponse}, 500: {"model": ReversePennyDropErrorResponse}})
async def create_reverse_penny_drop(request: ReversePennyDropRequest, settings=Depends(get_settings), db: Session = Depends(get_db)):
    """
    Create a reverse penny drop request using Setu API.
    
    This endpoint creates a reverse penny drop request which generates a UPI payment link.
    The user can make a small payment (usually ₹1) to verify their bank account.
    
    - **additional_data**: Optional additional information to include with the request
    - **redirection_config**: Optional configuration for redirect behavior after transaction
    """
    print("request",request)
    
    # Extract the flow trace_id from the request if available
    flow_trace_id = None
    if request.additionalData and "flowTraceId" in request.additionalData:
        flow_trace_id = request.additionalData["flowTraceId"]
    
    # Validate that a trace_id is provided
    if not flow_trace_id:
        error_response = ReversePennyDropErrorResponse(
            status="failed",
            message="Missing trace_id for the verification flow. Please complete PAN verification first.",
            trace_id=f"error_{uuid.uuid4()}"
        )
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(error_response)
        )
    
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
    #     # Create a copy of additionalData without our custom flowTraceId
    #     additional_data = {k: v for k, v in request.additionalData.items() if k != "flowTraceId"}
    #     payload["additionalData"] = additional_data
    # if request.redirectionConfig:
    #     payload["redirectionConfig"] = {
    #         "redirectURL": request.redirectionConfig.redirectUrl,
    #         "timeout": request.redirectionConfig.timeout
    #     }
    
    # Add our trace_id to the payload if available
    if flow_trace_id:
        payload["traceId"] = flow_trace_id
    
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
                        "trace_id": flow_trace_id if flow_trace_id else response_data.get("traceId", response_data.get("trace_id", "")),
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
                        trace_id=flow_trace_id if flow_trace_id else response_data.get("trace_id", ""),
                        upi_bill_id="",
                        upi_link="",
                        valid_upto=""
                    )
                    db.add(db_rpd)
                    db.commit()
                except Exception as db_error:
                    print(f"Error storing failed reverse penny drop: {str(db_error)}")
                
                error_message = response_data.get("error", {}).get("message", "Error from Setu API")
                error_response = ReversePennyDropErrorResponse(
                    status="failed",
                    message=f"Reverse Penny Drop Failed: {error_message}",
                    trace_id=flow_trace_id if flow_trace_id else f"error_{uuid.uuid4()}"
                )
                return JSONResponse(
                    status_code=response.status_code,
                    content=jsonable_encoder(error_response)
                )
                
        except httpx.RequestError as e:
            # Try to store the connection error
            try:
                db_rpd = ReversePennyDrop(
                    id=f"connection_error_{uuid.uuid4()}",
                    short_url="",
                    status="CONNECTION_ERROR",
                    trace_id=flow_trace_id if flow_trace_id else "",
                    upi_bill_id="",
                    upi_link="",
                    valid_upto=""
                )
                db.add(db_rpd)
                db.commit()
            except Exception as db_error:
                print(f"Error storing connection error reverse penny drop: {str(db_error)}")
            
            error_response = ReversePennyDropErrorResponse(
                status="connection_error",
                message=f"Reverse Penny Drop Failed: Error communicating with verification service",
                trace_id=flow_trace_id if flow_trace_id else f"error_{uuid.uuid4()}"
            )
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(error_response)
            )
        except Exception as e:
            print(f"Unexpected error in create_reverse_penny_drop: {str(e)}")
            error_response = ReversePennyDropErrorResponse(
                status="error",
                message=f"Reverse Penny Drop Failed: An unexpected error occurred",
                trace_id=flow_trace_id if flow_trace_id else f"error_{uuid.uuid4()}"
            )
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(error_response)
            )

@app.post("/api/rpd/mock-payment", response_model=MockPaymentResponse, responses={400: {"model": ReversePennyDropErrorResponse}, 404: {"model": ReversePennyDropErrorResponse}, 500: {"model": ReversePennyDropErrorResponse}})
async def mock_payment(request: MockPaymentRequest, settings=Depends(get_settings), db: Session = Depends(get_db)):
    """
    Mock a payment for a reverse penny drop request (sandbox only).
    
    This endpoint simulates a payment for a reverse penny drop request.
    It's used for testing the flow without making actual payments.
    
    - **request_id**: ID of the reverse penny drop request
    - **payment_status**: Whether the payment was successful (default: True)
    """
    # Get the RPD record to retrieve the trace_id
    rpd = db.query(ReversePennyDrop).filter(ReversePennyDrop.id == request.request_id).first()
    if not rpd:
        error_response = ReversePennyDropErrorResponse(
            status="not_found",
            message="Reverse penny drop request not found. Please check the request ID and try again.",
            trace_id=f"error_{uuid.uuid4()}"
        )
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder(error_response)
        )
    
    # Use the same trace_id from the RPD record
    flow_trace_id = rpd.trace_id
    
    # Validate that the RPD record has a valid trace_id
    if not flow_trace_id:
        error_response = ReversePennyDropErrorResponse(
            status="invalid_request",
            message="Invalid verification flow. Missing trace_id in the reverse penny drop record.",
            trace_id=f"error_{uuid.uuid4()}"
        )
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(error_response)
        )
    
    # Prepare request to Setu API
    url = f"{settings.setu_base_url}/api/verify/ban/reverse/mock_payment/{request.request_id}"
    headers = {
        "x-client-id": settings.setu_client_id,
        "x-client-secret": settings.setu_client_secret,
        "x-product-instance-id": settings.setu_product_instance_rpd_id,
        "Content-Type": "application/json"
    }
    
    # Prepare payload
    payload = {
        "requestId": request.request_id,
        "status": "SUCCESS" if request.payment_status else "FAILURE",
        "traceId": flow_trace_id  # Use the same trace_id
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
                        "trace_id": flow_trace_id  # Use the same trace_id
                    }
                    
                    # Store the payment in the database
                    db_payment = Payment(
                        request_id=request.request_id,
                        payment_status=request.payment_status,
                        trace_id=flow_trace_id  # Use the same trace_id
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
                error_response = ReversePennyDropErrorResponse(
                    status="failed",
                    message=f"Payment Failed: {error_message}",
                    trace_id=flow_trace_id
                )
                return JSONResponse(
                    status_code=response.status_code,
                    content=jsonable_encoder(error_response)
                )
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
            
            error_response = ReversePennyDropErrorResponse(
                status="connection_error",
                message="Payment Failed: Error communicating with verification service",
                trace_id=flow_trace_id
            )
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(error_response)
            )
        except Exception as e:
            print(f"Unexpected error in mock_payment: {str(e)}")
            error_response = ReversePennyDropErrorResponse(
                status="error",
                message="Payment Failed: An unexpected error occurred",
                trace_id=flow_trace_id
            )
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(error_response)
            )

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
async def get_admin_metrics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get admin metrics (admin only)
    """
    try:
        # Get total KYC attempted (PAN verifications)
        total_kyc_attempted = db.query(PANVerification).count()
        
        # Get successful PAN verifications
        successful_pan_verifications = db.query(PANVerification).filter(
            PANVerification.status == "success"
        ).all()
        
        # Get successful RPD attempts
        successful_rpd_attempts = db.query(ReversePennyDrop).filter(
            (ReversePennyDrop.status == "SUCCESS") | (ReversePennyDrop.status == "BAV_REVERSE_PENNY_DROP_CREATED")
        ).all()

        # Create sets of trace_ids for successful verifications
        successful_pan_trace_ids = {pan.trace_id for pan in successful_pan_verifications if pan.trace_id}
        successful_rpd_trace_ids = {rpd.trace_id for rpd in successful_rpd_attempts if rpd.trace_id}

        print(successful_pan_trace_ids)
        print(successful_rpd_trace_ids)
        
        # Calculate total KYC successful (both PAN and RPD successful)
        # Find the intersection of trace_ids that appear in both successful PAN and RPD
        successful_both_trace_ids = successful_pan_trace_ids.intersection(successful_rpd_trace_ids)
        total_kyc_successful = len(successful_both_trace_ids)
        
        # Get total KYC failed
        total_kyc_failed = total_kyc_attempted - total_kyc_successful
        
        # Get total KYC failed due to PAN
        # This includes cases where PAN failed but RPD might have succeeded or not been attempted
        failed_pan_verifications = db.query(PANVerification).filter(
            PANVerification.status != "success"
        ).all()
        failed_pan_trace_ids = {pan.trace_id for pan in failed_pan_verifications if pan.trace_id}
        total_kyc_failed_due_to_pan = len(failed_pan_trace_ids)
    
        
        # Get total RPD failed
        failed_rpd_attempts = db.query(ReversePennyDrop).filter(
            ReversePennyDrop.status != "SUCCESS"
        ).all()
        failed_rpd_trace_ids = {rpd.trace_id for rpd in failed_rpd_attempts if rpd.trace_id}
        
        # Calculate KYC failed due to bank account
        # This includes cases where RPD failed but PAN succeeded
        total_kyc_failed_due_to_bank = len(failed_rpd_trace_ids.intersection(successful_pan_trace_ids))
        
        # Calculate KYC failed due to both
        # This includes cases where both PAN and RPD failed
        total_kyc_failed_due_to_both = len(failed_pan_trace_ids.intersection(failed_rpd_trace_ids))
        
        # Get all RPD attempts (both successful and failed)
        all_rpd_attempts = db.query(ReversePennyDrop).all()
        all_rpd_trace_ids = {rpd.trace_id for rpd in all_rpd_attempts if rpd.trace_id}
        
        # Calculate PAN verifications without RPD entries
        # This includes cases where PAN succeeded but no RPD was attempted
        pan_without_rpd = successful_pan_trace_ids.difference(all_rpd_trace_ids)
        total_pan_without_rpd = len(pan_without_rpd)
        
        return {
            "totalKycAttempted": total_kyc_attempted,
            "totalKycSuccessful": total_kyc_successful,
            "totalKycFailed": total_kyc_failed,
            "totalKycFailedDueToPan": total_kyc_failed_due_to_pan - total_kyc_failed_due_to_both,
            "totalKycFailedDueToBankAccount": total_kyc_failed_due_to_bank,
            "totalKycFailedDueToBoth": total_kyc_failed_due_to_both,
            "totalPanWithoutRpd": total_pan_without_rpd
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
            "totalKycFailedDueToBoth": 0,
            "totalPanWithoutRpd": 0
        }
