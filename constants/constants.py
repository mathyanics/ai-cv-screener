SCORING_PROMPT = """Act as an expert HR AI specialized in CV analysis.

Job Description:
{job_description}

CANDIDATE #{candidate_number} CV:
{cv_content}

Analyze the CV against the Job Description using the following logic:

1. **Filter Requirements**: Focus ONLY on professional qualifications and competencies. IGNORE availability, location, salary, and notice period.

2. **Evaluation Logic**:
   - **Trajectory**: Assess growth via title changes (Junior -> Senior) or Role Expansion (increased scope, budget, mentorship) if the title is static >2 years.
   - **Impact**: Prioritize "Achievements" (quantifiable metrics, %, $) over passive "Responsibilities."
   - **Validation**: Verify listed skills exist within the "Work History" context.

3. **Scoring Instructions**:
   - Score each category on a **precise 0-100 scale**.
   - **Use specific integers** (e.g., 26, 51, 87) based on exact merit. **DO NOT** default to round numbers (20, 50, 90).
   - **Experience**: Relevance, trajectory, and tenure. Deduct for unjustified gaps >6mo or excessive job hopping.
   - **Impact**: Quantifiable results vs. generic duties (0 if no metrics).
   - **Skills**: Hard/soft skills validated by context.
   - **Education**: Degree relevance (allow industry equivalents).
   - **Extras**: Certs, awards, languages.

4. **Output**:
   - Return ONLY the JSON below.
   - Do not mention formatting/design.
   - Use 'Candidate #{candidate_number}' in text, not the name.

{{
    "experience_score": <0-100>,
    "experience_reason": "<Analysis of relevance, trajectory, and tenure>",
    "impact_score": <0-100>,
    "impact_reason": "<Analysis of quantifiable achievements vs duties>",
    "skills_score": <0-100>,
    "skills_reason": "<Analysis of context-validated skills>",
    "education_score": <0-100>,
    "education_reason": "<Analysis of degree relevance>",
    "certs_extras_score": <0-100>,
    "certs_extras_reason": "<Analysis of certifications/extras>",
    "red_flags": [
        "List gaps >6mo, frequent hops, or skill anomalies. Empty if none."
    ],
    "strengths": [
        "Point 1",
        "Point 2",
        "Point 3"
    ],
    "weaknesses": [
        "Point 1",
        "Point 2"
    ],
    "summary": "<2-3 sentence assessment for Candidate #{candidate_number}>"
}}"""

CV_PARSING_PROMPT = """You are an expert CV parser. Extract ALL information from this CV and return it in JSON format.

CV Text:
{cv_text}

Extract and return ONLY a valid JSON object with these fields:
{{
    "name": "<candidate's full name>",
    "email": "<email address or 'Not found'>",
    "phone": "<phone number or 'Not found'>",
    "location": "<city/country or 'Not found'>",
    "summary": "<professional summary in 2-3 sentences>",
    "education": [
        {{
            "degree": "<degree/certification>",
            "institution": "<school/university>",
            "year": "<graduation year or period>",
            "details": "<GPA, honors, relevant coursework>"
        }}
    ],
    "experience": [
        {{
            "title": "<job title>",
            "company": "<company name>",
            "duration": "<time period>",
            "responsibilities": "<key responsibilities and achievements>"
        }}
    ],
    "skills": ["<skill1>", "<skill2>", "<skill3>"],
    "certifications": ["<certification1>", "<certification2>"],
    "languages": ["<language1>", "<language2>"]
}}

Rules:
- Extract ALL available information from the CV
- If information is not found, use "Not found" or empty arrays []
- Be thorough and accurate
- Keep it factual, no assumptions
- Return ONLY the JSON object, no additional text
"""

# Manual weights for scoring criteria (as percentages, must sum to 1.0)
WEIGHTS = {
    'experience': 0.30,  # 30% - Work experience and career trajectory
    'impact': 0.20,      # 20% - Measurable achievements and contributions
    'skills': 0.20,      # 20% - Technical and soft skills match
    'education': 0.20,   # 20% - Educational background
    'certs_extras': 0.10 # 10% - Certifications and additional qualifications
}

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2
MAX_RETRY_DELAY = 30