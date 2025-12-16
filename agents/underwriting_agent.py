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
        
        # ADD DEBUG LOGS
        print(f"\n📊 UNDERWRITING AGENT STARTED:")
        print(f"   Customer ID from context: {context.get('customer_id')}")
        print(f"   Verification status: {context.get('verification_result', {}).get('verified')}")
        print(f"   Loan amount from intent: {request.loan_intent.amount if request.loan_intent else None}")
        print(f"   Context keys: {list(context.keys())}")
        
        # CRITICAL FIX: Try multiple sources for customer_id
        customer_id = context.get("customer_id")
        
        if not customer_id:
            # Try to get from verification_result as backup
            customer_id = context.get("verification_result", {}).get("customer_id")
            if customer_id:
                context["customer_id"] = customer_id  # Store it back
                print(f"   ℹ️ Recovered customer_id from verification_result: {customer_id}")
        
        # Get loan amount and tenure
        loan_amount = request.loan_intent.amount if request.loan_intent and request.loan_intent.amount else None
        tenure = request.loan_intent.tenure if request.loan_intent and request.loan_intent.tenure else 24
        purpose = request.loan_intent.purpose if request.loan_intent and request.loan_intent.purpose else None
        
        # If no customer_id found anywhere, return error
        if not customer_id:
            print("   ❌ ERROR: No customer_id found")
            return AgentResponse(
                message="🔐 **Customer ID Required**\n\nI need to verify your identity first to check loan eligibility.\nCould you please provide your registered phone number?",
                next_agent=AgentType.VERIFICATION,
                context=context
            )
        
        # If no loan amount specified, ask for it
        if not loan_amount:
            print("   ❌ ERROR: No loan amount specified")
            return AgentResponse(
                message="💰 **Loan Amount Required**\n\nTo check your eligibility, I need to know how much loan you're looking for.\n\nExample: '₹3 lakh' or '₹500000'",
                next_agent=AgentType.SALES,
                context=context,
                loan_intent=request.loan_intent
            )
        
        print(f"   ✅ Proceeding with customer_id: {customer_id}, loan_amount: ₹{loan_amount:,}, tenure: {tenure} months, purpose: {purpose}")
        
        # Fetch customer data
        customers_col = db.get_collection("customers")
        customer = customers_col.find_one({"customer_id": customer_id})
        
        if not customer:
            print(f"   ❌ ERROR: Customer {customer_id} not found in database")
            return AgentResponse(
                message="❌ **Customer Details Not Found**\n\nPlease complete verification first to proceed with loan eligibility.",
                next_agent=AgentType.VERIFICATION,
                context=context
            )
        
        # Check if KYC is complete
        kyc_complete = customer.get("kyc_verified", False)
        if not kyc_complete:
            print(f"   ⚠️ Customer KYC incomplete, but proceeding with eligibility check")
        
        # Get credit score from database
        credit_score = customer.get("credit_score", 700)
        preapproved_limit = customer.get("preapproved_limit", 100000)
        salary = customer.get("salary", 50000)
        
        print(f"   📊 Customer Data: credit_score={credit_score}, preapproved_limit=₹{preapproved_limit:,}, salary=₹{salary:,}")
        
        # CRITICAL FIX: Get customer-specific interest rate from offers
        interest_rate = 14.0  # Default
        offers_col = db.get_collection("offers")
        offer = offers_col.find_one({"customer_id": customer_id})
        if offer:
            interest_rate = offer.get("interest_rate", 14.0)
            print(f"   💡 Using customer-specific interest rate: {interest_rate}%")
        else:
            print(f"   ℹ️ Using default interest rate: {interest_rate}%")
        
        # Underwriting Rules as per challenge - FIXED ORDER
        decision = ""
        reason = ""
        conditions = []
        
        print(f"   📈 Rule Check: Loan ₹{loan_amount:,} vs Pre-approved ₹{preapproved_limit:,} (2x limit: ₹{2*preapproved_limit:,})")
        
        # Rule 1: Credit score check - TEST 3
        if credit_score < 700:
            decision = "rejected"
            reason = f"Credit score {credit_score} is below minimum requirement of 700"
            print(f"   ❌ REJECTED: Credit score {credit_score} < 700")
        
        # Rule 4: More than 2x limit - REJECTED regardless of salary slip - TEST 5
        elif loan_amount > 2 * preapproved_limit:
            decision = "rejected"
            reason = f"Loan amount ₹{loan_amount:,} exceeds 2x pre-approved limit of ₹{2*preapproved_limit:,}"
            print(f"   ❌ REJECTED: Loan ₹{loan_amount:,} > 2x pre-approved ₹{2*preapproved_limit:,}")
        
        # Rule 2: Compare with pre-approved limit - TEST 1, 4
        elif loan_amount <= preapproved_limit:
            decision = "approved"
            reason = f"Loan amount within pre-approved limit of ₹{preapproved_limit:,}"
            print(f"   ✅ APPROVED: Loan ₹{loan_amount:,} ≤ pre-approved ₹{preapproved_limit:,}")
        
        # Rule 3: Up to 2x limit with salary slip - TEST 2
        elif loan_amount <= 2 * preapproved_limit:
            # Check if salary slip is already uploaded
            if context.get("salary_slip_verified"):
                verified_salary = context.get("verified_salary", salary)
                emi = self.calculate_emi(loan_amount, interest_rate, tenure)
                
                print(f"   📄 Salary slip verified: ₹{verified_salary:,}")
                print(f"   🧮 EMI Calculation: EMI ₹{emi:,} vs 50% salary: ₹{verified_salary * 0.5:,}")
                
                if emi <= 0.5 * verified_salary:
                    decision = "approved"
                    reason = f"Loan approved with salary slip verification. EMI ₹{emi:,} is ≤ 50% of salary ₹{verified_salary:,}"
                    print(f"   ✅ APPROVED: EMI ₹{emi:,} ≤ 50% of salary ₹{verified_salary:,}")
                else:
                    decision = "rejected"
                    reason = f"EMI ₹{emi:,} exceeds 50% of salary ₹{verified_salary:,}"
                    print(f"   ❌ REJECTED: EMI ₹{emi:,} > 50% of salary ₹{verified_salary:,}")
            else:
                decision = "pending"
                reason = f"Loan amount ₹{loan_amount:,} exceeds pre-approved limit ₹{preapproved_limit:,}. Please upload salary slip for verification."
                conditions = ["Salary slip required"]
                print(f"   ⏳ PENDING: Need salary slip for loan ₹{loan_amount:,} > pre-approved ₹{preapproved_limit:,}")
                
                # Calculate potential EMI for information
                potential_emi = self.calculate_emi(loan_amount, interest_rate, tenure)
                print(f"   📊 Potential EMI would be: ₹{potential_emi:,} (≤50% of ₹{salary:,} salary)")
        
        # Calculate EMI for approved loans
        emi_value = None
        if decision == "approved":
            emi_value = self.calculate_emi(loan_amount, interest_rate, tenure)
            context["emi"] = emi_value
            context["approved_amount"] = loan_amount
            context["tenure"] = tenure
            context["interest_rate"] = interest_rate
        
        underwriting_result = UnderwritingResult(
            decision=decision,
            max_eligible_amount=min(loan_amount, 2 * preapproved_limit) if decision != "rejected" else preapproved_limit,
            emi=emi_value,
            reason=reason,
            conditions=conditions
        )
        
        context["underwriting_result"] = underwriting_result.dict()
        
        print(f"   📋 Underwriting Decision: {decision}")
        print(f"   💰 Max Eligible Amount: ₹{underwriting_result.max_eligible_amount:,}")
        print(f"   📝 Reason: {reason}")
        
        # Generate response message
        if decision == "approved":
            message = f"🎉 **LOAN APPROVED!**\n\n"
            message += f"Congratulations! Your loan application has been approved.\n\n"
            message += f"**📋 Loan Details:**\n"
            message += f"• **Amount:** ₹{loan_amount:,}\n"
            if tenure:
                message += f"• **Tenure:** {tenure} months ({tenure//12} years)\n"
            message += f"• **Interest Rate:** {interest_rate}% p.a.\n"
            if emi_value:
                message += f"• **EMI:** ₹{emi_value:,}/month\n"
                message += f"• **Total Payable:** ₹{emi_value * tenure:,}\n"
            message += f"• **Purpose:** {purpose if purpose else 'Not specified'}\n\n"
            
            message += f"**📊 Credit Assessment:**\n"
            message += f"• Credit Score: {credit_score}/900 {'✅' if credit_score >= 750 else '⚠️'}\n"
            message += f"• Pre-approved Limit: ₹{preapproved_limit:,}\n"
            message += f"• Your Custom Rate: {interest_rate}% p.a.\n\n"
            
            message += f"**📝 Approval Summary:**\n"
            message += f"{reason}\n\n"
            
            message += "**Would you like me to generate your sanction letter?** 📜\n"
            message += "_(Just say 'yes' or 'generate sanction letter')_"
            next_agent = AgentType.SANCTION
        
        elif decision == "pending":
            # Calculate potential EMI for the message
            potential_emi = self.calculate_emi(loan_amount, interest_rate, tenure)
            
            message = f"📄 **Additional Documentation Required**\n\n"
            message += f"Your loan request for **₹{loan_amount:,}** is being processed.\n\n"
            message += f"**Status:** {reason}\n\n"
            message += f"**📊 Current Assessment:**\n"
            message += f"• Requested Amount: ₹{loan_amount:,}\n"
            message += f"• Pre-approved Limit: ₹{preapproved_limit:,}\n"
            message += f"• Maximum Eligible: ₹{2 * preapproved_limit:,} (with salary proof)\n"
            message += f"• Your Salary: ₹{salary:,}/month\n"
            message += f"• Potential EMI: ₹{potential_emi:,}/month\n\n"
            
            message += f"**📈 EMI vs Salary Check:**\n"
            message += f"EMI (₹{potential_emi:,}) must be ≤ 50% of verified salary\n"
            message += f"50% of ₹{salary:,} = ₹{salary * 0.5:,}\n\n"
            
            message += f"**📝 What you need to do:**\n"
            message += f"1. Upload your **latest salary slip** using the file upload section below\n"
            message += f"2. Ensure it clearly shows monthly salary of ₹{salary:,} or more\n"
            message += f"3. We'll verify that EMI (₹{potential_emi:,}) is ≤ 50% of your verified salary\n\n"
            message += "**👇 Please scroll down to upload your salary slip.**"
            next_agent = AgentType.UNDERWRITING
        
        else:  # rejected
            message = f"❌ **Loan Application Status**\n\n"
            message += f"I'm sorry, but your loan application for **₹{loan_amount:,}** cannot be approved at this time.\n\n"
            message += f"**Reason:** {reason}\n\n"
            
            if credit_score < 700:
                gap = 700 - credit_score
                message += f"**📊 Your Credit Profile:**\n"
                message += f"• Current Score: {credit_score}/900\n"
                message += f"• Minimum Required: 700/900\n"
                message += f"• Gap: {gap} points\n\n"
                
                message += f"**💡 Quick Wins to Improve Your Credit Score:**\n"
                message += f"• Pay 2-3 EMIs on time → +30-40 points (2-3 months)\n"
                message += f"• Clear credit card dues → +40-50 points (1 month)\n"
                message += f"• Fix credit report errors → +50-100 points (immediate)\n"
                message += f"• Reduce credit utilization to <30% → +30 points (1 month)\n\n"
                
                message += f"**Your Current Eligible Amount:** ₹{preapproved_limit:,}\n"
                message += f"Would you like to apply for ₹{preapproved_limit:,} instead?"
            else:
                message += f"**Alternative Options:**\n"
                message += f"• Your pre-approved limit: ₹{preapproved_limit:,}\n"
                message += f"• Maximum eligible: ₹{2 * preapproved_limit:,} (with salary slip)\n\n"
                message += f"Would you like to apply for an amount within your eligible limit?"
            
            next_agent = AgentType.SALES
        
        print(f"   📤 Returning response. Next agent: {next_agent}")
        
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
                "emi": emi_value,
                "interest_rate": interest_rate,
                "salary": salary,
                "tenure": tenure
            }
        )