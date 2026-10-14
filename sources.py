"""Fetch and normalize listings. Every source returns a list of dicts with the same keys:
company, title, terms (list of str), location, url, posted (YYYY-MM-DD or ""), source, kind ("role" or "program"), note
"""
import csv
import datetime
import io
import json
import os
import re
import urllib.request

UA = {"User-Agent": "job-finder (personal use)"}
TERM_RE = re.compile(r"\b(summer|spring|fall|winter) 20\d\d\b", re.I)
LINK_RE = re.compile(r'href="([^"]+)"|\]\((https?://[^)\s]+)\)')
TAG_RE = re.compile(r"<[^>]+>|\*\*")


def fetch(url, local_dir=None, name=None):
    """Download text. In local mode (for testing) read a saved copy instead."""
    if local_dir:
        with open(os.path.join(local_dir, name), encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def _date(value):
    """Turn epoch seconds, epoch ms, or ISO strings into YYYY-MM-DD."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        if value > 1e12:
            value /= 1000
        return datetime.datetime.utcfromtimestamp(value).strftime("%Y-%m-%d")
    return str(value)[:10]


def _role(**kw):
    base = dict(company="", title="", terms=[], location="", url="", posted="", source="", kind="role", note="")
    base.update(kw)
    return base


def _first_link(line):
    for a, b in LINK_RE.findall(line):
        u = a or b
        if "imgur" not in u and "shields.io" not in u and "camo." not in u:
            return u
    return ""


# --- community repos -------------------------------------------------------

def simplify(text):
    out = []
    for j in json.loads(text):
        if not j.get("active") or not j.get("is_visible", True):
            continue
        out.append(_role(company=j.get("company_name", ""), title=j.get("title", ""),
                         terms=[t for t in j.get("terms") or [] if t and t != "N/A"],
                         location="; ".join(j.get("locations") or []), url=j.get("url", ""),
                         posted=_date(j.get("date_posted")), source="Simplify"))
    return out


def zshah(text):
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        seasons = r.get("seasons") or r.get("season") or ""
        terms = [s.strip() for s in seasons.split(";") if TERM_RE.fullmatch(s.strip())]
        loc = r.get("location", "")
        if (r.get("remote") or "").lower() in ("true", "remote", "yes"):
            loc += "; Remote"
        out.append(_role(company=r.get("company", ""), title=r.get("title", ""), terms=terms,
                         location=loc, url=r.get("url", ""), posted=_date(r.get("posted_at")),
                         source="zshah101"))
    return out


def markdown_table(text, source, default_terms):
    """Generic parser for README tables shaped Company | Role | Location | ..."""
    out, last_company = [], ""
    for line in text.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        if "🔒" in line:  # closed
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        company = TAG_RE.sub("", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cells[0])).strip()
        if company.lower() in ("company", "status"):
            continue
        if company in ("↳", ""):
            company = last_company
        else:
            last_company = company
        title = TAG_RE.sub("", cells[1]).strip()
        terms = TERM_RE.findall(title) and [m.group(0) for m in TERM_RE.finditer(title)] or default_terms
        out.append(_role(company=company, title=title, terms=terms,
                         location=TAG_RE.sub(" ", cells[2]).strip(), url=_first_link(line), source=source))
    return out


def underclassmen(text, source):
    """Sophomore/early programs. Kept raw; filters.py decides what is relevant."""
    out = []
    for line in text.splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        low = line.lower()
        if "closed" in low or "🔒" in line:
            continue
        if not re.search(r"sophomore|second[- ]year|2029|underclass", low):
            continue
        cells = [TAG_RE.sub("", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", c)).strip()
                 for c in line.strip().strip("|").split("|")]
        if source == "underclassmen-opportunities" and len(cells) >= 3:
            company, title, detail = cells[1], cells[2], " ".join(cells[3:4])
        else:
            company, title = cells[0], cells[0]
            detail = " ".join(cells[1:4]).replace("?", "status unknown,").replace("✅", "").strip()
        deadline = re.search(r"Deadline:\s*([^|()]+?)(?:\s*\(|$| —)", title)
        out.append(_role(company=company, title=title[:180], location=detail[:140], url=_first_link(line),
                         source=source, kind="program",
                         note=("closing soon" if "closing soon" in low else "") +
                              (f" · deadline {deadline.group(1).strip()}" if deadline else "")))
    return out


# --- company boards (for design roles) -------------------------------------

def ats_board(ats, slug, name):
    if ats == "greenhouse":
        data = json.loads(fetch(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"))
        return [_role(company=name, title=j["title"], location=(j.get("location") or {}).get("name", ""),
                      url=j.get("absolute_url", ""), posted=_date(j.get("first_published") or j.get("updated_at")),
                      terms=[m.group(0) for m in TERM_RE.finditer(j["title"])], source=f"{name} board")
                for j in data.get("jobs", [])]
    if ats == "lever":
        data = json.loads(fetch(f"https://api.lever.co/v0/postings/{slug}?mode=json"))
        out = []
        for j in data:
            cat = j.get("categories") or {}
            loc = cat.get("location", "")
            if (j.get("workplaceType") or "").lower() == "remote":
                loc += "; Remote"
            out.append(_role(company=name, title=j.get("text", ""), location=loc, url=j.get("hostedUrl", ""),
                             posted=_date(j.get("createdAt")),
                             terms=[m.group(0) for m in TERM_RE.finditer(j.get("text", ""))], source=f"{name} board"))
        return out
    if ats == "ashby":
        data = json.loads(fetch(f"https://api.ashbyhq.com/posting-api/job-board/{slug}"))
        out = []
        for j in data.get("jobs", []):
            if j.get("isListed") is False:
                continue
            loc = j.get("location", "") + ("; Remote" if j.get("isRemote") else "")
            out.append(_role(company=name, title=j.get("title", ""), location=loc, url=j.get("jobUrl", ""),
                             posted=_date(j.get("publishedAt")),
                             terms=[m.group(0) for m in TERM_RE.finditer(j.get("title", ""))], source=f"{name} board"))
        return out
    raise ValueError(f"unknown ATS {ats}")


def collect(repo_sources, watchlist, local_dir=None):
    """Pull everything. Returns (rows, failures). One broken source never stops the run."""
    rows, failures = [], []
    parsers = {
        "simplify": simplify,
        "zshah": zshah,
        "vansh": lambda t: markdown_table(t, "vanshb03", ["Summer 2027"]),
        "vansh_off": lambda t: markdown_table(t, "vanshb03 off-season", []),
        "speedy_swe": lambda t: markdown_table(t, "speedyapply", []),
        "speedy_ai": lambda t: markdown_table(t, "speedyapply", []),
        "under_zapply": lambda t: underclassmen(t, "zapplyjobs"),
        "under_jose": lambda t: underclassmen(t, "underclassmen-opportunities"),
    }
    local_names = {"simplify": "simplify.json", "zshah": "zshah.csv", "vansh": "vansh.md", "vansh_off": "vansh_off.md",
                   "speedy_swe": "speedy_swe.md", "speedy_ai": "speedy_ai.md",
                   "under_zapply": "under1.md", "under_jose": "under2.md"}
    for key, url in repo_sources.items():
        try:
            rows += parsers[key](fetch(url, local_dir, local_names.get(key)))
        except Exception as e:  # noqa: BLE001 - report and keep going
            failures.append(f"{key}: {type(e).__name__}")
    if not local_dir:
        for ats, slug, name in watchlist:
            try:
                rows += ats_board(ats, slug, name)
            except Exception as e:  # noqa: BLE001
                failures.append(f"{name} ({ats}:{slug}): {type(e).__name__}")
    return rows, failures
