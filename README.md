# 🏦 Tata Capital AI Loan Assistant

An intelligent, multi-agent AI system for automated loan processing using FastAPI, Streamlit, and OpenAI.

## ✨ Features

- **Multi-Agent Architecture**: Sales, Verification, Underwriting, and Sanction agents working seamlessly
- **Real-time Processing**: Instant loan eligibility checks and approvals
- **Intelligent Routing**: Context-aware agent orchestration
- **KYC Verification**: Automated customer verification system
- **Credit Scoring**: Integration with mock credit bureau APIs
- **PDF Generation**: Automated sanction letter generation
- **Beautiful UI**: Modern, gradient-based Streamlit interface

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Master Agent                             │
│              (Orchestration Layer)                           │
└────────┬────────┬─────────────┬──────────────┬──────────────┘
         │        │             │              │
    ┌────▼───┐ ┌─▼────┐ ┌──────▼─────┐ ┌─────▼────────┐
    │ Sales  │ │ KYC  │ │Underwriting│ │  Sanction    │
    │ Agent  │ │Agent │ │   Agent    │ │   Agent      │
    └────────┘ └──────┘ └────────────┘ └──────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key
- MongoDB (optional - has in-memory fallback)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ey_bfsi_loan_assistant
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration (optional)
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=loan_assistant

# API Configuration
API_BASE_URL=http://localhost:8000
```

### 5. Run the Application

**Terminal 1 - Start Backend:**
```bash
python run.py
# or
uvicorn backend:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run app.py
```

The application will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📱 Usage

### Test Customer Data

Use these phone numbers to test the system:

| Phone       | Name          | Credit Score | Pre-approved Limit | KYC Status |
|-------------|---------------|--------------|-------------------|------------|
| 9876543210  | Rahul Sharma  | 785          | ₹5,00,000        | ✅ Verified |
| 9876543211  | Priya Patel   | 720          | ₹3,00,000        | ✅ Verified |
| 9876543212  | Amit Kumar    | 680          | ₹2,00,000        | ❌ Pending  |
| 9876543213  | Sneha Reddy   | 810          | ₹7,00,000        | ✅ Verified |
| 9876543214  | Vikram Singh  | 650          | ₹1,50,000        | ✅ Verified |

### Sample Conversations

**Conversation 1: Quick Approval**
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

**Conversation 2: Additional Documentation Required**
```
User: I want 8 lakh loan
User: 9876543210
Bot: [Requires salary slip for higher amount]
User: [Uploads salary slip]
Bot: [Approves after verification]
```

## 🎯 Underwriting Rules

1. **Credit Score < 700**: ❌ Rejected
2. **Amount ≤ Pre-approved Limit**: ✅ Approved
3. **Amount ≤ 2x Pre-approved Limit**: 
   - Requires salary slip
   - EMI must be ≤ 50% of salary
4. **Amount > 2x Pre-approved Limit**: ❌ Rejected

## 📊 API Endpoints

### Chat Endpoint
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "I need a loan",
  "session_id": "uuid",
  "context": {},
  "loan_intent": {},
  "customer_info": {}
}
```

### Mock APIs
- `GET /api/mock/crm/customer/{phone}` - Customer lookup
- `GET /api/mock/credit/score/{customer_id}` - Credit score
- `GET /api/mock/offer/preapproved/{customer_id}` - Pre-approved offers
- `POST /api/mock/upload/salary-slip` - Document upload

## 🐛 Troubleshooting

### MongoDB Connection Issues
If MongoDB is not available, the system automatically falls back to in-memory storage. You'll see:
```
⚠️ MongoDB connection failed
⚠️ Using in-memory fallback storage
```

### API Connection Errors
Ensure the FastAPI backend is running:
```bash
# Check if backend is running
curl http://localhost:8000/api/health
```

### OpenAI API Errors
Verify your API key is valid and has credits:
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY
```

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
├── run.py                     # Launch script
├── requirements.txt           # Dependencies
└── .env                       # Configuration
```

## 🎨 UI Features

- **Gradient Backgrounds**: Modern, professional design
- **Agent Badges**: Color-coded agent identification
- **Status Indicators**: Real-time application status
- **Quick Actions**: Pre-defined message templates
- **File Upload**: Drag-and-drop document upload
- **PDF Download**: One-click sanction letter download
- **Error Handling**: User-friendly error messages
- **Session Management**: Persistent conversation state

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for EY BFSI Challenge**