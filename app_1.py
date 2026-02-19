import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/analyze"

st.set_page_config(page_title="Financial Document Analyzer", layout="wide")

st.title("📊 Financial Document Analyzer")
st.markdown("Upload a financial PDF and get investment insights powered by AI.")

# File uploader
uploaded_file = st.file_uploader("Upload Financial PDF", type=["pdf"])

# Query input
query = st.text_area(
    "Enter your analysis query",
    value="Analyze this financial document for investment insights"
)

if st.button("Analyze Document"):

    if uploaded_file is None:
        st.error("Please upload a PDF file first.")
    else:
        with st.spinner("Analyzing document... Please wait ⏳"):

            files = {
                "file": (uploaded_file.name, uploaded_file, "application/pdf")
            }

            data = {
                "query": query
            }

            try:
                response = requests.post(API_URL, files=files, data=data)

                if response.status_code == 200:
                    result = response.json()

                    st.success("Analysis Completed ✅")

                    st.subheader("📌 Query Used")
                    st.write(result.get("query"))

                    st.subheader("📄 File Processed")
                    st.write(result.get("file_processed"))

                    st.subheader("📈 Investment Analysis")
                    st.write(result.get("analysis"))

                else:
                    st.error(f"Error: {response.status_code}")
                    st.json(response.json())

            except Exception as e:
                st.error(f"Connection Error: {str(e)}")