"""Explainable lead scoring and deduplication, with no external services."""
from __future__ import annotations
import csv
import re
from pathlib import Path

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
WEIGHTS = {"industry": 35, "size": 30, "title": 25, "source": 10}
INDUSTRIES = {"saas", "software", "information technology", "it services"}
TITLES = ("founder", "ceo", "vp", "director", "head of", "chief")
SOURCES = {"referral", "inbound", "website"}

def score_lead(lead: dict) -> dict:
    reasons = []
    score = 0
    industry = lead["industry"].casefold().strip()
    if industry in INDUSTRIES:
        score += WEIGHTS["industry"]
        reasons.append("target industry (+35)")
    try:
        size = int(lead["company_size"])
    except (ValueError, TypeError):
        size = -1
    if 10 <= size <= 500:
        score += WEIGHTS["size"]
        reasons.append("target company size (+30)")
    title = lead["job_title"].casefold().strip()
    if any(t in title for t in TITLES):
        score += WEIGHTS["title"]
        reasons.append("decision-maker title (+25)")
    if lead["source"].casefold().strip() in SOURCES:
        score += WEIGHTS["source"]
        reasons.append("high-intent source (+10)")
    route = "HOT" if score >= 70 else "WARM" if score >= 40 else "COLD"
    action = {"HOT": "sales_review", "WARM": "nurture_review", "COLD": "research"}[route]
    return {**lead, "score": score, "reasons": reasons, "segment": route, "next_action": action}

REQUIRED = ("name", "email", "company", "industry", "company_size", "job_title", "source")

def process_csv(path: str | Path) -> dict:
    leads, errors, seen = [], [], set()
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(col not in reader.fieldnames for col in REQUIRED):
            missing = sorted(set(REQUIRED) - set(reader.fieldnames or []))
            raise ValueError(f"Missing CSV columns: {', '.join(missing)}")
        for line, row in enumerate(reader, 2):
            if any(row.get(k) is None or not str(row[k]).strip() for k in REQUIRED):
                errors.append({"line": line, "reason": "missing required field"})
                continue
            email = row["email"].strip().casefold()
            if not EMAIL.fullmatch(email):
                errors.append({"line": line, "reason": "invalid email"})
                continue
            try:
                if int(row["company_size"]) < 1:
                    raise ValueError()
            except ValueError:
                errors.append({"line": line, "reason": "invalid company size"})
                continue
            if email in seen:
                errors.append({"line": line, "reason": "duplicate email"})
                continue
            seen.add(email)
            cleaned = {k: row[k].strip() for k in REQUIRED}
            cleaned["email"] = email
            leads.append(score_lead(cleaned))
    summary = {label: sum(l["segment"] == label for l in leads) for label in ("HOT", "WARM", "COLD")}
    return {"summary": {"processed": len(leads), "rejected": len(errors), "segments": summary},
            "leads": leads, "errors": errors}
