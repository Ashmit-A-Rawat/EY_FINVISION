import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

from models.schemas import (
    AgentRequest,
    AgentResponse,
    AgentType,
    LoanIntent,
)

from agents.sales_agent import SalesAgent
from agents.verification_agent import VerificationAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.sanction_agent import SanctionAgent

load_dotenv()


class MasterAgent:
    """
    Master Agent
    ------------
    Central orchestrator for the Tata Capital Agentic AI Loan Assistant.
    Owns:
    - Routing logic
    - Conversation state continuity
    - Agent transitions
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-pro")
        else:
            self.model = None
            print("⚠️ Gemini API key not found — running deterministic routing only")

        self.sales_agent = SalesAgent()
        self.verification_agent = VerificationAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.sanction_agent = SanctionAgent()

    # ------------------------------------------------------------------
    # ROUTING LOGIC (CRITICAL FIX)
    # ------------------------------------------------------------------
    def determine_next_agent(
        self,
        message: str,
        context: dict,
        loan_intent: LoanIntent | None,
    ) -> AgentType:
        """
        Deterministic routing logic.
        THIS IS THE MOST IMPORTANT FUNCTION IN THE SYSTEM.
        """

        msg = message.lower().strip()

        # 0️⃣ SANCTION TAKES ABSOLUTE PRIORITY
        if context.get("underwriting_result", {}).get("decision") == "approved":
            if any(
                k in msg
                for k in [
                    "yes",
                    "generate",
                    "sanction",
                    "letter",
                    "download",
                    "ok",
                    "proceed",
                ]
            ):
                return AgentType.SANCTION

        # 1️⃣ IF CUSTOMER IS IDENTIFIED → ALWAYS UNDERWRITING
        # (THIS FIXES YOUR BUG)
        if context.get("customer_id"):
            return AgentType.UNDERWRITING

        # 2️⃣ PHONE NUMBER → VERIFICATION
        if re.search(r"\b\d{10}\b", msg):
            return AgentType.VERIFICATION

        if any(k in msg for k in ["phone", "number", "verify"]):
            return AgentType.VERIFICATION

        # 3️⃣ ELIGIBILITY INTENT → UNDERWRITING (even without amount)
        if any(
            k in msg
            for k in [
                "check eligibility",
                "am i eligible",
                "eligible",
                "can i get",
                "loan status",
            ]
        ):
            return AgentType.UNDERWRITING

        # 4️⃣ DEFAULT → SALES
        return AgentType.SALES

    # ------------------------------------------------------------------
    # LOAN INTENT EXTRACTION
    # ------------------------------------------------------------------
    def extract_loan_intent(
        self, message: str, existing_intent: LoanIntent | None
    ) -> LoanIntent:
        """
        Extract amount, tenure, purpose from message.
        NEVER wipes previously captured intent.
        """

        intent = existing_intent or LoanIntent()
        msg = message.lower()

        # ---------------- AMOUNT ----------------
        if intent.amount is None:
            patterns = [
                r"(\d+(?:\.\d+)?)\s*(lakh|lac)",
                r"₹\s*(\d+(?:,\d{3})+)",
                r"rs\.?\s*(\d+(?:,\d{3})+)",
                r"(\d+(?:\.\d+)?)\s*(k|thousand)",
            ]

            for p in patterns:
                m = re.search(p, msg)
                if not m:
                    continue

                val = float(m.group(1).replace(",", ""))
                unit = m.group(2) if len(m.groups()) > 1 else ""

                if unit in ["lakh", "lac"]:
                    intent.amount = val * 100000
                elif unit in ["k", "thousand"]:
                    intent.amount = val * 1000
                else:
                    intent.amount = val

                break

        # ---------------- TENURE ----------------
        if intent.tenure is None:
            m = re.search(r"(\d+)\s*(year|month)", msg)
            if m:
                t = int(m.group(1))
                intent.tenure = t * 12 if "year" in m.group(2) else t

        # Default tenure
        if intent.amount and intent.tenure is None:
            intent.tenure = 24

        # ---------------- PURPOSE ----------------
        if intent.purpose is None:
            for p in [
                "home",
                "car",
                "education",
                "medical",
                "business",
                "wedding",
                "renovation",
                "emergency",
            ]:
                if p in msg:
                    intent.purpose = p.capitalize()
                    break

        return intent

    # ------------------------------------------------------------------
    # MAIN ORCHESTRATION
    # ------------------------------------------------------------------
    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Entry point for all chat messages.
        """

        try:
            context = request.context.copy() if request.context else {}

            # Extract & persist intent
            loan_intent = self.extract_loan_intent(
                request.message, request.loan_intent
            )

            if loan_intent.amount:
                context["loan_intent"] = loan_intent.dict()

            # Decide agent
            next_agent = self.determine_next_agent(
                request.message, context, loan_intent
            )

            # Debug
            print("\n" + "=" * 70)
            print("🧠 MASTER AGENT")
            print(f"Message: {request.message}")
            print(f"Next Agent: {next_agent}")
            print(f"Customer ID: {context.get('customer_id')}")
            print(f"Loan Intent: {loan_intent}")
            print("=" * 70 + "\n")

            # Build downstream request
            agent_request = AgentRequest(
                message=request.message,
                session_id=request.session_id,
                customer_info=request.customer_info,
                loan_intent=loan_intent,
                context=context,
            )

            # Route
            if next_agent == AgentType.SALES:
                response = self.sales_agent.process(agent_request)
            elif next_agent == AgentType.VERIFICATION:
                response = self.verification_agent.process(agent_request)
            elif next_agent == AgentType.UNDERWRITING:
                response = self.underwriting_agent.process(agent_request)
            elif next_agent == AgentType.SANCTION:
                response = self.sanction_agent.process(agent_request)
            else:
                response = self.sales_agent.process(agent_request)

            # Merge context safely
            if response.context:
                context.update(response.context)

            context["current_agent"] = next_agent.value

            response.context = context
            response.loan_intent = loan_intent
            response.next_agent = next_agent

            return response

        except Exception as e:
            print("❌ MASTER AGENT ERROR:", e)
            import traceback

            traceback.print_exc()

            return AgentResponse(
                message=(
                    "I ran into a technical issue. "
                    "Could you please tell me the loan amount and your phone number?"
                ),
                next_agent=AgentType.SALES,
                context=request.context or {},
                metadata={"error": str(e)},
            )
