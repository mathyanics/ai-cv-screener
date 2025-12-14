"""
CV Processing utilities for extracting and analyzing CV content.
Supports PDF, DOCX, and TXT formats.
"""

import tempfile
import os
from typing import Dict, List, Optional
import PyPDF2
import docx
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
import json
import re
import logging
from constants.constants import CV_PARSING_PROMPT

# Import utilities
from utils.helpers import retry_with_exponential_backoff

# Configure logging
logger = logging.getLogger(__name__)


class CVProcessor:
    """Handles CV file processing and content extraction."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        text = ""
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.debug(f"PDF has {num_pages} pages")
                for page in pdf_reader.pages:
                    text += page.extract_text()
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
        except FileNotFoundError as e:
            logger.error(f"PDF file not found: {file_path}", exc_info=True)
            raise Exception(f"Error extracting PDF: File not found - {file_path}")
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"PDF read error for {file_path}: {e}", exc_info=True)
            raise Exception(f"Error extracting PDF: Invalid or corrupted PDF file")
        except Exception as e:
            logger.error(f"Unexpected error extracting PDF {file_path}: {e}", exc_info=True)
            raise Exception(f"Error extracting PDF: {str(e)}")
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file."""
        try:
            logger.info(f"Extracting text from DOCX: {file_path}")
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            logger.info(f"Successfully extracted {len(text)} characters from DOCX")
        except FileNotFoundError as e:
            logger.error(f"DOCX file not found: {file_path}", exc_info=True)
            raise Exception(f"Error extracting DOCX: File not found - {file_path}")
        except docx.opc.exceptions.PackageNotFoundError as e:
            logger.error(f"Invalid DOCX file: {file_path}", exc_info=True)
            raise Exception(f"Error extracting DOCX: Invalid or corrupted DOCX file")
        except Exception as e:
            logger.error(f"Unexpected error extracting DOCX {file_path}: {e}", exc_info=True)
            raise Exception(f"Error extracting DOCX: {str(e)}")
        return text
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from a TXT file."""
        try:
            logger.info(f"Extracting text from TXT: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            logger.info(f"Successfully extracted {len(text)} characters from TXT")
        except FileNotFoundError as e:
            logger.error(f"TXT file not found: {file_path}", exc_info=True)
            raise Exception(f"Error extracting TXT: File not found - {file_path}")
        except UnicodeDecodeError as e:
            logger.warning(f"UTF-8 decode failed for {file_path}, trying latin-1", exc_info=True)
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                logger.info(f"Successfully extracted using latin-1 encoding")
            except Exception as e2:
                logger.error(f"Failed with both encodings: {e2}", exc_info=True)
                raise Exception(f"Error extracting TXT: Encoding error")
        except Exception as e:
            logger.error(f"Unexpected error extracting TXT {file_path}: {e}", exc_info=True)
            raise Exception(f"Error extracting TXT: {str(e)}")
        return text
    
    def extract_text_from_file(self, uploaded_file) -> str:
        """
        Extract text from an uploaded file based on its extension.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Extracted text content
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                text = self.extract_text_from_pdf(tmp_file_path)
            elif file_extension == 'docx':
                text = self.extract_text_from_docx(tmp_file_path)
            elif file_extension == 'txt':
                text = self.extract_text_from_txt(tmp_file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            return text
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    @retry_with_exponential_backoff(max_retries=3)
    def extract_candidate_info_with_llm(self, text: str, llm) -> Dict[str, str]:
        """Use LLM to extract ALL structured information from CV text with retry logic."""
        try:
            logger.info("Extracting candidate info using LLM")
            extraction_prompt = PromptTemplate(
                input_variables=["cv_text"],
                template=CV_PARSING_PROMPT
            )
            
            chain = extraction_prompt | llm
            result = chain.invoke({"cv_text": text})
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
            if json_match:
                info = json.loads(json_match.group())
                logger.info(f"Successfully extracted candidate info: {info.get('name', 'Unknown')}")
                return info
            else:
                logger.warning("No JSON found in LLM response, using fallback extraction")
                # Fallback to regex parsing
                return self._fallback_extraction(text)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in LLM extraction: {e}", exc_info=True)
            return self._fallback_extraction(text)
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}", exc_info=True)
            # Fallback to regex parsing if LLM fails
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text: str) -> Dict[str, str]:
        """Fallback regex-based extraction."""
        import re
        
        logger.info("Using fallback regex extraction")
        try:
            # Extract email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            email = email_match.group(0) if email_match else "Not found"
            
            # Extract phone
            phone_match = re.search(r'\b(?:\+?\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}\b', text)
            phone = phone_match.group(0) if phone_match else "Not found"
            
            # Extract name (first non-empty line that looks like a name)
            name = self.extract_candidate_name(text)
            
            logger.info(f"Fallback extraction completed for: {name}")
            return {
                "name": name,
                "email": email,
                "phone": phone,
                "location": "Not found",
                "summary": "Information extracted using pattern matching"
            }
        except Exception as e:
            logger.error(f"Error in fallback extraction: {e}", exc_info=True)
            return {
                "name": "Unknown Candidate",
                "email": "Not found",
                "phone": "Not found",
                "location": "Not found",
                "summary": "Extraction failed"
            }
    
    def extract_candidate_name(self, text: str) -> str:
        """Extract candidate name from CV text (regex-based fallback)."""
        try:
            logger.debug("Extracting candidate name using regex")
            lines = text.strip().split('\n')
            
            # Try to find name in first few lines
            for i, line in enumerate(lines[:5]):
                line = line.strip()
                # Skip empty lines and common headers
                if not line or line.upper() in ['CURRICULUM VITAE', 'CV', 'RESUME', 'CONTACT', 'PERSONAL INFORMATION']:
                    continue
                # Check if line looks like a name (2-4 words, mostly alphabetic)
                words = line.split()
                if 2 <= len(words) <= 4 and all(w.replace('.', '').replace(',', '').isalpha() for w in words):
                    logger.debug(f"Found candidate name: {line}")
                    return line
            
            # Fallback: return first non-empty line
            for line in lines[:10]:
                line = line.strip()
                if line and len(line) < 50:  # Names are typically short
                    logger.debug(f"Using fallback name: {line}")
                    return line
            
            logger.warning("Could not extract candidate name, using default")
            return "Unknown Candidate"
        except Exception as e:
            logger.error(f"Error extracting candidate name: {e}", exc_info=True)
            return "Unknown Candidate"
    
    def extract_cv_sections(self, text: str) -> Dict[str, str]:
        """
        Extract common CV sections from text.
        
        Returns:
            Dictionary with sections: personal_info, education, experience, skills, etc.
        """
        sections = {
            "personal_info": "",
            "education": "",
            "experience": "",
            "skills": "",
            "other": ""
        }
        
        # Simple keyword-based section detection
        text_lower = text.lower()
        
        # Education keywords
        education_keywords = ['education', 'qualification', 'academic', 'degree', 'university', 'college']
        # Experience keywords
        experience_keywords = ['experience', 'employment', 'work history', 'career', 'professional background']
        # Skills keywords
        skills_keywords = ['skills', 'competencies', 'expertise', 'technical skills', 'abilities']
        
        # Split text into lines for better parsing
        lines = text.split('\n')
        current_section = "other"
        
        for line in lines:
            line_lower = line.lower()
            
            # Detect section headers
            if any(keyword in line_lower for keyword in education_keywords):
                current_section = "education"
            elif any(keyword in line_lower for keyword in experience_keywords):
                current_section = "experience"
            elif any(keyword in line_lower for keyword in skills_keywords):
                current_section = "skills"
            
            # Add line to current section
            sections[current_section] += line + "\n"
        
        # Extract email and phone as personal info
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        
        if emails or phones:
            sections["personal_info"] = f"Email: {', '.join(emails)}\nPhone: {', '.join(phones)}"
        
        return sections
    
    def create_vectorstore(self, text: str, embeddings) -> FAISS:
        """
        Create a FAISS vector store from CV text.
        
        Args:
            text: Extracted CV text
            embeddings: Embedding model
            
        Returns:
            FAISS vector store
        """
        # Split text into chunks
        texts = self.text_splitter.split_text(text)
        
        # Create vector store
        vectorstore = FAISS.from_texts(texts, embeddings)
        
        return vectorstore
    
    def process_cv_for_comparison(self, uploaded_file, embeddings) -> Dict:
        """
        Process a CV file for comparison with job description.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            embeddings: Embedding model
            
        Returns:
            Dictionary containing extracted text, sections, and vectorstore
        """
        # Extract text
        text = self.extract_text_from_file(uploaded_file)
        
        # Extract sections
        sections = self.extract_cv_sections(text)
        
        # Create vectorstore
        vectorstore = self.create_vectorstore(text, embeddings)
        
        return {
            "file_name": uploaded_file.name,
            "text": text,
            "sections": sections,
            "vectorstore": vectorstore
        }


# Singleton instance
cv_processor = CVProcessor()
