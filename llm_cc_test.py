import pandas as pd
import numpy as np
import pickle
import time
from datetime import datetime
import sys
import os
import math
import oss2
import io
from io import BytesIO
import pickle
import warnings
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict
import psutil
import gc
import math
import gc
from datetime import datetime
from odps.df import DataFrame as ODPSDataFrame  # Important: Alias to avoid confusion with pandas
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from http import HTTPStatus
from dashscope import Application
import dashscope
import math
import time
from odps.df import DataFrame as ODPSDataFrame  # Important: Alias to avoid confusion with pandas
import streamlit as st
import pandas as pd
import requests
from http import HTTPStatus
import ast
from PIL import Image

# Read the Excel file
# df = pd.read_excel('Unique_Remarks.xlsx')
# remarks_sample = df['remarks'].dropna().unique()

# # Set the batch size and saving frequency
# batch_size = 100
# save_every = 1  # Save after every 5 batches

# Setup API endpoint
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
# Ignore all warnings
warnings.filterwarnings("ignore")
# Get the absolute path of the 'util' directory
util_dir = os.path.abspath('/mnt/data/util')
# Add the absolute path to the Python module search path
sys.path.append(util_dir)

# --------------------
# API Call Function
# --------------------
def call_qwen_model(batch_remarks):
    prompt = "\n".join(f"{i+1}. {remark}" for i, remark in enumerate(batch_remarks))
    
    response = Application.call(
        api_key="sk-79768e18331148889d9908693a81ba11",
        app_id='e9aae7dafdf44379bb33ad89a1221e11',
        prompt=prompt
    )

    if response.status_code != HTTPStatus.OK:
        st.error(f"❌ API Error: {response.status_code}, {response.json().get('message', '')}")
        return None

    output_text = response.output.text  # ✅ This is correct for the DashScope SDK
    print(type(output_text))
    print(output_text)
    cleaned_output = output_text.replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned_output)
    df = pd.DataFrame(data)
    # print(df.head())
    return df

# Step 1: Clean the response
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data
# --------------------
# Streamlit App
# --------------------
st.title("📝 Campaign Contents Request Submission")

# st.markdown("Enter multiple content prompts below (one per line):")

sample_input = """Apr25 Comms Materials: OSQR Cashless Songkran Awareniess Campaign
Division: FS
Business: Finance 
Product: CTOS 
Sub-Product / Campaign Name: CTOS_RM3 
Objective: Acquisition 

Push Notification
Date :20250427 - 20250429
Link: tngdwallet://client/dl/webview?url=https%3A%2F%2Fh5-web.tngdigital.com.my%2Fpromotion%2Fcashlesss-songkran-in-thailand
EN Title: Hi 
EN Body: How are you? 
CN Title: 你好
CN Body: 你好吗？
Image Link: tngdwallet://client/dl/webview?url=https%3A%2F%2Fh5-web.tngdigital.com.my%2Fpromotion%2Fcashlesss-songkran-in-thailand 
Target Impression: 10000
Traffic Type: Paid
Campaign Type : Tactical
Target Segment Tag Type: New 
Target Segment: Clicked Travel & Transport P1Y

Dynamic Banner
Date :20250429 - 20250431
Link: tngdwallet://client/dl/webview?url=https%3A%2F%2Fh5-web.tngdigital.com.my%2Fpromotion%2Fcashlesss-songkran-in-thailand
Img Link:tngdwallet://client/dl/webview?url=https%3A%2F%2Fh5-web.tngdigital.com.my%2Fpromotion%2Fcashlesss-songkran-in-Thailand
Priority: 3
Traffic Type: Strategic"""
# Initialize session state
# Preserve state
if "show_instructions" not in st.session_state:
    st.session_state.show_instructions = False
if "generated_df" not in st.session_state:
    st.session_state.generated_df = None
if "excel_data" not in st.session_state:
    st.session_state.excel_data = None

with st.expander("📘 Show Sample Input Format"):
    st.code(sample_input, language="text")

user_input = st.text_area("Content Input", height=300)
submit = st.button("Generate Structured Output")

# Handle submission
if submit and user_input.strip():
    batch_remarks = [line.strip() for line in user_input.strip().split("\n") if line.strip()]
    df = call_qwen_model(batch_remarks)
    print(df)
    if df is not None:
        # Dynamic file name from campaign name + timestamp
        campaign_name = df["Campaign Name"].iloc[0] if "Campaign Name" in df.columns else "output"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{campaign_name}_{timestamp}.xlsx"

        # Save to session state
        st.session_state.generated_df = df
        st.session_state.excel_data = to_excel(df)
        st.session_state.file_name = filename
        st.session_state.show_instructions = True

# Show results and download option
if st.session_state.generated_df is not None:
    st.dataframe(st.session_state.generated_df)
    st.markdown("### 📄 Instructions")
    st.markdown("**Step 1: Review & Click the Download Excel Button to download the file**")

    st.download_button(
        label="📥 Download Excel",
        data=st.session_state.excel_data,
        file_name=st.session_state.get("file_name", "output.xlsx"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Persisted instructions and images
if st.session_state.show_instructions:
    st.markdown("""
    **Step 2:** Upload the downloaded Excel file to [QuickBI](https://bi-ap-southeast-3.data.aliyun.com/form-system/publish/manage/0d8871c2-a596-4473-9a51-05bf192ba4e0) via the **Batch Input** feature. Follow the example steps below.
    """)

    # Replace with your actual image paths
    image1 = Image.open("step1.png")
    st.image(image1, caption="Example Step 1")

    image2 = Image.open("step2.png")
    st.image(image2, caption="Example Step 2")

    image3 = Image.open("step3.png")
    st.image(image3, caption="Example Step 3")

#     if output_text:
#         # This part depends on how your model returns structured data.
#         # Example: let's assume it returns newline-separated CSV-like strings.
#         lines = output_text.strip().split("\n")
#         structured_data = [line.split(",") for line in lines]

#         # Example column names (replace with your actual structure)
#         df = pd.DataFrame(structured_data, columns=["Field1", "Field2", "Field3"])

#         st.success("✅ Structured data generated!")
#         st.dataframe(df)

#         # Optional: Save to a database
#         save = st.checkbox("Save to DB (Simulated)")
#         if save:
#             # You can replace this with actual DB code, e.g., SQLAlchemy, ODPS, etc.
#             st.write("Data would be saved to DB here...")
#             st.json(df.to_dict(orient="records"))
