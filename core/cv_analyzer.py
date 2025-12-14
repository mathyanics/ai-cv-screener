"""
CV Analysis and Scoring Engine.
Compares CVs with job descriptions and provides detailed scoring and analysis.
"""

from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import OpenAI
import re
import json
import logging
from constants.constants import SCORING_PROMPT, WEIGHTS

# Import utilities
from utils.helpers import retry_with_exponential_backoff

# Configure logging
logger = logging.getLogger(__name__)


class CVAnalyzer:
    """Analyzes and scores CVs against job descriptions."""

    WEIGHTS = WEIGHTS.copy()  # Load weights from constants
    
    def __init__(self, llm):
        """
        Initialize the CV analyzer.
        
        Args:
            llm: Language model for analysis
        """
        self.llm = llm
        
        # Scoring prompt template (anonymous with detailed reasons)
        self.scoring_prompt = PromptTemplate(
            input_variables=["job_description", "cv_content", "candidate_number"],
            template=SCORING_PROMPT
        )
    
    def calculate_weighted_score(self, llm_scores: Dict) -> Dict:
        """
        Calculate weighted score from LLM's individual criterion scores.
        
        Args:
            llm_scores: Dictionary with LLM scores for each criterion (0-100 scale)
            
        Returns:
            Dictionary with weighted scores and final score
        """
        try:
            # Extract LLM scores (0-100 scale)
            experience_raw = float(llm_scores.get('experience_score', 50))
            impact_raw = float(llm_scores.get('impact_score', 50))
            skills_raw = float(llm_scores.get('skills_score', 50))
            education_raw = float(llm_scores.get('education_score', 50))
            certs_raw = float(llm_scores.get('certs_extras_score', 50))
            
            # Ensure scores are within 0-100 range
            experience_raw = max(0, min(100, experience_raw))
            impact_raw = max(0, min(100, impact_raw))
            skills_raw = max(0, min(100, skills_raw))
            education_raw = max(0, min(100, education_raw))
            certs_raw = max(0, min(100, certs_raw))
            
            # Apply manual weights to get final weighted scores
            experience_weighted = experience_raw * self.WEIGHTS['experience']
            impact_weighted = impact_raw * self.WEIGHTS['impact']
            skills_weighted = skills_raw * self.WEIGHTS['skills']
            education_weighted = education_raw * self.WEIGHTS['education']
            certs_weighted = certs_raw * self.WEIGHTS['certs_extras']
            
            # Calculate total score (0-100)
            total_score = (
                experience_weighted + 
                impact_weighted + 
                skills_weighted + 
                education_weighted + 
                certs_weighted
            )
            
            # Determine recommendation based on total score
            if total_score >= 80:
                recommendation = "STRONGLY RECOMMEND"
            elif total_score >= 60:
                recommendation = "RECOMMEND"
            elif total_score >= 40:
                recommendation = "CONSIDER"
            else:
                recommendation = "REJECT"
            
            return {
                'experience_score': round(experience_weighted, 1),
                'impact_score': round(impact_weighted, 1),
                'skills_score': round(skills_weighted, 1),
                'education_score': round(education_weighted, 1),
                'certs_extras_score': round(certs_weighted, 1),
                'score': round(total_score, 1),
                'recommendation': recommendation,
                # Include raw LLM scores for reference
                'experience_score_raw': round(experience_raw, 1),
                'impact_score_raw': round(impact_raw, 1),
                'skills_score_raw': round(skills_raw, 1),
                'education_score_raw': round(education_raw, 1),
                'certs_extras_score_raw': round(certs_raw, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}", exc_info=True)
            # Return default scores
            return {
                'experience_score': 15,
                'impact_score': 10,
                'skills_score': 10,
                'education_score': 10,
                'certs_extras_score': 5,
                'score': 50,
                'recommendation': 'CONSIDER',
                'experience_score_raw': 50,
                'impact_score_raw': 50,
                'skills_score_raw': 50,
                'education_score_raw': 50,
                'certs_extras_score_raw': 50
            }
    
    def parse_score_from_json(self, json_str: str) -> Dict:
        """
        Parse the JSON response from LLM and calculate weighted scores.
        
        Args:
            json_str: JSON string from LLM
            
        Returns:
            Parsed dictionary with weighted scores
        """
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
                
                # Calculate weighted scores from LLM scores
                weighted_scores = self.calculate_weighted_score(json_data)
                
                # Merge LLM analysis with calculated scores
                result = {**json_data, **weighted_scores}
                
                return result
            else:
                # Fallback if no JSON found
                return {
                    "score": 50,
                    "recommendation": "CONSIDER",
                    "strengths": ["Unable to parse analysis"],
                    "weaknesses": ["Analysis format error"],
                    "summary": "Error parsing response",
                    "detailed_reasoning": json_str,
                    **self.calculate_weighted_score({})
                }
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}", exc_info=True)
            return {
                "score": 50,
                "recommendation": "CONSIDER",
                "strengths": ["Unable to parse analysis"],
                "weaknesses": [f"Parse error: {str(e)}"],
                "summary": "Error parsing response",
                "detailed_reasoning": json_str,
                **self.calculate_weighted_score({})
            }
    
    @retry_with_exponential_backoff(max_retries=3)
    def score_cv(self, job_description: str, cv_content: str, candidate_number: int = 1) -> Dict:
        """
        Score a CV against a job description with retry logic (anonymous analysis).
        
        Args:
            job_description: The job description text
            cv_content: The CV text content (full, no truncation)
            candidate_number: Candidate number for anonymous analysis
            
        Returns:
            Dictionary with score, recommendation, and detailed scoring reasons
        """
        try:
            # Create chain
            chain = self.scoring_prompt | self.llm
            
            # Run analysis with full content
            result = chain.invoke({
                "job_description": job_description,
                "cv_content": cv_content,
                "candidate_number": candidate_number
            })
            
            # Parse JSON response
            analysis = self.parse_score_from_json(result.content)
            
            return analysis
            
        except Exception as e:
            return {
                "score": 0,
                "recommendation": "ERROR",
                "strengths": [],
                "weaknesses": [f"Analysis error: {str(e)}"],
                "key_matches": {},
                "summary": "Error during analysis",
                "detailed_reasoning": str(e)
            }
    
    def batch_score_cvs(self, job_description: str, cv_data_list: List[Dict]) -> List[Dict]:
        """
        Score multiple CVs and return them ranked by score.
        
        Args:
            job_description: The job description text
            cv_data_list: List of dictionaries with CV data (must include 'text' and 'file_name')
            
        Returns:
            List of dictionaries with scores, ranked by score (highest first)
        """
        results = []
        
        for cv_data in cv_data_list:
            analysis = self.score_cv(job_description, cv_data['text'])
            
            results.append({
                'file_name': cv_data['file_name'],
                'cv_data': cv_data,
                'score': analysis['score'],
                'recommendation': analysis['recommendation'],
                'analysis': analysis
            })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def get_top_candidates(self, scored_cvs: List[Dict], top_n: int = 5) -> List[Dict]:
        """
        Get top N candidates from scored CVs.
        
        Args:
            scored_cvs: List of scored CV dictionaries
            top_n: Number of top candidates to return
            
        Returns:
            List of top N candidates
        """
        return scored_cvs[:top_n]
    
    def get_candidates_by_recommendation(self, scored_cvs: List[Dict], 
                                       recommendation: str) -> List[Dict]:
        """
        Filter candidates by recommendation level.
        
        Args:
            scored_cvs: List of scored CV dictionaries
            recommendation: One of "STRONGLY RECOMMEND", "RECOMMEND", "CONSIDER", "REJECT"
            
        Returns:
            Filtered list of candidates
        """
        return [cv for cv in scored_cvs if cv['recommendation'] == recommendation]
    
    def generate_summary_report(self, scored_cvs: List[Dict]) -> str:
        """
        Generate a summary report of all analyzed CVs.
        
        Args:
            scored_cvs: List of scored CV dictionaries
            
        Returns:
            Summary report in markdown format
        """
        total = len(scored_cvs)
        if total == 0:
            return "No CVs analyzed yet."
        
        # Calculate statistics
        strongly_recommend = len([cv for cv in scored_cvs if cv['recommendation'] == 'STRONGLY RECOMMEND'])
        recommend = len([cv for cv in scored_cvs if cv['recommendation'] == 'RECOMMEND'])
        consider = len([cv for cv in scored_cvs if cv['recommendation'] == 'CONSIDER'])
        reject = len([cv for cv in scored_cvs if cv['recommendation'] == 'REJECT'])
        
        avg_score = sum([cv['score'] for cv in scored_cvs]) / total
        
        report = f"""# CV Analysis Summary Report

## Overview
- **Total CVs Analyzed**: {total}
- **Average Score**: {avg_score:.1f}/100

## Recommendation Breakdown
- **Strongly Recommend** (80-100): {strongly_recommend} candidates ({strongly_recommend/total*100:.1f}%)
- **Recommend** (60-79): {recommend} candidates ({recommend/total*100:.1f}%)
- **Consider** (40-59): {consider} candidates ({consider/total*100:.1f}%)
- **Reject** (0-39): {reject} candidates ({reject/total*100:.1f}%)

## Top 3 Candidates
"""
        
        top_3 = scored_cvs[:3]
        for i, cv in enumerate(top_3, 1):
            report += f"\n### {i}. {cv['file_name']}\n"
            report += f"- **Score**: {cv['score']}/100\n"
            report += f"- **Recommendation**: {cv['recommendation']}\n"
            report += f"- **Summary**: {cv['analysis'].get('summary', 'N/A')}\n"
        
        return report
