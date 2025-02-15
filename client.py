import streamlit as st
import requests
import json
import pandas as pd

def process_tool_data(tool_data):
    if not tool_data:
        return None
    try:
        # Parse the JSON string into a Python object
        data = json.loads(tool_data)
        
        # Debug print to see the data structure
        print("Parsed tool data:", data)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Check if DataFrame has the required columns
        required_columns = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell', 'period']
        if not all(col in df.columns for col in required_columns):
            print(f"Missing columns. Available columns: {df.columns.tolist()}")
            return None
            
        # Format period column
        df['period'] = pd.to_datetime(df['period']).dt.strftime('%Y-%m')
        df.set_index('period', inplace=True)
        
        print("Processed DataFrame:", df)
        return df
        
    except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
        print(f"Error processing tool data: {e}")
        print(f"Tool data received: {tool_data}")
        return None

# Set page config to change the title on the navbar
st.set_page_config(page_title="Stonks Chat 📈")

URL = 'http://server:8000'

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
                tool_data = parsed_response.get("tool_data")
                
                # Check if tool_data contains news data by attempting to parse it
                if tool_data:
                    try:
                        data = json.loads(tool_data)
                        # If the data has 'summaries' key, it's from getCompanyNews
                        if 'summaries' in data:
                            # Only display the markdown formatted message from LLM
                            st.markdown(message_content)
                        else:
                            # For other tools like stock recommendations, process and show charts
                            df = process_tool_data(tool_data)
                            if df is not None and not df.empty:
                                st.bar_chart(df[['strongBuy', 'buy', 'hold', 'sell', 'strongSell']])
                            st.markdown(message_content)
                    except json.JSONDecodeError:
                        # If tool_data isn't valid JSON, just show the message
                        st.markdown(message_content)
                else:
                    # If no tool_data, just show the message
                    st.markdown(message_content)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": message_content
                })
            except json.JSONDecodeError:
                st.error("Failed to parse server response as JSON.")
    else:
        st.error("Failed to get response from server.")
        
# Footer for streamlit chat UI
footer = st._bottom.empty()
footer.markdown("---")
footer.markdown("*All responses are **AI generated**, so please __do your own due-diligence__ before making any decisions*")