from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime
from models.schemas import SanctionLetter

def generate_sanction_letter_pdf(letter: SanctionLetter, output_path: str = None) -> str:
    """Generate sanction letter PDF"""
    if not output_path:
        os.makedirs("sanction_letters", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"sanction_letters/sanction_{timestamp}.pdf"
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("TATA CAPITAL", title_style))
    story.append(Paragraph("SANCTION LETTER", title_style))
    story.append(Spacer(1, 20))
    
    # Reference and Date
    ref_data = [
        [Paragraph(f"<b>Reference No:</b> {letter.reference_number}", normal_style),
         Paragraph(f"<b>Date:</b> {letter.sanction_date}", normal_style)]
    ]
    
    ref_table = Table(ref_data, colWidths=[3.5*inch, 3.5*inch])
    ref_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 20))
    
    # Customer Details
    story.append(Paragraph("To,", normal_style))
    story.append(Paragraph(f"<b>{letter.customer_name}</b>", heading_style))
    story.append(Spacer(1, 20))
    
    # Body
    body_text = f"""
    Dear {letter.customer_name},
    
    We are pleased to inform you that your loan application has been approved by Tata Capital. 
    The details of your sanctioned loan are as follows:
    """
    story.append(Paragraph(body_text, normal_style))
    story.append(Spacer(1, 15))
    
    # Loan Details Table
    loan_data = [
        ['Particulars', 'Details'],
        ['Loan Amount', f'₹ {letter.loan_amount:,.2f}'],
        ['Loan Tenure', f'{letter.tenure} months'],
        ['Rate of Interest', f'{letter.interest_rate}% p.a.'],
        ['EMI Amount', f'₹ {letter.emi:,.2f} per month'],
        ['Sanction Date', letter.sanction_date],
        ['Sanction Valid Until', letter.validity_date]
    ]
    
    loan_table = Table(loan_data, colWidths=[2.5*inch, 4*inch])
    loan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(loan_table)
    story.append(Spacer(1, 25))
    
    # Terms and Conditions
    story.append(Paragraph("<b>Terms and Conditions:</b>", heading_style))
    
    terms = [
        "1. This sanction is valid until the validity date mentioned above.",
        "2. The loan will be disbursed subject to execution of required documents.",
        "3. EMI payment will start from the month following disbursement.",
        "4. Late payment charges of 2% per month will be applicable on overdue amounts.",
        "5. Prepayment charges may apply as per the loan agreement.",
        "6. Tata Capital reserves the right to modify terms if required."
    ]
    
    for term in terms:
        story.append(Paragraph(term, normal_style))
    
    story.append(Spacer(1, 30))
    
    # Signature
    sig_data = [
        [Paragraph("For Tata Capital Limited", normal_style), 
         Paragraph("Authorized Signatory", normal_style)],
        [Spacer(1, 40), Spacer(1, 40)],
        [Paragraph("(Digital Signature)", normal_style),
         Paragraph("(Digital Signature)", normal_style)]
    ]
    
    sig_table = Table(sig_data, colWidths=[3*inch, 3*inch])
    story.append(sig_table)
    
    # Build PDF
    doc.build(story)
    return output_path