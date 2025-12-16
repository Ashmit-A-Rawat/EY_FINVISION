import google.generativeai as genai
import os
from dotenv import load_dotenv
from models.schemas import AgentRequest, AgentResponse, AgentType
from services.database import db
import re

load_dotenv()

class SalesAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
        
        self.system_prompt = """You are a persuasive loan sales agent for Tata Capital. Your role is to:
        1. Understand the customer's loan needs
        2. Build rapport and trust
        3. Negotiate loan amount and tenure
        4. Explain benefits clearly
        5. Overcome objections professionally
        6. Collect necessary information for verification
        
        Be empathetic, professional, and sales-focused. Always maintain a helpful tone.
        Keep responses concise (2-3 sentences max).
        
        IMPORTANT: If the customer mentions a loan amount, confirm it with them and ask for their phone number to proceed."""
    
    def process(self, request: AgentRequest) -> AgentResponse:
        # Fetch customer's pre-approved offer if phone is available
        customers_col = db.get_collection("customers")
        customer = None
        
        if request.customer_info and request.customer_info.phone:
            customer = customers_col.find_one({"phone": request.customer_info.phone})
        
        context = request.context.copy()
        context["agent"] = "sales"
        
        # Prepare conversation
        conversation_history = ""
        if "conversation_history" in context:
            for msg in context["conversation_history"][-6:]:  # Last 6 messages
                role = "Customer" if msg["role"] == "user" else "Agent"
                conversation_history += f"{role}: {msg['content']}\n"
        
        # Check if loan intent has amount
        loan_amount = None
        tenure = None
        purpose = None
        if request.loan_intent:
            loan_amount = request.loan_intent.amount
            tenure = request.loan_intent.tenure
            purpose = request.loan_intent.purpose
        
        # Build prompt with intent awareness
        intent_context = ""
        if loan_amount:
            # Format amount nicely
            if loan_amount >= 100000:
                amount_str = f"₹{loan_amount/100000:.1f} lakh" if loan_amount % 100000 != 0 else f"₹{loan_amount//100000} lakh"
            else:
                amount_str = f"₹{loan_amount:,}"
            
            intent_context = f"\n\nCustomer has expressed interest in: {amount_str}"
            if tenure:
                intent_context += f" for {tenure} months"
            if purpose:
                intent_context += f" for {purpose}"
            intent_context += "\n\nConfirm these details and ask for their phone number to proceed with verification."
        
        # Build prompt
        prompt = f"""{self.system_prompt}

Previous conversation:
{conversation_history}

Customer message: {request.message}
{intent_context}

Respond as the sales agent. Be helpful and guide them towards verification."""
        
        try:
            # Call Gemini API
            if self.model:
                response = self.model.generate_content(prompt)
                ai_response = response.text
            else:
                # Fallback response
                ai_response = self._get_fallback_response(request, loan_amount, tenure, purpose)
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            ai_response = self._get_fallback_response(request, loan_amount, tenure, purpose)
        
        # ENHANCED: Add confirmation if loan amount is captured
        if loan_amount and not context.get("amount_confirmed"):
            # Format amount properly
            if loan_amount >= 100000:
                amount_str = f"₹{loan_amount/100000:.1f} lakh" if loan_amount % 100000 != 0 else f"₹{loan_amount//100000} lakh"
            else:
                amount_str = f"₹{loan_amount:,}"
            
            ai_response += f"\n\n**Just to confirm:**\n"
            ai_response += f"• Loan Amount: {amount_str} (₹{loan_amount:,})\n"
            if tenure:
                ai_response += f"• Tenure: {tenure} months ({tenure//12} years)\n"
            if purpose:
                ai_response += f"• Purpose: {purpose}\n"
            ai_response += f"\nTo proceed, I'll need your registered phone number for quick verification. 📱"
            context["amount_confirmed"] = True
        
        # Check if we have enough info to proceed to verification
        proceed_to_verification = False
        message_lower = request.message.lower()
        
        # Extract phone if mentioned
        phone_match = re.search(r'\b\d{10}\b', request.message)
        if phone_match:
            proceed_to_verification = True
        elif customer or any(word in message_lower for word in ["phone", "number", "verify", "987"]):
            proceed_to_verification = True
        
        return AgentResponse(
            message=ai_response,
            next_agent=AgentType.VERIFICATION if proceed_to_verification else AgentType.SALES,
            customer_info=request.customer_info,
            loan_intent=request.loan_intent,
            context=context,
            metadata={
                "agent": "sales",
                "proceed_to_verification": proceed_to_verification,
                "amount_captured": loan_amount is not None
            }
        )
    
    def _get_fallback_response(self, request: AgentRequest, loan_amount=None, tenure=None, purpose=None) -> str:
        """Rule-based fallback when API is unavailable"""
        message_lower = request.message.lower()
        
        # Greeting
        if any(word in message_lower for word in ["hi", "hello", "hey", "good morning", "good afternoon"]):
            return "Hello! Welcome to Tata Capital. I'm here to help you with your personal loan needs. What amount are you looking for?"
        
        # Loan request with amount already captured
        if loan_amount:
            if loan_amount >= 100000:
                amount_str = f"₹{loan_amount/100000:.1f} lakh" if loan_amount % 100000 != 0 else f"₹{loan_amount//100000} lakh"
            else:
                amount_str = f"₹{loan_amount:,}"
            
            response = f"Great! I see you're interested in {amount_str}."
            if purpose:
                response += f" for {purpose}"
            response += " To check your eligibility and get instant approval, I'll need your registered phone number."
            return response
        
        # Loan request
        if any(word in message_lower for word in ["loan", "need", "want", "looking", "apply"]):
            return "I'd be happy to help you with a personal loan! Could you tell me how much you need and what it's for?"
        
        # Amount mentioned
        if any(word in message_lower for word in ["lakh", "thousand", "₹", "rs", "crore"]):
            return "Perfect! To proceed with your loan application, I'll need to verify your details. Could you please share your registered phone number?"
        
        # Default
        return "I'd be happy to help you with your loan application. To get started, could you tell me: 1) How much loan you're looking for? 2) Your registered phone number?"