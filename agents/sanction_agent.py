import google.generativeai as genai
import os
from dotenv import load_dotenv
from models.schemas import AgentRequest, AgentResponse, AgentType, SanctionLetter
from services.pdf_generator import generate_sanction_letter_pdf
import uuid
from datetime import datetime, timedelta

load_dotenv()

class SanctionAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
    
    def process(self, request: AgentRequest) -> AgentResponse:
        context = request.context.copy()
        context["agent"] = "sanction"
        
        # Get customer name
        customer_name = "Valued Customer"
        if request.customer_info and request.customer_info.name:
            customer_name = request.customer_info.name
        elif context.get("verification_result", {}).get("details", {}).get("name"):
            customer_name = context["verification_result"]["details"]["name"]
        
        # Get loan details from context
        loan_amount = context.get("approved_amount", 100000)
        tenure = context.get("tenure", 24)
        emi = context.get("emi", 5000)
        
        # Generate unique reference number
        reference_number = f"TCL/{datetime.now().strftime('%Y%m')}/{str(uuid.uuid4())[:8].upper()}"
        
        # Generate sanction letter
        sanction_letter = SanctionLetter(
            customer_name=customer_name,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=14.0,
            emi=emi,
            sanction_date=datetime.now().strftime("%d-%m-%Y"),
            validity_date=(datetime.now() + timedelta(days=30)).strftime("%d-%m-%Y"),
            reference_number=reference_number
        )
        
        # Generate PDF
        try:
            pdf_path = generate_sanction_letter_pdf(sanction_letter)
            pdf_generated = True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            pdf_path = None
            pdf_generated = False
        
        context["sanction_letter"] = sanction_letter.dict()
        if pdf_path:
            context["pdf_path"] = pdf_path
        
        # Create response message
        message = f"📜 **SANCTION LETTER GENERATED!**\n\n"
        message += f"Dear **{customer_name}**,\n\n"
        message += f"🎉 Congratulations! Your loan has been officially sanctioned.\n\n"
        
        message += f"**📋 Sanction Details:**\n"
        message += f"• **Reference No:** {sanction_letter.reference_number}\n"
        message += f"• **Loan Amount:** ₹{loan_amount:,}\n"
        message += f"• **EMI:** ₹{emi:,} per month\n"
        message += f"• **Tenure:** {tenure} months ({tenure//12} years)\n"
        message += f"• **Interest Rate:** 14.0% per annum\n"
        message += f"• **Sanction Date:** {sanction_letter.sanction_date}\n"
        message += f"• **Valid Until:** {sanction_letter.validity_date}\n\n"
        
        if pdf_generated:
            message += f"✅ Your official sanction letter PDF is ready for download!\n\n"
        else:
            message += f"⚠️ PDF generation in progress. You can download it shortly.\n\n"
        
        message += f"**📝 Next Steps:**\n"
        message += f"1. Download and review the sanction letter\n"
        message += f"2. E-sign the loan agreement document\n"
        message += f"3. Submit any pending documents (if required)\n"
        message += f"4. Loan amount will be disbursed within 24-48 hours\n\n"
        
        message += f"**💰 Disbursement Details:**\n"
        message += f"• Total Amount: ₹{loan_amount:,}\n"
        message += f"• Processing Fee: ₹{loan_amount * 0.015:,.2f} (1.5%)\n"
        message += f"• Net Disbursement: ₹{loan_amount * 0.985:,.2f}\n\n"
        
        message += f"**📞 Need Help?**\n"
        message += f"Contact our customer support:\n"
        message += f"• Phone: 1800-209-8800\n"
        message += f"• Email: support@tatacapital.com\n\n"
        
        message += f"Thank you for choosing **Tata Capital**! 🏦\n"
        message += f"We're here to support your financial journey. 💙"
        
        return AgentResponse(
            message=message,
            next_agent=None,  # End of flow
            customer_info=request.customer_info,
            loan_intent=request.loan_intent,
            context=context,
            metadata={
                "agent": "sanction",
                "sanction_letter": sanction_letter.dict(),
                "pdf_path": pdf_path,
                "reference_number": reference_number,
                "pdf_generated": pdf_generated
            }
        )