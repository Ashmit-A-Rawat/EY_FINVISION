import google.generativeai as genai
import os
from dotenv import load_dotenv
from models.schemas import AgentRequest, AgentResponse, AgentType, LoanIntent
from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.sanction_agent import SanctionAgent
import re

load_dotenv()

class MasterAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
        
        self.sales_agent = SalesAgent()
        self.verification_agent = VerificationAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.sanction_agent = SanctionAgent()
        
        self.system_prompt = """You are the Master Agent orchestrating a loan application process for Tata Capital. 
        Your job is to:
        1. Understand the user's initial message
        2. Determine which worker agent should handle it
        3. Maintain conversation context
        4. Route between agents seamlessly
        
        Available agents:
        - sales: For initial conversation, needs analysis, persuasion
        - verification: For KYC and identity verification
        - underwriting: For credit evaluation and eligibility
        - sanction: For generating sanction letter
        
        Always respond naturally while maintaining the orchestration logic."""
    
    def determine_next_agent(self, message: str, current_context: dict, loan_intent: LoanIntent = None) -> AgentType:
        """Determine which agent should handle the message"""
        message_lower = message.lower()
        
        # Check context first
        if "conversation_stage" not in current_context:
            current_context["conversation_stage"] = "initial"
        
        # Priority 1: If loan approved and user wants sanction letter
        if current_context.get("underwriting_result", {}).get("decision") == "approved":
            if any(word in message_lower for word in ["yes", "generate", "sanction", "letter", "proceed", "ok", "sure", "download"]):
                return AgentType.SANCTION
        
        # Priority 2: If customer verified AND loan amount is known (FIXED)
        if current_context.get("customer_id") and current_context.get("verification_result", {}).get("verified"):
            # Check if loan_intent already has amount from previous messages (CRITICAL FIX)
            existing_amount = loan_intent.amount if loan_intent else None
            
            # Check current message for amount keywords
            has_amount = any(word in message_lower for word in ["lakh", "lac", "thousand", "₹", "rs", "amount"])
            has_numbers = bool(re.search(r'\d+', message))
            has_loan_intent_keywords = any(word in message_lower for word in ["need", "want", "loan", "borrow", "apply"])
            
            # Route to underwriting if:
            # 1. Amount already captured in loan_intent, OR
            # 2. Current message mentions amount, OR
            # 3. User says "check eligibility" or similar
            if existing_amount or has_amount or (has_numbers and has_loan_intent_keywords):
                print(f"   ✅ Routing to Underwriting: existing_amount={existing_amount}, has_amount={has_amount}")
                return AgentType.UNDERWRITING
            
            # Check for explicit underwriting triggers
            if any(word in message_lower for word in ["eligibility", "eligible", "check", "approve", "emi", "salary", "uploaded", "slip"]):
                return AgentType.UNDERWRITING
        
        # Priority 3: Check for verification triggers - only if not verified yet
        if not current_context.get("customer_id"):
            # Phone number pattern
            if re.search(r'\d{10}', message):
                return AgentType.VERIFICATION
            # Explicit verification keywords
            if any(word in message_lower for word in ["phone", "number", "verify", "987"]):
                return AgentType.VERIFICATION
        
        # Priority 4: If already underwriting and pending docs
        if current_context.get("underwriting_result", {}).get("decision") == "pending":
            return AgentType.UNDERWRITING
        
        # Priority 5: Initial contact or general queries - sales
        return AgentType.SALES
    
    def extract_loan_intent(self, message: str, existing_intent: LoanIntent = None) -> LoanIntent:
        """Extract loan amount and tenure from message"""
        intent = existing_intent if existing_intent else LoanIntent()
        
        # Extract amount (only if not already set)
        if not intent.amount:
            amount_patterns = [
                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:lakh|lac)',
                r'(\d+)\s*(?:thousand)',
                r'(\d+)\s*(?:lakh|lac)',
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '')
                        amount = float(amount_str)
                        
                        if 'lakh' in message.lower() or 'lac' in message.lower():
                            intent.amount = amount * 100000
                        elif 'thousand' in message.lower():
                            intent.amount = amount * 1000
                        else:
                            # If amount is small (< 1000), assume it's in lakhs
                            if amount < 1000:
                                intent.amount = amount * 100000
                            else:
                                intent.amount = amount
                        break
                    except ValueError:
                        pass
        
        # Extract tenure (only if not already set)
        if not intent.tenure:
            tenure_patterns = [
                r'(\d+)\s*(?:months?)',
                r'(\d+)\s*(?:years?)',
                r'for\s*(\d+)\s*(?:months?|years?)',
            ]
            
            for pattern in tenure_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    try:
                        tenure = int(match.group(1))
                        if 'year' in message.lower():
                            tenure *= 12
                        intent.tenure = tenure
                        break
                    except ValueError:
                        pass
        
        # Set default tenure if amount is present but tenure is not
        if intent.amount and not intent.tenure:
            intent.tenure = 24  # Default 2 years
        
        # Extract purpose
        if not intent.purpose:
            purposes = ["home", "car", "education", "medical", "business", "wedding", "travel", "debt", "renovation"]
            for purpose in purposes:
                if purpose in message.lower():
                    intent.purpose = purpose.capitalize()
                    break
        
        return intent
    
    def _build_conversation_summary(self, context: dict) -> str:
        """Build a summary of conversation state for better routing"""
        summary = []
        if context.get("customer_id"):
            summary.append(f"Customer: {context['customer_id']}")
        if context.get("verification_result", {}).get("verified"):
            summary.append("KYC: ✅")
        if context.get("underwriting_result"):
            decision = context['underwriting_result'].get('decision', 'unknown')
            summary.append(f"Loan: {decision}")
        return " | ".join(summary) if summary else "New Session"
    
    def process(self, request: AgentRequest) -> AgentResponse:
        """Main orchestration method"""
        try:
            context = request.context.copy() if request.context else {}
            
            # Extract loan intent from message
            loan_intent = self.extract_loan_intent(request.message, request.loan_intent)
            
            # Determine which agent should handle this
            next_agent_type = self.determine_next_agent(request.message, context, loan_intent)
            
            # Debug logging
            print(f"🔍 Master Agent Debug:")
            print(f"   Message: {request.message}")
            print(f"   Context Summary: {self._build_conversation_summary(context)}")
            print(f"   Loan Intent: Amount={loan_intent.amount}, Tenure={loan_intent.tenure}")
            print(f"   Routing to: {next_agent_type.value}")
            
            # Update context
            context["current_agent"] = next_agent_type.value
            context["conversation_history"] = context.get("conversation_history", []) + [
                {"role": "user", "content": request.message}
            ]
            
            # Route to appropriate agent
            agent_request = AgentRequest(
                message=request.message,
                session_id=request.session_id,
                customer_info=request.customer_info,
                loan_intent=loan_intent,
                context=context
            )
            
            if next_agent_type == AgentType.SALES:
                response = self.sales_agent.process(agent_request)
            elif next_agent_type == AgentType.VERIFICATION:
                response = self.verification_agent.process(agent_request)
            elif next_agent_type == AgentType.UNDERWRITING:
                response = self.underwriting_agent.process(agent_request)
            elif next_agent_type == AgentType.SANCTION:
                response = self.sanction_agent.process(agent_request)
            else:
                # Default to sales agent
                response = self.sales_agent.process(agent_request)
            
            # Update conversation history with AI response
            context["conversation_history"] = context.get("conversation_history", []) + [
                {"role": "assistant", "content": response.message}
            ]
            
            response.context = context
            response.loan_intent = loan_intent  # Make sure loan intent is passed through
            
            return response
            
        except Exception as e:
            # Error handling - return error response
            print(f"❌ Master Agent Error: {e}")
            import traceback
            traceback.print_exc()
            
            return AgentResponse(
                message=f"I apologize for the technical difficulty. Let me help you with your loan application. Could you please tell me: 1) How much loan you need? 2) Your registered phone number?",
                next_agent=AgentType.SALES,
                context=context if 'context' in locals() else {},
                metadata={"error": str(e)}
            )