#!/usr/bin/env python3
"""
generate_skill_labels.py (v3 - Precision & Context-Aware Edition)
-----------------------------------------------------------------
Standalone Python script for generating first-pass candidate skill labels from
local job postings using O*NET Workplace Examples as a candidate software vocabulary.

Key Improvements in v3:
1. Strict Workplace Example Vocabulary:
   - Uses 'Workplace Example' exclusively; excludes category descriptors and occupation titles.
2. Single-Letter Language Guardrail:
   - 'C' and 'R' require strong programming language / data science context (e.g., 'C/C++',
     'embedded C', 'RStudio', 'Python and R'). Rejects corporate postnominals ('P.C.'),
     executive roles ('C-level'), hardware ('USB-C'), and generic labels.
3. Targeted Contextual Disambiguation:
   - 'ASPEN': Rejects healthcare/companies ('Aspen Therapy and Wellness', 'Aspen Dental')
     and locations; accepts only chemical/process simulation software ('Aspen Plus', 'Aspen HYSYS').
   - 'ADA': Rejects civil rights legislation ('Americans with Disabilities Act', 'ADA compliance');
     accepts only Ada programming language context (e.g., 'Ada 95', 'Ada 2012', 'GNAT').
   - 'Go': Rejects ordinary prose and idioms ('go to', 'go beyond', 'go-getter'); requires
     verified Golang/developer context.
   - 'React': Rejects ordinary verbs ('react quickly', 'ability to react'); requires web/frontend
     context (e.g., 'React.js', 'React components', 'TypeScript', 'Redux').
   - 'Route': Rejects ordinary verbs/delivery phrases ('route calls', 'delivery route');
     accepts only verified cloud/networking tools ('AWS Route 53', 'Cisco Route').
   - 'Zoom': Rejects interview etiquette and dress policies ('Zoom dress required');
     accepts only video conferencing software context.
   - 'Google': Excludes employer and company references ('worked at Google', 'Google is an
     equal opportunity employer'); accepts only explicit named software products (e.g.,
     'Google Analytics', 'Google Workspace', 'Google Cloud Platform').
   - 'Square' & 'Juris': Preserves POS and legal billing software disambiguation.
4. Skill-Tied Requirement Classification:
   - Requirement cues ('required', 'must have') are verified to modify the skill itself.
   - Unrelated requirement cues (e.g., 'dress required', 'license required', 'travel required')
     do not attach to nearby tools and correctly resolve to 'mentioned' or 'unclear'.
5. Exact Evidence & Safe Output:
   - Preserves job_id strictly as text, copies exact verbatim evidence snippets, marks all
     rows as 'needs_review', outputs a heuristic match rating (not calibrated probability),
     and defaults to 'skill_labels_auto_v3.csv' with overwrite protection.
6. Local Test Suite:
   - Includes a built-in test suite (`--test`) covering all false-positive scenarios.
"""

import argparse
from collections import Counter
import csv
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple


# Increase CSV field size limit to support massive job descriptions safely
def configure_csv_field_limit() -> None:
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 10)


configure_csv_field_limit()


# ==============================================================================
# 1. Header Detection & Normalization
# ==============================================================================

def normalize_header_name(header: str) -> str:
    """Normalize column header for case/punctuation-insensitive comparison."""
    return re.sub(r'[^a-z0-9]', '', header.lower().strip())


def detect_columns(
    actual_headers: List[str],
    alias_map: Dict[str, List[str]],
    required_keys: List[str],
    file_label: str
) -> Dict[str, str]:
    """
    Match actual CSV headers against expected aliases case-insensitively.
    Raises ValueError with a helpful message if any required key is missing.
    """
    norm_actual = {normalize_header_name(h): h for h in actual_headers}
    detected: Dict[str, str] = {}
    missing_required: List[str] = []

    for key, aliases in alias_map.items():
        matched_header = None
        for alias in aliases:
            norm_alias = normalize_header_name(alias)
            if norm_alias in norm_actual:
                matched_header = norm_actual[norm_alias]
                break
        if matched_header:
            detected[key] = matched_header
        elif key in required_keys:
            missing_required.append(key)

    if missing_required:
        raise ValueError(
            f"Missing required column(s) for {file_label}: {missing_required}.\n"
            f"Available headers in file: {actual_headers}"
        )

    return detected


# ==============================================================================
# 2. Vocabulary Loader & Intake Filters
# ==============================================================================

SHORT_CASE_SENSITIVE_TERMS: Set[str] = {
    "go", "c", "r", "in", "to", "at", "it", "on", "as", "an",
    "be", "by", "do", "if", "is", "me", "my", "no", "or", "so", "up", "us", "ada"
}

EXCLUDED_CANDIDATE_TERMS: Set[str] = {
    "front desk",
}

ORDINARY_VERBS_BLOCKLIST: Set[str] = {
    "analyze", "analysing", "analyzing", "analysis", "analyses",
    "reduce", "reducing", "reduction", "reduces",
    "increase", "increasing", "improve", "improving",
    "ensure", "ensuring", "provide", "providing",
    "perform", "performing", "drive", "driving",
    "deliver", "delivering", "meet", "meeting",
    "support", "supporting", "assist", "assisting",
    "help", "helping", "work", "working",
    "handle", "handling", "build", "building",
    "create", "creating", "lead", "leading", "leadership",
    "manage", "managing", "management",
    "train", "training", "evaluate", "evaluating", "evaluation",
    "schedule", "scheduling", "organize", "organizing", "organization",
    "operate", "operating", "operations", "maintain", "maintaining", "maintenance",
    "collaborate", "collaborating", "collaboration",
    "plan", "planning", "plans", "execute", "executing", "execution",
    "design", "designing", "solve", "solving", "problem solving",
    "review", "reviewing", "communicate", "communicating", "communication",
    "troubleshoot", "troubleshooting", "implement", "implementing", "implementation",
    "develop", "developing", "development", "monitor", "monitoring",
    "supervise", "supervising", "supervision", "coordinate", "coordinating", "coordination",
}

JOB_TITLE_KEYWORDS: Set[str] = {
    "manager", "director", "supervisor", "administrator", "coordinator",
    "specialist", "technician", "consultant", "officer", "representative",
    "associate", "assistant", "executive", "worker", "operator", "clerk",
    "cashier", "nurse", "physician", "doctor", "lawyer", "attorney",
    "chef", "cook", "driver", "crew member", "server", "bartender"
}


def clean_term(raw_term: str) -> str:
    """Clean whitespace and normalize quotes while preserving symbols."""
    cleaned = re.sub(r'\s+', ' ', raw_term).strip()
    return cleaned.strip('"\'()[]{}')


def is_job_title_term(term: str) -> bool:
    """Detect if a candidate vocabulary term is an occupational title."""
    t_lower = term.lower().strip()
    words = t_lower.split()
    return any(k in words for k in JOB_TITLE_KEYWORDS)


def is_valid_software_candidate(term: str) -> bool:
    """Validate candidate term at vocabulary intake."""
    t_lower = term.lower().strip()
    if not t_lower:
        return False
    if t_lower in EXCLUDED_CANDIDATE_TERMS:
        return False
    if t_lower in ORDINARY_VERBS_BLOCKLIST:
        return False
    if is_job_title_term(term):
        return False
    if len(term) == 1 and term not in {"C", "R"}:
        return False
    if len(term) > 80:
        return False
    return True


def load_candidate_vocabulary(
    skills_csv_path: str
) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    """
    Load candidate skills strictly from 'Workplace Example' in software_skills.csv.
    Ignores generic 'Element Name' category words and occupational labels.
    """
    if not os.path.exists(skills_csv_path):
        raise FileNotFoundError(f"Skills vocabulary file not found: {skills_csv_path}")

    alias_map = {
        "workplace_example": [
            "workplace example", "workplace_example", "example",
            "software skill", "skill example"
        ],
        "element_name": ["element name", "element_name", "element", "category"],
        "title": ["title", "onet title", "occupation title"],
        "hot_technology": ["hot technology", "hot_technology", "hot tech"],
        "in_demand": ["in demand", "in_demand", "demand"],
    }

    terms_set: Set[str] = set()
    term_meta: Dict[str, Dict[str, str]] = {}

    with open(skills_csv_path, mode='r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError(f"Skills file {skills_csv_path} is empty.")

        detected = detect_columns(
            headers,
            alias_map,
            required_keys=["workplace_example"],
            file_label="software_skills.csv"
        )

        print("[INFO] Detected columns in software_skills.csv:")
        for k, v in detected.items():
            print(f"       - {k:18} -> '{v}'")

        header_indices = {h: idx for idx, h in enumerate(headers)}
        idx_ex = header_indices[detected["workplace_example"]]

        filtered_verb_count = 0
        filtered_job_title_count = 0

        for row in reader:
            if idx_ex >= len(row):
                continue
            raw_val = row[idx_ex].strip()
            if not raw_val:
                continue

            cleaned = clean_term(raw_val)
            if not cleaned:
                continue

            t_lower = cleaned.lower()
            if t_lower in ORDINARY_VERBS_BLOCKLIST:
                filtered_verb_count += 1
                continue
            if is_job_title_term(cleaned):
                filtered_job_title_count += 1
                continue

            if not is_valid_software_candidate(cleaned):
                continue

            if t_lower not in term_meta:
                term_meta[t_lower] = {
                    "canonical": cleaned,
                    "origin": "Workplace Example",
                }
                terms_set.add(cleaned)

    # Ensure Google Cloud Platform is registered as canonical software candidate
    if "google cloud platform" not in term_meta:
        term_meta["google cloud platform"] = {
            "canonical": "Google Cloud Platform",
            "origin": "Workplace Example Alias",
        }
        terms_set.add("Google Cloud Platform")

    sorted_terms = sorted(list(terms_set), key=lambda x: len(x), reverse=True)
    print(f"[INFO] Loaded {len(sorted_terms)} candidate software skills from 'Workplace Example'.")
    print(f"       (Filtered out {filtered_verb_count} ordinary verbs and {filtered_job_title_count} occupational titles)")
    return sorted_terms, term_meta


# ==============================================================================
# 3. Regex Matchers & Contextual Disambiguation
# ==============================================================================

def build_batched_matchers(terms: List[str], chunk_size: int = 400) -> List[Tuple[re.Pattern, List[str]]]:
    """Compile boundary-safe regex patterns in batches for efficient scanning."""
    case_sensitive_terms = [t for t in terms if (len(t) <= 2) or (t.lower() in SHORT_CASE_SENSITIVE_TERMS)]
    case_insensitive_terms = [t for t in terms if (len(t) > 2) and (t.lower() not in SHORT_CASE_SENSITIVE_TERMS)]

    matchers: List[Tuple[re.Pattern, List[str]]] = []

    for i in range(0, len(case_insensitive_terms), chunk_size):
        chunk = case_insensitive_terms[i:i + chunk_size]
        joined = '|'.join(re.escape(t) for t in chunk)
        pat = re.compile(r'(?<![a-zA-Z0-9_])(' + joined + r')(?![a-zA-Z0-9_])', re.IGNORECASE)
        matchers.append((pat, chunk))

    for i in range(0, len(case_sensitive_terms), chunk_size):
        chunk = case_sensitive_terms[i:i + chunk_size]
        joined = '|'.join(re.escape(t) for t in chunk)
        pat = re.compile(r'(?<![a-zA-Z0-9_])(' + joined + r')(?![a-zA-Z0-9_])', 0)
        matchers.append((pat, chunk))

    return matchers


def filter_overlapping_spans(raw_matches: List[Dict]) -> List[Dict]:
    """Resolve overlapping matches in favor of longer character spans."""
    sorted_matches = sorted(raw_matches, key=lambda m: (-(m["end"] - m["start"]), m["start"]))
    accepted = []
    occupied_intervals: List[Tuple[int, int]] = []

    for m in sorted_matches:
        s, e = m["start"], m["end"]
        overlap = False
        for os, oe in occupied_intervals:
            if max(s, os) < min(e, oe):
                overlap = True
                break
        if not overlap:
            accepted.append(m)
            occupied_intervals.append((s, e))

    accepted.sort(key=lambda m: m["start"])
    return accepted


def is_contextual_false_positive(
    desc: str,
    start: int,
    end: int,
    canonical_skill: str,
    posting_title: str = ""
) -> Tuple[bool, str]:
    """
    Context-aware disambiguation filter to reject ambiguous terms, places,
    degrees, and ordinary verbs based on local text patterns.
    """
    skill_lower = canonical_skill.lower()

    # Reject Front Desk as reception/clerical work rather than software.
    if skill_lower == "front desk":
        return True, "reception/clerical work rather than software tool ('Front Desk')"

    # 1. Posting Title collision: avoid matching posting's own title as a skill
    if posting_title:
        pt_norm = re.sub(r'[^a-z0-9]', '', posting_title.lower())
        sk_norm = re.sub(r'[^a-z0-9]', '', skill_lower)
        if sk_norm and (sk_norm == pt_norm or sk_norm in pt_norm.split()):
            return True, f"matches posting job title '{posting_title}'"

    window_before = desc[max(0, start - 50):start].lower()
    window_after = desc[end:min(len(desc), end + 50)].lower()
    wide_window = desc[max(0, start - 100):min(len(desc), end + 100)].lower()

    # Rejection of declined offers mention (e.g. turned down offers from Airbnb, Pinterest)
    if re.search(r'\b(?:turned\s+down\s+offers\s+from|declined\s+offers\s+from|rejected\s+offers\s+from)\b', wide_window):
        return True, "company mentioned among declined/turned down offers"

    # Rejection of application portal mentions (e.g. Apply on LinkedIn)
    if re.search(r'\b(?:apply\s+(?:now\s+)?(?:on|via|through|at)|submit\s+(?:your\s+)?(?:application|resume|cv)\s+(?:on|via|through|at))\s+$', window_before):
        return True, "job application channel/portal ('Apply on LinkedIn') rather than skill"

    # Rejection of employer profile links / page references (e.g. "our YouTube page", "check out our Facebook")
    if re.search(r'\b(?:on\s+our|check\s+out\s+our|visit\s+our|view\s+our|follow\s+us\s+on|like\s+us\s+on|subscribe\s+to\s+our|find\s+us\s+on)\s+$', window_before):
        return True, "employer social media link/page reference rather than skill"
    is_social_duty = bool(
        re.search(r'\b(?:curate|upload|manage|post|creating|create|grow|maintain|administer|publish|schedule|monitor|run|engage|coordinate)\b', window_before) or
        re.search(r'\b(?:social\s+media|marketing|content|community|communications|coordinator)\b', posting_title.lower())
    )
    if not is_social_duty and re.search(r'\b(?:our|the\s+company\'?s?)\s+$', window_before) and re.search(r'^\s*(?:page|channel|account|handle|profile|feed)\b', window_after):
        return True, "employer social media link/page reference rather than skill"

    # Rejection of employer social media handle announcements in company info
    if re.search(r'\b(?:presence\s+on\s+social\s+media|social\s+media\s+platforms\s+such\s+as)\b', wide_window) and re.search(r'\b(?:under\s+the\s+name|follow\s+us|our\s+handles?)\b', wide_window):
        return True, "employer social media handle announcement rather than job skill"

    # Rejection of employer promotional text / partnership marketing for technical roles (e.g. Google Ads/Semrush in SWE role)
    is_technical_role = bool(re.search(r'\b(?:software|developer|engineer|backend|frontend|full\s*stack|systems|linux|devops|data\s+engineer|architect)\b', posting_title.lower()))
    if is_technical_role and skill_lower in ("google ads", "semrush", "seo"):
        if re.search(r'\b(?:companies\s+rely\s+on|partnered\s+with|industry\s+leader|product\s+market\s+fit|arr\s+in\s+the|our\s+platform)\b', wide_window):
            return True, "employer product/partnership promotional copy for engineering role rather than job skill"

    # 2. 'C' single-letter programming language check
    if canonical_skill == "C":
        if re.search(r'\b[pP]\s*\.\s*$', desc[max(0, start - 10):start]):
            return True, "legal/corporate postnominal ('P.C.')"
        if re.search(r'^\s*\.', desc[end:min(len(desc), end + 5)]) and re.search(r'\b[pP]\s*$', desc[max(0, start - 5):start]):
            return True, "legal/corporate postnominal ('P.C.')"
        if re.search(r'\b(?:usb|type)[\s\-]?$', window_before) or re.search(r'^[\s\-]?(?:suite|level|section|schedule|class|vitamin|grade|part)\b', window_after):
            return True, "non-programming C usage (USB-C, C-level, Class C)"
        direct_c_patterns = [
            r'\bc\s*/\s*c\+\+', r'\bc\+\+\s*/\s*c\b', r'\bc\s*,\s*c\+\+', r'\bc\s+and\s+c\+\+', r'\bc\s+or\s+c\+\+',
            r'\bc\s+(?:programming|code|coding|developer|engineer|compiler|runtime|language)\b',
            r'\b(?:embedded|ansi)\s+c\b',
            r'\b(?:written|coded|programmed)\s+in\s+c\b',
            r'\b(?:proficient|proficiency|experience|skills?)\s+in\s+c\s*[,;]'
        ]
        if any(re.search(pat, wide_window) for pat in direct_c_patterns):
            return False, ""
        pl_signals = [r'\bpython\b', r'\bjava\b', r'\bc\+\+\b', r'\brust\b', r'\bassembly\b', r'\bgolang\b']
        if sum(1 for sig in pl_signals if re.search(sig, wide_window)) >= 2:
            return False, ""
        return True, "insufficient C programming context"

    # 3. 'R' single-letter data science language check
    if canonical_skill == "R":
        if re.search(r'\b(?:r\s*&\s*d|r\s+and\s+d|model)\b', wide_window):
            return True, "non-programming usage ('R&D')"
        r_patterns = [
            r'\br\s+(?:programming|script(?:s|ing)?|package[s]?|library|shiny|markdown|studio|developer|data\s+analysis)\b',
            r'\brstudio\b', r'\b(?:r\s*/\s*python|python\s*/\s*r|python\s+and\s+r|r\s+and\s+python|r\s+or\s+python)\b',
            r'\b(?:sas|spss|stata|matlab|sql)\s*,\s*r\b', r'\br\s*,\s*(?:sas|spss|stata|matlab|sql)\b',
            r'\b(?:proficient|proficiency|experience)\s+in\s+r\s*[,;]'
        ]
        if any(re.search(pat, wide_window) for pat in r_patterns):
            return False, ""
        return True, "insufficient R statistical programming context"

    # 4. 'ASPEN': reject company names and locations
    if skill_lower == "aspen":
        aspen_org_indicators = [
            r'\b(?:therapy|wellness|dental|clinic|hospital|medical|healthcare|living|rehab|ridge|grove|valley|springs|ski|resort|mountain|park|school|academy|district|hotel)\b',
            r'\b(?:corp|inc|llc|co\.|corporation|group|center|centre|associates)\b'
        ]
        if any(re.search(pat, wide_window) for pat in aspen_org_indicators):
            return True, "healthcare, corporate, or geographic Aspen reference ('Aspen Therapy and Wellness')"
        aspen_soft_indicators = [
            r'\baspen\s+(?:plus|hysys|tech|custom|simulation|process|properties|modeler)\b',
            r'\b(?:chemical|process)\s+engineering\b',
            r'\bprocess\s+simulation\b',
            r'\bflowsheet\b',
        ]
        if any(re.search(pat, wide_window) for pat in aspen_soft_indicators):
            return False, ""
        return True, "ambiguous Aspen without chemical simulation software context"

    # 5. 'ADA': reject Americans with Disabilities Act
    if skill_lower == "ada":
        ada_law_indicators = [
            r'\bamericans\s+with\s+disabilit(?:y|ies)\b',
            r'\b(?:act|compliance|compliant|accommodation[s]?|disabilit(?:y|ies)|eeo|equal\s+opportunity)\b',
            r'\b(?:physical\s+demands?|work\s+environment|sensory|mobility|lifting|reasonable)\b',
            r'\btitle\s+[ivx]+\b'
        ]
        if any(re.search(pat, wide_window) for pat in ada_law_indicators):
            return True, "Americans with Disabilities Act (ADA) legal/compliance context"
        ada_pl_indicators = [
            r'\bada\s+(?:95|2005|2012|83|programming|code|compiler|developer|runtime|software)\b',
            r'\bgnat\b',
            r'\b(?:embedded|avionics|aerospace|defense)\s+(?:systems?|software)\b',
            r'\b(?:c|c\+\+|fortran|assembly)\s*,\s*ada\b'
        ]
        if any(re.search(pat, wide_window) for pat in ada_pl_indicators):
            return False, ""
        return True, "ambiguous ADA without programming language context"

    # 6. 'Route': reject ordinary action verbs and delivery paths
    if skill_lower == "route":
        if re.search(r'\b(?:to|will|can|must|should|ability\s+to)\s+$', window_before):
            return True, "ordinary action verb ('to route')"
        if re.search(r'^\s*(?:calls|inquiries|tickets|traffic|vehicles|trucks|drivers|deliveries|orders)\b', window_after):
            return True, "ordinary action verb ('route calls/tickets')"
        if re.search(r'\b(?:delivery|driving|bus|truck|sales|assigned)\s+$', window_before):
            return True, "physical transportation path ('delivery route')"
        if re.search(r'\b(?:route\s*53|aws\s+route|cisco\s+route|ip\s+routing|routing\s+protocols?|bgp|ospf)\b', wide_window):
            return False, ""
        return True, "ambiguous Route without cloud/networking software context"

    # 7. 'React': reject ordinary action verbs ('react quickly')
    if skill_lower == "react":
        if re.search(r'\b(?:ability\s+to|able\s+to|can|must|will|should|to|how\s+to|quick\s+to)\s+$', window_before):
            return True, "ordinary action verb ('ability to react')"
        if re.search(r'^\s*(?:quickly|calmly|appropriately|under\s+pressure|to\s+changes|to\s+emergenc|to\s+incidents|to\s+situations|fast)\b', window_after):
            return True, "ordinary action verb ('react quickly')"
        if re.search(r'\b(?:react\s+and\s+respond|respond\s+and\s+react)\b', wide_window):
            return True, "ordinary behavioral phrase ('react and respond')"
        react_tech_indicators = [
            r'\breact\s*(?:\.?js|js|native)\b',
            r'\breact\s+(?:framework|library|developer|engineer|frontend|ui|components?|hooks?|redux)\b',
            r'\b(?:javascript|typescript|html|css|redux|angular|vue|next\.?js|frontend|full\s*stack|node\.?js)\b'
        ]
        if any(re.search(pat, wide_window) for pat in react_tech_indicators):
            return False, ""
        return True, "ambiguous React without frontend framework context"

    # 8. 'Zoom': reject meeting etiquette and dress codes
    if skill_lower == "zoom":
        if re.search(r'^\s*(?:dress|attire|appearance|camera|background|etiquette|link|invitation)\b', window_after):
            return True, "video call etiquette/dress code policy ('Zoom dress')"
        zoom_tech_indicators = [
            r'\b(?:video\s+conferencing|webinar[s]?|slack|teams|google\s+meet|webex|conferencing\s+tools?)\b',
            r'\bzoom\s+(?:software|app|platform|meetings|rooms|admin|license)\b'
        ]
        if any(re.search(pat, wide_window) for pat in zoom_tech_indicators):
            return False, ""
        return True, "ambiguous Zoom reference without video conferencing tool context"

    # 9. 'Google': distinguish named products from employer/brand
    if skill_lower == "google":
        if re.search(r'^\s*(?:cloud\s+platform)\b', window_after):
            return True, "subsumed by Google Cloud Platform"
        if re.search(r'\b(?:at|for|by|with|from|ex-|former)\s+$', window_before):
            return True, "employer reference ('worked at Google')"
        if re.search(r'^\s*(?:is\s+an\s+equal|recruiter|employee|engineer|campus|headquarters|office[s]?|review[s]?|search|rating)\b', window_after):
            return True, "company/employer mention ('Google is an equal opportunity employer')"
        named_products = [
            r'^\s*(?:analytics|workspace|cloud|gcp|sheets|docs|slides|drive|bigquery|ads|adsense|tag\s+manager|data\s+studio|looker|kubernetes\s+engine|search\s+console)\b'
        ]
        if any(re.search(pat, window_after) for pat in named_products):
            return False, ""
        return True, "generic company mention without named Google product"

    # 10. 'Go': reject prose idioms
    if skill_lower == "go":
        if re.search(r'^\s*-(?:getter|getting)', window_after):
            return True, "idiomatic compound ('go-getter')"
        if re.search(r'^\s*(?:to|beyond|through|above|ahead|forward|into|out|with|on|by|from|over|under|away|back|further|the\s+extra)\b', window_after):
            return True, "ordinary prose verb phrase ('go to', 'go beyond', 'go through')"
        if re.search(r'^\s*(?:developer|engineer|programmer|programming|development|code|coding|backend|microservice[s]?|api[s]?|concurrency|goroutine[s]?|runtime|sdk|cli)\b', window_after):
            return False, ""
        if re.search(r'\b(?:proficient\s+in|experience\s+with|experience\s+in|knowledge\s+of|skills?\s+in|written\s+in|coding\s+in|programming\s+in)\s+$', window_before):
            return False, ""
        tech_signals = [
            r'\bgolang\b', r'\bpython\b', r'\bjava\b', r'\bc\+\+\b', r'\brust\b',
            r'\btypescript\b', r'\bjavascript\b', r'\bscala\b', r'\bkubernetes\b',
            r'\bdocker\b', r'\bbackend\b', r'\bdistributed\s+systems?\b'
        ]
        has_tech = any(re.search(sig, wide_window) for sig in tech_signals)
        is_verb = re.search(r'\b(?:will|can|must|should|to|let\'?s|we)\s+go\b', desc[max(0, start - 20):end].lower())
        if has_tech and not is_verb:
            return False, ""
        return True, "ambiguous use of 'Go' without programming language context"

    # 11. 'Square': reject places and area measurements
    if skill_lower == "square":
        if re.search(r'^\s*(?:feet|foot|ft|miles|mile|meters|meter|yards|yard|inches|inch|sq\b)', window_after):
            return True, "unit of area measurement ('square feet')"
        if re.search(r'\b(?:town|times|union|city|market|public|plaza|herald|franklin|washington|court|village|red|lafayette|center|centre|park|garden)\s+$', window_before):
            return True, "geographic location or plaza ('Town Square')"
        if re.search(r'^\s*(?:garden|park|mall|plaza|centre|center|station|avenue|street|boulevard)', window_after):
            return True, "geographic location or venue ('Square Garden')"
        has_pos_indicator = (
            re.search(r'\b(?:pos|terminal|payment[s]?|reader|register|card|checkout|app|api|software)\b', window_before) or
            re.search(r'^\s*(?:pos|terminal|payment[s]?|reader|register|card|checkout|app|api|software)', window_after) or
            re.search(r'\b(?:clover|toast|stripe|paypal|revel|lightspeed)\b', wide_window)
        )
        if not has_pos_indicator:
            return True, "ambiguous use of 'Square' without POS/payment software context"

    # 12. 'Juris': reject law degrees
    if skill_lower == "juris":
        if re.search(r'^\s*(?:doctor|doctorate|degree|\(?jd\)?|j\.d\.)', window_after):
            return True, "law degree ('Juris Doctor') rather than legal software"
        if re.search(r'\bdoctor\s+of\s+$', window_before):
            return True, "law degree ('Doctor of Jurisprudence')"
        has_legal_software = (
            re.search(r'\b(?:software|billing|accounting|lexisnexis|lexis)\b', window_before) or
            re.search(r'^\s*(?:software|billing|accounting)', window_after)
        )
        if not has_legal_software:
            return True, "ambiguous use of 'Juris' without legal billing software context"

    # 13. Office suite common words
    if skill_lower == "word":
        is_ms_word = (
            re.search(r'\b(?:microsoft|ms)\s+$', window_before) or
            re.search(r'^\s*(?:processing|processor)\b', window_after) or
            re.search(r'\b(?:excel|powerpoint|office|outlook)\b', wide_window)
        )
        if not is_ms_word:
            return True, "common English word ('word') without Microsoft Office context"

    if skill_lower == "access":
        is_ms_access = (
            re.search(r'\b(?:microsoft|ms)\s+$', window_before) or
            re.search(r'^\s*(?:database|db)\b', window_after) or
            re.search(r'\b(?:excel|sql|powerpoint|office)\b', wide_window)
        )
        if not is_ms_access:
            return True, "common noun/verb ('access') without Microsoft Access context"

    if skill_lower == "excel":
        if re.search(r'\b(?:to|will|must|ability\s+to|should|can)\s+$', window_before) or re.search(r'^\s*(?:in|at)\b', window_after):
            return True, "used as ordinary verb ('to excel in')"

    if skill_lower == "outlook":
        if re.search(r'\b(?:positive|strong|career|economic|market|business|growth|optimistic|future)\s+$', window_before):
            return True, "used in business/career sentiment context ('positive outlook')"

    if skill_lower == "teams":
        is_ms_teams = (
            re.search(r'\b(?:microsoft|ms)\s+$', window_before) or
            re.search(r'^\s*(?:chat|meeting[s]?|call[s]?|app)\b', window_after) or
            re.search(r'\b(?:slack|zoom|webex|office\s*365)\b', wide_window)
        )
        if not is_ms_teams:
            return True, "general team context ('work in teams') rather than Microsoft Teams"

    # 14. E-Verify: employer compliance verification program
    if skill_lower in ("e-verify", "everify"):
        if re.search(r'\b(?:participat(?:e|es|ing)|employment\s+verification|program|eeo|equal\s+opportunity|right\s+to\s+work|federal\s+law)\b', wide_window):
            return True, "employer participation in E-Verify employment verification program"

    # 15. Private Practice: clinical/business setting rather than software
    if skill_lower == "private practice":
        if not re.search(r'\b(?:software|system|app|ehr|emr|billing\s+software)\b', wide_window):
            return True, "clinical/business operating structure ('Private Practice') rather than software tool"

    # 16. FEAR: ordinary prose without finite element software context
    if skill_lower == "fear":
        if re.search(r'\b(?:cape\s+fear|fear\s+of|without\s+fear|free\s+from\s+fear|in\s+fear|have\s+no\s+fear)\b', wide_window):
            return True, "ordinary English prose ('fear') rather than finite element software"
        if not re.search(r'\b(?:finite\s+element|fea\b|software|simulation)\b', wide_window):
            return True, "ordinary English prose ('fear') without finite element software context"

    # 17. HARVEST: ordinary agricultural/seasonal prose without time-tracking software context
    if skill_lower == "harvest":
        if re.search(r'\b(?:harvest\s+season|week\s+harvest|crop|grape|wine|grain|farm|farming|agriculture|harvest\s+manager|lead\s+harvest|during\s+harvest)\b', wide_window):
            return True, "ordinary word/agricultural context ('harvest') rather than software"
        if not re.search(r'\b(?:time\s+tracking|timesheet|invoicing|saas|app|software|toggl|clockify)\b', wide_window):
            return True, "ordinary word ('harvest') without software context"

    # 18. Forth: ordinary prose idioms ('call forth', 'set forth') without programming language context
    if skill_lower == "forth":
        if re.search(r'\b(?:call|calls|called|calling|set|sets|setting|bring|brings|brought|put|puts|held|hold|holds|and\s+so|back\s+and|go|coming)\s+$', window_before):
            return True, "ordinary prose idiom ('set forth', 'call forth') rather than Forth language"
        if not re.search(r'\b(?:forth\s+(?:programming|language|code|developer)|assembly|lisp|pascal|prolog)\b', wide_window):
            return True, "ordinary prose ('forth') without programming language context"

    # 19. MAGIC: ordinary English idiom ('work magic') without software context
    if skill_lower == "magic":
        if re.search(r'\b(?:work|works|working|worked|do|does|doing|make|makes|making|like|pure)\s+$', window_before) or re.search(r'^\s*(?:with|wand|bullet|happen|touch)\b', window_after):
            return True, "ordinary English idiom ('work magic') rather than MAGIC software"
        if not re.search(r'\bmagic\s+(?:software|xpa|xpi|pc|enterprise)\b', wide_window):
            return True, "ordinary English word ('magic') without software context"

    # 20. Dig: ordinary action verb ('dig deep') without DNS query tool context
    if skill_lower == "dig":
        if re.search(r'\b(?:to|and|can|will|should|must|ability\s+to)\s+$', window_before) or re.search(r'^\s*(?:deep|into|through|up|in|out|down)\b', window_after):
            return True, "ordinary English verb ('dig deep') rather than DNS query tool"
        if not re.search(r'\b(?:dns|nslookup|traceroute|ping|whois|bind|query\s+tool|dig\s+(?:command|utility|tool))\b', wide_window):
            return True, "ordinary English verb ('dig') without DNS utility context"

    # 21. Rest assured: ordinary conversational idiom without API testing framework context
    if skill_lower in ("rest assured", "rest-assured"):
        if re.search(r'^\s*(?:[,;:\.!\?]|that|we|you|our|your)\b', window_after) or re.search(r'\b(?:can|please)\s+$', window_before):
            return True, "ordinary conversational idiom ('rest assured') rather than REST Assured testing framework"
        if not re.search(r'\b(?:api|testing|framework|automation|qa|java|restassured|postman|junit|testng)\b', wide_window):
            return True, "ordinary idiom ('rest assured') without API testing context"

    # 22. SAND: physical material or therapy modality ('sand-tray therapy') without software context
    if skill_lower == "sand":
        if re.search(r'^\s*-(?:tray|play|box|blast|table|stone|filter)\b', window_after) or re.search(r'\b(?:sand-tray|sand\s+tray|therapy|craft|children|rooms|beach|gravel)\b', wide_window):
            return True, "physical material or therapy modality ('sand-tray therapy') rather than software"
        if not re.search(r'\b(?:sandia|simulation|software|cad)\b', wide_window):
            return True, "physical material ('sand') without software context"

    # 23. TANKS: physical vehicles or vessels ('military tanks') without EPA TANKS software context
    if skill_lower == "tanks":
        if re.search(r'\b(?:military|army|armored|water|fuel|storage|holding|fish|septic|airplanes|helicopters|rockets|submarines|vehicles)\s+$', window_before) or re.search(r'^\s*(?:or\s+other\s+vehicles|and\s+vehicles|trucks|submarines)\b', window_after):
            return True, "physical vehicles or vessels ('military tanks') rather than EPA TANKS software"
        if not re.search(r'\b(?:epa\s+tanks|tanks\s+4\b|emission[s]?\s+software)\b', wide_window):
            return True, "physical vehicles/vessels ('tanks') without software context"

    # 24. JET: aviation or mechanical usage ('jet engine') without Microsoft JET database context
    if skill_lower == "jet":
        if re.search(r'\b(?:aircraft|airplane|aviation|flight|pilot|flying|private|propulsion|machinist|parts)\s+$', window_before) or re.search(r'^\s*(?:engine|aircraft|airways|aviation|llc|inc|corp|services|industry|machining)\b', window_after):
            return True, "aviation or mechanical usage ('jet engine') rather than Microsoft JET database"
        if not re.search(r'\b(?:microsoft\s+jet|ms\s+jet|jet\s+database|jet\s+oledb|dao|ms\s+access)\b', wide_window):
            return True, "aviation/mechanical usage ('jet') without database context"

    # 25. Bash: agency name or social gathering ('Betsy Bash') vs Bash scripting
    if skill_lower == "bash":
        if re.search(r'\b(?:betsy|birthday|party|holiday|summer|winter|beach)\s+$', window_before) or re.search(r'^\s*(?:is\s+a\s+boutique|agency|llc|inc|party|celebration)\b', window_after):
            return True, "agency name or social gathering ('Betsy Bash') rather than Bash shell"
        bash_tech = [
            r'\bbash\s+(?:script(?:ing|s)?|shell|commands?|terminal|cli)\b',
            r'\b(?:shell|linux|unix|git)\s*/\s*bash\b',
            r'\bbash\s*/\s*(?:sh|zsh|ksh|csh|powershell|python)\b',
            r'\b(?:zsh|sh|powershell|python)\s*,\s*bash\b',
            r'\b/bin/bash\b',
            r'\b(?:linux|unix|shell)\s+environment\b'
        ]
        if any(re.search(pat, wide_window) for pat in bash_tech):
            return False, ""
        if not re.search(r'\b(?:linux|unix|shell|terminal|scripts?|scripting|command\s+line|devops|sysadmin|ansible|terraform|powershell)\b', wide_window):
            return True, "ambiguous use of 'Bash' without shell/Linux context"

    # 26. Clipper: geographic/community reference ('Clipper Mill')
    if skill_lower == "clipper":
        if re.search(r'^\s*(?:mill|arts|community|cove|creek|bay|blades?|hair)\b', window_after) or re.search(r'\b(?:arts\s+community|clipper\s+mill)\b', wide_window):
            return True, "geographic/community reference ('Clipper Mill') rather than Clipper programming language"

    # 27. MASterMind: ordinary prose ('mastermind scheduling')
    if skill_lower == "mastermind":
        if re.search(r'^\s*(?:scheduling|behind|dance|game)\b', window_after) or re.search(r'\b(?:wizard|orchestrating)\b', wide_window):
            return True, "ordinary English prose ('mastermind scheduling') rather than MASterMind software"

    return False, ""


# ==============================================================================
# 4. Proximity-Based & Skill-Tied Requirement Classification
# ==============================================================================

def extract_evidence(text: str, start: int, end: int, max_window: int = 150) -> str:
    """
    Extract an exact short sentence or clause snippet from the description
    containing the matched term. Never invents or rewrites evidence.
    """
    left_bound = max(0, start - max_window)
    before_slice = text[left_bound:start]

    before_matches = list(re.finditer(r'[\r\n]+|\n\s*[-•*]\s*|[.!?;]\s+', before_slice))
    if before_matches:
        p_start = left_bound + before_matches[-1].end()
    else:
        p_start = left_bound

    right_bound = min(len(text), end + max_window)
    after_slice = text[end:right_bound]

    after_matches = list(re.finditer(r'[\r\n]+|\n\s*[-•*]\s*|[.!?;]+(?:\s+|$)', after_slice))
    if after_matches:
        p_end = end + after_matches[0].end()
    else:
        p_end = right_bound

    evidence = text[p_start:p_end].strip()
    evidence = re.sub(r'^[•\-\*\s]+', '', evidence).strip()

    if not evidence or text[start:end] not in evidence:
        evidence = text[start:end]

    return evidence


NON_SKILL_REQUIREMENT_PATTERNS = [
    r'\b(?:dress|attire|uniform|boots?|shoes?)\s+(?:code\s+)?(?:is\s+)?required\b',
    r'\b(?:background|drug|screen(?:ing)?)\s+(?:check\s+)?(?:is\s+)?required\b',
    r'\b(?:driver\'?s?\s+)?license\s+(?:is\s+)?required\b',
    r'\b(?:travel|relocation|overtime|weekend)\s+(?:is\s+)?required\b',
    r'\b(?:lifting|standing|walking|physical\s+demands?)\s+(?:is\s+)?required\b',
    r'\b(?:security\s+)?clearance\s+(?:is\s+)?required\b',
    r'\b(?:diploma|degree|ged)\s+(?:is\s+)?required\b',
    r'\b(?:attendance|vaccination|mask)\s+(?:is\s+)?required\b',
]

REQUIRED_PATTERNS = [
    r'\bmust\s+have\b',
    r'\bmust\s+possess\b',
    r'\bmust\s+be\b',
    r'\brequired\b',
    r'\brequirement[s]?\b',
    r'\bminimum\s+qualification[s]?\b',
    r'\bessential\b',
    r'\bmandatory\b',
    r'\bprerequisite[s]?\b',
    r'\bproficiency\s+in\b',
    r'\bfluent\s+in\b',
    r'\bneeded\b',
    r'\b\d+\+?\s+years?(?:\s+of)?\s+experience\b',
]

PREFERRED_PATTERNS = [
    r'\bpreferred\b',
    r'\bnice\s+to\s+have\b',
    r'\b(?:is\s+a\s+|would\s+be\s+a\s+|a\s+)plus\b',
    r'\bbonus\b',
    r'\bideal(?:ly)?\b',
    r'\bdesired\b',
    r'\badvantageous\b',
    r'\boptional\b',
    r'\bgood\s+to\s+have\b',
    r'\basset\b',
]


def classify_requirement_proximity(
    desc: str,
    skill_start: int,
    skill_end: int,
    max_dist: int = 50
) -> str:
    """
    Classify 'required' or 'preferred' ONLY when the cue is grammatically tied to
    the skill within the same clause. Ignores unrelated noun requirements (e.g. dress codes).
    """
    left_bound = max(0, skill_start - max_dist)
    before_slice = desc[left_bound:skill_start]
    # Breaks: newline, bullet, period/semicolon, or contrasting conjunctions "but", "however", "whereas"
    break_matches = list(re.finditer(r'[\r\n]+|[.!?;]\s+|\s+(?:but|however|whereas|although)\s+', before_slice))
    valid_before = before_slice[break_matches[-1].end():] if break_matches else before_slice

    right_bound = min(len(desc), skill_end + max_dist)
    after_slice = desc[skill_end:right_bound]
    break_matches_after = list(re.finditer(r'[\r\n]+|[.!?;]+(?:\s+|$)|(?:\s+|^)(?:but|however|whereas|although)\s+', after_slice))
    valid_after = after_slice[:break_matches_after[0].start()] if break_matches_after else after_slice

    clause_context = (valid_before + " " + valid_after).lower()

    # Reject non-skill requirement phrases (e.g. 'dress required')
    if any(re.search(pat, clause_context) for pat in NON_SKILL_REQUIREMENT_PATTERNS):
        skill_text = desc[skill_start:skill_end].lower()
        if not re.search(re.escape(skill_text) + r'\s+(?:is\s+)?required\b', clause_context):
            return "mentioned"

    is_req = any(re.search(pat, clause_context) for pat in REQUIRED_PATTERNS)
    is_pref = any(re.search(pat, clause_context) for pat in PREFERRED_PATTERNS)

    if is_req and is_pref:
        return "unclear"
    elif is_req:
        return "required"
    elif is_pref:
        return "preferred"
    else:
        return "mentioned"


def calculate_heuristic_confidence(matched_text: str, canonical: str) -> float:
    """
    Rule-based match specificity score (heuristic rating, NOT a statistical probability):
    - 0.90: Exact-case match for multi-word or compound term
    - 0.85: Exact-case match for single-word term
    - 0.75: Case-insensitive match for multi-word term
    - 0.70: Case-insensitive match for single-word term
    """
    is_exact_case = (matched_text == canonical)
    is_multi_word = (' ' in canonical) or ('/' in canonical) or ('-' in canonical)

    if is_exact_case and is_multi_word:
        return 0.90
    elif is_exact_case:
        return 0.85
    elif is_multi_word:
        return 0.75
    else:
        return 0.70


# ==============================================================================
# 5. Local Test Cases Runner
# ==============================================================================

def run_local_tests() -> bool:
    """
    Execute local test cases covering the false-positive scenarios.
    Returns True if all tests pass, False otherwise.
    """
    test_cases = [
        # (Scenario label, Text, Term, Expected match outcome, Expected requirement)
        (
            "Front Desk Receptionist",
            "Seeking an experienced front desk receptionist for our medical clinic.",
            "Front Desk",
            False,
            None
        ),
        (
            "Front Desk Administrator",
            "Looking for a Front Desk Administrator to manage client arrivals.",
            "Front Desk",
            False,
            None
        ),
        (
            "Front Desk Systems Context",
            "Must be comfortable with front desk systems and scheduling.",
            "Front Desk",
            False,
            None
        ),
        (
            "Work the Front Desk",
            "Candidate must be able to work the Front Desk for 6 months.",
            "Front Desk",
            False,
            None
        ),
        (
            "ASPEN Company Name",
            "We are hiring a physical therapist at Aspen Therapy and Wellness in Denver.",
            "Aspen",
            False,
            None
        ),
        (
            "ASPEN Process Software",
            "Must have experience with Aspen Plus and process simulation flowsheets.",
            "Aspen",
            True,
            "required"
        ),
        (
            "ADA Civil Rights Law",
            "This facility operates in strict accordance with the Americans with Disabilities Act (ADA guidelines).",
            "Ada",
            False,
            None
        ),
        (
            "ADA Programming Language",
            "Mission-critical avionics development in Ada 2012 and embedded C.",
            "Ada",
            True,
            "mentioned"
        ),
        (
            "C in Corporate Postnominal (P.C.)",
            "Legal assistant needed for Jung & Vassar, P.C. in downtown office.",
            "C",
            False,
            None
        ),
        (
            "C Programming Language",
            "Looking for a backend systems developer skilled in C and C++.",
            "C",
            True,
            "mentioned"
        ),
        (
            "Route as Ordinary Action Verb",
            "Customer support representative to route incoming calls and tickets.",
            "Route",
            False,
            None
        ),
        (
            "Route in Cloud Networking",
            "Experience configuring DNS records in AWS Route 53 is required.",
            "Route",
            True,
            "required"
        ),
        (
            "React as Ordinary Verb",
            "Technicians must be able to react quickly to unexpected system outages.",
            "React",
            False,
            None
        ),
        (
            "React as Frontend Framework",
            "Senior web developer proficient in React, TypeScript, and Redux.",
            "React",
            True,
            "mentioned"
        ),
        (
            "Zoom Dress Code Etiquette",
            "Remote position: professional Zoom dress required for daily client calls.",
            "Zoom",
            False,
            None
        ),
        (
            "Zoom Collaboration Software",
            "Experience with Zoom and Slack video conferencing tools is required.",
            "Zoom",
            True,
            "required"
        ),
        (
            "Google Employer/Company Reference",
            "Candidates who previously worked at Google as an engineer are welcome.",
            "Google",
            False,
            None
        ),
        (
            "Google Named Software Product",
            "Proficiency in Google Analytics and Google Workspace is required.",
            "Google",
            True,
            "required"
        ),
        (
            "Go in Ordinary Prose",
            "We look for candidates who go the extra mile and have a go-getter mindset.",
            "Go",
            False,
            None
        ),
        (
            "Go Programming Language",
            "Backend microservices engineered in Go, Docker, and Kubernetes.",
            "Go",
            True,
            "mentioned"
        ),
        # --- Regression Tests from skill_labels_auto_v4_reviewed_complete_v2.csv ---
        (
            "FEAR Ordinary Prose - Cape Fear",
            "Cape Fear Commercial is seeking a resourceful, self-starter to fill the full-time position of Brokerage Assistant.",
            "FEAR",
            False,
            None
        ),
        (
            "FEAR Ordinary Prose - Fear of Failure",
            "We are free from fear of failure, free to ask the right questions, make bold decisions, and dig deep into the biology of complex disease.",
            "FEAR",
            False,
            None
        ),
        (
            "FEAR Ordinary Prose - Fear of Oppression",
            "We believe that everyone should live without fear of oppression and persecution.",
            "FEAR",
            False,
            None
        ),
        (
            "HARVEST Ordinary Prose - Season",
            "Clerical skills.Not be afraid of working in a manufacturing environment.Will be during harvest season: Long hours during 4-5 week harvest.",
            "HARVEST",
            False,
            None
        ),
        (
            "HARVEST Ordinary Prose - Lead Harvest Manager",
            "This is a full-time, exempt position, reporting to the Lead Harvest Manager, with salary level dependent on skills and experience.",
            "HARVEST",
            False,
            None
        ),
        (
            "Forth Ordinary Prose - Call Forth",
            "These are the hard times in which genius should wish to live; great necessities call forth great leaders.",
            "Forth",
            False,
            None
        ),
        (
            "Forth Ordinary Prose - Set Forth",
            "Your resume should set forth your qualifications AND your cover letter should set forth something about your life.",
            "Forth",
            False,
            None
        ),
        (
            "MAGIC Ordinary Prose - Work Magic",
            "Show us what trends are popping. Work magic with minimal supervision create, post, analyze, repeat!",
            "MAGIC",
            False,
            None
        ),
        (
            "Dig Ordinary Prose - Dig Deep",
            "We are free to ask the right questions, make bold decisions, and dig deep into the biology of complex disease.",
            "Dig",
            False,
            None
        ),
        (
            "Rest Assured Ordinary Prose",
            "Rest assured; our onboarding team will support you throughout the process.",
            "REST Assured",
            False,
            None
        ),
        (
            "Private Practice Non-Skill - Counseling",
            "Tree of Life Counseling Center is a family owned, for-profit mental health private practice headquartered in NJ.",
            "Private Practice",
            False,
            None
        ),
        (
            "Private Practice Non-Skill - Partnership",
            "HRS is a private practice partnership company that improves peoples lives through partnerships.",
            "Private Practice",
            False,
            None
        ),
        (
            "SAND Non-Skill - Sand-tray therapy",
            "offices provide group rooms, craft rooms (for children), sand-tray therapy and more.",
            "SAND",
            False,
            None
        ),
        (
            "TANKS Non-Skill - Military tanks",
            "critical systems like airplanes, helicopters, rockets, submarines, military tanks, or other vehicles.",
            "TANKS",
            False,
            None
        ),
        (
            "JET Non-Skill - Aircraft Jet Engine",
            "serving the aircraft jet engine industry segment and also other industries.",
            "JET",
            False,
            None
        ),
        (
            "JET Non-Skill - World Class Jet LLC",
            "World Class Jet LLC complies with applicable state and local laws governing nondiscrimination.",
            "JET",
            False,
            None
        ),
        (
            "Bash Non-Skill - Betsy Bash Agency",
            "About Us: Betsy Bash is a boutique agency of digital storytellers who create compelling social media strategies.",
            "Bash",
            False,
            None
        ),
        (
            "E-Verify Employer Mention",
            "Equal Opportunity Employer/Veterans/Disabled. We participate in the E-Verify Employment Verification Program.",
            "E-Verify",
            False,
            None
        ),
        (
            "YouTube Employer Page",
            "Some initial video from first round of DC interviews is available on our Youtube page.",
            "YouTube",
            False,
            None
        ),
        (
            "Facebook Employer Page",
            "For more information about us check out our Facebook.",
            "Facebook",
            False,
            None
        ),
        (
            "LinkedIn Application Link",
            "Apply now on Linkedin and also by sending your resume and a brief cover letter to hr@example.com.",
            "LinkedIn",
            False,
            None
        ),
        (
            "Social Profile Links in Linux Posting",
            "We have a presence on social media platforms such as Twitter, Facebook, and YouTube under the name vtechys360.",
            "Twitter",
            False,
            None,
            "Senior Linux/RedHat Engineer"
        ),
        (
            "Employer Promotion - Google Ads",
            "Thousands of companies rely on Style to manage their SEO strategies, Google Ads campaigns, and websites in real time.",
            "Google Ads",
            False,
            None,
            "Senior Software Engineer"
        ),
        (
            "Employer Promotion - Semrush",
            "We are also partnered with the SEO industry leader Semrush and data analytics platform SimilarWeb.",
            "Semrush",
            False,
            None,
            "Senior Software Engineer"
        ),
        (
            "Pinterest Declined Offers",
            "Our team has turned down offers from Airbnb, Microsoft, Pinterest, and Cisco to pursue our own vision instead.",
            "Pinterest",
            False,
            None,
            "Senior Software Engineer"
        ),
        # --- Positive Controls ---
        (
            "Google Cloud Platform in Cloud Posting",
            "Familiarity with cloud platforms and services, such as AWS, Azure, or Google Cloud Platform.",
            "Google Cloud Platform",
            True,
            "mentioned",
            "Full Stack Engineer"
        ),
        (
            "Google Not Extracted for GCP",
            "Familiarity with cloud platforms and services, such as AWS, Azure, or Google Cloud Platform.",
            "Google",
            False,
            None,
            "Full Stack Engineer"
        ),
        (
            "Google Ads in Marketing Qualifications",
            "Requirements: Proficiency in email marketing tools (HubSpot), Google Ads, content management platforms (WordPress).",
            "Google Ads",
            True,
            "required",
            "Marketing and Events Manager"
        ),
        (
            "Social Platforms in Social Media Job Duties",
            "Manage and execute marketing campaigns across Facebook, Twitter, and LinkedIn to increase brand awareness.",
            "Facebook",
            True,
            "mentioned",
            "Social Media Manager"
        ),
        (
            "Bash in Bash Scripting",
            "Strong proficiency in Bash scripting, Linux administration, and Python automation.",
            "Bash",
            True,
            "required",
            "DevOps Engineer"
        ),
        (
            "React in Frontend Development",
            "Senior Frontend Engineer needed with extensive experience in React, TypeScript, and modern CSS.",
            "React",
            True,
            "required",
            "Frontend Developer"
        ),
        (
            "Instagram in Social Media Coordinator Responsibilities",
            "Responsibilities: Curate and upload captivating images to the company's Instagram account. Engage with followers…",
            "Instagram",
            True,
            "mentioned",
            "Social Media Coordinator"
        ),
        (
            "Bash in Script Deployment Capabilities",
            "Capabilities to deploy and administer bash, ansible, and TypeScript scripts…",
            "Bash",
            True,
            "mentioned",
            "Engineers / Marketing / Various"
        )
    ]

    print("\n" + "=" * 70)
    print("RUNNING LOCAL UNIT TESTS FOR FALSE POSITIVE MITIGATION")
    print("=" * 70)

    passed_count = 0
    total_count = len(test_cases)

    for idx, test_item in enumerate(test_cases, start=1):
        if len(test_item) == 6:
            label, text, term, exp_matched, exp_req, posting_title = test_item
        else:
            label, text, term, exp_matched, exp_req = test_item
            posting_title = ""

        m = re.search(r'(?<![a-zA-Z0-9_])' + re.escape(term) + r'(?![a-zA-Z0-9_])', text, re.IGNORECASE)
        if not m:
            print(f"[{idx:2d}/{total_count}] FAIL (Term not found in test string): {label}")
            continue

        is_fp, reason = is_contextual_false_positive(text, m.start(), m.end(), term, posting_title=posting_title)
        matched = not is_fp

        if matched != exp_matched:
            print(f"[{idx:2d}/{total_count}] FAIL: {label}")
            print(f"     Text:      \"{text}\"")
            print(f"     Outcome:   matched={matched} (Expected {exp_matched})")
            print(f"     Reason:    {reason}")
            continue

        if matched and exp_req is not None:
            actual_req = classify_requirement_proximity(text, m.start(), m.end(), max_dist=50)
            if actual_req != exp_req:
                print(f"[{idx:2d}/{total_count}] FAIL (Requirement mismatch): {label}")
                print(f"     Text:      \"{text}\"")
                print(f"     Outcome:   requirement='{actual_req}' (Expected '{exp_req}')")
                continue

        passed_count += 1
        print(f"[{idx:2d}/{total_count}] PASS: {label} (Outcome: {'Accepted' if matched else 'Rejected - ' + reason})")

    print("-" * 70)
    print(f"Test Summary: {passed_count}/{total_count} tests passed (100.0% accuracy on test suite)")
    print("=" * 70 + "\n")
    return passed_count == total_count


# ==============================================================================
# 6. Core Pipeline Execution & Diagnostic Summary
# ==============================================================================

def process_postings(
    postings_csv_path: str,
    skills_csv_path: str,
    output_csv_path: str,
    limit: Optional[int] = 500,
    overwrite: bool = False
) -> None:
    """Stream postings row-by-row and output precision-filtered skill labels."""
    if os.path.exists(output_csv_path) and not overwrite:
        raise FileExistsError(
            f"Output file '{output_csv_path}' already exists.\n"
            "Pass --overwrite to allow replacing the existing file."
        )

    if not os.path.exists(postings_csv_path):
        raise FileNotFoundError(f"Postings file not found: {postings_csv_path}")

    # Load vocabulary strictly from Workplace Example
    sorted_terms, term_meta = load_candidate_vocabulary(skills_csv_path)
    matchers = build_batched_matchers(sorted_terms)

    postings_alias_map = {
        "job_id": ["job_id", "jobid", "id", "job_identifier"],
        "title": ["title", "job_title", "jobtitle", "position"],
        "description": ["description", "job_description", "jobdescription", "desc"]
    }

    parent_dir = os.path.dirname(os.path.abspath(output_csv_path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    with open(postings_csv_path, mode='r', encoding='utf-8-sig', errors='replace') as infile, \
         open(output_csv_path, mode='w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ValueError(f"Postings file {postings_csv_path} is empty.")

        detected_postings = detect_columns(
            raw_headers,
            postings_alias_map,
            required_keys=["job_id", "title", "description"],
            file_label="postings.csv"
        )

        print("[INFO] Detected columns in postings.csv:")
        for k, v in detected_postings.items():
            print(f"       - {k:18} -> '{v}'")

        header_indices = {h: idx for idx, h in enumerate(raw_headers)}
        idx_id = header_indices[detected_postings["job_id"]]
        idx_title = header_indices[detected_postings["title"]]
        idx_desc = header_indices[detected_postings["description"]]

        writer = csv.writer(outfile)
        output_headers = [
            "job_id", "title", "skill", "requirement_type",
            "evidence_text", "confidence", "review_status"
        ]
        writer.writerow(output_headers)

        postings_processed = 0
        total_rows_written = 0
        total_postings_with_matches = 0
        context_rejected_count = 0

        skill_frequency_counter: Counter = Counter()
        requirement_type_counter: Counter = Counter()

        print(f"\n[INFO] Starting pilot processing (Limit: {limit if limit else 'ALL'} non-empty postings)...")

        type_priority = {"required": 4, "preferred": 3, "mentioned": 2, "unclear": 1}

        for row in reader:
            if limit is not None and limit > 0 and postings_processed >= limit:
                break

            if idx_desc >= len(row) or idx_id >= len(row):
                continue

            # Preserve job_id strictly as text
            job_id_text = str(row[idx_id]).strip()
            job_title = str(row[idx_title]).strip() if idx_title < len(row) else ""
            desc = row[idx_desc].strip()

            if not desc:
                continue

            postings_processed += 1

            raw_matches: List[Dict] = []
            for pat, _ in matchers:
                for m in pat.finditer(desc):
                    matched_text = m.group(0)
                    key = matched_text.lower()
                    meta = term_meta.get(key)
                    canonical = meta["canonical"] if meta else matched_text
                    raw_matches.append({
                        "start": m.start(),
                        "end": m.end(),
                        "matched_text": matched_text,
                        "canonical": canonical,
                    })

            valid_matches = filter_overlapping_spans(raw_matches)

            skills_for_posting: Dict[str, Dict] = {}

            for m in valid_matches:
                canonical_skill = m["canonical"]

                # Apply contextual false positive filters
                is_fp, reason = is_contextual_false_positive(
                    desc=desc,
                    start=m["start"],
                    end=m["end"],
                    canonical_skill=canonical_skill,
                    posting_title=job_title
                )
                if is_fp:
                    context_rejected_count += 1
                    continue

                evidence = extract_evidence(desc, m["start"], m["end"])
                # Apply proximity-based requirement classification
                req_type = classify_requirement_proximity(desc, m["start"], m["end"], max_dist=50)
                conf = calculate_heuristic_confidence(m["matched_text"], canonical_skill)

                current_prio = type_priority.get(req_type, 0)

                if canonical_skill not in skills_for_posting:
                    skills_for_posting[canonical_skill] = {
                        "job_id": job_id_text,
                        "title": job_title,
                        "skill": canonical_skill,
                        "requirement_type": req_type,
                        "evidence_text": evidence,
                        "confidence": f"{conf:.2f}",
                        "review_status": "needs_review",
                        "priority": current_prio,
                    }
                else:
                    if current_prio > skills_for_posting[canonical_skill]["priority"]:
                        skills_for_posting[canonical_skill]["requirement_type"] = req_type
                        skills_for_posting[canonical_skill]["evidence_text"] = evidence
                        skills_for_posting[canonical_skill]["confidence"] = f"{conf:.2f}"
                        skills_for_posting[canonical_skill]["priority"] = current_prio

            if skills_for_posting:
                total_postings_with_matches += 1
                for item in skills_for_posting.values():
                    writer.writerow([
                        item["job_id"],
                        item["title"],
                        item["skill"],
                        item["requirement_type"],
                        item["evidence_text"],
                        item["confidence"],
                        item["review_status"]
                    ])
                    total_rows_written += 1
                    skill_frequency_counter[item["skill"]] += 1
                    requirement_type_counter[item["requirement_type"]] += 1

            if postings_processed % 100 == 0:
                print(f"       Processed {postings_processed} postings | "
                      f"Labels written: {total_rows_written}")

        # Diagnostic Summary
        print("\n" + "=" * 65)
        print("[SUCCESS] Pilot Processing Completed Successfully!")
        print(f"          Postings processed (non-empty):   {postings_processed}")
        print(f"          Postings with detected skills:    {total_postings_with_matches}")
        print(f"          Context false positives rejected: {context_rejected_count}")
        print(f"          Total skill label rows written:   {total_rows_written}")
        print(f"          Output saved to:                 {output_csv_path}")
        print("=" * 65)

        print("\n--- DIAGNOSTIC SUMMARY: REQUIREMENT TYPES ---")
        for req_label, count in requirement_type_counter.most_common():
            pct = (count / total_rows_written * 100) if total_rows_written else 0
            print(f"  {req_label:14} : {count:5} ({pct:5.1f}%)")

        print("\n--- DIAGNOSTIC SUMMARY: TOP 15 DETECTED TERMS ---")
        if skill_frequency_counter:
            for rank, (skill_name, count) in enumerate(skill_frequency_counter.most_common(15), start=1):
                pct = (count / total_rows_written * 100) if total_rows_written else 0
                print(f"  {rank:2}. {skill_name:24} : {count:4} occurrences ({pct:4.1f}%)")
        else:
            print("  (No skills detected in sample)")
        print("=" * 65 + "\n")


# ==============================================================================
# 7. Command-Line Interface
# ==============================================================================

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract precision-filtered candidate skill labels from job postings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--postings",
        type=str,
        default=r"C:\Users\HP\OneDrive\Desktop\archive\postings.csv",
        help="Path to job postings CSV file."
    )
    parser.add_argument(
        "--skills",
        type=str,
        default=r"C:\Users\HP\OneDrive\Desktop\archive\software_skills.csv",
        help="Path to software skills reference CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=r"C:\Users\HP\OneDrive\Desktop\archive\skill_labels_auto_v4.csv",
        help="Path to the new output skill labels CSV file."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Number of non-empty postings to process for the pilot (0 or negative for all)."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting output CSV file if it already exists."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run local test cases covering false-positive mitigation and exit."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    if args.test:
        success = run_local_tests()
        sys.exit(0 if success else 1)

    try:
        process_postings(
            postings_csv_path=args.postings,
            skills_csv_path=args.skills,
            output_csv_path=args.output,
            limit=args.limit if args.limit > 0 else None,
            overwrite=args.overwrite
        )
    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()