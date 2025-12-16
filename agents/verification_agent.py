import google.generativeai as genai
import os
from dotenv import load_dotenv
from models.schemas import AgentRequest, AgentResponse, AgentType, VerificationResult
from services.database import db
import re

load_dotenv()

class VerificationAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
        
        self.system_prompt = """You are a KYC verification agent for Tata Capital. Your role is to:
        1. Verify customer identity using CRM data
        2. Collect any missing KYC information
        3. Confirm contact details
        4. Explain the verification process
        5. Proceed to underwriting once verified
        
        Be professional, thorough, and reassuring about data security.
        Keep responses brief (2-3 sentences)."""
    
    def process(self, request: AgentRequest) -> AgentResponse:
        context = request.context.copy()
        context["agent"] = "verification"
        
        # Extract phone number from message or context
        phone_number = None
        if request.customer_info and request.customer_info.phone:
            phone_number = request.customer_info.phone
        else:
            # Try to extract from message
            phones = re.findall(r'\b\d{10}\b', request.message)
            if phones:
                phone_number = phones[0]
        
        verification_result = None
        if phone_number:
            try:
                # Get customer from database
                customers_col = db.get_collection("customers")
                customer = customers_col.find_one({"phone": phone_number})
                
                if customer:
                    verification_result = VerificationResult(
                        verified=customer.get("kyc_verified", False),
                        customer_id=customer["customer_id"],
                        details={
                            "name": customer["name"],
                            "address": customer["address"],
                            "city": customer["city"]
                        }
                    )
                    context["verification_result"] = verification_result.dict()
                    context["customer_id"] = customer["customer_id"]
                    
                    if customer.get("kyc_verified", False):
                        verification_message = f"✅ **Verification Successful!**\n\n"
                        verification_message += f"Hello **{customer['name']}**, I've verified your identity.\n"
                        verification_message += f"📍 Location: {customer['city']}\n"
                        verification_message += f"🆔 Customer ID: {customer['customer_id']}\n\n"
                        verification_message += "Your KYC is complete. Let me now check your loan eligibility..."
                        next_agent = AgentType.UNDERWRITING
                    else:
                        verification_message = f"⚠️ **Additional Verification Required**\n\n"
                        verification_message += f"Hello **{customer['name']}**, I found your record but your KYC is incomplete.\n"
                        verification_message += f"Could you please upload your Aadhaar card to complete verification?"
                        next_agent = AgentType.VERIFICATION
                else:
                    verification_message = "❌ **Customer Not Found**\n\n"
                    verification_message += "I couldn't find your details in our system with this phone number.\n"
                    verification_message += "Could you please verify the number or register with us first?"
                    next_agent = AgentType.VERIFICATION
                    
            except Exception as e:
                print(f"Database error in verification: {e}")
                verification_message = "⚠️ **Verification Service Temporarily Unavailable**\n\n"
                verification_message += "I'm having trouble accessing the verification system.\n"
                verification_message += "Let me proceed with basic details for now."
                next_agent = AgentType.UNDERWRITING
        else:
            verification_message = "📱 **Phone Verification Required**\n\n"
            verification_message += "To verify your identity, I need your 10-digit registered phone number.\n"
            verification_message += "Please share your phone number (e.g., 9876543210)"
            next_agent = AgentType.VERIFICATION
        
        return AgentResponse(
            message=verification_message,
            next_agent=next_agent,
            customer_info=request.customer_info,
            loan_intent=request.loan_intent,
            context=context,
            metadata={
                "agent": "verification",
                "phone_provided": phone_number is not None,
                "verification_result": verification_result.dict() if verification_result else None
            }
        )