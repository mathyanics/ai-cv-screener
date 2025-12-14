"""
Database models and setup for the AI CV Screener application.
Uses SQLite for local storage of users, CV data, and analysis results.
Optimized with singleton pattern and lazy initialization.
"""

import sqlite3
from datetime import datetime
import hashlib
import json
from typing import List, Dict, Optional
import os
import logging

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
DATABASE_PATH = "ai_cv_screener.db"

class DatabaseSingleton:
    """Singleton pattern for database manager."""
    _instance = None
    _initialized = False
    
    def __new__(cls, db_path=DATABASE_PATH):
        if cls._instance is None:
            cls._instance = super(DatabaseSingleton, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_path=DATABASE_PATH):
        # Only initialize once
        if not DatabaseSingleton._initialized:
            self.db_path = db_path
            self._ensure_tables_exist()
            DatabaseSingleton._initialized = True
    
    def _ensure_tables_exist(self):
        """Check if tables exist, create only if needed (optimized)."""
        conn = None
        try:
            logger.info("Initializing database tables...")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if tables already exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            logger.info(f"Existing tables: {existing_tables}")
            
            # Only create tables that don't exist
            if 'users' not in existing_tables:
                logger.info("Creating 'users' table...")
                cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            if 'job_postings' not in existing_tables:
                logger.info("Creating 'job_postings' table...")
                cursor.execute("""
                    CREATE TABLE job_postings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
            
            if 'cvs' not in existing_tables:
                logger.info("Creating 'cvs' table...")
                cursor.execute("""
                    CREATE TABLE cvs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_posting_id INTEGER NOT NULL,
                        file_name TEXT NOT NULL,
                        file_content TEXT,
                        parsed_info TEXT,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_posting_id) REFERENCES job_postings (id)
                    )
                """)
            
            if 'cv_analyses' not in existing_tables:
                logger.info("Creating 'cv_analyses' table...")
                cursor.execute("""
                    CREATE TABLE cv_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cv_id INTEGER NOT NULL,
                        candidate_number INTEGER,
                        score REAL NOT NULL,
                        reasons TEXT NOT NULL,
                        detailed_analysis TEXT,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (cv_id) REFERENCES cvs (id)
                    )
                """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database error during table initialization: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during table initialization: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


class Database(DatabaseSingleton):
    """Database manager for the CV Screener application."""
    
    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str) -> tuple[bool, str]:
        """
        Create a new user.
        Returns: (success: bool, message: str)
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            
            conn.commit()
            conn.close()
            return True, "User created successfully!"
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Username already exists."
            elif "email" in str(e):
                return False, "Email already exists."
            return False, "User creation failed."
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user.
        Returns: User dict if successful, None otherwise.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id, username, email FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2]
            }
        return None
    
    def create_job_posting(self, user_id: int, title: str, description: str) -> int:
        """Create a new job posting and return its ID."""
        conn = None
        try:
            logger.info(f"Creating job posting: {title} for user_id: {user_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO job_postings (user_id, title, description) VALUES (?, ?, ?)",
                (user_id, title, description)
            )
            
            job_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Job posting created successfully with ID: {job_id}")
            return job_id
        except sqlite3.Error as e:
            logger.error(f"Database error creating job posting '{title}': {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating job posting '{title}': {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def get_user_job_postings(self, user_id: int) -> List[Dict]:
        """Get all job postings for a user."""
        conn = None
        try:
            logger.info(f"Retrieving job postings for user_id: {user_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, title, description, created_at FROM job_postings WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            
            results = cursor.fetchall()
            logger.info(f"Retrieved {len(results)} job postings for user_id: {user_id}")
            
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "created_at": row[3]
                }
                for row in results
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving job postings for user_id {user_id}: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving job postings for user_id {user_id}: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def save_cv(self, job_posting_id: int, file_name: str, file_content: str, parsed_info: str = None) -> int:
        """Save a CV and return its ID."""
        conn = None
        try:
            logger.info(f"Saving CV: {file_name} for job_posting_id: {job_posting_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO cvs (job_posting_id, file_name, file_content, parsed_info) VALUES (?, ?, ?, ?)",
                (job_posting_id, file_name, file_content, parsed_info)
            )
            
            cv_id = cursor.lastrowid
            conn.commit()
            logger.info(f"CV saved successfully with ID: {cv_id}")
            return cv_id
        except sqlite3.Error as e:
            logger.error(f"Database error saving CV '{file_name}': {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving CV '{file_name}': {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def save_cv_analysis(self, cv_id: int, score: float, reasons: str, detailed_analysis: str, candidate_number: int = None) -> int:
        """Save CV analysis results and return the analysis ID."""
        conn = None
        try:
            logger.info(f"Saving CV analysis for cv_id: {cv_id}, candidate_number: {candidate_number}, score: {score}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO cv_analyses (cv_id, candidate_number, score, reasons, detailed_analysis) VALUES (?, ?, ?, ?, ?)",
                (cv_id, candidate_number, score, reasons, detailed_analysis)
            )
            
            analysis_id = cursor.lastrowid
            conn.commit()
            logger.info(f"CV analysis saved successfully with ID: {analysis_id}")
            return analysis_id
        except sqlite3.Error as e:
            logger.error(f"Database error saving CV analysis for cv_id {cv_id}: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving CV analysis for cv_id {cv_id}: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def get_cv_analyses_for_job(self, job_posting_id: int) -> List[Dict]:
        """Get all CV analyses for a specific job posting, ordered by score."""
        conn = None
        try:
            logger.info(f"Retrieving CV analyses for job_posting_id: {job_posting_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.id, c.file_name, c.uploaded_at,
                    ca.candidate_number, ca.score, ca.reasons, ca.detailed_analysis, ca.analyzed_at
                FROM cvs c
                JOIN cv_analyses ca ON c.id = ca.cv_id
                WHERE c.job_posting_id = ?
                ORDER BY ca.score DESC
            """, (job_posting_id,))
            
            results = cursor.fetchall()
            logger.info(f"Retrieved {len(results)} CV analyses for job_posting_id: {job_posting_id}")
            
            return [
                {
                    "cv_id": row[0],
                    "file_name": row[1],
                    "uploaded_at": row[2],
                    "candidate_number": row[3],
                    "score": row[4],
                    "reasons": row[5],
                    "detailed_analysis": row[6],
                    "analyzed_at": row[7]
                }
                for row in results
            ]
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving CV analyses for job_posting_id {job_posting_id}: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving CV analyses for job_posting_id {job_posting_id}: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def get_cv_content(self, cv_id: int) -> Optional[str]:
        """Get CV content by CV ID."""
        conn = None
        try:
            logger.debug(f"Retrieving CV content for cv_id: {cv_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT file_content FROM cvs WHERE id = ?",
                (cv_id,)
            )
            
            result = cursor.fetchone()
            if result:
                logger.debug(f"CV content retrieved for cv_id: {cv_id}")
            else:
                logger.warning(f"No CV content found for cv_id: {cv_id}")
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving CV content for cv_id {cv_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving CV content for cv_id {cv_id}: {e}", exc_info=True)
            return None
        finally:
            if conn:
                conn.close()
    
    def update_cv_parsed_info(self, cv_id: int, parsed_info: str) -> None:
        """Update CV with parsed information."""
        conn = None
        try:
            logger.info(f"Updating parsed info for cv_id: {cv_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE cvs SET parsed_info = ? WHERE id = ?",
                (parsed_info, cv_id)
            )
            
            conn.commit()
            logger.info(f"Parsed info updated successfully for cv_id: {cv_id}")
        except sqlite3.Error as e:
            logger.error(f"Database error updating parsed info for cv_id {cv_id}: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating parsed info for cv_id {cv_id}: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def get_cv_parsed_info(self, cv_id: int) -> Optional[Dict]:
        """Get parsed CV information by CV ID."""
        conn = None
        try:
            logger.debug(f"Retrieving parsed info for cv_id: {cv_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT parsed_info FROM cvs WHERE id = ?",
                (cv_id,)
            )
            
            result = cursor.fetchone()
            
            if result and result[0]:
                try:
                    parsed_data = json.loads(result[0])
                    logger.debug(f"Parsed info retrieved for cv_id: {cv_id}")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for cv_id {cv_id}: {e}", exc_info=True)
                    return None
            else:
                logger.debug(f"No parsed info found for cv_id: {cv_id}")
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving parsed info for cv_id {cv_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving parsed info for cv_id {cv_id}: {e}", exc_info=True)
            return None
        finally:
            if conn:
                conn.close()


# Singleton instance
db = Database()
