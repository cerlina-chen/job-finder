"""Decide what is relevant to you and in what order."""
import hashlib
import re

import config as C

I = re.I
FOREIGN = re.compile(r"\b(uk|united kingdom|london|canada|toronto|vancouver|montr[eé]al|india|bengaluru|germany|berlin|"
                     r"ireland|dublin|singapore|china|japan|france|paris|netherlands|amsterdam|poland|israel|mexico|"
                     r"brazil|australia|hong kong|emea)\b", I)


def category(title):
    if re.search(C.DESIGN, title, I) and not re.search(C.DESIGN_EXCLUDE, title, I):
        return "Design & UX"
    if re.search(C.SWE, title, I) and not re.search(C.SWE_EXCLUDE, title, I):
        return "Software"
    if re.search(C.DATA, title, I) and not re.search(C.DATA_EXCLUDE, title, I):
        return "Data"
    return None


def term_ok(terms, location):
    """Apply your term rules. Unknown terms pass so nothing good is silently dropped."""
    if not terms:
        return True
    keep = []
    for t in terms:
        season, _, year = t.partition(" ")
        if year.isdigit() and int(year) < C.MIN_TERM_YEAR:
            continue
        if C.DROP_FALL and season.lower() == "fall":
            continue
        if C.SPRING_REQUIRES_REMOTE and season.lower() in ("spring", "winter") and "remote" not in location.lower():
            continue
        keep.append(t)
    return bool(keep)


def in_us(location):
    if not location.strip():
        return True
    if re.search(r"united states|\busa?\b", location, I):
        return True
    if FOREIGN.search(location):  # catches "Remote in UK" before the remote hint lets it through
        return False
    return True


def key(row):
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    return hashlib.sha1(f"{norm(row['company'])}|{norm(row['title'])}".encode()).hexdigest()[:16]


def score(row):
    text = f"{row['title']} {row['location']} {row['note']}"
    s = sum(points for pattern, points in C.BOOST.values() if re.search(pattern, text, I))
    if "closing soon" in row["note"]:
        s += 2
    return s


def relevant_program(row):
    text = f"{row['company']} {row['title']} {row['location']}"
    if re.search(C.PROGRAM_DROP, text, I) and not re.search(C.PROGRAM_RESCUE, text, I):
        return False
    if re.search(C.PROGRAM_SCHOOL_ONLY, row["company"], I) and not re.search(r"wisconsin|uw-madison", text, I):
        return False
    return bool(re.search(C.PROGRAM_KEEP, text, I))


def apply(rows):
    """Filter, categorize, dedupe. Returns list of rows with 'section', 'id', 'sources'."""
    kept = {}
    for r in rows:
        if r["kind"] == "program":
            if not relevant_program(r):
                continue
            r["section"] = "Sophomore & early programs"
        else:
            if r["source"].endswith(" board") and not re.search(C.EARLY_TALENT, r["title"], I):
                continue
            if re.search(C.LEVEL_EXCLUDE, r["title"], I):
                continue
            sec = category(r["title"])
            if not sec or not term_ok(r["terms"], r["location"]) or not in_us(r["location"]):
                continue
            r["section"] = sec
        r["id"] = key(r)
        if r["id"] in kept:
            kept[r["id"]]["sources"].add(r["source"])
            continue
        r["sources"] = {r["source"]}
        r["score"] = score(r)
        kept[r["id"]] = r
    return list(kept.values())
