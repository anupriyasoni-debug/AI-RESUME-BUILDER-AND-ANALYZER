"""
Local AI Engine for Resume Builder and Analyzer.
Provides offline, transparent, rule-based and NLP algorithms:
- TF-IDF and Cosine Similarity for resume-to-job-description matching
- Skill and keyword extraction using curated domain taxonomy
- Multi-factor resume scoring (ATS, skills, project quality, formatting, job fit)
- Rule-based bullet rewriter supporting 6 enhancement modes
- Contextual section-based writing recommendations
- Modular base class for plugging in custom-trained machine learning models
"""

import os
import re
import math
from collections import Counter
from typing import Dict, List, Any, Tuple, Optional


# ============================================================================
# Stopwords and Preprocessing Utilities
# ============================================================================

COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "role", "job", "candidate", "responsibilities",
    "requirements", "required", "preferred", "including", "experience", "years",
    "work", "working", "must", "plus", "ability", "strong", "team", "opportunity",
    "proven", "skills", "overview", "qualification", "qualifications", "responsibilities",
    "datasets", "dataset", "build", "builds", "building", "applies", "apply", "applying",
    "problems", "problem", "core", "solutions", "solution", "complex", "techniques", "technique",
}

STRONG_ACTION_VERBS = [
    "accelerated", "accomplished", "achieved", "administered", "advanced",
    "analyzed", "architected", "automated", "built", "championed",
    "collaborated", "constructed", "coordinated", "created", "decreased",
    "delivered", "deployed", "designed", "developed", "directed",
    "engineered", "enhanced", "established", "executed", "expanded",
    "formulated", "generated", "implemented", "improved", "increased",
    "initiated", "innovated", "instituted", "integrated", "introduced",
    "launched", "led", "managed", "maximized", "mentored",
    "minimized", "modernized", "negotiated", "optimized", "orchestrated",
    "overhauled", "pioneered", "produced", "reduced", "refactored",
    "resolved", "restructured", "revamped", "scaled", "simplified",
    "spearheaded", "standardized", "streamlined", "strengthened", "transformed",
]

WEAK_OPENERS = [
    "responsible for", "duties included", "worked on", "helped with",
    "assisted in", "assisted with", "participated in", "tasked with",
    "handled", "served as", "was involved in", "contributed to",
]


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric and technical terms."""
    clean = text.lower()
    clean = re.sub(r"[^\w\s+#.-]", " ", clean)
    tokens = [t.strip(".-") for t in clean.split() if t.strip(".-")]
    return [t for t in tokens if len(t) > 1 and t not in COMMON_STOPWORDS]


# ============================================================================
# Local TF-IDF & Cosine Similarity Implementation
# ============================================================================

class LocalTfidfMatcher:
    """
    Computes TF-IDF vectorization and cosine similarity locally using pure Python
    and math, with zero external service or cloud API dependency.
    """

    @staticmethod
    def compute_similarity(doc1: str, doc2: str) -> Tuple[float, List[str], List[str]]:
        """
        Calculates cosine similarity and keyword coverage between two documents.
        Returns:
            (similarity_percentage, doc2_terms_in_doc1, doc2_terms_missing)
        """
        tokens1 = tokenize(doc1)
        tokens2 = tokenize(doc2)

        if not tokens1 or not tokens2:
            return 0.0, [], []

        vocab = sorted(list(set(tokens1 + tokens2)))
        tf1 = Counter(tokens1)
        tf2 = Counter(tokens2)

        # Smoothed Inverse Document Frequency across the pair
        idf = {}
        for word in vocab:
            df = (1 if word in tf1 else 0) + (1 if word in tf2 else 0)
            idf[word] = math.log((2.0 + 1.0) / (df + 1.0)) + 1.0

        vec1 = [tf1.get(word, 0) * idf[word] for word in vocab]
        vec2 = [tf2.get(word, 0) * idf[word] for word in vocab]

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            sim = 0.0
        else:
            sim = dot_product / (norm1 * norm2)

        # Significant terms in doc2 (target) ordered by TF-IDF weight in doc2
        sorted_terms_doc2 = sorted(
            [w for w in set(tokens2) if len(w) > 2],
            key=lambda w: tf2.get(w, 0) * idf.get(w, 1.0),
            reverse=True,
        )

        doc1_lower = doc1.lower()
        matched_terms = []
        missing_terms = []

        for w in sorted_terms_doc2:
            # Check exact token match or root/morphological match in doc1
            stem = w.rstrip("sedign") if len(w) > 4 else w
            if w in tf1 or re.search(rf"\b{re.escape(stem)}[a-z]*\b", doc1_lower):
                matched_terms.append(w)
            else:
                missing_terms.append(w)

        total_terms = len(sorted_terms_doc2)
        coverage_rate = len(matched_terms) / max(1, total_terms)

        # Industry standard composite matching: 60% term coverage + 40% length-normalized TF-IDF vector similarity
        composite_score = (0.60 * coverage_rate * 100) + (0.40 * min(100.0, sim * 220))
        final_score = max(0.0, min(100.0, round(composite_score, 1)))

        return final_score, matched_terms[:20], missing_terms[:20]


# ============================================================================
# Modular Base Interface for Trained ML Models
# ============================================================================

class BaseResumeModel:
    """
    Abstract interface for resume scoring, matching, and generation.
    Any custom model trained via the training/ pipeline should inherit from this
    class and implement these methods.
    """

    def analyze_job_fit(self, resume_text: str, job_description: str, target_role: str = "") -> Dict[str, Any]:
        raise NotImplementedError

    def rewrite_bullet(self, original_bullet: str, mode: str = "Improve", context: Optional[List[str]] = None) -> str:
        raise NotImplementedError

    def get_writing_suggestions(self, text: str, section: str, context: Optional[str] = None) -> str:
        raise NotImplementedError

    def compare_resumes(self, text_a: str, text_b: str, target_role: str, job_description: str = "") -> Dict[str, Any]:
        raise NotImplementedError


# ============================================================================
# Limited Structural Checks for Rule-Based Rewrites
# ============================================================================

_STRUCTURAL_TOKEN_PATTERN = re.compile(
    r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?%?"
    r"|\d+(?:,\d{3})*(?:\.\d+)?%?"
    r"|\.?[A-Za-z][A-Za-z0-9]*(?:(?:[.#][A-Za-z0-9]+)|\+\+|#)*"
    r"|[A-Za-z0-9]+|[+#]+"
)
_STRUCTURAL_NUMBER_PATTERN = re.compile(
    r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?%?"
    r"|\d+(?:,\d{3})*(?:\.\d+)?%?"
)
_ALLOWED_CONCISE_FILLER_REPLACEMENTS = {"in order to": "to"}


def _structural_tokens(text: str) -> List[str]:
    return [token.casefold() for token in _STRUCTURAL_TOKEN_PATTERN.findall(text)]


def _expected_tokens_after_filler_removal(
    original: str,
    filler_replacements: Dict[str, str],
) -> List[str]:
    tokens = _structural_tokens(original)
    for phrase, replacement in filler_replacements.items():
        phrase_tokens = _structural_tokens(phrase)
        replacement_tokens = _structural_tokens(replacement)
        if not phrase_tokens:
            continue

        expected = []
        index = 0
        while index < len(tokens):
            end = index + len(phrase_tokens)
            if tokens[index:end] == phrase_tokens:
                expected.extend(replacement_tokens)
                index = end
            else:
                expected.append(tokens[index])
                index += 1
        tokens = expected
    return tokens


def check_rewrite_structure(
    original: str,
    candidate: str,
    allowed_filler_replacements: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Run a limited structural check; this does not establish semantic or factual preservation.

    This finite, rule-based check verifies basic syntactic invariants:
    - Numeric values and their relative order must match exactly.
    - Token sequence must match the original tokens, accounting only for explicitly
      allowed filler replacements (e.g., 'in order to' -> 'to').
    - Disallows additions, deletions, replacements, or reordering of substantive terms
      (tools, roles, team nouns, metrics, and outcomes).

    LIMITATIONS:
    This check operates on token sequences and numbers. It CANNOT prove full semantic
    or factual preservation, discern deep nuance, or verify real-world accuracy.
    """
    original_numbers = _STRUCTURAL_NUMBER_PATTERN.findall(original)
    candidate_numbers = _STRUCTURAL_NUMBER_PATTERN.findall(candidate)
    if original_numbers != candidate_numbers:
        return False, "Numeric text or its order changed."

    expected_tokens = _expected_tokens_after_filler_removal(
        original,
        allowed_filler_replacements or {},
    )
    if _structural_tokens(candidate) != expected_tokens:
        return False, "Terms were added, removed, replaced, or reordered."

    return True, None


def _candidate_or_original(
    original: str,
    candidate: str,
    allowed_filler_replacements: Optional[Dict[str, str]] = None,
) -> Tuple[str, Optional[str]]:
    valid, reason = check_rewrite_structure(
        original,
        candidate,
        allowed_filler_replacements=allowed_filler_replacements,
    )
    if valid:
        return candidate, None
    return (
        original,
        "Original kept because the candidate failed a limited structural check "
        f"({reason}). Edit manually if you want to change the wording.",
    )


# ============================================================================
# Local Offline Rule-Based & NLP Implementation
# ============================================================================

class LocalResumeEngine(BaseResumeModel):
    """
    Transparent, high-performance local AI engine.
    Executes entirely on-device without any API keys, network requests, or paid services.
    Supports seamless loading of user-trained ML models from models/ when available.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "models", "resume_classifier.joblib"
        )
        self.is_custom_model_loaded = False
        self.custom_model = None
        self.vectorizer = None
        self.classes_ = []
        use_custom = os.getenv("USE_CUSTOM_MODEL", "false").lower() in ("true", "1", "yes")
        if use_custom and os.path.exists(self.model_path):
            self._try_load_custom_model(self.model_path)

    def _try_load_custom_model(self, path: str):
        try:
            import joblib
            vec_path = os.path.join(os.path.dirname(path), "tfidf_vectorizer.joblib")
            if os.path.exists(path) and os.path.exists(vec_path):
                self.custom_model = joblib.load(path)
                self.vectorizer = joblib.load(vec_path)
                self.classes_ = list(getattr(self.custom_model, "classes_", []))
                self.is_custom_model_loaded = True
        except Exception:
            self.is_custom_model_loaded = False

    def predict_role(self, resume_text: str) -> Optional[str]:
        """
        Predicts role/category using the trained ML classifier if available.
        Note: This model classifies the resume's broad domain/category only; it does
        not perform skill extraction, resume scoring, or bullet rewriting.
        """
        if not self.is_custom_model_loaded or not self.custom_model or not self.vectorizer:
            return None
        try:
            vec = self.vectorizer.transform([resume_text])
            return str(self.custom_model.predict(vec)[0])
        except Exception:
            return None

    def analyze_job_fit(self, resume_text: str, job_description: str, target_role: str = "") -> Dict[str, Any]:
        """
        Analyzes alignment between resume and job description using local TF-IDF
        and keyword intersection.
        """
        if not resume_text.strip() or not job_description.strip():
            raise ValueError("Provide both resume text and a job description for analysis.")

        score, matched_terms, missing_terms = LocalTfidfMatcher.compute_similarity(
            resume_text, job_description
        )

        feedback = []
        if score >= 75:
            feedback.append("Strong lexical text similarity detected with job description requirements.")
        elif score >= 50:
            feedback.append("Moderate alignment; incorporate core missing keywords in your Experience bullets if you possess relevant experience.")
        else:
            feedback.append("Low text similarity; tailor your summary and technical skills to the job description where applicable.")

        if missing_terms:
            top_missing = ", ".join(missing_terms[:5])
            feedback.append(f"Consider addressing key job requirements such as: {top_missing} (only if you have relevant experience).")

        # Check for metrics
        has_metrics = bool(re.search(r"(?:\$\s?\d|\b\d+(?:\.\d+)?\s?%|\b\d{2,}\b)", resume_text))
        if not has_metrics:
            feedback.append("Consider adding measurable outcomes (percentages, scale, or volume) if your achievements produced quantifiable results.")

        model_name = "Local Lexical & TF-IDF Engine (Offline)"
        if self.is_custom_model_loaded:
            predicted_role = self.predict_role(resume_text)
            if predicted_role:
                feedback.insert(0, f"Custom ML Domain Classifier predicted resume category: '{predicted_role}'.")
                model_name = f"Custom ML Role Classifier + TF-IDF (Offline)"

        return {
            "score": int(score),
            "matched_terms": matched_terms,
            "missing_terms": missing_terms,
            "feedback": feedback,
            "model": model_name,
        }

    def generate_bullet_alternatives(
        self,
        original_bullet: str,
        context: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        Generates conservative alternatives using only punctuation and one explicit
        filler substitution. Structural checks do not establish semantic safety.
        """
        raw = original_bullet.strip()
        clean = re.sub(r"^\s*(?:[-*•▪◦]\s+|\d+[.)]\s+)", "", raw).strip()
        if not clean:
            return {
                "professional": {"text": raw, "note": "Empty bullet"},
                "concise": {"text": raw, "note": "Empty bullet"},
                "impact": {"text": raw, "note": "Empty bullet"},
            }

        professional_candidate = clean
        if not professional_candidate.endswith((".", "?", "!")):
            professional_candidate += "."
        professional_text, professional_fallback = _candidate_or_original(
            clean,
            professional_candidate,
        )
        professional_note = professional_fallback or (
            "Original wording retained; only terminal punctuation was added where needed. "
            "For broader grammar or wording changes, edit manually. The limited structural "
            "check does not verify meaning."
        )

        def preserve_initial_case(match: re.Match) -> str:
            phrase = match.group(0)
            if phrase.isupper():
                return "TO"
            if phrase[0].isupper():
                return "To"
            return "to"

        concise_candidate = re.sub(
            r"\bin order to\b",
            preserve_initial_case,
            clean,
            flags=re.IGNORECASE,
        )
        concise_text, concise_fallback = _candidate_or_original(
            clean,
            concise_candidate,
            allowed_filler_replacements=_ALLOWED_CONCISE_FILLER_REPLACEMENTS,
        )
        if concise_fallback:
            concise_note = concise_fallback
        elif re.search(r"\bin order to\b", clean, flags=re.IGNORECASE):
            concise_note = (
                "Removed only the unambiguous filler phrase 'in order to'; other wording "
                "is retained. The limited structural check does not verify meaning."
            )
        else:
            concise_note = (
                "No unambiguous filler was removed; the original wording is retained. "
                "Edit manually for other changes; structural checks do not verify meaning."
            )

        has_numeric_metric = bool(_STRUCTURAL_NUMBER_PATTERN.search(clean))
        impact_text = clean
        if has_numeric_metric:
            impact_note = (
                "Original shown unchanged, keeping any numeric metric wording and its relationship "
                "to the action exactly as written; no impact claim was added."
            )
        else:
            impact_note = (
                "Original shown unchanged. No numeric metric was detected; add a real outcome "
                "manually if you have one."
            )

        return {
            "professional": {"text": professional_text, "note": professional_note},
            "concise": {"text": concise_text, "note": concise_note},
            "impact": {"text": impact_text, "note": impact_note},
        }

    def rewrite_bullet(
        self,
        original_bullet: str,
        mode: str = "Improve",
        context: Optional[List[str]] = None,
    ) -> str:
        """
        Returns a conservative rule-based alternative; checks are structural only.
        """
        alternatives = self.generate_bullet_alternatives(original_bullet, context)
        mode_lower = mode.lower()
        if "concise" in mode_lower:
            return alternatives["concise"]["text"]
        elif "impact" in mode_lower:
            return alternatives["impact"]["text"]
        else:
            return alternatives["professional"]["text"]

    def get_writing_suggestions(self, text: str, section: str, context: Optional[str] = None) -> str:
        """
        Generates section-specific, contextual writing recommendations locally.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        word_count = len(text.split())
        section_lower = section.lower()

        suggestions = []

        if "summary" in section_lower:
            target = (context or "").strip()
            sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
            suggestions.append(
                f"Draft check: {word_count} words across {len(sentences)} sentence(s). "
                + (f"Your selected headline is ‘{target}’; check that the opening supports it." if target else
                   "Add an intended role to your headline so the summary has a clear career direction.")
            )

            if word_count < 35:
                suggestions.append("Content gap: the summary is brief. Add one relevant area of expertise and one concrete example, if you can support both.")
            elif word_count > 85:
                suggestions.append("Focus: this summary is long for a quick scan. Keep the role, strongest evidence, and relevant skills; move detail to experience or projects.")
            else:
                opening = sentences[0] if sentences else text.strip()
                suggestions.append(f"Opening line to review: ‘{opening[:150]}’. Check that it names your role or specialization rather than only describing general strengths.")

            metric_match = re.search(
                r"(?:\$\s?\d[\d,.]*|\b\d+(?:\.\d+)?\s?%|\b\d{2,}\+?\s+(?:users|customers|projects|years|records|teams))",
                text,
                re.I,
            )
            if metric_match:
                suggestions.append(f"Evidence found: ‘{metric_match.group(0)}’. Keep it only if you can explain what it measures and where it came from.")
            else:
                suggestions.append("Evidence gap: no clear scale or result was detected. Add a real metric or specific project outcome only when you can verify it.")

        elif "experience" in section_lower or "work" in section_lower:
            has_action = any(
                re.search(rf"\b{re.escape(verb)}\b", text, re.I) for verb in STRONG_ACTION_VERBS[:15]
            )
            if not has_action:
                suggestions.append("1. Begin each accomplishment with an active leadership verb (e.g., 'Engineered', 'Orchestrated', 'Delivered').")
            else:
                suggestions.append("1. Diversify action verbs across bullet points to demonstrate multi-faceted leadership and execution.")

            has_quant = bool(re.search(r"(?:\$\s?\d|\b\d+(?:\.\d+)?\s?%|\b\d{2,}\b)", text))
            if not has_quant:
                suggestions.append("2. Quantify results using metrics (e.g., 'reduced latency by 35%', 'managed $50K budget', 'served 10,000+ users').")
            else:
                suggestions.append("2. Connect every metric to business impact (explain what the quantitative improvement achieved for the company).")

            suggestions.append("3. Adopt the Google XYZ formula: 'Accomplished [X], as measured by [Y], by doing [Z]'.")

        elif "project" in section_lower:
            suggestions.append("1. Highlight the technical architecture, key libraries, and frameworks utilized for each project.")
            suggestions.append("2. Clarify whether the project was deployed to production, containerized (Docker), or published open-source.")
            suggestions.append("3. Include direct links to GitHub repositories or live demonstrations where applicable.")

        else:
            suggestions.append("1. Maintain clean, standardized formatting without complex multi-column tables for maximum ATS readability.")
            suggestions.append("2. Verify that industry-standard terminology is spelled accurately without non-standard abbreviations.")
            suggestions.append("3. Keep bullet points concise (under 2 lines each) for quick scanning by recruiters.")

        return "\n".join(suggestions)

    def compare_resumes(
        self,
        text_a: str,
        text_b: str,
        target_role: str,
        job_description: str = "",
        target_source_name: str = "",
    ) -> Dict[str, Any]:
        """
        Performs an in-depth, transparent multi-factor comparison of two resumes locally
        using the unified analyzer evaluation rubric.
        Ensures identical scoring, taxonomy, and job description prioritization.
        """
        import analyzer

        eval_a = analyzer.analyze_resume(
            text_a,
            target_role=target_role,
            pasted_jd=job_description,
            target_source_name=target_source_name,
        )
        eval_b = analyzer.analyze_resume(
            text_b,
            target_role=target_role,
            pasted_jd=job_description,
            target_source_name=target_source_name,
        )

        def build_resume_metric_dict(ev: Dict[str, Any], text: str) -> Dict[str, Any]:
            lower = text.lower()
            action_count = sum(1 for verb in STRONG_ACTION_VERBS if re.search(rf"\b{re.escape(verb)}\b", lower))
            has_metrics = len(re.findall(r"(?:\$\s?\d|\b\d+(?:\.\d+)?\s?%|\b\d{2,}\b)", text))

            skills_pct = int(round((ev["role_score"] / 40.0) * 100))
            format_pct = int(round((ev["section_score"] / 30.0) * 100))
            project_pct = int(round((ev["impact_score"] / 15.0) * 100))

            jd_info = ev.get("jd_analysis", {})
            if job_description.strip() and jd_info.get("available") and jd_info.get("score") is not None:
                job_score = jd_info["score"]
            else:
                job_score = skills_pct

            feedback = analyzer.generate_suggestions(ev, target_role)

            return {
                "ats_score": ev["total_score"],
                "skills_match": skills_pct,
                "projects_quality": project_pct,
                "format_structure": format_pct,
                "job_match_score": job_score,
                "role_score": ev["role_score"],
                "section_score": ev["section_score"],
                "impact_score": ev["impact_score"],
                "length_score": ev["length_score"],
                "matched_skills": ev["matched_skills"],
                "missing_skills": ev["missing_skills"],
                "analyzed_skills": ev.get("analyzed_skills", []),
                "role_fit_source": ev.get("role_fit_source", "Target Role Preset"),
                "score_breakdown": ev.get("score_breakdown", {}),
                "feedback": feedback[:4],
                "action_count": action_count,
                "metrics_count": has_metrics,
                "word_count": ev["word_count"],
            }

        res_a = build_resume_metric_dict(eval_a, text_a)
        res_b = build_resume_metric_dict(eval_b, text_b)

        # Highlights of differences
        highlights = []
        delta_ats = res_b["ats_score"] - res_a["ats_score"]
        if delta_ats > 0:
            highlights.append(f"Resume B has a higher overall ATS score (+{delta_ats} points).")
        elif delta_ats < 0:
            highlights.append(f"Resume A leads in overall ATS score (+{abs(delta_ats)} points).")
        else:
            highlights.append("Both resumes have comparable overall ATS scoring.")

        delta_role = res_b["role_score"] - res_a["role_score"]
        role_label = eval_a.get("role_fit_target_name", target_role)
        if delta_role > 0:
            highlights.append(f"Resume B matched more target skills for {role_label} ({len(res_b['matched_skills'])} vs {len(res_a['matched_skills'])} matched).")
        elif delta_role < 0:
            highlights.append(f"Resume A matched more target skills for {role_label} ({len(res_a['matched_skills'])} vs {len(res_b['matched_skills'])} matched).")
        else:
            highlights.append(f"Both resumes matched {len(res_a['matched_skills'])} target skills for {role_label}.")

        if res_b["metrics_count"] > res_a["metrics_count"]:
            highlights.append(f"Resume B includes more quantified achievements ({res_b['metrics_count']} vs {res_a['metrics_count']} metrics).")
        elif res_a["metrics_count"] > res_b["metrics_count"]:
            highlights.append(f"Resume A includes more quantified achievements ({res_a['metrics_count']} vs {res_b['metrics_count']} metrics).")

        role_target_name = eval_a.get("role_fit_target_name", target_role)
        rank_a = (res_a["ats_score"], res_a["role_score"], res_a["impact_score"], res_a["section_score"], res_a["length_score"])
        rank_b = (res_b["ats_score"], res_b["role_score"], res_b["impact_score"], res_b["section_score"], res_b["length_score"])
        if rank_a > rank_b:
            winner_label, winner, runner_up = "Resume A", res_a, res_b
        elif rank_b > rank_a:
            winner_label, winner, runner_up = "Resume B", res_b, res_a
        else:
            winner_label, winner, runner_up = "Close match", None, None

        recommendation_reasons = []
        if winner:
            newly_matched = [skill for skill in winner["matched_skills"] if skill not in runner_up["matched_skills"]]
            if newly_matched:
                detail = ", ".join(newly_matched[:5])
                recommendation_reasons.append(
                    "It contains target-skill evidence not detected in the other version: " + detail + "."
                )
            elif len(winner["matched_skills"]) > len(runner_up["matched_skills"]):
                recommendation_reasons.append(
                    f"It matches {len(winner['matched_skills']) - len(runner_up['matched_skills'])} more target skill(s)."
                )
            for key, label in (("impact_score", "achievement evidence"), ("section_score", "resume structure"), ("length_score", "length")):
                delta = winner[key] - runner_up[key]
                if delta:
                    recommendation_reasons.append(f"It scores {delta} points higher for {label}.")
            if winner["metrics_count"] > runner_up["metrics_count"]:
                recommendation_reasons.append(
                    f"It includes more numeric evidence ({winner['metrics_count']} detected metric(s) vs {runner_up['metrics_count']})."
                )
            if winner["missing_skills"]:
                recommendation_reasons.append(
                    "Its main remaining target-skill gaps are " + ", ".join(winner["missing_skills"][:4]) + "."
                )
        else:
            recommendation_reasons.append("The two resumes received the same score on the available comparison signals.")

        report = (
            f"Local Comparative Analysis ({role_target_name}):\n\n"
            f"- Resume A: Total Score {res_a['ats_score']}/100 (Role Fit: {res_a['role_score']}/40, "
            f"Sections: {res_a['section_score']}/30, Impact: {res_a['impact_score']}/15, Length: {res_a['length_score']}/15). "
            f"Contains {res_a['word_count']} words with {len(res_a['matched_skills'])} matched target skills.\n"
            f"- Resume B: Total Score {res_b['ats_score']}/100 (Role Fit: {res_b['role_score']}/40, "
            f"Sections: {res_b['section_score']}/30, Impact: {res_b['impact_score']}/15, Length: {res_b['length_score']}/15). "
            f"Contains {res_b['word_count']} words with {len(res_b['matched_skills'])} matched target skills.\n\n"
            f"Recommendation: {winner_label} has the stronger measured alignment on this rubric. "
            "Use the reasons and remaining gaps below as a review aid, not as a hiring decision."
        )

        return {
            "resume_a": res_a,
            "resume_b": res_b,
            "target_skills": eval_a.get("analyzed_skills", []),
            "role_fit_source": eval_a.get("role_fit_source", "Target Role Preset"),
            "jd_fallback_notice": eval_a.get("jd_fallback_notice"),
            "report": report,
            "highlights": highlights,
            "winner": winner_label,
            "recommendation_reasons": recommendation_reasons,
            "model": "Local Unified Evaluator (Offline)",
        }


# Global singleton instance for easy import across modules
local_engine = LocalResumeEngine()
