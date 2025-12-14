"""
LLM Engine for AI CV Screener.
Handles initialization and configuration of language models.
"""

import os
import streamlit as st
import logging

logger = logging.getLogger(__name__)

# LLM Configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_BASE_URL = os.getenv("CEREBRAS_BASE_URL")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL")
MAX_TOKENS_PER_REQUEST = 4000

# Lazy import
_langchain_imported = False
ChatOpenAI = None


def lazy_import_langchain():
    """Lazy import of langchain modules."""
    global _langchain_imported, ChatOpenAI
    if not _langchain_imported:
        try:
            from langchain_openai import ChatOpenAI
            _langchain_imported = True
            logger.info("Langchain modules imported successfully")
        except Exception as e:
            logger.error(f"Error importing langchain: {e}", exc_info=True)
            raise
    return ChatOpenAI


@st.cache_resource
def get_llm():
    """Initialize Cerebras LLM with token limits for free tier."""
    if not CEREBRAS_API_KEY:
        logger.error("CEREBRAS_API_KEY is not set in .env")
        st.error("CEREBRAS_API_KEY is not set in .env")
        return None
    
    try:
        logger.info("Initializing Cerebras LLM...")
        # Lazy import
        ChatOpenAI = lazy_import_langchain()
        
        llm = ChatOpenAI(
            api_key=CEREBRAS_API_KEY,
            base_url=CEREBRAS_BASE_URL,
            model=CEREBRAS_MODEL,
            temperature=0.0,
            max_tokens=MAX_TOKENS_PER_REQUEST,  # Limit for free tier
            request_timeout=60  # 60 second timeout
        )
        logger.info("Cerebras LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}", exc_info=True)
        st.error(f"Error initializing LLM: {e}")
        return None
