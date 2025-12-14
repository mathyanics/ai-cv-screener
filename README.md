# AI-Powered CV Screener 📄🤖

A comprehensive, intelligent CV screening and analysis system built with Streamlit, LangChain, and AI. This application helps HR professionals and recruiters efficiently evaluate and rank candidate CVs against job descriptions using advanced AI analysis.

## ✨ Features

### 🔐 User Management
- **User Registration**: Create secure accounts with username, email, and password
- **Authentication**: Secure login system with encrypted password storage
- **Session Management**: Persistent user sessions throughout the application

### 📋 Job Management
- **Create Job Postings**: Define job titles and detailed descriptions
- **Track Multiple Jobs**: Manage multiple job postings simultaneously
- **Historical Records**: Access past job postings and their analyses

### 📄 CV Processing
- **Multiple Format Support**: Upload CVs in PDF, DOCX, or TXT format
- **Batch Processing**: Analyze multiple CVs simultaneously
- **Text Extraction**: Intelligent extraction of content from various document formats
- **Section Detection**: Automatic identification of key CV sections (education, experience, skills)

### 🤖 AI-Powered Analysis
- **Intelligent Scoring**: Each CV receives a score from 0-100 based on job requirements
- **Detailed Reasoning**: Comprehensive explanation of why each score was assigned
- **Strength & Weakness Analysis**: Clear identification of candidate strengths and gaps
- **Recommendation Levels**:
  - 🟢 **Strongly Recommend** (80-100): Top candidates
  - 🟡 **Recommend** (60-79): Good candidates
  - 🟠 **Consider** (40-59): Potential candidates
  - 🔴 **Reject** (0-39): Not suitable

### 📊 Results & Analytics
- **Ranked Results**: CVs automatically ordered by score (highest first)
- **Visual Charts**: Score distribution visualization using Plotly
- **Filtering Options**: Filter results by recommendation level
- **Detailed Reports**: In-depth analysis for each candidate
- **Summary Statistics**: Overview of all analyzed CVs

### 💾 Database Storage
- **Local SQLite Database**: All data stored locally
- **Persistent Storage**: User accounts, job postings, CVs, and analyses saved
- **Embedding Cache**: Optional caching of CV embeddings for faster processing

## 🚀 Quick Setup Guide

### Prerequisites

- Python 3.11 or higher
- API Keys:
  - Cerebras API Key (for LLM)

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/mathyanics/ai-cv-screener.git
cd ai-cv-screener
```

#### 2. Install Python Packages
Run this command to install all required dependencies:

```bash
pip install -r requirements.txt
```

#### 3. Get Your API Keys

**Cerebras API Key:**
1. Go to https://cerebras.ai/
2. Sign up or log in
3. Navigate to API settings
4. Generate an API key

#### 4. Create Environment File

Copy the `.env.example` file to `.env`:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On Mac/Linux:**
```bash
cp .env.example .env
```

Then edit the `.env` file with your actual API keys:

```env
# Cerebras API Configuration
CEREBRAS_API_KEY=your_actual_cerebras_api_key
CEREBRAS_BASE_URL=https://api.cerebras.ai/v1
CEREBRAS_MODEL=llama3.1-8b
```

⚠️ **Important**: Ensure no extra spaces in the `.env` file

#### 5. Run the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### First Time Use

#### 1. Register an Account
- Click "Don't have an account? Register here"
- Enter username, email, and password
- Click "Register"

#### 2. Login
- Enter your username and password
- Click "Login"

#### 3. Create a New Analysis
- Go to "New Analysis" in the sidebar
- Enter the job title
- Paste the complete job description
- Upload one or more CVs (PDF, DOCX, or TXT)
- Click "Start Analysis"

### 4. View Results
- Navigate to "Results" or click "View Results" after analysis
- See the score distribution chart
- Filter results by recommendation level
- Expand each CV to see detailed analysis:
  - Overall score
  - Strengths
  - Weaknesses
  - Summary
  - Detailed reasoning

### 5. Dashboard
- View all your job postings
- See statistics (total jobs, CVs analyzed)
- Quick access to previous analyses

## 🏗️ Project Structure

```
ai-cv-screener/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your environment variables (create this)
├── ai_cv_screener.db          # SQLite database (auto-created)
│
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── database.py           # Database models and operations
│   ├── cv_processor.py       # CV text extraction and processing
│   └── cv_analyzer.py        # AI-powered CV analysis and scoring
│
├── features/                  # Streamlit UI features
│   ├── __init__.py
│   ├── auth.py               # Login and registration pages
│   ├── dashboard.py          # Dashboard with statistics
│   ├── analysis.py           # New analysis and history
│   ├── results.py            # Results display and filtering
│   └── sidebar.py            # Navigation sidebar
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── helpers.py            # Helper functions (retry logic, etc.)
│
└── README.md                  # This file
```

## 🔧 Technical Details

### Database Schema

**users**
- id (PRIMARY KEY)
- username (UNIQUE)
- email (UNIQUE)
- password_hash
- created_at

**job_postings**
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- title
- description
- created_at

**cvs**
- id (PRIMARY KEY)
- job_posting_id (FOREIGN KEY)
- file_name
- file_content
- uploaded_at

**cv_analyses**
- id (PRIMARY KEY)
- cv_id (FOREIGN KEY)
- score
- reasons
- detailed_analysis
- analyzed_at

**cv_embeddings** (optional)
- id (PRIMARY KEY)
- cv_id (FOREIGN KEY)
- embedding_data
- created_at

### AI Models

- **LLM**: Cerebras (using OpenAI-compatible API)
  - Used for intelligent CV analysis and scoring
  - Generates detailed reasoning and recommendations

### Key Technologies

- **Streamlit**: Web interface
- **LangChain**: LLM orchestration and chains
- **SQLite**: Local database
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX text extraction
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation

## 🎯 Scoring Methodology

The AI analyzes each CV using a weighted scoring system (0-100):

### Scoring Criteria

1. **Relevant Experience (30%)**
   - Years of experience in relevant roles
   - Career progression and trajectory
   - Role expansion and increased responsibilities
   - Alignment with job requirements

2. **Impact & Achievements (20%)**
   - Quantifiable results and metrics
   - Revenue/cost impact
   - Project outcomes
   - Leadership and influence

3. **Skills Match (20%)**
   - Technical skills alignment
   - Soft skills demonstrated
   - Tool/technology proficiency
   - Skill validation through work history

4. **Education & Qualifications (20%)**
   - Required degrees and certifications
   - Relevant coursework
   - Academic achievements
   - Continuous learning

5. **Certifications & Extras (10%)**
   - Professional certifications
   - Awards and recognition
   - Publications and presentations
   - Additional qualifications

### How It Works

1. **LLM Scoring**: The AI evaluates each criterion and assigns a score from 0-100 based on content quality
2. **Manual Weighting**: Each criterion is weighted according to importance (30%, 20%, 20%, 20%, 10%)
3. **Final Score**: The weighted scores are summed to produce the final score (0-100)

**Example:**
- Experience: 85/100 × 30% = 25.5 points
- Impact: 75/100 × 20% = 15.0 points
- Skills: 80/100 × 20% = 16.0 points
- Education: 70/100 × 20% = 14.0 points
- Certifications: 60/100 × 10% = 6.0 points
- **Total Score: 76.5/100**

### Recommendation Levels
- 🟢 **Strongly Recommend** (80-100): Top candidates with excellent match
- 🟡 **Recommend** (60-79): Good candidates worth interviewing
- 🟠 **Consider** (40-59): Potential candidates with some gaps
- 🔴 **Reject** (0-39): Not suitable for the position

## 🔒 Security

- Passwords are hashed using SHA-256
- Local database (no external data transmission except API calls)
- Session-based authentication
- API keys stored in environment variables