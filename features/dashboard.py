"""
Dashboard feature module.
Displays statistics and quick actions for the user.
"""

import streamlit as st
import logging
from utils.helpers import get_jakarta_time

logger = logging.getLogger(__name__)


def show_dashboard(db, user_id):
    """Display main dashboard with statistics only."""
    try:
        # Welcome header with modern styling
        current_time = get_jakarta_time()
        hour = current_time.hour
        greeting = "Good Morning ☀️" if hour < 12 else "Good Afternoon 🌤️" if hour < 18 else "Good Evening 🌙"
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h1 style='color: white; margin: 0; font-size: 2rem;'>👋 {greeting}</h1>
            <h2 style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-weight: 400; font-size: 1.5rem;'>{st.session_state['user']['username']}</h2>
            <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;'>📅 {current_time.strftime('%A, %d %B %Y')} | ⏰ {current_time.strftime('%H:%M')} WIB</p>
        </div>
        """, unsafe_allow_html=True)
        
        job_postings = db.get_user_job_postings(user_id)
        
        # Calculate statistics
        total_jobs = len(job_postings)
        total_cvs = sum([len(db.get_cv_analyses_for_job(job['id'])) for job in job_postings])
        avg_cvs_per_job = total_cvs / total_jobs if total_jobs > 0 else 0
        
        # Get all analyses for additional stats
        all_analyses = []
        for job in job_postings:
            all_analyses.extend(db.get_cv_analyses_for_job(job['id']))
        
        avg_score = sum([a['score'] for a in all_analyses]) / len(all_analyses) if all_analyses else 0
        top_candidates = len([a for a in all_analyses if a['score'] >= 80])
        
        # Main Statistics Cards with friendly styling
        st.markdown("### 📊 Your Recruitment Overview")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style='background: #1a1a1a; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #667eea; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
                <p style='margin: 0; font-size: 0.9rem; color: #aaa;'>📋 Active Positions</p>
                <h1 style='margin: 0.5rem 0 0 0; font-size: 2.5rem; color: #667eea;'>{total_jobs}</h1>
                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #666;'>Job Postings</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background: #1a1a1a; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #f093fb; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
                <p style='margin: 0; font-size: 0.9rem; color: #aaa;'>👥 Applications</p>
                <h1 style='margin: 0.5rem 0 0 0; font-size: 2.5rem; color: #f093fb;'>{total_cvs}</h1>
                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #666;'>CVs Reviewed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background: #1a1a1a; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #4facfe; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
                <p style='margin: 0; font-size: 0.9rem; color: #aaa;'>📈 Average Score</p>
                <h1 style='margin: 0.5rem 0 0 0; font-size: 2.5rem; color: #4facfe;'>{avg_score:.1f}</h1>
                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #666;'>Out of 100</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style='background: #1a1a1a; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #43e97b; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
                <p style='margin: 0; font-size: 0.9rem; color: #aaa;'>⭐ Top Talent</p>
                <h1 style='margin: 0.5rem 0 0 0; font-size: 2.5rem; color: #43e97b;'>{top_candidates}</h1>
                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #666;'>Score 80+</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Quick Actions with card styling
        st.markdown("### 🚀 Quick Actions")
        st.markdown("<p style='color: #666; margin-bottom: 1rem;'>Get started with your recruitment tasks</p>", unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("➕ New Job Analysis", use_container_width=True, type="primary"):
                st.session_state["navigate_to"] = "New Analysis"
                st.query_params["page"] = "new_analysis"
                st.rerun()
        
        with col_b:
            if st.button("📊 View All Results", use_container_width=True):
                st.session_state["navigate_to"] = "Analysis History"
                st.query_params["page"] = "analysis_history"
                st.rerun()
        
        with col_c:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        # Recent Activity Summary
        if job_postings:
            st.markdown("---")
            st.subheader("📌 Recent Activity")
            
            recent_jobs = sorted(job_postings, key=lambda x: x['created_at'], reverse=True)[:3]
            
            for job in recent_jobs:
                analyses = db.get_cv_analyses_for_job(job['id'])
                avg_job_score = sum([a['score'] for a in analyses]) / len(analyses) if analyses else 0
                
                st.markdown(f"""
                <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #667eea;'>
                    <h4 style='margin: 0 0 5px 0;'>📋 {job['title']}</h4>
                    <p style='color: #666; font-size: 13px; margin: 0;'>Created: {job['created_at'][:10]} | Candidates: {len(analyses)} | Avg Score: {avg_job_score:.1f}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("👋 Welcome! Start by creating your first job posting in the 'New Analysis' section.")
            
    except Exception as e:
        logger.error(f"Error displaying dashboard: {e}", exc_info=True)
        st.error(f"An error occurred while loading the dashboard: {str(e)}")
