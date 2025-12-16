import google.generativeai as genai
import os
from dotenv import load_dotenv
from models.schemas import AgentRequest, AgentResponse, AgentType
from services.database import db

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
        Keep responses concise (2-3 sentences max)."""
    
    def process(self, request: AgentRequest) -> AgentResponse:
        # Fetch customer's pre-approved offer
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
        
        # Build prompt
        prompt = f"""{self.system_prompt}

Previous conversation:
{conversation_history}

Customer message: {request.message}

Respond as the sales agent. If customer mentions a phone number, guide them to verification."""
        
        try:
            # Call Gemini API
            if self.model:
                response = self.model.generate_content(prompt)
                ai_response = response.text
            else:
                # Fallback response
                ai_response = self._get_fallback_response(request)
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            ai_response = self._get_fallback_response(request)
        
        # Check if we have enough info to proceed to verification
        proceed_to_verification = False
        message_lower = request.message.lower()
        
        if customer or any(word in message_lower for word in ["phone", "number", "verify", "987"]):
            proceed_to_verification = True
        
        return AgentResponse(
            message=ai_response,
            next_agent=AgentType.VERIFICATION if proceed_to_verification else AgentType.SALES,
            customer_info=request.customer_info,
            loan_intent=request.loan_intent,
            context=context,
            metadata={
                "agent": "sales",
                "proceed_to_verification": proceed_to_verification
            }
        )
    
    def _get_fallback_response(self, request: AgentRequest) -> str:
        """Rule-based fallback when API is unavailable"""
        message_lower = request.message.lower()
        
        # Greeting
        if any(word in message_lower for word in ["hi", "hello", "hey", "good morning", "good afternoon"]):
            return "Hello! Welcome to Tata Capital. I'm here to help you with your personal loan needs. What amount are you looking for?"
        
        # Loan request
        if any(word in message_lower for word in ["loan", "need", "want", "looking"]):
            return "Great! I can definitely help you with that. Could you please share: 1) How much loan amount you need? 2) Your registered phone number for quick verification?"
        
        # Amount mentioned
        if any(word in message_lower for word in ["lakh", "thousand", "₹", "rs"]):
            return "Perfect! To proceed with your loan application, I'll need to verify your details. Could you please share your registered phone number?"
        
        # Default
        return "I'd be happy to help you with your loan application. To get started, could you tell me how much loan you're looking for and your registered phone number?"