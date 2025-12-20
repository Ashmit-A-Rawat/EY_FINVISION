# 🏦 Tata Capital Agentic AI Loan Assistant

**BFSI Challenge II – Personal Loan Sales & Approval Platform**

> An Agentic AI-powered platform that automates the complete NBFC personal loan journey — from conversation to sanction.

---

## 🔗 Live Demo

- **Frontend Application:** https://tatacapitalloanassistant.streamlit.app/
- **Backend API:** https://web-production-c3d87.up.railway.app/
- **Demo Video:** https://drive.google.com/file/d/1tYKaIb-xkqBH_4rBcf_8syzY2U-8o8sn/view

---

## 📋 Table of Contents

- [Live Demo](#-live-demo)
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Agent System](#-agent-system)
- [Installation](#-installation)
- [Usage](#-usage)
- [Underwriting Rules](#-underwriting-rules)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Test Customer Data](#-test-customer-data)
- [Mock BFSI APIs](#-mock-bfsi-apis)
- [Troubleshooting](#-troubleshooting)
- [Key Differentiators](#-key-differentiators)
- [License](#-license)

---

## 🎯 Overview

The **Tata Capital Agentic AI Loan Assistant** is a production-style, multi-agent conversational AI system designed to automate the end-to-end personal loan sales and approval journey for large Non-Banking Financial Companies (NBFCs).

This system replaces traditional form-based workflows with a human-like conversational interface, capable of autonomously performing:

- ✅ Loan discovery and sales conversation
- ✅ Customer verification (KYC/CRM)
- ✅ Credit underwriting and eligibility checks
- ✅ Conditional document handling (salary slip)
- ✅ Automated sanction letter generation (PDF)

The solution is built using a **Master–Worker Agentic AI architecture**, ensuring modularity, scalability, and deterministic BFSI decisioning.

---

## ✨ Key Features

### 🔹 Agentic AI Architecture

- Central Master Agent orchestrating multiple specialized worker agents
- Clear separation of responsibilities across agents
- Context-aware routing and workflow control

### 🔹 End-to-End Loan Automation

- Conversational loan intake
- Automated credit eligibility checks
- Rule-based underwriting aligned with NBFC practices
- Sanction letter generation without human intervention

### 🔹 BFSI-Aligned Decision Logic

- Credit score–based risk evaluation
- Pre-approved limit checks
- EMI-to-salary validation
- Transparent rejection reasoning

### 🔹 Enterprise-Grade UX

- Modern Streamlit chat interface
- Agent-tagged responses
- Real-time application status panel
- Salary slip upload & validation
- One-click PDF sanction letter download

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        Master Agent                        │
│                (Conversation Orchestrator)                 │
└───────────────┬──────────────┬──────────────┬──────────────┘
                │              │              │
        ┌───────▼────-───┐ ┌────▼─────┐ ┌──────▼────────┐ ┌────▼──────┐
        │ Sales Agent    │ │Verification│ │Underwriting│  │Sanction   │
        │ (Engagement)   │ │ Agent      │ │ Agent      │  │ Agent     │
        └────────────────┘ └────────────┘ └────────────┘  └───────────┘
                                   │
                          ┌────────▼────────┐
                          │ MongoDB / Mock  │
                          │ BFSI APIs       │
                          └─────────────────┘
```

### Workflow Overview

```
Customer initiates chat
        ↓
Sales Agent captures intent
        ↓
Verification Agent validates identity
        ↓
Underwriting Agent evaluates eligibility
        ↓
(Optional) Salary slip upload
        ↓
Final decision
        ↓
Sanction Agent generates PDF
```

---

## 💻 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Conversational chatbot UI |
| **Backend** | FastAPI | API & agent orchestration |
| **AI Model** | Google Gemini (gemini-pro) | Natural language understanding |
| **Database** | MongoDB | Customer & offer data |
| **Fallback Storage** | In-memory | Resilience when DB unavailable |
| **Document Engine** | ReportLab | Sanction letter PDF generation |
| **Architecture** | Agentic AI | Modular intelligence |

---

## 🤖 Agent System

### 1. Master Agent (Orchestrator)

**Responsibilities:**
- Interprets user intent
- Maintains session context
- Determines next agent dynamically
- Ensures correct workflow sequencing

### 2. Sales Agent

**Responsibilities:**
- Greets users and builds rapport
- Captures loan amount, tenure, and purpose
- Explains benefits and next steps
- Persuades and transitions to verification

### 3. Verification Agent (KYC/CRM)

**Responsibilities:**
- Extracts phone number from conversation
- Validates customer against CRM data
- Assigns customer ID
- Handles KYC-verified and KYC-pending cases

> **Design Note:** Even with incomplete KYC, underwriting is allowed — reflecting real NBFC pre-eligibility flows.

### 4. Underwriting Agent

**Responsibilities:**
- Applies explicit rule-based credit logic
- Calculates EMI based on tenure
- Validates salary slip when required
- Outputs approval/rejection with reasoning

**Credit Rules:**

| Rule | Condition | Decision |
|------|-----------|----------|
| Rule 1 | Credit score < 700 | ❌ Reject |
| Rule 2 | Loan ≤ pre-approved limit | ✅ Approve |
| Rule 3 | Loan ≤ 2× limit + salary slip | ✅ Approve if EMI ≤ 50% salary |
| Rule 4 | Loan > 2× limit | ❌ Reject |

### 5. Sanction Agent

**Responsibilities:**
- Generates official sanction details
- Creates PDF sanction letter with unique reference number
- Enables download via UI

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- MongoDB (optional - has in-memory fallback)

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd ey_bfsi_loan_assistant
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables

Create a `.env` file in the root directory:

```env
# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB Configuration (optional)
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=loan_assistant

# API Configuration
API_BASE_URL=http://localhost:8000
```

### Step 5: Run the Application

**Terminal 1 - Start Backend Server:**
```bash
uvicorn backend:app --reload --port 8000
```

**Terminal 2 - Start Frontend UI:**
```bash
streamlit run app.py
```

### Access the Application

**Live Deployment:**
- **Frontend:** https://tatacapitalloanassistant.streamlit.app/
- **Backend API:** https://web-production-c3d87.up.railway.app/

**Local Development:**
- **Frontend UI:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

**Demo:**
- **Video Tutorial:** https://drive.google.com/file/d/1tYKaIb-xkqBH_4rBcf_8syzY2U-8o8sn/view

---

## 📱 Usage

### Test Customer Data

Use these pre-seeded phone numbers to test different scenarios:

| Phone | Name | Credit Score | Pre-approved Limit | KYC Status |
|-------|------|--------------|-------------------|------------|
| 9876543210 | Rahul Sharma | 785 | ₹5,00,000 | ✅ Verified |
| 9876543211 | Priya Patel | 720 | ₹3,00,000 | ✅ Verified |
| 9876543212 | Amit Kumar | 680 | ₹2,00,000 | ❌ Pending |
| 9876543213 | Sneha Reddy | 810 | ₹7,00,000 | ✅ Verified |
| 9876543214 | Vikram Singh | 650 | ₹1,50,000 | ✅ Verified |

**These cover approval, conditional approval, and rejection scenarios.**

### Sample Conversations

#### Conversation 1: Quick Approval
```
User: Hi, I need a personal loan
Bot: [Sales Agent engages]
User: My phone is 9876543210
Bot: [Verifies customer]
User: I need 4 lakhs for 2 years
Bot: [Checks eligibility and approves]
User: Yes, generate sanction letter
Bot: [Creates PDF]
```

#### Conversation 2: Additional Documentation Required
```
User: I want 8 lakh loan
User: 9876543210
Bot: [Requires salary slip for higher amount]
User: [Uploads salary slip]
Bot: [Approves after verification]
```

#### Conversation 3: Rejection Due to Low Credit Score
```
User: Hi, I need a loan
User: My number is 9876543214
Bot: [Verifies customer]
User: I need 3 lakhs
Bot: [Rejects due to credit score < 700]
```

---

## 🎯 Underwriting Rules

The system applies deterministic, rule-based credit logic:

1. **Credit Score < 700**: ❌ **Rejected**
   - Reason: Does not meet minimum credit score requirement

2. **Amount ≤ Pre-approved Limit**: ✅ **Approved**
   - Instant approval within existing limit

3. **Amount ≤ 2x Pre-approved Limit**: ⚠️ **Conditional Approval**
   - Requires salary slip upload
   - EMI must be ≤ 50% of monthly salary
   - Auto-approved if condition met

4. **Amount > 2x Pre-approved Limit**: ❌ **Rejected**
   - Reason: Exceeds maximum permissible limit

---

## 📊 API Endpoints

### Main Chat Endpoint

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "I need a loan",
  "session_id": "uuid-string",
  "context": {},
  "loan_intent": {},
  "customer_info": {}
}
```

### Utility Endpoints

- **Health Check**
  ```bash
  GET /api/health
  ```

- **Download Sanction Letter**
  ```bash
  GET /api/download-pdf/{filename}
  ```

### Mock BFSI APIs

- **Customer Lookup (CRM)**
  ```bash
  GET /api/mock/crm/customer/{phone}
  ```

- **Credit Score Check**
  ```bash
  GET /api/mock/credit/score/{customer_id}
  ```

- **Pre-approved Offers**
  ```bash
  GET /api/mock/offer/preapproved/{customer_id}
  ```

- **Salary Slip Upload**
  ```bash
  POST /api/mock/upload/salary-slip
  Content-Type: multipart/form-data
  ```

---

## 🔧 Project Structure

```
ey_bfsi_loan_assistant/
├── agents/
│   ├── master_agent.py       # Orchestration logic
│   ├── sales_agent.py         # Sales conversations
│   ├── verification_agent.py  # KYC verification
│   ├── underwriting_agent.py  # Credit evaluation
│   └── sanction_agent.py      # Letter generation
├── models/
│   └── schemas.py             # Pydantic models
├── services/
│   ├── database.py            # MongoDB + fallback
│   ├── mock_apis.py           # Mock external APIs
│   └── pdf_generator.py       # Sanction letter PDF
├── app.py                     # Streamlit frontend
├── backend.py                 # FastAPI backend
├── requirements.txt           # Dependencies
└── .env                       # Configuration
```

---

## 🧪 Test Customer Data

Pre-seeded test customers for various scenarios:

| Phone | Name | Credit Score | Limit | KYC | Test Scenario |
|-------|------|--------------|-------|-----|---------------|
| 9876543210 | Rahul Sharma | 785 | ₹5,00,000 | ✅ | Quick approval |
| 9876543212 | Amit Kumar | 680 | ₹2,00,000 | ❌ | KYC pending |
| 9876543214 | Vikram Singh | 650 | ₹1,50,000 | ✅ | Credit score rejection |

---

## 🔌 Mock BFSI APIs

To simulate real NBFC integrations, the following mock APIs are implemented:

1. **CRM API** – Customer lookup & KYC verification
2. **Credit Bureau API** – Credit score retrieval
3. **OfferMart API** – Pre-approved offers management
4. **Document Upload API** – Salary slip validation

All implemented as FastAPI mock endpoints with realistic response times and data structures.

---

## 🐛 Troubleshooting

### MongoDB Connection Issues

If MongoDB is not available, the system automatically falls back to in-memory storage:

```
⚠️ MongoDB connection failed
⚠️ Using in-memory fallback storage
```

**Solution:** Install and start MongoDB, or continue with in-memory mode for testing.

### API Connection Errors

Ensure the FastAPI backend is running:

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Expected response
{"status": "healthy", "timestamp": "..."}
```

### Gemini API Errors

Verify your API key is valid:

```bash
# Check .env file
cat .env | grep GEMINI_API_KEY
```

**Common issues:**
- Invalid API key
- Rate limits exceeded
- No internet connection

### Port Already in Use

If port 8000 or 8501 is already in use:

```bash
# Kill the process using the port (Linux/Mac)
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn backend:app --reload --port 8001
streamlit run app.py --server.port 8502
```

---

## 🎨 UI Features

- **Gradient Backgrounds**: Modern, professional design
- **Agent Badges**: Color-coded agent identification
- **Status Indicators**: Real-time application status
- **Quick Actions**: Pre-defined message templates
- **File Upload**: Drag-and-drop document upload
- **PDF Download**: One-click sanction letter download
- **Error Handling**: User-friendly error messages
- **Session Management**: Persistent conversation state

---

## 🌟 Key Differentiators

1. **True Agentic AI Orchestration**
   - Not just a chatbot, but a coordinated multi-agent system

2. **Deterministic BFSI Underwriting Logic**
   - Rule-based decisioning aligned with NBFC practices

3. **End-to-End Automation**
   - From first conversation to PDF sanction letter

4. **Human-like Conversational Sales**
   - Natural language processing for loan discovery

5. **Production-style Sanction Documentation**
   - Professional PDF generation with unique reference numbers

6. **Modular & Scalable Architecture**
   - Easy to extend with new agents and integrations

---

## 📝 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🏆 Conclusion

This project demonstrates how **Agentic AI** can transform NBFC personal loan sales, delivering:

- ⚡ **Faster approvals**
- 📈 **Higher conversion rates**
- 💰 **Reduced operational overhead**
- 🎯 **Maintained credit discipline**
- 🔍 **Complete transparency**

**Submission Tagline:**  
*"An Agentic AI-powered platform that automates the complete NBFC personal loan journey — from conversation to sanction."*

---

**Built with ❤️ for EY BFSI Challenge II**
