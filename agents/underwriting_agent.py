import google.generativeai as genai
import os
from dotenv import load_dotenv
from models.schemas import AgentRequest, AgentResponse, AgentType, UnderwritingResult
from services.database import db
import math

load_dotenv()

class UnderwritingAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
    
    def calculate_emi(self, principal, annual_rate, months):
        """Calculate EMI using standard formula"""
        monthly_rate = annual_rate / 12 / 100
        if monthly_rate == 0:
            return principal / months
        emi = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
        return round(emi, 2)
    
    def process(self, request: AgentRequest) -> AgentResponse:
        context = request.context.copy()
        context["agent"] = "underwriting"
        
        customer_id = context.get("customer_id")
        loan_amount = request.loan_intent.amount if request.loan_intent and request.loan_intent.amount else 100000
        tenure = request.loan_intent.tenure if request.loan_intent and request.loan_intent.tenure else 24
        
        if not customer_id:
            return AgentResponse(
                message="🔐 **Customer ID Required**\n\nI need your customer ID to check loan eligibility.\nCould you please provide it or verify your phone number first?",
                next_agent=AgentType.VERIFICATION,
                context=context
            )
        
        # Fetch customer data
        customers_col = db.get_collection("customers")
        customer = customers_col.find_one({"customer_id": customer_id})
        
        if not customer:
            return AgentResponse(
                message="❌ **Customer Details Not Found**\n\nPlease complete verification first to proceed with loan eligibility.",
                next_agent=AgentType.VERIFICATION,
                context=context
            )
        
        # Get credit score from database
        credit_score = customer.get("credit_score", 700)
        preapproved_limit = customer.get("preapproved_limit", 100000)
        salary = customer.get("salary", 50000)
        
        # Underwriting Rules as per challenge
        decision = ""
        reason = ""
        conditions = []
        
        # Rule 1: Credit score check
        if credit_score < 700:
            decision = "rejected"
            reason = f"Credit score {credit_score} is below minimum requirement of 700"
        
        # Rule 2: Compare with pre-approved limit
        elif loan_amount <= preapproved_limit:
            decision = "approved"
            reason = f"Loan amount within pre-approved limit of ₹{preapproved_limit:,}"
        
        # Rule 3: Up to 2x limit with salary slip
        elif loan_amount <= 2 * preapproved_limit:
            # Check if salary slip is already uploaded
            if context.get("salary_slip_verified"):
                emi = self.calculate_emi(loan_amount, 14.0, tenure)
                if emi <= 0.5 * salary:
                    decision = "approved"
                    reason = f"Loan approved with salary slip verification. EMI ₹{emi:,} is ≤ 50% of salary ₹{salary:,}"
                else:
                    decision = "rejected"
                    reason = f"EMI ₹{emi:,} exceeds 50% of salary ₹{salary:,}"
            else:
                decision = "pending"
                reason = f"Loan amount ₹{loan_amount:,} exceeds pre-approved limit ₹{preapproved_limit:,}. Please upload salary slip for verification."
                conditions = ["Salary slip required"]
        
        # Rule 4: More than 2x limit
        else:
            decision = "rejected"
            reason = f"Loan amount ₹{loan_amount:,} exceeds 2x pre-approved limit of ₹{2*preapproved_limit:,}"
        
        # Calculate EMI for approved loans
        emi_value = None
        if decision == "approved":
            emi_value = self.calculate_emi(loan_amount, 14.0, tenure)
            context["emi"] = emi_value
            context["approved_amount"] = loan_amount
            context["tenure"] = tenure
        
        underwriting_result = UnderwritingResult(
            decision=decision,
            max_eligible_amount=min(loan_amount, 2 * preapproved_limit) if decision != "rejected" else 0,
            emi=emi_value,
            reason=reason,
            conditions=conditions
        )
        
        context["underwriting_result"] = underwriting_result.dict()
        
        # Generate response message
        if decision == "approved":
            message = f"🎉 **LOAN APPROVED!**\n\n"
            message += f"Congratulations! Your loan application has been approved.\n\n"
            message += f"**Loan Details:**\n"
            message += f"• **Amount:** ₹{loan_amount:,}\n"
            message += f"• **Tenure:** {tenure} months ({tenure//12} years)\n"
            message += f"• **EMI:** ₹{emi_value:,}/month\n"
            message += f"• **Interest Rate:** 14.0% p.a.\n"
            message += f"• **Total Payable:** ₹{emi_value * tenure:,}\n\n"
            message += f"📊 **Credit Assessment:**\n"
            message += f"• Credit Score: {credit_score}\n"
            message += f"• Pre-approved Limit: ₹{preapproved_limit:,}\n\n"
            message += "Would you like me to generate your sanction letter? 📜"
            next_agent = AgentType.SANCTION
        
        elif decision == "pending":
            message = f"📄 **Additional Documentation Required**\n\n"
            message += f"Your loan request for ₹{loan_amount:,} is being processed.\n\n"
            message += f"**Status:** {reason}\n\n"
            message += f"**What you need to do:**\n"
            message += f"1. Upload your latest salary slip\n"
            message += f"2. Ensure it shows salary of ₹{salary:,} or more\n"
            message += f"3. File should be clear and readable\n\n"
            message += "Please upload your salary slip using the file upload section below. 👇"
            next_agent = AgentType.UNDERWRITING
        
        else:  # rejected
            message = f"❌ **Loan Application Status**\n\n"
            message += f"I'm sorry, but your loan application for ₹{loan_amount:,} cannot be approved at this time.\n\n"
            message += f"**Reason:** {reason}\n\n"
            
            if credit_score < 700:
                message += f"**💡 Suggestions to improve your eligibility:**\n"
                message += f"• Pay existing loans on time to improve credit score\n"
                message += f"• Reduce credit card utilization\n"
                message += f"• Clear any pending dues\n"
                message += f"• Check your credit report for errors\n\n"
                message += f"Your current eligible amount: ₹{preapproved_limit:,}\n"
                message += f"Would you like to apply for this amount instead?"
            else:
                message += f"**Alternative Options:**\n"
                message += f"• Your pre-approved limit: ₹{preapproved_limit:,}\n"
                message += f"• Maximum eligible: ₹{2 * preapproved_limit:,} (with salary slip)\n\n"
                message += "Would you like to apply for an amount within your eligible limit?"
            
            next_agent = AgentType.SALES
        
        return AgentResponse(
            message=message,
            next_agent=next_agent,
            customer_info=request.customer_info,
            loan_intent=request.loan_intent,
            context=context,
            metadata={
                "agent": "underwriting",
                "decision": decision,
                "credit_score": credit_score,
                "preapproved_limit": preapproved_limit,
                "requested_amount": loan_amount,
                "emi": emi_value
            }
        )