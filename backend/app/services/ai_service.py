import re
from typing import List, Dict, Tuple, Any

# Category keyword rules for fast keyword-based matching
CATEGORY_KEYWORDS = {
    "Technical": ["technology", "stack", "code", "programming", "python", "java", "react", "backend", "frontend", "database", "ai", "ml", "system", "architecture", "developer", "engineering", "git", "api", "framework"],
    "HR": ["process", "rounds", "interview", "hr", "hiring", "selection", "shortlist", "test", "aptitude", "group discussion", "gd"],
    "Internship": ["internship", "stipend", "duration", "ppo", "convert", "convertible", "project", "summer"],
    "Career": ["growth", "role", "promotion", "career", "path", "learning", "mentorship", "training", "skills"],
    "Company": ["company", "location", "office", "headquarters", "clients", "domain", "products", "services", "branches"],
    "Salary": ["salary", "package", "ctc", "base", "bonus", "perks", "allowance", "compensation", "pay"],
    "Work Culture": ["culture", "hours", "work-life", "wfh", "remote", "hybrid", "environment", "team", "leave", "shifts"]
}

def classify_question(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
        if score > 0:
            scores[cat] = score
    if not scores:
        return "General"
    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_cats[0][0]

def compute_jaccard_similarity(text1: str, text2: str) -> float:
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def detect_duplicates_and_prioritize(new_text: str, existing_questions: List[Dict[str, Any]]) -> Tuple[bool, float, float, str]:
    """
    Returns (is_duplicate, max_similarity, priority_score, category)
    """
    category = classify_question(new_text)
    max_sim = 0.0
    is_dup = False
    dup_group = f"group_{category.lower()}"

    for q in existing_questions:
        sim = compute_jaccard_similarity(new_text, q.get("text", ""))
        if sim > max_sim:
            max_sim = sim

    if max_sim >= 0.50: # 50% jaccard similarity threshold for duplicates
        is_dup = True

    # Base priority score
    priority = 1.0
    if category in ["Technical", "HR", "Internship"]:
        priority += 0.5
    if is_dup:
        priority += 0.3 * (max_sim * 10) # increase priority if multiple students ask similar question

    return is_dup, round(max_sim * 100, 1), round(priority, 2), category
