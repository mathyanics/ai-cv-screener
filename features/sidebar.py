"""
Sidebar navigation module.
Displays sidebar with navigation menu and user information.
"""

import streamlit as st
import logging
from utils.helpers import get_jakarta_time

logger = logging.getLogger(__name__)


def show_sidebar(logout_callback):
    """Display sidebar navigation with styled menu buttons."""
    try:
        st.sidebar.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; margin: 0;'>🎯</h1>
            <h3 style='margin: 5px 0; color: white;'>CV Screener</h3>
            <p style='color: rgba(255,255,255,0.8); font-size: 12px; margin: 0;'>AI-Powered Recruitment</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown(f"""<div style='background: rgba(255,255,255,0.15); padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.2);'>
        <p style='margin: 0; color: white; font-weight: bold;'>👤 {st.session_state['user']['username']}</p>
        <p style='margin: 0; color: rgba(255,255,255,0.8); font-size: 12px;'>{st.session_state['user']['email']}</p>
        </div>""", unsafe_allow_html=True)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📍 Navigation")
        
        # URL to page name mapping
        url_to_page = {
            'dashboard': 'Dashboard',
            'new-analysis': 'New Analysis',
            'history': 'Analysis History',
            'results': 'Results'
        }
        
        # Get current page from URL query params or session state
        query_params = st.query_params
        if 'page' in query_params and query_params['page'] in url_to_page:
            page = url_to_page[query_params['page']]
            st.session_state["current_page"] = page
        elif "navigate_to" in st.session_state:
            page = st.session_state["navigate_to"]
            del st.session_state["navigate_to"]
            st.session_state["current_page"] = page
        else:
            page = st.session_state.get("current_page", "Dashboard")
        
        # Menu items with icons
        menu_items = [
            ("Dashboard", "📊", "dashboard"),
            ("New Analysis", "➕", "new-analysis"),
            ("Analysis History", "📚", "history"),
            ("Results", "📋", "results")
        ]
        
        for menu_name, icon, url_param in menu_items:
            is_active = (page == menu_name)
            button_style = "primary" if is_active else "secondary"
            
            if st.sidebar.button(
                f"{icon} {menu_name}",
                key=f"nav_{menu_name}",
                use_container_width=True,
                type=button_style if is_active else "secondary",
                disabled=is_active
            ):
                st.session_state["current_page"] = menu_name
                st.query_params["page"] = url_param
                st.rerun()
        
        st.sidebar.markdown("---")
        
        # System info
        current_time = get_jakarta_time()
        time_icon = "⏰"
        date_icon = "📅"
        st.sidebar.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; font-size: 11px; color: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,0.2);'>
            <p style='margin: 0;'>{time_icon} {current_time.strftime('%H:%M:%S')} WIB</p>
            <p style='margin: 0;'>{date_icon} {current_time.strftime('%d %b %Y')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("")
        st.sidebar.button("🚪 Logout", on_click=logout_callback, use_container_width=True)
        
        return page
        
    except Exception as e:
        logger.error(f"Error in show_sidebar: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        return "Dashboard"
