from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class AgentType(str, Enum):
    MASTER = "master"
    SALES = "sales"
    VERIFICATION = "verification"
    UNDERWRITING = "underwriting"
    SANCTION = "sanction"

class LoanIntent(BaseModel):
    amount: Optional[float] = None
    tenure: Optional[int] = None
    purpose: Optional[str] = None

class CustomerInfo(BaseModel):
    customer_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class AgentRequest(BaseModel):
    message: str
    session_id: str
    customer_info: Optional[CustomerInfo] = None
    loan_intent: Optional[LoanIntent] = None
    context: Optional[Dict[str, Any]] = {}

class AgentResponse(BaseModel):
    message: str
    next_agent: Optional[AgentType] = None
    customer_info: Optional[CustomerInfo] = None
    loan_intent: Optional[LoanIntent] = None
    context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class VerificationResult(BaseModel):
    verified: bool
    customer_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class UnderwritingResult(BaseModel):
    decision: str  # "approved", "rejected", "pending"
    max_eligible_amount: Optional[float] = None
    emi: Optional[float] = None
    reason: Optional[str] = None
    conditions: Optional[List[str]] = None

class SanctionLetter(BaseModel):
    customer_name: str
    loan_amount: float
    tenure: int
    interest_rate: float
    emi: float
    sanction_date: str
    validity_date: str
    reference_number: str