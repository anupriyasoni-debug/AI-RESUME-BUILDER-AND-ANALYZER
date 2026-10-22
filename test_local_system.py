"""
Automated Verification Test Suite for Local AI Resume Builder and Analyzer.
Tests that all features execute completely locally without external API keys or cloud calls,
and exercises the limited structural checks used by bullet rewrite modes.
"""

import sys
import os
import io
import re

print("=== 1. Testing Imports & Modules ===")
try:
    import analyzer
    import local_model
    import resume_builder
    import resume_comparison
    import pdf_generator
    import style
    import training.data_preprocessing
    import training.evaluate
    import training.train_classifier
    print("[PASS] All modules imported successfully.")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

print("\n=== 2. Testing PyMuPDF and Text Extraction ===")
try:
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Alex Morgan\nEmail: alex@example.com\nPhone: +1 555 123 4567\nExperience\nDeveloped high-throughput APIs using Python and Docker.")
    pdf_bytes = io.BytesIO(doc.tobytes())
    pdf_bytes.name = "sample_resume.pdf"
    
    extracted_text = analyzer.extract_text(pdf_bytes)
    assert "Alex Morgan" in extracted_text, "Failed to extract name"
    assert "Python" in extracted_text, "Failed to extract skills"
    print(f"[PASS] PyMuPDF text extraction verified. Extracted {len(extracted_text)} characters.")
except Exception as e:
    print(f"[FAIL] PDF extraction failed: {e}")
    sys.exit(1)

print("\n=== 3. Testing Resume Analysis & ATS Scoring ===")
try:
    sample_resume = (
        "Alex Morgan\nalex@example.com | +1 555 123 4567 | linkedin.com/in/alex\n\n"
        "Professional Summary\n"
        "Senior AI Engineer with 5+ years of experience designing scalable machine learning pipelines.\n\n"
        "Experience\n"
        "- Spearheaded end-to-end LLM fine-tuning, improving response quality by 34%.\n"
        "- Engineered microservices utilizing Python, PyTorch, and Docker on AWS.\n"
        "- Automated ETL data pipelines, processing 10M records daily.\n\n"
        "Skills\n"
        "Python, PyTorch, TensorFlow, Transformers, Docker, MLOps, LangChain, Vector Databases.\n\n"
        "Education\n"
        "B.Tech in Computer Science, University of Technology.\n\n"
        "Projects\n"
        "- Built enterprise RAG system with Pinecone and FastAPI, reducing search latency by 45%.\n\n"
        "Certifications\n"
        "- AWS Certified Machine Learning Specialist.\n"
    )
    analysis = analyzer.analyze_resume(sample_resume, target_role="AI Engineer")
    assert 0 <= analysis["total_score"] <= 100, "ATS score out of bounds"
    assert len(analysis["matched_skills"]) > 0, "No skills matched"
    print(f"[PASS] Resume Analysis verified: Total ATS Score = {analysis['total_score']}/100")
    print(f"       Matched Skills ({len(analysis['matched_skills'])}): {', '.join(analysis['matched_skills'][:4])}")
    print(f"       Section Score: {analysis['section_score']}/30, Role Score: {analysis['role_score']}/40")
except Exception as e:
    print(f"[FAIL] Resume analysis failed: {e}")
    sys.exit(1)

print("\n=== 4. Testing Local Job Description Match (TF-IDF Cosine Sim) ===")
try:
    job_description = (
        "We are looking for an AI Engineer experienced in Python, PyTorch, Transformers, "
        "and MLOps. The ideal candidate will design, fine-tune, and deploy deep learning models."
    )
    jd_fit = analyzer.analyze_job_description_local(sample_resume, job_description, target_role="AI Engineer")
    assert jd_fit["score"] > 30, f"Expected reasonable similarity, got {jd_fit['score']}"
    assert len(jd_fit["matched_terms"]) > 0, "No terms matched"
    print(f"[PASS] TF-IDF Cosine Similarity Match: {jd_fit['score']}%")
    print(f"       Model: {jd_fit['model']}")
    print(f"       Matched Terms: {', '.join(jd_fit['matched_terms'][:5])}")
    print(f"       Feedback: {jd_fit['feedback'][0]}")
except Exception as e:
    print(f"[FAIL] Job description analysis failed: {e}")
    sys.exit(1)

print("\n=== 5. Testing Structural Rewrite Checks & 3 Bullet Alternatives ===")
try:
    raw_bullet = "responsible for working with the team to fix bugs and made things better"
    alts = local_model.local_engine.generate_bullet_alternatives(raw_bullet)
    
    assert "professional" in alts and "concise" in alts and "impact" in alts, "Missing required alternatives"
    
    prof_text = alts["professional"]["text"]
    conc_text = alts["concise"]["text"]
    imp_text = alts["impact"]["text"]
    
    print(f"  [Original    ] -> {raw_bullet}")
    print(f"  [Professional] -> {prof_text}")
    print(f"  [Concise     ] -> {conc_text}")
    print(f"  [Impact      ] -> {imp_text}")
    print(f"  [Impact Note ] -> {alts['impact']['note']}")

    # 1. Verify NO 'spearheaded' introduced for 'responsible for'
    for k, v in [("Professional", prof_text), ("Concise", conc_text), ("Impact", imp_text)]:
        assert not v.lower().startswith("spearheaded"), f"{k} introduced unsupported 'spearheaded'"
        assert "resulting in measurable efficiency gains" not in v.lower(), f"{k} introduced fabricated outcome phrase"
        # Verify no numbers were invented
        nums = re.findall(r"\b\d+\b", v)
        assert len(nums) == 0, f"{k} introduced unsupported numbers: {nums}"

    # 2. Verify number preservation when original contains metrics
    bullet_with_metrics = "Managed a team of 5 engineers to deliver backend services within 3 months."
    alts_metrics = local_model.local_engine.generate_bullet_alternatives(bullet_with_metrics)
    for k in ["professional", "concise", "impact"]:
        txt = alts_metrics[k]["text"]
        assert "5" in txt, f"Alternative {k} dropped original metric '5'"
        assert "3" in txt, f"Alternative {k} dropped original metric '3'"

    # 3. Regression: 'made things better' is NOT expanded into unstated application/result claims
    vague_bullet = "made things better"
    vague_alts = local_model.local_engine.generate_bullet_alternatives(vague_bullet)
    assert vague_alts["concise"]["text"] == vague_bullet, "Concise altered vague bullet without safe rule"
    assert vague_alts["impact"]["text"] == vague_bullet, "Impact altered vague bullet without metric"
    assert "application" not in str(vague_alts).lower(), "Expanded 'made things better' with 'application'"
    assert "functionality" not in str(vague_alts).lower(), "Expanded 'made things better' with 'functionality'"
    valid_vague, _ = local_model.check_rewrite_structure(vague_bullet, "improved application functionality")
    assert not valid_vague, "Structural check allowed vague phrase expansion"

    # 4. Regression: A tool or technology cannot be swapped, added, or removed
    orig_tools = "Built reports using Python and SQL."
    for tool_candidate in (
        "Built reports using Python and Java.",          # swapped
        "Built reports using Python, SQL, and Tableau.",  # added
        "Built reports using Python.",                   # removed
    ):
        v_tool, _ = local_model.check_rewrite_structure(orig_tools, tool_candidate)
        assert not v_tool, f"Structural check allowed invalid tool candidate: {tool_candidate}"

    # 5. Regression: A number stays the same but meaning changes ('5 engineers' -> '5 customers')
    v_assoc, _ = local_model.check_rewrite_structure("Managed 5 engineers.", "Managed 5 customers.")
    assert not v_assoc, "Structural check allowed number association reassignment ('engineers' -> 'customers')"

    # 6. Regression: Leadership, ownership, causation, or outcome cannot be added
    orig_action = "Worked with the team on deployment."
    for unsafe_action in (
        "Led the team on deployment.",
        "Owned deployment.",
        "Worked with the team on deployment, reducing costs.",
        "Worked with the team on deployment, improving reliability.",
    ):
        v_act, _ = local_model.check_rewrite_structure(orig_action, unsafe_action)
        assert not v_act, f"Structural check allowed unsafe action modification: {unsafe_action}"

    # 7. Regression: A metric's relationship to the action cannot be changed
    orig_rel = "Reduced latency by 20% using Python."
    cand_rel = "Used Python to reduce costs by 20%."
    v_rel, _ = local_model.check_rewrite_structure(orig_rel, cand_rel)
    assert not v_rel, "Structural check allowed changing metric relationship to action"
    alts_rel = local_model.local_engine.generate_bullet_alternatives(orig_rel)
    assert alts_rel["impact"]["text"] == orig_rel, "Impact mode altered text with metric instead of preserving it"
    assert "metric" in alts_rel["impact"]["note"].lower(), "Impact note does not reference metric"

    # 8. Regression: Unsafe candidate falls back to original with manual guidance
    orig_safe = "Worked with five engineers."
    unsafe_cand = "Led five engineers."
    fb_text, fb_note = local_model._candidate_or_original(orig_safe, unsafe_cand)
    assert fb_text == orig_safe, "Unsafe candidate did not fall back to original"
    assert fb_note and "original" in fb_note.lower() and "manually" in fb_note.lower(), "Missing manual edit guidance"

    # 9. Regression: Structural check docstring explicitly denies semantic verification
    doc = local_model.check_rewrite_structure.__doc__.lower()
    assert "limited" in doc and "does not establish semantic" in doc, "Docstring does not declare check limits"

    # 10. Direct structural check rejections
    valid, err = local_model.check_rewrite_structure(
        "Fixed login bug.",
        "Fixed login bug resulting in measurable efficiency gains."
    )
    assert not valid and err, "Structural checker accepted added outcome wording"

    valid2, err2 = local_model.check_rewrite_structure(
        "Managed database servers.",
        "Managed 15 database servers."
    )
    assert not valid2 and err2, "Structural checker accepted an added number"

    print("[PASS] Structural checks and all regression boundary invariants verified.")
except Exception as e:
    print(f"[FAIL] Factual preservation test failed: {e}")
    sys.exit(1)

print("\n=== 6. Testing Local Contextual Writing Suggestions ===")
try:
    sugg = local_model.local_engine.get_writing_suggestions(
        "Worked on various web projects for clients.", section="Experience"
    )
    assert "1." in sugg and "2." in sugg and "3." in sugg, "Expected 3 numbered suggestions"
    print("[PASS] Writing suggestions generated locally:")
    for line in sugg.splitlines():
        print(f"       {line}")
except Exception as e:
    print(f"[FAIL] Writing suggestions failed: {e}")
    sys.exit(1)

print("\n=== 7. Testing Local Resume Comparison Engine ===")
try:
    resume_b = sample_resume + "\n- System refactoring leading to 25% cost reduction."
    comparison = local_model.local_engine.compare_resumes(sample_resume, resume_b, "AI Engineer", job_description)
    assert "resume_a" in comparison and "resume_b" in comparison, "Missing resume comparison keys"
    assert "ats_score" in comparison["resume_a"] and "ats_score" in comparison["resume_b"]
    print("[PASS] Resume Comparison verified:")
    print(f"       Resume A ATS: {comparison['resume_a']['ats_score']}, Resume B ATS: {comparison['resume_b']['ats_score']}")
    print(f"       Highlights: {comparison['highlights'][0] if comparison['highlights'] else 'None'}")
except Exception as e:
    print(f"[FAIL] Resume comparison failed: {e}")
    sys.exit(1)

print("\n=== 8. Testing Local PDF Generation ===")
try:
    builder_data = {
        "personal": {
            "full_name": "Alex Morgan",
            "email": "alex@example.com",
            "phone": "+1 555 123 4567",
            "location": "San Francisco, CA",
            "title": "Senior AI Engineer",
            "summary": "Experienced AI engineer specializing in NLP systems.",
        },
        "education": [{"degree": "B.S. CS", "school": "Tech Univ", "year": "2024", "details": ""}],
        "experience": [{"role": "AI Dev", "company": "Tech Corp", "dates": "2024-Present", "description": "Built AI systems."}],
        "projects": [{"name": "Local LLM", "tech": "Python", "description": "Offline inference."}],
        "skills": ["Python", "SQL", "Docker"],
        "certifications": ["AWS Certified"],
    }
    pdf_bytes = pdf_generator.generate_resume_pdf(builder_data, template="Professional Layout", color_scheme="Classic Black & White")
    assert pdf_bytes and len(pdf_bytes) > 500, "PDF generation produced empty output"
    print(f"[PASS] PDF Generation verified. Produced {len(pdf_bytes)} bytes.")
except Exception as e:
    print(f"[FAIL] PDF generation failed: {e}")
    sys.exit(1)

print("\n=== 9. Testing Evaluation Module ===")
try:
    eval_res = training.evaluate.evaluate_predictions(
        ["AI Engineer", "Data Scientist", "AI Engineer"],
        ["AI Engineer", "Data Scientist", "Data Scientist"]
    )
    assert eval_res["accuracy"] == 0.6667 or round(eval_res["accuracy"], 2) == 0.67
    print(f"[PASS] Evaluation module verified: Accuracy = {eval_res['accuracy'] * 100:.1f}%, Macro F1 = {eval_res['macro_f1']}")
except Exception as e:
    print(f"[FAIL] Evaluation failed: {e}")
    sys.exit(1)

print("\n=== 10. Auditing External Network Requests ===")
try:
    with open("style.py", "r", encoding="utf-8") as f:
        style_content = f.read()
    assert "fonts.googleapis.com" not in style_content, "Found fonts.googleapis.com in style.py"
    assert "@import url" not in style_content, "Found @import url in style.py"
    print("[PASS] External font request audit passed: Zero external font requests in style.py.")
except Exception as e:
    print(f"[FAIL] Network audit failed: {e}")
    sys.exit(1)

print("\n==================================================")
print("ALL LOCAL VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("==================================================")
