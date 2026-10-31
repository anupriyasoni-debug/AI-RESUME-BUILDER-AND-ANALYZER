"""Compatibility exports for older imports; AI insights now use Sarvam."""

from sarvam_client import (
    compare_resumes_with_ai,
    format_ai_error,
    generate_resume_insights,
)


format_gemini_error = format_ai_error


def create_gemini_model():
    """Keep the legacy factory pointed at the offline local engine."""
    from local_model import local_engine

    return "Local Model (Offline)", local_engine
