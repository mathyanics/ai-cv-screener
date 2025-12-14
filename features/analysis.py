"""
Analysis feature module.
Handles CV upload, extraction, parsing, and analysis.
"""

import streamlit as st
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def show_new_analysis(db, cv_processor, user_id):
    """Display new CV analysis interface."""
    try:
        st.title("🆕 New CV Analysis")
        
        # Job posting input
        st.subheader("1️⃣ Job Description")
        
        job_title = st.text_input("Job Title", placeholder="e.g., Senior Python Developer")
        job_description = st.text_area(
            "Job Description and Requirements",
            placeholder="Enter the complete job description including required skills, experience, qualifications...",
            height=250
        )
        
        # CV upload
        st.subheader("2️⃣ Upload CVs")
        uploaded_files = st.file_uploader(
            "Upload Candidate CVs (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="You can upload multiple CV files at once"
        )
        
        if uploaded_files:
            st.info(f"✅ {len(uploaded_files)} CV(s) uploaded")
        
        # Analysis button
        st.markdown("---")
        
        if st.button("🚀 Start Analysis", type="primary", disabled=not (job_title and job_description and uploaded_files)):
            analyze_cvs(job_title, job_description, uploaded_files, db, cv_processor, user_id)
            
    except Exception as e:
        logger.error(f"Error in show_new_analysis: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")


def analyze_cvs(job_title, job_description, uploaded_files, db, cv_processor, user_id):
    """Process and analyze all CVs."""
    try:
        logger.info(f"Starting CV analysis for job: {job_title}")
        
        # Import LLM and analyzer
        from utils.llm_engine import get_llm
        from core.cv_analyzer import CVAnalyzer
        
        # Get LLM
        llm = get_llm()
        
        if not llm:
            st.error("Failed to initialize AI model. Check your CEREBRAS_API_KEY in .env file.")
            logger.error("LLM initialization failed")
            return
        
        # Create CV analyzer
        analyzer = CVAnalyzer(llm)
        
        # Create job posting
        job_id = db.create_job_posting(user_id, job_title, job_description)
        st.success(f"✅ Job posting created: {job_title}")
        logger.info(f"Job posting created with ID: {job_id}")
        
        # STEP 1: Extract text from all CVs
        st.subheader("📥 Step 1: Extracting CV Content...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        cv_raw_list = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Extracting text from {uploaded_file.name}...")
            
            try:
                # Extract text from CV
                cv_text = cv_processor.extract_text_from_file(uploaded_file)
                
                # Save CV to database
                cv_id = db.save_cv(job_id, uploaded_file.name, cv_text)
                
                cv_raw_list.append({
                    'file_name': uploaded_file.name,
                    'text': cv_text,
                    'cv_id': cv_id
                })
                logger.info(f"CV extracted: {uploaded_file.name} (cv_id: {cv_id})")
                
            except Exception as e:
                logger.error(f"Error processing {uploaded_file.name}: {e}", exc_info=True)
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        progress_bar.empty()
        status_text.empty()
        
        # STEP 2: Parse all CV information with LLM
        st.subheader("🧠 Step 2: Parsing CV Information with AI...")
        parse_progress = st.progress(0)
        status_text = st.empty()
        
        parsed_cv_list = []
        
        for i, cv_data in enumerate(cv_raw_list):
            status_text.text(f"Parsing {cv_data['file_name']}...")
            
            try:
                # Extract ALL information using LLM
                parsed_info = cv_processor.extract_candidate_info_with_llm(cv_data['text'], llm)
                
                # Save parsed info to database
                db.update_cv_parsed_info(cv_data['cv_id'], json.dumps(parsed_info))
                
                parsed_cv_list.append({
                    'file_name': cv_data['file_name'],
                    'cv_id': cv_data['cv_id'],
                    'raw_text': cv_data['text'],
                    'parsed_info': parsed_info,
                    'candidate_number': i + 1  # Anonymous numbering
                })
                logger.info(f"CV parsed: {cv_data['file_name']}")
                
            except Exception as e:
                logger.warning(f"LLM parsing failed for {cv_data['file_name']}, using fallback: {e}")
                st.warning(f"LLM parsing failed for {cv_data['file_name']}, using fallback: {str(e)}")
                # Fallback to basic extraction
                parsed_info = cv_processor._fallback_extraction(cv_data['text'])
                
                # Save fallback parsed info
                db.update_cv_parsed_info(cv_data['cv_id'], json.dumps(parsed_info))
                
                parsed_cv_list.append({
                    'file_name': cv_data['file_name'],
                    'cv_id': cv_data['cv_id'],
                    'raw_text': cv_data['text'],
                    'parsed_info': parsed_info,
                    'candidate_number': i + 1
                })
            
            parse_progress.progress((i + 1) / len(cv_raw_list))
        
        parse_progress.empty()
        status_text.empty()
        
        # STEP 3: Analyze CVs anonymously (concurrent)
        st.subheader("🎯 Step 3: Analyzing CVs Anonymously...")
        analysis_progress = st.progress(0)
        status_text.text("Processing multiple CVs in parallel...")
        
        completed = 0
        total = len(parsed_cv_list)
        
        def analyze_single_cv(cv_data):
            """Analyze a single CV anonymously."""
            try:
                # Use full raw text (no truncation)
                analysis = analyzer.score_cv(
                    job_description, 
                    cv_data['raw_text'],
                    cv_data['candidate_number']
                )
                return (cv_data, analysis, None)
            except Exception as e:
                logger.error(f"Error analyzing candidate #{cv_data['candidate_number']}: {e}", exc_info=True)
                return (cv_data, None, str(e))
        
        # Concurrent processing
        with ThreadPoolExecutor(max_workers=min(5, total)) as executor:
            futures = {executor.submit(analyze_single_cv, cv_data): cv_data for cv_data in parsed_cv_list}
            
            for future in as_completed(futures):
                cv_data, analysis, error = future.result()
                completed += 1
                
                status_text.text(f"Completed {completed}/{total}: Candidate #{cv_data['candidate_number']}")
                analysis_progress.progress(completed / total)
                
                if error:
                    st.error(f"Error analyzing Candidate #{cv_data['candidate_number']}: {error}")
                elif analysis:
                    # Save with detailed scoring reasons
                    scoring_reasons = {
                        'experience_score': analysis.get('experience_score', 0),
                        'experience_reason': analysis.get('experience_reason', ''),
                        'impact_score': analysis.get('impact_score', 0),
                        'impact_reason': analysis.get('impact_reason', ''),
                        'skills_score': analysis.get('skills_score', 0),
                        'skills_reason': analysis.get('skills_reason', ''),
                        'education_score': analysis.get('education_score', 0),
                        'education_reason': analysis.get('education_reason', ''),
                        'certs_extras_score': analysis.get('certs_extras_score', 0),
                        'certs_extras_reason': analysis.get('certs_extras_reason', ''),
                        'red_flags': analysis.get('red_flags', []),
                        'strengths': analysis.get('strengths', []),
                        'weaknesses': analysis.get('weaknesses', []),
                        'summary': analysis.get('summary', '')
                    }
                    
                    db.save_cv_analysis(
                        cv_data['cv_id'],
                        analysis['score'],
                        str(analysis),
                        str(scoring_reasons),
                        cv_data['candidate_number']
                    )
                    logger.info(f"Analysis saved for candidate #{cv_data['candidate_number']}")
        
        analysis_progress.empty()
        status_text.empty()
        
        st.success("🎉 Analysis complete!")
        logger.info(f"Analysis complete for job: {job_title}")
        
        # Show results button with unique key
        if st.button("📊 View Results", key=f"view_results_{job_id}"):
            st.session_state["view_job_id"] = job_id
            st.session_state["navigate_to"] = "Results"
            st.query_params["page"] = "results"
            st.query_params["job_id"] = str(job_id)
            st.rerun()
            
    except Exception as e:
        logger.error(f"Error in analyze_cvs: {e}", exc_info=True)
        st.error(f"An error occurred during analysis: {str(e)}")


def show_analysis_history(db, user_id):
    """Display analysis history with all job postings."""
    try:
        st.title("📚 Analysis History")
        st.markdown("View all your job postings and their analysis results")
        
        job_postings = db.get_user_job_postings(user_id)
        
        if not job_postings:
            st.info("📭 No job postings yet. Create one in the 'New Analysis' section!")
            return
        
        st.markdown("---")
        
        # Search and filter
        search_term = st.text_input("🔍 Search job titles", placeholder="Type to search...")
        
        filtered_jobs = job_postings
        if search_term:
            filtered_jobs = [job for job in job_postings if search_term.lower() in job['title'].lower()]
        
        st.markdown(f"**Showing {len(filtered_jobs)} of {len(job_postings)} job postings**")
        
        # Display job postings
        for job in filtered_jobs:
            analyses = db.get_cv_analyses_for_job(job['id'])
            avg_score = sum([a['score'] for a in analyses]) / len(analyses) if analyses else 0
            top_candidates = len([a for a in analyses if a['score'] >= 80])
            
            # Job card with dark theme
            st.markdown(f"""
            <div style='
                background: #1a1a1a;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                border-left: 4px solid #667eea;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            '>
                <h3 style='color: #667eea; margin: 0 0 0.5rem 0;'>{job['title']}</h3>
                <p style='color: #aaa; margin: 0; font-size: 0.9rem;'>
                    📅 Created: {job['created_at'][:10]} | 
                    📊 {len(analyses)} CVs analyzed | 
                    ⭐ Avg Score: {avg_score:.1f} | 
                    🎯 Top Candidates: {top_candidates}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                with st.expander("📄 Job Description"):
                    st.write(job['description'])
            
            with col2:
                if st.button("👁️ View Results", key=f"view_{job['id']}"):
                    st.session_state["view_job_id"] = job['id']
                    st.session_state["navigate_to"] = "Results"
                    st.query_params["page"] = "results"
                    st.query_params["job_id"] = str(job['id'])
                    st.rerun()
                    
    except Exception as e:
        logger.error(f"Error in show_analysis_history: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
