import streamlit as st
import requests
import json
import re
import pandas as pd

# Function to extract data from the text response
def extract_data_from_text(text):
    pattern = r"(\w+ \d{4}):\n\nStrong Buy: (\d+)\nBuy: (\d+)\nHold: (\d+)\nSell: (\d+)\nStrong Sell: (\d+)"
    matches = re.findall(pattern, text)
    data = []
    for match in matches:
        period, strong_buy, buy, hold, sell, strong_sell = match
        data.append({
            "period": period,
            "Strong Buy": int(strong_buy),
            "Buy": int(buy),
            "Hold": int(hold),
            "Sell": int(sell),
            "Strong Sell": int(strong_sell)
        })
    return data

# Set page config to change the title on the navbar
st.set_page_config(page_title="Stonks Chat 📈")

URL = 'http://localhost:8000'

st.title("🔍 Search Stonks")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Mono:wght@400;500;700&family=Geist+Mono:wght@100..900&family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    code {
        font-family: 'Fira Mono', monospace;
    }
    pre {
        font-family: 'Geist Mono', monospace;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Type a message..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send prompt to server and get response
    data = {'prompt': prompt}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(URL, data=json.dumps(data), headers=headers)
    
    if response.status_code == 200:
        with st.chat_message("assistant"):
            full_response = ""
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    full_response += chunk.decode('utf-8')
            
            try:
                parsed_response = json.loads(full_response)
                message_content = parsed_response.get("message", "")
                
                # Extract data from the message content
                data = extract_data_from_text(message_content)
                
                if data:
                    # Create a DataFrame from the extracted data
                    df = pd.DataFrame(data)
                    df.set_index('period', inplace=True)
                    
                    # Sort the DataFrame by the index (period) in descending order
                    df = df.sort_index(ascending=False)
                    
                    # Display the stacked bar chart
                    st.bar_chart(df)
                    
                    # Optionally, you can still display the original message content
                    st.markdown(message_content)
                else:
                    # If no data was extracted, just display the original message
                    st.markdown(message_content)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": message_content})
            except json.JSONDecodeError:
                st.error("Failed to parse server response as JSON.")
    else:
        st.error("Failed to get response from server.")
        
# Footer for streamlit chat UI
footer = st._bottom.empty()
footer.markdown("---")
footer.markdown("*All responses are **AI generated**, so please __do your own due-diligence__ before making any decisions*")