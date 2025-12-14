"""
Results feature module.
Displays CV analysis results with detailed scoring and candidate information.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import json
import ast

logger = logging.getLogger(__name__)


def show_results(db, cv_processor):
    """Display CV analysis results for a specific job."""
    try:
        # Get job_id from URL params or session state
        query_params = st.query_params
        if 'job_id' in query_params:
            job_id = int(query_params['job_id'])
            st.session_state["view_job_id"] = job_id
        elif "view_job_id" in st.session_state:
            job_id = st.session_state["view_job_id"]
            # Update URL with job_id
            st.query_params["job_id"] = str(job_id)
        else:
            st.warning("⚠️ No job selected. Please select a job from Analysis History.")
            if st.button("← Back to Analysis History"):
                st.session_state["navigate_to"] = "Analysis History"
                st.query_params.clear()
                st.rerun()
            return
        
        analyses = db.get_cv_analyses_for_job(job_id)
        
        if not analyses:
            st.warning("No CVs analyzed for this job yet.")
            return
        
        st.title("📊 CV Analysis Results")
        
        # Summary statistics
        st.subheader("📈 Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total CVs", len(analyses))
        with col2:
            avg_score = sum([a['score'] for a in analyses]) / len(analyses)
            st.metric("Average Score", f"{avg_score:.1f}")
        with col3:
            top_score = max([a['score'] for a in analyses])
            st.metric("Top Score", f"{top_score:.1f}")
        with col4:
            recommended = len([a for a in analyses if a['score'] >= 60])
            st.metric("Recommended", recommended)
        
        # Score distribution chart
        st.subheader("📊 Score Distribution")
        
        # Extract candidate names for chart using stored parsed info
        chart_data = []
        
        for i, analysis in enumerate(analyses, 1):
            # Get parsed info from database (no re-parsing needed)
            parsed_info = db.get_cv_parsed_info(analysis['cv_id'])
            
            if parsed_info:
                candidate_name = parsed_info.get('name', f'Candidate #{i}')
            else:
                candidate_name = f'Candidate #{i}'
            
            chart_data.append({
                'name': candidate_name,
                'score': analysis['score']
            })
        
        df = pd.DataFrame(chart_data)
        
        fig = px.bar(
            df,
            x='name',
            y='score',
            color='score',
            color_continuous_scale='RdYlGn',
            labels={'name': 'Candidate', 'score': 'Score'},
            title='Candidate Scores',
            text='score'
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed results
        st.subheader("📋 Detailed Analysis")
        
        # Add filtering
        filter_option = st.selectbox(
            "Filter by recommendation:",
            ["All", "Strongly Recommend (80+)", "Recommend (60-79)", "Consider (40-59)", "Reject (0-39)"]
        )
        
        filtered_analyses = analyses
        if filter_option == "Strongly Recommend (80+)":
            filtered_analyses = [a for a in analyses if a['score'] >= 80]
        elif filter_option == "Recommend (60-79)":
            filtered_analyses = [a for a in analyses if 60 <= a['score'] < 80]
        elif filter_option == "Consider (40-59)":
            filtered_analyses = [a for a in analyses if 40 <= a['score'] < 60]
        elif filter_option == "Reject (0-39)":
            filtered_analyses = [a for a in analyses if a['score'] < 40]
        
        # Prepare table data
        table_data = []
        
        for i, analysis in enumerate(filtered_analyses, 1):
            score = analysis['score']
            
            # Get parsed info from database (no re-parsing needed)
            parsed_info = db.get_cv_parsed_info(analysis['cv_id'])
            
            if parsed_info:
                candidate_name = parsed_info.get('name', f'Candidate #{i}')
                email = parsed_info.get('email', 'N/A')
                phone = parsed_info.get('phone', 'N/A')
            else:
                # Fallback if no parsed info available
                candidate_name = f'Candidate #{i}'
                email = 'N/A'
                phone = 'N/A'
            
            # Recommendation badge
            if score >= 80:
                badge = "🟢 Strongly Recommend"
            elif score >= 60:
                badge = "🟡 Recommend"
            elif score >= 40:
                badge = "🟠 Consider"
            else:
                badge = "🔴 Reject"
            
            table_data.append({
                'rank': i,
                'name': candidate_name,
                'email': email,
                'phone': phone,
                'score': score,
                'recommendation': badge,
                'cv_id': analysis['cv_id'],
                'analysis': analysis
            })
        
        # Display as professional table
        st.markdown("### 📋 Candidates Overview")
        
        for candidate in table_data:
            # Create a card for each candidate
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"""
                <div style='background: #1a1a1a; padding: 15px; border-radius: 8px; border-left: 4px solid {"#10b981" if candidate["score"] >= 80 else "#f59e0b" if candidate["score"] >= 60 else "#ef4444"}; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
                    <h4 style='margin: 0 0 8px 0; color: #fff;'>#{candidate['rank']} {candidate['name']}</h4>
                    <p style='margin: 0; color: #aaa; font-size: 13px;'>📧 {candidate['email']} | 📱 {candidate['phone']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Score", f"{candidate['score']:.0f}/100", delta=candidate['recommendation'])
            
            with col3:
                if st.button("📄 Details", key=f"detail_{candidate['cv_id']}", use_container_width=True):
                    st.session_state[f"show_detail_{candidate['cv_id']}"] = True
            
            # Show details if button clicked
            if st.session_state.get(f"show_detail_{candidate['cv_id']}", False):
                _show_candidate_details(candidate, db, cv_processor)
                
    except Exception as e:
        logger.error(f"Error in show_results: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")


def _show_candidate_details(candidate, db, cv_processor):
    """Display detailed information for a candidate."""
    try:
        with st.container():
            st.markdown("---")
            analysis = candidate['analysis']
            
            # Close button
            if st.button("✖ Close", key=f"close_{candidate['cv_id']}"):
                st.session_state[f"show_detail_{candidate['cv_id']}"] = False
                st.rerun()
        
            # Candidate Biography Section
            st.markdown("""<div style='background: #f1f5f9; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>""", unsafe_allow_html=True)
            st.markdown("### 👤 Candidate Profile")
            
            # Get CV content from database
            cv_content = db.get_cv_content(analysis['cv_id'])
            
            if cv_content:
                # Extract biography/personal info from CV
                sections = cv_processor.extract_cv_sections(cv_content)
                
                bio_col1, bio_col2 = st.columns(2)
                
                with bio_col1:
                    st.markdown("**👤 Name:**")
                    st.text(candidate['name'])
                    st.markdown("**📧 Email:**")
                    st.text(candidate['email'])
                    st.markdown("**📱 Phone:**")
                    st.text(candidate['phone'])
                
                with bio_col2:
                    st.markdown("**📄 File Information:**")
                    st.text(f"File: {analysis['file_name']}")
                    st.text(f"Uploaded: {analysis['uploaded_at'][:16]} WIB")
                    st.text(f"Analyzed: {analysis['analyzed_at'][:16]} WIB")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Parse and display detailed scoring reasons
            try:
                # Try to parse scoring reasons from detailed_analysis field
                try:
                    reasons_dict = ast.literal_eval(analysis['detailed_analysis'])
                except:
                    # Try JSON parse
                    try:
                        reasons_dict = json.loads(analysis['detailed_analysis'])
                    except:
                        reasons_dict = {}
                
                # Display Detailed Scoring Breakdown
                if reasons_dict:
                    st.markdown("### 📊 Detailed Scoring Breakdown")
                    st.markdown("<p style='color: #aaa; margin-bottom: 1rem;'>Weighted scores: LLM evaluation (0-100) × Manual weights</p>", unsafe_allow_html=True)
                    
                    score_col1, score_col2 = st.columns(2)
                    
                    with score_col1:
                        # Experience
                        if 'experience_score' in reasons_dict:
                            raw_score = reasons_dict.get('experience_score_raw', 0)
                            weighted_score = reasons_dict['experience_score']
                            st.markdown(f"""
                            <div style='background: #1e1e1e; padding: 1rem; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 1rem;'>
                                <p style='margin: 0; color: #667eea; font-weight: bold;'>💼 Experience: {weighted_score}/30</p>
                                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #888;'>LLM Score: {raw_score}/100 × Weight: 30%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.info(reasons_dict.get('experience_reason', 'N/A'))
                        
                        # Skills  
                        if 'skills_score' in reasons_dict:
                            raw_score = reasons_dict.get('skills_score_raw', 0)
                            weighted_score = reasons_dict['skills_score']
                            st.markdown(f"""
                            <div style='background: #1e1e1e; padding: 1rem; border-radius: 8px; border-left: 4px solid #4facfe; margin-bottom: 1rem;'>
                                <p style='margin: 0; color: #4facfe; font-weight: bold;'>🔧 Skills: {weighted_score}/20</p>
                                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #888;'>LLM Score: {raw_score}/100 × Weight: 20%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.info(reasons_dict.get('skills_reason', 'N/A'))
                        
                        # Certifications
                        if 'certs_extras_score' in reasons_dict:
                            raw_score = reasons_dict.get('certs_extras_score_raw', 0)
                            weighted_score = reasons_dict['certs_extras_score']
                            st.markdown(f"""
                            <div style='background: #1e1e1e; padding: 1rem; border-radius: 8px; border-left: 4px solid #43e97b; margin-bottom: 1rem;'>
                                <p style='margin: 0; color: #43e97b; font-weight: bold;'>🏆 Certifications & Extras: {weighted_score}/10</p>
                                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #888;'>LLM Score: {raw_score}/100 × Weight: 10%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.info(reasons_dict.get('certs_extras_reason', 'N/A'))
                    
                    with score_col2:
                        # Impact
                        if 'impact_score' in reasons_dict:
                            raw_score = reasons_dict.get('impact_score_raw', 0)
                            weighted_score = reasons_dict['impact_score']
                            st.markdown(f"""
                            <div style='background: #1e1e1e; padding: 1rem; border-radius: 8px; border-left: 4px solid #f093fb; margin-bottom: 1rem;'>
                                <p style='margin: 0; color: #f093fb; font-weight: bold;'>🚀 Impact: {weighted_score}/20</p>
                                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #888;'>LLM Score: {raw_score}/100 × Weight: 20%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.info(reasons_dict.get('impact_reason', 'N/A'))

                        # Education
                        if 'education_score' in reasons_dict:
                            raw_score = reasons_dict.get('education_score_raw', 0)
                            weighted_score = reasons_dict['education_score']
                            st.markdown(f"""
                            <div style='background: #1e1e1e; padding: 1rem; border-radius: 8px; border-left: 4px solid #764ba2; margin-bottom: 1rem;'>
                                <p style='margin: 0; color: #764ba2; font-weight: bold;'>🎓 Education: {weighted_score}/20</p>
                                <p style='margin: 0.3rem 0 0 0; font-size: 0.8rem; color: #888;'>LLM Score: {raw_score}/100 × Weight: 20%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.info(reasons_dict.get('education_reason', 'N/A'))
                    
                    st.markdown("---")
                
                # Display Strengths and Weaknesses
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ✅ Strengths")
                    if 'strengths' in reasons_dict and reasons_dict['strengths']:
                        for strength in reasons_dict['strengths']:
                            st.success(f"✓ {strength}")
                    else:
                        st.info("No specific strengths listed")
                
                with col2:
                    st.markdown("### ⚠️ Areas for Consideration")
                    if 'weaknesses' in reasons_dict and reasons_dict['weaknesses']:
                        for weakness in reasons_dict['weaknesses']:
                            st.warning(f"• {weakness}")
                    else:
                        st.info("No specific concerns listed")

                # Red Flags
                if 'red_flags' in reasons_dict and reasons_dict['red_flags']:
                    st.markdown("### ❗ Red Flags")
                    for flag in reasons_dict['red_flags']:
                        st.error(f"• {flag}")
                
                # Summary
                if 'summary' in reasons_dict and reasons_dict['summary']:
                    st.markdown("### 📝 Overall Assessment")
                    st.info(reasons_dict['summary'])
                
            except Exception as e:
                # Fallback if parsing fails
                logger.warning(f"Error parsing analysis details: {e}", exc_info=True)
                st.markdown("### 📝 Analysis Details")
                if analysis.get('detailed_analysis'):
                    st.markdown(analysis['detailed_analysis'])
                if analysis.get('reasons'):
                    st.markdown(analysis['reasons'])
            
            st.caption(f"📅 Analyzed: {analysis['analyzed_at'][:16]} WIB")
            
    except Exception as e:
        logger.error(f"Error in _show_candidate_details: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
