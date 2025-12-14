"""
AI-Powered CV Screener Application
A comprehensive system for screening and analyzing CVs against job descriptions.

Features:
- User registration and authentication
- CV upload and text extraction
- Intelligent CV scoring and ranking
- Detailed analysis and recommendations
- Database storage for all data
"""

import streamlit as st
from dotenv import load_dotenv
import logging

# Import core modules
from core.database import db
from core.cv_processor import cv_processor

# Import feature modules
from features.auth import show_register_form, show_login_form, logout
from features.dashboard import show_dashboard
from features.analysis import show_new_analysis, show_analysis_history
from features.results import show_results
from features.sidebar import show_sidebar

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cv_screener.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    try:
        # Page configuration
        st.set_page_config(
            page_title="AI CV Screener",
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False
        if "user" not in st.session_state:
            st.session_state["user"] = None
        if "show_login" not in st.session_state:
            st.session_state["show_login"] = True
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Dashboard"
        
        # Custom CSS for dark theme UI
        st.markdown("""
        <style>
            /* Dark theme - Main app styling */
            .stApp {
                background: #0e1117;
            }
            
            /* Button styling - dark theme */
            .stButton>button {
                border-radius: 10px;
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                background: #1e1e1e;
                color: white;
                border: 1px solid #333;
            }
            
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(102,126,234,0.3);
                border-color: #667eea;
            }
            
            /* Primary buttons */
            .stButton>button[kind="primary"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
            }
            
            /* Input fields - dark theme */
            .stTextInput>div>div>input,
            .stTextArea>div>div>textarea {
                border-radius: 10px;
                border: 2px solid #333;
                background: #1e1e1e;
                color: white;
                transition: border-color 0.3s ease;
            }
            
            .stTextInput>div>div>input:focus,
            .stTextArea>div>div>textarea:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
            }
            
            /* Form containers - dark theme */
            div[data-testid="stForm"] {
                background: #1a1a1a;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                border: 1px solid #333;
            }
            
            /* Expanders - dark theme */
            div[data-testid="stExpander"] {
                border-radius: 10px;
                border: 1px solid #333;
                background: #1a1a1a;
            }
            
            /* Sidebar styling - gradient */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            }
            
            section[data-testid="stSidebar"] .stButton>button {
                background: rgba(255,255,255,0.1);
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            section[data-testid="stSidebar"] .stButton>button:hover {
                background: rgba(255,255,255,0.2);
            }
            
            /* Metrics - dark theme */
            div[data-testid="stMetricValue"] {
                font-size: 1.8rem;
                font-weight: 600;
                color: #667eea;
            }
            
            /* File uploader - dark theme */
            div[data-testid="stFileUploader"] {
                background: #1a1a1a;
                border-radius: 10px;
                padding: 1rem;
                border: 2px dashed #333;
            }
            
            /* Info/Warning/Error boxes - dark theme */
            .stAlert {
                background: #1e1e1e;
                border: 1px solid #333;
                color: white;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Check authentication
        if not st.session_state["logged_in"]:
            # Clear URL params on logout
            st.query_params.clear()
            # Show login or register
            if st.session_state["show_login"]:
                show_login_form(db)
            else:
                show_register_form(db)
        else:
            # Show main application
            page = show_sidebar(logout)
            
            # Map URL params to page names
            url_to_page = {
                'dashboard': 'Dashboard',
                'new-analysis': 'New Analysis',
                'history': 'Analysis History',
                'results': 'Results'
            }
            
            page_to_url = {v: k for k, v in url_to_page.items()}
            
            # Update URL if needed
            if page in page_to_url:
                st.query_params['page'] = page_to_url[page]
            
            # Route to appropriate page
            if page == "Dashboard":
                show_dashboard(db, st.session_state['user']['id'])
            elif page == "New Analysis":
                show_new_analysis(db, cv_processor, st.session_state['user']['id'])
            elif page == "Analysis History":
                show_analysis_history(db, st.session_state['user']['id'])
            elif page == "Results":
                show_results(db, cv_processor)
                
        logger.info("Application rendered successfully")
        
    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details.")


if __name__ == "__main__":
    main()
