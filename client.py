import streamlit as st
import requests
import json
import pandas as pd
import altair as alt
import time

def process_tool_data(tool_data):
    if not tool_data:
        return None
    try:
        data = json.loads(tool_data)
        df = pd.DataFrame(data)
        
        required_columns = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell', 'period']
        if not all(col in df.columns for col in required_columns):
            print(f"Missing columns. Available columns: {df.columns.tolist()}")
            return None
            
        df['period'] = pd.to_datetime(df['period']).dt.strftime('%Y-%m')
        
        df_melted = df.melt(
            id_vars=['period'],
            value_vars=['strongBuy', 'buy', 'hold', 'sell', 'strongSell'],
            var_name='Recommendation',
            value_name='Count'
        )
        
        return df_melted
        
    except Exception as e:
        print(f"Error processing tool data: {e}")
        return None

def create_altair_chart(df):
    if df is None or df.empty:
        return None
        
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('period:N', title='Period'),
        y=alt.Y('Count:Q', title='Number of Recommendations'),
        color=alt.Color('Recommendation:N', 
            scale=alt.Scale(
                domain=['strongBuy', 'buy', 'hold', 'sell', 'strongSell'],
                range=['#1a9850', '#91cf60', '#ffffbf', '#fc8d59', '#d73027']
            )
        ),
        tooltip=['period', 'Recommendation', 'Count']
    ).properties(
        width=600,
        height=400,
        title='Analyst Recommendations'
    )
    
    return chart

def reset_server_state():
    """Reset the server state completely"""
    try:
        reset_response = requests.post(f"{URL}/reset")
        if reset_response.status_code == 200:
            print("Server state reset successfully")
        else:
            print(f"Failed to reset server state: {reset_response.status_code}")
    except Exception as e:
        print(f"Error resetting server state: {e}")

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

# Initialize session state for conversation
if "conversation" not in st.session_state:
    st.session_state.conversation = []
    st.session_state.message_counter = 0
    st.session_state.current_chart_id = None  # Track which message has a chart

# Function to render all messages including charts
def render_conversation():
    for message in st.session_state.conversation:
        with st.chat_message(message["role"]):
            # Always render the content
            st.markdown(message["content"])
            
            # Handle chart rendering - only for the current active chart
            if message.get("chart_data") and message.get("id") == st.session_state.current_chart_id:
                df = process_tool_data(message["chart_data"])
                if df is not None and not df.empty:
                    chart = create_altair_chart(df)
                    if chart:
                        # Generate a unique key for this chart
                        chart_key = f"chart_{message.get('id', 'default')}"
                        st.altair_chart(chart, use_container_width=True, key=chart_key)

# Render existing conversation
render_conversation()

# Accept user input
if prompt := st.chat_input("Type a message..."):
    # IMPORTANT: Reset chart state completely for ALL messages when new prompt received
    for message in st.session_state.conversation:
        if "chart_data" in message:
            message["chart_data"] = None
    
    # Create a new user message
    user_message = {
        "role": "user",
        "content": prompt,
        "id": f"user_{st.session_state.message_counter}"
    }
    st.session_state.message_counter += 1
    
    # Add to conversation and display
    st.session_state.conversation.append(user_message)
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Create API request
    data = {'prompt': prompt}
    headers = {'Content-Type': 'application/json'}
    
    # Process response with a placeholder
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        # Get response from server
        response = requests.post(URL, data=json.dumps(data), headers=headers)
        
        if response.status_code == 200:
            try:
                # Parse response data
                parsed_response = json.loads(response.content)
                message_content = parsed_response.get("message", "")
                tool_data = parsed_response.get("tool_data")
                tool_type = parsed_response.get("tool_type")
                message_id = parsed_response.get("message_id") or f"assistant_{st.session_state.message_counter}"
                
                # Update placeholder with response text
                message_placeholder.markdown(message_content)
                
                # Create assistant message with proper ID
                assistant_message = {
                    "role": "assistant",
                    "content": message_content,
                    "id": message_id,
                    "chart_data": None  # Will be set only if chart data exists
                }
                st.session_state.message_counter += 1
                
                # Handle chart data if present
                chart_container = st.container()
                if tool_data and tool_type == "chart":
                    # Store chart data in message
                    assistant_message["chart_data"] = tool_data
                    st.session_state.current_chart_id = message_id
                    
                    # Display chart for current response
                    with chart_container:
                        df = process_tool_data(tool_data)
                        if df is not None and not df.empty:
                            chart = create_altair_chart(df)
                            if chart:
                                # Use message ID as part of chart key
                                st.altair_chart(chart, use_container_width=True, key=f"new_chart_{message_id}")
                
                # Add message to conversation
                st.session_state.conversation.append(assistant_message)
                
            except json.JSONDecodeError:
                message_placeholder.error("Failed to parse server response as JSON.")
        else:
            message_placeholder.error(f"Error from server: {response.status_code}")
        
# Footer for streamlit chat UI
footer = st._bottom.empty()
footer.markdown("---")
footer.markdown("*All responses are **AI generated**, so please __do your own due-diligence__ before making any decisions*")