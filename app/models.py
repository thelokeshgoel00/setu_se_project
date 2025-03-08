from pydantic import BaseModel, Field, validator
import re

class PANVerificationRequest(BaseModel):
    """
    Request model for PAN verification
    """
    pan: str = Field(..., description="PAN number to verify", min_length=10, max_length=10)
    consent: str = Field(..., description="Consent for verification (must be 'Y')")
    reason: str = Field(..., description="Reason for verification (min 20 characters)", min_length=20)
    
    @validator('pan')
    def validate_pan_format(cls, v):
        """Validate PAN format: 5 uppercase letters, 4 digits, 1 uppercase letter"""
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', v):
            raise ValueError("Invalid PAN format. Expected format: ABCDE1234A")
        return v
    
    @validator('consent')
    def validate_consent(cls, v):
        """Validate consent is 'Y' or 'y'"""
        if v.upper() != 'Y':
            raise ValueError("Consent must be 'Y' to proceed with verification")
        return v

class PANData(BaseModel):
    """
    Model for PAN verification data
    """
    aadhaar_seeding_status: str = Field(None, description="Aadhaar seeding status")
    category: str = Field(..., description="Category of PAN holder")
    full_name: str = Field(..., description="Full name of PAN holder")
    first_name: str = Field(None, description="First name of PAN holder")
    middle_name: str = Field(None, description="Middle name of PAN holder")
    last_name: str = Field(None, description="Last name of PAN holder")

class PANVerificationResponse(BaseModel):
    """
    Response model for PAN verification
    """
    status: str = Field(..., description="Status of verification")
    data: PANData = Field(..., description="PAN holder data")
    message: str = Field(..., description="Verification message")
    trace_id: str = Field(..., description="Trace ID for the request")

# New models for Reverse Penny Drop

class RedirectionConfig(BaseModel):
    """
    Configuration for redirect behavior after transaction completion
    """
    redirectUrl: str = Field(..., description="URL where the user will be redirected after transaction")
    timeout: int = Field(30, description="Duration in seconds to wait before redirection occurs")

class ReversePennyDropRequest(BaseModel):
    """
    Request model for creating a reverse penny drop request
    """
    additionalData: dict = Field(None, description="Additional information to be included with the request")
    redirectionConfig: RedirectionConfig = Field(None, description="Configuration for redirect behavior")

class ReversePennyDropResponse(BaseModel):
    """
    Response model for reverse penny drop request
    """
    id: str = Field(..., description="Request ID for the reverse penny drop")
    short_url: str = Field(..., description="Short URL for payment")
    status: str = Field(..., description="Status of the request")
    trace_id: str = Field(..., description="Trace ID for the request")
    upi_bill_id: str = Field(..., description="UPI Bill ID")
    upi_link: str = Field(..., description="UPI link for payment")
    valid_upto: str = Field(..., description="Expiry timestamp for the request")

class MockPaymentRequest(BaseModel):
    """
    Request model for mocking a payment (sandbox only)
    """
    request_id: str = Field(..., description="Request ID for the reverse penny drop")
    payment_status: bool = Field(True, description="Payment status (successful or failed): Default is True")

class MockPaymentResponse(BaseModel):
    """
    Response model for mock payment
    """
    success: bool = Field(..., description="Whether the mock payment was successful")
    trace_id: str = Field(..., description="Trace ID for the request") 