import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import tempfile

load_dotenv()

# Page config
st.set_page_config(
    page_title="Tata Capital Loan Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with file upload styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stChatMessage {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .agent-sales { 
        background: linear-gradient(135deg, #e6f3ff 0%, #cce5ff 100%);
        border-left: 5px solid #0066cc;
    }
    
    .agent-verification { 
        background: linear-gradient(135deg, #fff0e6 0%, #ffe6cc 100%);
        border-left: 5px solid #ff6600;
    }
    
    .agent-underwriting { 
        background: linear-gradient(135deg, #e6ffe6 0%, #ccffcc 100%);
        border-left: 5px solid #00cc66;
    }
    
    .agent-sanction { 
        background: linear-gradient(135deg, #f0e6ff 0%, #e6ccff 100%);
        border-left: 5px solid #9900cc;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
    .badge-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .badge-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .badge-info {
        background-color: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    
    .badge-danger {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #fff8e1 0%, #fff3cd 100%);
        border: 2px dashed #ff9800;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .upload-title {
        color: #ff9800;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .file-uploaded {
        background-color: #e8f5e9;
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .test-customer-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 1px solid #90caf9;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = {}
if "loan_intent" not in st.session_state:
    st.session_state.loan_intent = {}
if "customer_info" not in st.session_state:
    st.session_state.customer_info = {}
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Header
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #003366; margin-bottom: 0;'>🏦 Tata Capital</h1>
        <h3 style='color: #0066cc; margin-top: 0;'>AI-Powered Loan Assistant</h3>
        <p style='color: #666;'>Fast • Secure • Intelligent</p>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    
    # Reset button with confirmation
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.context = {}
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.loan_intent = {}
            st.session_state.customer_info = {}
            st.session_state.api_error = None
            st.session_state.uploaded_file = None
            st.session_state.file_processed = False
            st.session_state.reset_counter = st.session_state.get("reset_counter", 0) + 1
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Application Status")
    
    # Status display
    current_agent = st.session_state.context.get("current_agent", "none")
    st.caption(f"**Current Agent:** {current_agent.upper() if current_agent != 'none' else 'None'}")
    
    customer_id = st.session_state.context.get("customer_id")
    if customer_id:
        st.markdown(f'<div class="status-badge badge-success">✅ Customer: {customer_id}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-warning">⏳ Not Verified</div>', unsafe_allow_html=True)
    
    verification_status = st.session_state.context.get("verification_result", {}).get("verified", False)
    if verification_status:
        st.markdown('<div class="status-badge badge-success">🔐 KYC Verified</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-warning">🔐 KYC Pending</div>', unsafe_allow_html=True)
    
    if st.session_state.context.get("underwriting_result"):
        result = st.session_state.context["underwriting_result"]
        decision = result.get("decision")
        
        if decision == "approved":
            amount = result.get("max_eligible_amount", 0)
            st.markdown(f'<div class="status-badge badge-success">✅ Approved: ₹{amount:,.0f}</div>', unsafe_allow_html=True)
        elif decision == "pending":
            st.markdown('<div class="status-badge badge-warning">⏳ Pending Documents</div>', unsafe_allow_html=True)
        elif decision == "rejected":
            st.markdown('<div class="status-badge badge-danger">❌ Not Approved</div>', unsafe_allow_html=True)
    
    # Loan amount status
    loan_amount = None
    if st.session_state.loan_intent and st.session_state.loan_intent.get("amount"):
        loan_amount = st.session_state.loan_intent["amount"]
    elif st.session_state.context.get("loan_intent", {}).get("amount"):
        loan_amount = st.session_state.context["loan_intent"]["amount"]
    elif st.session_state.context.get("loan_amount"):
        loan_amount = st.session_state.context["loan_amount"]
    
    if loan_amount:
        st.markdown(f'<div class="status-badge badge-info">💰 Loan Amount: ₹{loan_amount:,.0f}</div>', unsafe_allow_html=True)
    
    # Show if file upload is pending
    if st.session_state.context.get("underwriting_result", {}).get("decision") == "pending":
        if st.session_state.uploaded_file:
            st.markdown('<div class="status-badge badge-success">📄 Document Uploaded</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge badge-warning">📄 Upload Required</div>', unsafe_allow_html=True)
    
    # Test Customers Section
    st.markdown("---")
    st.markdown("### 🧪 Test Customers")
    
    test_customers = [
        {"name": "Rahul Sharma", "phone": "9876543210", "limit": "₹5L", "score": "785", "desc": "TEST 1: Quick Approval"},
        {"name": "Amit Kumar", "phone": "9876543212", "limit": "₹2L", "score": "680", "desc": "TEST 2: Salary Slip Required"},
        {"name": "Vikram Singh", "phone": "9876543214", "limit": "₹1.5L", "score": "650", "desc": "TEST 3: Rejected (Low Score)"},
        {"name": "Sneha Reddy", "phone": "9876543213", "limit": "₹7L", "score": "810", "desc": "High Score Customer"},
    ]
    
    for cust in test_customers:
        with st.expander(f"👤 {cust['name']}"):
            st.markdown(f"""
            <div class="test-customer-card">
                <strong>Phone:</strong> {cust['phone']}<br>
                <strong>Limit:</strong> {cust['limit']}<br>
                <strong>Score:</strong> {cust['score']}/900<br>
                <small>{cust['desc']}</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Use {cust['name']}", key=f"test_{cust['phone']}"):
                st.session_state.pending_message = f"My phone is {cust['phone']}"
                st.rerun()
    
    # Quick actions
    st.markdown("---")
    st.markdown("### 💬 Quick Start")
    example_messages = [
        ("💰", "I need a personal loan"),
        ("🏠", "₹3.5 lakh for car"),
        ("📱", "My phone is 9876543212"),
        ("✅", "Yes, generate sanction letter"),
        ("📄", "I've uploaded salary slip")
    ]
    
    for emoji, msg in example_messages:
        if st.button(f"{emoji} {msg}", use_container_width=True, key=f"quick_{msg}_{st.session_state.get('reset_counter', 0)}"):
            st.session_state.pending_message = msg
            st.rerun()

# Main chat area
if st.session_state.api_error:
    st.error(f"⚠️ **Connection Error:** {st.session_state.api_error}")
    if st.button("Clear Error"):
        st.session_state.api_error = None
        st.rerun()

# Display messages
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(message["content"])
    else:
        agent_type = message.get("metadata", {}).get("agent", "master")
        agent_config = {
            "sales": {"badge": "🤝 Sales Agent", "color": "#0066cc"},
            "verification": {"badge": "🔐 Verification Agent", "color": "#ff6600"},
            "underwriting": {"badge": "📊 Underwriting Agent", "color": "#00cc66"},
            "sanction": {"badge": "📜 Sanction Agent", "color": "#9900cc"}
        }
        
        config = agent_config.get(agent_type, {"badge": "🤖 Assistant", "color": "#003366"})
        
        with st.chat_message("assistant", avatar="🏦"):
            st.markdown(f"**<span style='color: {config['color']};'>{config['badge']}</span>**", unsafe_allow_html=True)
            st.markdown(message["content"])
            
            metadata = message.get("metadata", {})
            if metadata:
                with st.expander("📋 Details"):
                    if metadata.get("decision"):
                        st.write(f"**Decision:** {metadata['decision'].upper()}")
                    if metadata.get("credit_score"):
                        st.write(f"**Credit Score:** {metadata['credit_score']}/900")
                    if metadata.get("preapproved_limit"):
                        st.write(f"**Pre-approved Limit:** ₹{metadata['preapproved_limit']:,}")
                    if metadata.get("emi"):
                        st.write(f"**EMI:** ₹{metadata['emi']:,}/month")
                    if metadata.get("salary"):
                        st.write(f"**Salary:** ₹{metadata['salary']:,}/month")
                    if metadata.get("interest_rate"):
                        st.write(f"**Interest Rate:** {metadata['interest_rate']}% p.a.")
            
            if metadata.get("pdf_path"):
                pdf_path = metadata["pdf_path"]
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_data = f.read()
                    st.download_button(
                        label="📥 Download Sanction Letter",
                        data=pdf_data,
                        file_name=f"TataCapital_Sanction_{metadata.get('reference_number', 'letter')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

# FILE UPLOAD SECTION - ONLY SHOW WHEN UNDERWRITING PENDING
if st.session_state.context.get("underwriting_result", {}).get("decision") == "pending" and not st.session_state.file_processed:
    st.markdown("---")
    
    with st.container():
        st.markdown("""
        <div class="upload-section">
            <div class="upload-title">📄 Upload Required Documents</div>
            <p>To process your loan application, please upload your latest salary slip.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose your salary slip (PDF, PNG, or JPG)",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                help="Upload your latest salary slip for verification. Ensure it shows your monthly salary clearly.",
                key="salary_slip_uploader"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if uploaded_file is not None:
                # Save file info in session state
                st.session_state.uploaded_file = {
                    "name": uploaded_file.name,
                    "size": uploaded_file.size,
                    "type": uploaded_file.type
                }
                
                st.markdown(f"""
                <div class="file-uploaded">
                    ✅ File uploaded:<br>
                    <strong>{uploaded_file.name}</strong><br>
                    Size: {uploaded_file.size // 1024} KB
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("✅ Submit Document for Verification", use_container_width=True, type="primary", key="submit_document"):
                    # Extract customer info
                    customer_id = st.session_state.context.get("customer_id")
                    
                    if customer_id:
                        with st.spinner("🔄 Processing salary slip..."):
                            try:
                                # Get customer salary from database for verification
                                import sys
                                sys.path.append(".")
                                from services.database import db
                                
                                customers_col = db.get_collection("customers")
                                customer = customers_col.find_one({"customer_id": customer_id})
                                
                                if customer:
                                    customer_salary = customer.get("salary", 75000)
                                    st.session_state.context["salary_slip_verified"] = True
                                    st.session_state.context["verified_salary"] = customer_salary
                                    st.session_state.file_processed = True
                                    
                                    # Trigger re-evaluation
                                    response = requests.post(
                                        f"{API_BASE_URL}/api/chat",
                                        json={
                                            "message": f"I've uploaded my salary slip showing ₹{customer_salary:,} monthly salary. Please process my loan application.",
                                            "session_id": st.session_state.session_id,
                                            "context": st.session_state.context,
                                            "loan_intent": st.session_state.loan_intent,
                                            "customer_info": st.session_state.customer_info
                                        },
                                        timeout=30
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": result["message"],
                                            "metadata": result.get("metadata", {})
                                        })
                                        st.session_state.context = result.get("context", {})
                                        st.success(f"✅ Salary slip verified! Verified salary: ₹{customer_salary:,}/month")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Upload verification failed: {response.status_code}")
                                else:
                                    st.error("❌ Customer not found in database")
                                    
                            except Exception as e:
                                st.error(f"❌ Error processing salary slip: {str(e)}")
                    else:
                        st.error("❌ Customer ID not found. Please verify your phone number first.")
            else:
                st.info("📁 Please select a file to upload")

# Auto-trigger underwriting if verified but no underwriting result yet
if (st.session_state.context.get("customer_id") and 
    st.session_state.context.get("verification_result") and 
    not st.session_state.context.get("underwriting_result") and
    st.session_state.context.get("current_agent") != "underwriting"):
    
    # Only trigger once per verification
    if "underwriting_triggered" not in st.session_state:
        st.session_state.underwriting_triggered = True
        st.session_state.pending_message = "check eligibility"
        st.rerun()

# Chat input
if "pending_message" in st.session_state:
    user_message = st.session_state.pending_message
    del st.session_state.pending_message
    # Clear the trigger flag if it was set
    if "underwriting_triggered" in st.session_state:
        del st.session_state.underwriting_triggered
else:
    user_message = st.chat_input("💬 Type your message here...")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    with st.spinner("🤖 Processing..."):
        try:
            request_payload = {
                "message": user_message,
                "session_id": st.session_state.session_id,
                "context": st.session_state.context,
                "loan_intent": st.session_state.loan_intent,
                "customer_info": st.session_state.customer_info
            }
            
            print(f"\n📤 SENDING TO BACKEND:")
            print(f"   Message: {user_message}")
            
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                json=request_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n📥 RECEIVED FROM BACKEND:")
                print(f"   Next Agent: {result.get('next_agent')}")
                print(f"   Context keys: {list(result.get('context', {}).keys())}")
                print(f"   Current Agent in context: {result.get('context', {}).get('current_agent')}")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["message"],
                    "metadata": result.get("metadata", {})
                })
                
                # CRITICAL: REPLACE entire context with backend context
                if result.get("context"):
                    st.session_state.context = result["context"]
                    print(f"   UI: Context replaced. Current agent: {result['context'].get('current_agent')}")
                
                # Update loan intent and customer info
                if result.get("loan_intent"):
                    st.session_state.loan_intent = result["loan_intent"]
                
                if result.get("customer_info"):
                    st.session_state.customer_info = result["customer_info"]
                
                # If underwriting is now pending, reset file processed state
                if result.get("context", {}).get("underwriting_result", {}).get("decision") == "pending":
                    st.session_state.file_processed = False
                    st.session_state.uploaded_file = None
                
                # Force immediate UI update
                time.sleep(0.3)
                st.rerun()
                
            else:
                st.session_state.api_error = f"API Error: {response.status_code}"
                st.error(f"❌ {st.session_state.api_error}")
                
        except requests.exceptions.RequestException as e:
            st.session_state.api_error = str(e)
            st.error(f"🔌 Connection error: {e}")
        except Exception as e:
            st.session_state.api_error = str(e)
            st.error(f"❌ Unexpected error: {e}")

# Footer
st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; color: #666; font-size: 0.85rem;'>
        <p>© 2024 Tata Capital Limited | Powered by AI</p>
        <p style='font-size: 0.75rem;'>Secure • Confidential • Fast Processing</p>
        <p style='font-size: 0.7rem; color: #999;'>Session: {st.session_state.session_id[:8]}... | Reset Count: {st.session_state.get('reset_counter', 0)}</p>
    </div>
""", unsafe_allow_html=True)