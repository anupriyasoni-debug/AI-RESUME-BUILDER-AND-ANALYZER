"""
Deprecated: External AI API Client.
All external AI API dependencies have been removed and replaced with local_model.py.
This file is preserved for backward compatibility and makes zero external API or network calls.
"""

from local_model import local_engine, BaseResumeModel, LocalResumeEngine


def create_gemini_model():
    """Deprecated: Returns the local offline engine without requiring API keys."""
    return "Local Model (Offline)", local_engine
