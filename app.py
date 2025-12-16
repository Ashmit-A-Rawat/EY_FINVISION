import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Page config
st.set_page_config(
    page_title="Tata Capital Loan Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.context = {}
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.loan_intent = {}
        st.session_state.customer_info = {}
        st.session_state.api_error = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Application Status")
    
    # Status display - AUTO-REFRESH FIXED
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
            st.markdown('<div class="status-badge badge-warning">❌ Not Approved</div>', unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("---")
    st.markdown("### 💬 Quick Start")
    example_messages = [
        ("💰", "I need a personal loan"),
        ("🏠", "₹5 lakh for home renovation"),
        ("📊", "Check my eligibility"),
        ("📱", "My phone is 9876543210"),
        ("✅", "Yes, generate sanction letter")
    ]
    
    for emoji, msg in example_messages:
        if st.button(f"{emoji} {msg}", use_container_width=True, key=f"quick_{msg}"):
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
            
            if metadata.get("pdf_path"):
                pdf_path = metadata["pdf_path"]
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_data = f.read()
                    st.download_button(
                        label="📥 Download Sanction Letter",
                        data=pdf_data,
                        file_name=f"TataCapital_Sanction.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

# Check if we need to auto-send a follow-up message
if st.session_state.context.get("verification_result", {}).get("verified") and not st.session_state.context.get("underwriting_result"):
    # Auto-trigger underwriting by sending an empty message
    if "underwriting_triggered" not in st.session_state:
        st.session_state.underwriting_triggered = True
        st.session_state.pending_message = "check eligibility"
        st.rerun()

# Chat input
if "pending_message" in st.session_state:
    user_message = st.session_state.pending_message
    del st.session_state.pending_message
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
st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.85rem;'>
        <p>© 2024 Tata Capital Limited | Powered by AI</p>
        <p style='font-size: 0.75rem;'>Secure • Confidential • Fast Processing</p>
    </div>
""", unsafe_allow_html=True)