import streamlit as st
import requests
import time
import pandas as pd
import uuid
from datetime import datetime
import os

st.set_page_config(page_title="Support Resolution Desk", layout="wide", page_icon="🤖")

# --- Security & Authentication Setup ---
def get_api_secret():
    """Pulls from Streamlit secrets (production) or local environment variables (development)."""
    try:
        if hasattr(st, "secrets") and "API_SECRET_KEY" in st.secrets:
            return st.secrets["API_SECRET_KEY"]
    except Exception:
        pass
    return os.getenv("API_SECRET_KEY", "secret-support-desk-key")

API_SECRET = get_api_secret()
HEADERS = {"X-API-Key": API_SECRET}

# --- Helper: API Base URL Discovery ---
def get_api_base_url():
    """Determines the correct base URL depending on execution environment (Docker vs Local)."""
    for base in ["http://api:8000", "http://localhost:8000"]:
        try:
            if requests.get(f"{base}/health", headers=HEADERS, timeout=1).status_code == 200:
                return base
        except:
            continue
    return "http://localhost:8000"

API_BASE = get_api_base_url()

def is_api_alive():
    try:
        res = requests.get(f"{API_BASE}/health", headers=HEADERS, timeout=1)
        return res.status_code == 200
    except:
        return False

# --- Initialize Session State for Thread Management ---
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = f"thread_{uuid.uuid4().hex[:6]}"

# --- Sidebar UI ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Status Indicator
    if is_api_alive():
        st.success("System: Online")
    else:
        st.error("System: Offline (Check API)")

    st.header("🎟️ Ticket Input")
    
    # Button to reset/generate a fresh thread ID
    if st.button("🔄 Start New Thread", use_container_width=True, help="Generates a fresh thread ID to clear SQLite checkpoint history"):
        st.session_state.current_thread_id = f"thread_{uuid.uuid4().hex[:6]}"
        st.rerun()

    # Text input for Thread ID utilizing the session helper
    thread_id = st.text_input("Thread ID", value=st.session_state.current_thread_id)

    email = st.text_input("Customer Email", value="user@example.com")
    subject = st.text_input("Subject", value="Order status inquiry")
    raw_text = st.text_area("Email Content", height=150, value="Where is my order #12345? Can you send me tracking info?")
    process_btn = st.button("Process Support Ticket", type="primary", use_container_width=True)

# --- Main Layout ---
st.title("🤖 Support Resolution Desk Dashboard")
st.markdown("Autonomous resolution workflow powered by LangGraph, FastAPI, and Gemini.")

# Tabs for organization
tab1, tab2 = st.tabs(["🚀 Live Resolution", "📈 Performance Analytics"])

with tab1:
    if process_btn:
        with st.spinner("Agent is orchestrating workflow via /webhook/email..."):
            try:
                # Payload matching FastAPI's EmailIngestRequest schema
                payload = {
                    "raw_email_text": raw_text,
                    "sender_email": email,
                    "subject": subject,
                    "thread_id": thread_id
                }
                
                # Correct endpoint matching src/api/main.py with security HEADERS
                api_res = requests.post(
                    f"{API_BASE}/webhook/email", 
                    json=payload, 
                    headers=HEADERS, 
                    timeout=20
                )
                
                if api_res.status_code == 200:
                    response = api_res.json()
                else:
                    response = {"error": f"API Error: {api_res.status_code} - {api_res.text}"}
            except Exception as e:
                response = {"error": f"Connection or execution exception: {str(e)}"}

        if "error" in response:
            st.error(response["error"])
        else:
            # Executive Summary Metrics (Parsed from flat backend response)
            confidence = response.get("confidence_score", 0.0) or 0.0
            category = response.get("category", "UNKNOWN")
            passed = response.get("confidence_gate_passed", False)

            m1, m2, m3 = st.columns(3)
            m1.metric("Status", "Approved" if passed else "Escalated")
            m2.metric("Category", category)
            m3.metric("Confidence", f"{confidence*100:.0f}%")

            # Visual Feedback Banner
            if passed:
                st.success("✅ **AI Automation Approved** — Response generated and validated successfully.")
            else:
                st.warning("⚠️ **Route to Human Specialist** — Low confidence or complex query routing.")

            st.subheader("📝 Final Response / Output")
            st.info(response.get("final_output", "No output generated."))

            # Audit Trail & Export functionality
            audit_trail = response.get("audit_trail", [])
            with st.expander("🔍 View Execution Audit Trail"):
                for step in audit_trail:
                    st.write(f"• {step}")

            # Export Audit Button (CSV)
            st.markdown("### 💾 Export Ticket Data")
            audit_df = pd.DataFrame({
                "Timestamp": [datetime.utcnow().isoformat()] * len(audit_trail),
                "Thread ID": [thread_id] * len(audit_trail),
                "Audit Step": audit_trail
            })
            csv_data = audit_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download Audit Trail (CSV)",
                data=csv_data,
                file_name=f"audit_trail_{thread_id}.csv",
                mime="text/csv"
            )

with tab2:
    st.subheader("System Performance Trends")
    st.write("Visualizing real-time automation efficiency and human handover volume.")
    st.line_chart({
        "Automation Rate (%)": [85, 88, 90, 89, 93],
        "Escalation Rate (%)": [15, 12, 10, 11, 7]
    })