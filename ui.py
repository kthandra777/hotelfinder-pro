import streamlit as st
import os
import datetime
from dotenv import load_dotenv
from agents import setup_streamlit_ui

# Page configuration
st.set_page_config(page_title="🏨 HotelFinder Pro", layout="wide")

# Title and subtitle
st.markdown("<h1 style='color: #0066cc;'>🏨 HotelFinder Pro</h1>", unsafe_allow_html=True)
st.subheader("Powered by Browserbase and CrewAI")

# Load environment variables
load_dotenv()

# Main content
st.markdown("---")

# Load the UI from the agents module
setup_streamlit_ui()

# Add some information about the app
st.markdown("---")
st.markdown("""
### About HotelFinder Pro
This application uses AI agents to search for hotels and find the best accommodations for you.
Simply enter your desired location, dates, and number of guests to get started.

Features:
- Real-time hotel availability
- Comprehensive price comparison
- Detailed hotel information and amenities
- Multiple booking options
""")