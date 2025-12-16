from fastapi import APIRouter, HTTPException
from services.database import db
import random
from typing import Dict, Any

router = APIRouter()

@router.get("/crm/customer/{phone}")
async def get_customer_by_phone(phone: str) -> Dict[str, Any]:
    """Mock CRM API - Verify customer"""
    customers_col = db.get_collection("customers")
    customer = customers_col.find_one({"phone": phone})
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "verified": customer.get("kyc_verified", False),
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "address": customer["address"],
        "city": customer["city"],
        "email": customer["email"]
    }

@router.get("/credit/score/{customer_id}")
async def get_credit_score(customer_id: str) -> Dict[str, Any]:
    """Mock Credit Bureau API - Get credit score"""
    customers_col = db.get_collection("customers")
    customer = customers_col.find_one({"customer_id": customer_id})
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Add some randomness to make it realistic
    base_score = customer.get("credit_score", 700)
    variation = random.randint(-20, 20)
    final_score = max(300, min(900, base_score + variation))
    
    return {
        "customer_id": customer_id,
        "credit_score": final_score,
        "report_date": "2024-01-15",
        "risk_category": "LOW" if final_score >= 750 else "MEDIUM" if final_score >= 650 else "HIGH"
    }

@router.get("/offer/preapproved/{customer_id}")
async def get_preapproved_offer(customer_id: str) -> Dict[str, Any]:
    """Mock OfferMart API - Get pre-approved offers"""
    offers_col = db.get_collection("offers")
    offer = offers_col.find_one({"customer_id": customer_id})
    
    if not offer:
        # Return default offer
        return {
            "customer_id": customer_id,
            "preapproved_limit": 100000,
            "interest_rate": 15.0,
            "tenure_options": [12, 24],
            "processing_fee": 2.5,
            "special_offer": False
        }
    
    return {
        "customer_id": customer_id,
        "preapproved_limit": offer["max_amount"],
        "interest_rate": offer["interest_rate"],
        "tenure_options": offer["tenure_options"],
        "processing_fee": offer["processing_fee"],
        "special_offer": True
    }

@router.post("/upload/salary-slip")
async def upload_salary_slip(customer_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Mock salary slip upload endpoint"""
    # In real implementation, you would save the file
    # For mock, just validate
    salary = file_data.get("salary", 0)
    
    if salary >= 30000:
        return {
            "success": True,
            "message": "Salary slip verified",
            "verified_salary": salary,
            "verification_date": "2024-01-15"
        }
    else:
        return {
            "success": False,
            "message": "Salary slip verification failed - minimum salary requirement not met",
            "verified_salary": 0
        }