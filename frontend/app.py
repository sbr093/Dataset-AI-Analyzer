import streamlit as st
import requests

# 1. Dashboard Configuration
st.set_page_config(page_title="AI Data Automation", layout="wide")
st.title("📊 Logistics & Data Insights Dashboard")

# 2. Sidebar for Uploading (keeps the main screen clean)
with st.sidebar:
    st.header("Dataset Management")
    uploaded_file = st.file_uploader("Upload your CSV here", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("Process Dataset"):
            with st.spinner("Analyzing data..."):
                # Send the file to your FastAPI backend
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                response = requests.post("http://127.0.0.1:8000/api/upload", files=files)
                
                if response.status_code == 200:
                    st.success("File processed successfully!")
                    st.session_state['report'] = response.json()
                    st.session_state['filepath'] = f"data/{uploaded_file.name}"
                else:
                    st.error("Failed to process file.")

# 3. Main Screen: Major Metrics Only
if 'report' in st.session_state:
    st.subheader("Major File Metrics")
    
    # Clean, user-friendly visual cards
    col1, col2 = st.columns(2)
    col1.metric("Total Rows Processed", st.session_state['report']['total_rows'])
    col2.metric("Anomalies Detected", st.session_state['report']['anomaly_count'])
    
    st.divider()
    
    # 4. Interactive AI Chat Interface
    st.subheader("🤖 Chat with your Data Agent")
    user_query = st.text_input("Ask a custom question about this dataset:")
    
    if st.button("Ask AI") and user_query:
        with st.spinner("Agent is thinking..."):
            # Send the custom query to your LangGraph routing endpoint
            chat_response = requests.post(
                f"http://127.0.0.1:8000/api/chat?query={user_query}&file_path={st.session_state['filepath']}"
            )
            
            if chat_response.status_code == 200:
                st.info(chat_response.json()["response"])
            else:
                st.error("AI Agent is currently unavailable.")
else:
    st.info("👈 Please upload and process a CSV file in the sidebar to view metrics and enable the AI chatbot.")