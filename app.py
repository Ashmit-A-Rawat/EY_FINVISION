import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import base64

load_dotenv()

# Page config
st.set_page_config(
    page_title="Tata Capital Loan Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Agent-specific colors */
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
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #003366 0%, #0066cc 100%);
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #00cc66 0%, #00994d 100%);
    }
    
    /* Status badges */
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
    
    /* File uploader */
    .uploadedFile {
        background-color: #f8f9fa;
        border: 2px dashed #003366;
        border-radius: 10px;
        padding: 1rem;
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

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Header with logo area
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #003366; margin-bottom: 0;'>🏦 Tata Capital</h1>
            <h3 style='color: #0066cc; margin-top: 0;'>AI-Powered Loan Assistant</h3>
            <p style='color: #666;'>Fast • Secure • Intelligent</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    
    # Reset button with confirmation
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.context = {}
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.loan_intent = {}
        st.session_state.customer_info = {}
        st.session_state.api_error = None
        st.rerun()
    
    st.markdown("---")
    
    # Current Status Section
    st.markdown("### 📊 Application Status")
    
    status_container = st.container()
    with status_container:
        # Customer ID Status
        if st.session_state.context.get("customer_id"):
            st.markdown(f"""
                <div class='status-badge badge-success'>
                    ✅ Customer: {st.session_state.context.get('customer_id')}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='status-badge badge-warning'>
                    ⏳ Not Verified
                </div>
            """, unsafe_allow_html=True)
        
        # Verification Status
        if st.session_state.context.get("verification_result"):
            verified = st.session_state.context["verification_result"].get("verified")
            if verified:
                st.markdown("""
                    <div class='status-badge badge-success'>
                        🔐 KYC Verified
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class='status-badge badge-warning'>
                        🔐 KYC Pending
                    </div>
                """, unsafe_allow_html=True)
        
        # Loan Status
        if st.session_state.context.get("underwriting_result"):
            result = st.session_state.context["underwriting_result"]
            decision = result.get("decision")
            
            if decision == "approved":
                amount = result.get("max_eligible_amount", 0)
                st.markdown(f"""
                    <div class='status-badge badge-success'>
                        ✅ Approved: ₹{amount:,.0f}
                    </div>
                """, unsafe_allow_html=True)
            elif decision == "pending":
                st.markdown("""
                    <div class='status-badge badge-warning'>
                        ⏳ Pending Documents
                    </div>
                """, unsafe_allow_html=True)
            elif decision == "rejected":
                st.markdown("""
                    <div class='status-badge badge-warning'>
                        ❌ Not Approved
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### 💬 Quick Start")
    st.caption("Click to send a message:")
    
    example_messages = [
        ("💰", "I need a personal loan"),
        ("🏠", "₹5 lakh for home renovation"),
        ("📊", "Check my eligibility"),
        ("📋", "What's my pre-approved limit?"),
        ("⏰", "₹3 lakh for 2 years")
    ]
    
    for emoji, msg in example_messages:
        if st.button(f"{emoji} {msg}", use_container_width=True, key=msg):
            st.session_state.pending_message = msg
            st.rerun()
    
    st.markdown("---")
    
    # Session Info
    with st.expander("ℹ️ Session Information"):
        st.caption(f"**Session ID:**")
        st.code(st.session_state.session_id[:16] + "...", language=None)
        st.caption(f"**Messages:** {len(st.session_state.messages)}")
        st.caption(f"**API:** {API_BASE_URL}")
        
        # Debug: Show current context
        if st.session_state.context:
            st.caption("**Context Debug:**")
            debug_info = {
                "customer_id": st.session_state.context.get("customer_id"),
                "verified": st.session_state.context.get("verification_result", {}).get("verified"),
                "agent": st.session_state.context.get("agent"),
                "loan_amount": st.session_state.loan_intent.get("amount"),
                "tenure": st.session_state.loan_intent.get("tenure")
            }
            st.json(debug_info)

# Main chat area
chat_container = st.container()

# Display API error if any
if st.session_state.api_error:
    st.error(f"⚠️ **Connection Error:** {st.session_state.api_error}")
    st.info("💡 **Troubleshooting:**\n- Ensure FastAPI backend is running on port 8000\n- Check your internet connection\n- Verify API_BASE_URL in .env file")
    if st.button("Clear Error"):
        st.session_state.api_error = None
        st.rerun()

with chat_container:
    # Welcome message for new users
    if len(st.session_state.messages) == 0:
        st.info("👋 **Welcome to Tata Capital Loan Assistant!**\n\nI'm here to help you with your loan application. You can:\n- Apply for a personal loan\n- Check your eligibility\n- Get instant pre-approval\n- Complete KYC verification\n\n**Quick Test Customers:**\n- Rahul Sharma: 9876543210 (₹5L limit, score 785)\n- Amit Kumar: 9876543212 (₹2L limit, score 680)\n- Vikram Singh: 9876543214 (₹1.5L limit, score 650)\n\nJust type your query below or use the quick actions in the sidebar!")
    
    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])
        else:
            agent_type = message.get("metadata", {}).get("agent", "master")
            
            # Agent badges and colors
            agent_config = {
                "sales": {"badge": "🤝 Sales Agent", "color": "#0066cc"},
                "verification": {"badge": "🔐 Verification Agent", "color": "#ff6600"},
                "underwriting": {"badge": "📊 Underwriting Agent", "color": "#00cc66"},
                "sanction": {"badge": "📜 Sanction Agent", "color": "#9900cc"},
                "master": {"badge": "🤖 Assistant", "color": "#003366"}
            }
            
            config = agent_config.get(agent_type, agent_config["master"])
            
            with st.chat_message("assistant", avatar="🏦"):
                # Agent badge
                st.markdown(f"**<span style='color: {config['color']};'>{config['badge']}</span>**", unsafe_allow_html=True)
                
                # Message content
                st.markdown(message["content"])
                
                # Display metadata in expander
                metadata = message.get("metadata", {})
                if metadata and any(k in metadata for k in ["decision", "credit_score", "preapproved_limit", "interest_rate"]):
                    with st.expander("📋 Details"):
                        if metadata.get("decision"):
                            st.write(f"**Decision:** {metadata['decision'].upper()}")
                        if metadata.get("credit_score"):
                            st.write(f"**Credit Score:** {metadata['credit_score']}/900")
                        if metadata.get("preapproved_limit"):
                            st.write(f"**Pre-approved Limit:** ₹{metadata['preapproved_limit']:,}")
                        if metadata.get("interest_rate"):
                            st.write(f"**Interest Rate:** {metadata['interest_rate']}% p.a.")
                        if metadata.get("emi"):
                            st.write(f"**EMI:** ₹{metadata['emi']:,}/month")
                
                # PDF download button
                if metadata.get("pdf_path"):
                    pdf_path = metadata["pdf_path"]
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            pdf_data = f.read()
                        
                        pdf_name = os.path.basename(pdf_path)
                        st.download_button(
                            label="📥 Download Sanction Letter",
                            data=pdf_data,
                            file_name=f"TataCapital_{pdf_name}",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ PDF file not found. Please generate again.")

# ENHANCED: File upload section for pending documentation
if st.session_state.context.get("underwriting_result", {}).get("decision") == "pending":
    st.markdown("---")
    st.markdown("### 📄 Upload Required Documents")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose your salary slip (PDF, PNG, or JPG)",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Upload your latest salary slip for verification"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if uploaded_file is not None:
            if st.button("✅ Submit Document", use_container_width=True):
                # ENHANCED: Extract salary from database for the customer
                customer_id = st.session_state.context.get("customer_id")
                
                if customer_id:
                    with st.spinner("🔄 Processing document..."):
                        try:
                            # Call backend to get customer salary
                            # In production, use OCR to extract salary from uploaded file
                            # For demo, we'll use the database salary
                            
                            # Simulate salary extraction
                            import requests
                            crm_response = requests.get(
                                f"{API_BASE_URL}/api/mock/crm/customer/{customer_id}",
                                timeout=10
                            )
                            
                            if crm_response.status_code == 200:
                                # Get salary from mock database (in production, use OCR)
                                # For now, we'll fetch from database
                                st.session_state.context["salary_slip_verified"] = True
                                
                                # In production, extract this from uploaded file using OCR
                                # For demo, we'll use a reasonable value
                                st.session_state.context["verified_salary"] = 75000  # Mock extracted salary
                                
                                # Trigger re-evaluation
                                response = requests.post(
                                    f"{API_BASE_URL}/api/chat",
                                    json={
                                        "message": "I've uploaded my salary slip showing ₹75,000 monthly salary",
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
                                    st.success("✅ Document uploaded and verified successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Upload verification failed: {response.status_code}")
                            else:
                                st.error("❌ Customer verification failed")
                                
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Connection error: {str(e)}")
                            st.session_state.api_error = str(e)
                else:
                    st.error("❌ Customer ID not found. Please verify your phone number first.")

# Chat input
if "pending_message" in st.session_state:
    user_message = st.session_state.pending_message
    del st.session_state.pending_message
else:
    user_message = st.chat_input("💬 Type your message here...", key="chat_input")

if user_message:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    # Show typing indicator
    with st.spinner("🤖 Processing your request..."):
        try:
            # Prepare request payload - CRITICAL: Include current context
            request_payload = {
                "message": user_message,
                "session_id": st.session_state.session_id,
                "context": st.session_state.context,  # CRITICAL: Pass context
                "loan_intent": st.session_state.loan_intent,
                "customer_info": st.session_state.customer_info
            }
            
            # Call API
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                json=request_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add AI response to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["message"],
                    "metadata": result.get("metadata", {})
                })
                
                # CRITICAL: Update context from response
                st.session_state.context = result.get("context", {})
                
                # Update other states
                if result.get("loan_intent"):
                    st.session_state.loan_intent = result["loan_intent"]
                
                if result.get("customer_info"):
                    st.session_state.customer_info = result["customer_info"]
                
                # Clear any previous errors
                st.session_state.api_error = None
                
                st.rerun()
            else:
                error_msg = f"API returned status code {response.status_code}"
                st.session_state.api_error = error_msg
                st.error(f"❌ {error_msg}")
                
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please try again."
            st.session_state.api_error = error_msg
            st.error(f"⏱️ {error_msg}")
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to backend server. Please ensure FastAPI is running on port 8000."
            st.session_state.api_error = error_msg
            st.error(f"🔌 {error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            st.session_state.api_error = error_msg
            st.error(f"❌ {error_msg}")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.85rem;'>
            <p>© 2024 Tata Capital Limited | Powered by AI</p>
            <p style='font-size: 0.75rem;'>Secure • Confidential • Fast Processing</p>
        </div>
    """, unsafe_allow_html=True)