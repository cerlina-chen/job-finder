"""Daily run: pull sources, filter to your fit, show only what is new since last run.

    python main.py                 # normal run (updates state/seen.json)
    python main.py --dry-run       # preview without marking anything as seen
    python main.py --local DIR     # test against saved copies of the repo files
"""
import argparse
import csv
import datetime
import html
import json
import os
import smtplib
from email.message import EmailMessage

import config as C
import filters
import sources

ROOT = os.path.dirname(os.path.abspath(__file__))
SEEN_PATH = os.path.join(ROOT, "state", "seen.json")
SECTIONS = ["Sophomore & early programs", "Design & UX", "Software", "Data"]


def load_seen():
    try:
        with open(SEEN_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_seen(seen, current_ids, today):
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=90)).isoformat()
    pruned = {k: v for k, v in seen.items() if k in current_ids or v >= cutoff}
    os.makedirs(os.path.dirname(SEEN_PATH), exist_ok=True)
    with open(SEEN_PATH, "w") as f:
        json.dump(pruned, f, indent=0, sort_keys=True)


def by_section(rows):
    groups = {s: [] for s in SECTIONS}
    for r in rows:
        groups[r["section"]].append(r)
    for s in groups:
        groups[s] = sorted(groups[s], key=lambda r: (r["score"], r["posted"] or ""), reverse=True)
    return groups


def meta_line(r):
    bits = [r["location"][:60]] if r["location"] else []
    if r["terms"]:
        bits.append(", ".join(r["terms"]))
    if r["posted"]:
        bits.append(f"posted {r['posted']}")
    if r["note"]:
        bits.append(r["note"].strip(" ·"))
    return " · ".join(bits)


def render_md(groups, today, failures, total_tracked):
    n = sum(len(v) for v in groups.values())
    lines = [f"# New since last run · {today}", "",
             f"{n} new · {total_tracked} relevant roles tracked in total", ""]
    for sec in SECTIONS:
        rows = groups[sec]
        if not rows:
            continue
        lines.append(f"## {sec} ({len(rows)})")
        for r in rows[:C.PER_SECTION_LIMIT]:
            lines.append(f"- **{r['company']}**: [{r['title']}]({r['url']})  \n  {meta_line(r)}")
        if len(rows) > C.PER_SECTION_LIMIT:
            lines.append(f"- +{len(rows) - C.PER_SECTION_LIMIT} more in `data/new_today.csv`")
        lines.append("")
    if failures:
        lines.append("Sources that failed today: " + "; ".join(failures))
    return "\n".join(lines)


def render_html(groups, today, failures, total_tracked):
    n = sum(len(v) for v in groups.values())
    e = html.escape
    parts = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>New roles · {today}</title>
<style>
:root{{--bg:#fff;--fg:#111;--muted:#666;--line:#e5e5e5;--link:#0645ad}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111;--fg:#eee;--muted:#999;--line:#2a2a2a;--link:#8ab4f8}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif}}
main{{max-width:720px;margin:0 auto;padding:16px}}
h1{{font-size:20px;margin:8px 0 4px}} h2{{font-size:15px;margin:28px 0 8px;text-transform:uppercase;letter-spacing:.04em}}
.sum,.meta,.more,footer{{color:var(--muted);font-size:14px}}
li{{list-style:none;padding:10px 0;border-top:1px solid var(--line)}} ul{{padding:0;margin:0}}
a{{color:var(--link);text-decoration:none}} b{{font-weight:600}}
</style></head><body><main>
<h1>New since last run · {today}</h1><p class="sum">{n} new · {total_tracked} relevant roles tracked in total</p>"""]
    for sec in SECTIONS:
        rows = groups[sec]
        if not rows:
            continue
        parts.append(f"<h2>{e(sec)} ({len(rows)})</h2><ul>")
        for r in rows[:C.PER_SECTION_LIMIT]:
            parts.append(f'<li><b>{e(r["company"])}</b>: <a href="{e(r["url"])}">{e(r["title"])}</a>'
                         f'<div class="meta">{e(meta_line(r))}</div></li>')
        parts.append("</ul>")
        if len(rows) > C.PER_SECTION_LIMIT:
            parts.append(f'<p class="more">+{len(rows) - C.PER_SECTION_LIMIT} more in data/new_today.csv</p>')
    if n == 0:
        parts.append("<p>Nothing new today.</p>")
    if failures:
        parts.append(f"<footer><p>Sources that failed today: {e('; '.join(failures))}</p></footer>")
    parts.append("</main></body></html>")
    return "".join(parts)


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "company", "title", "terms", "location", "posted", "note", "sources", "url"])
        for r in rows:
            w.writerow([r["section"], r["company"], r["title"], "; ".join(r["terms"]), r["location"],
                        r["posted"], r["note"].strip(" ·"), ", ".join(sorted(r["sources"])), r["url"]])


def maybe_email(subject, body_html):
    """Optional. Set GMAIL_USER and GMAIL_APP_PASSWORD (and DIGEST_TO) as repo secrets to get it by email."""
    user, pw = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD")
    if not (user and pw):
        return False
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, os.environ.get("DIGEST_TO", user)
    msg.set_content("Your digest is attached as HTML.")
    msg.add_alternative(body_html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.send_message(msg)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    raw, failures = sources.collect(C.REPO_SOURCES, C.ATS_WATCHLIST, args.local)
    rows = filters.apply(raw)
    seen = load_seen()
    new = [r for r in rows if r["id"] not in seen]
    if not seen:
        # First run: everything is "new", so only show the last 2 weeks plus programs. The rest is baselined.
        recent = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()
        new_shown = [r for r in new if r["kind"] == "program" or r["section"] == "Design & UX" or r["posted"] >= recent]
    else:
        new_shown = new
    groups = by_section(new_shown)

    md = render_md(groups, today, failures, len(rows))
    page = render_html(groups, today, failures, len(rows))
    os.makedirs(os.path.join(ROOT, "digest"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    for path, text in [(f"digest/{today}.md", md), ("digest/latest.md", md), ("docs/index.html", page)]:
        with open(os.path.join(ROOT, path), "w") as f:
            f.write(text)
    write_csv(os.path.join(ROOT, "data", "new_today.csv"), [r for s in SECTIONS for r in groups[s]])
    write_csv(os.path.join(ROOT, "data", "all_current.csv"), [r for s in SECTIONS for r in by_section(rows)[s]])

    if not args.dry_run:
        for r in new:
            seen[r["id"]] = today
        save_seen(seen, {r["id"] for r in rows}, today)
        if new_shown:
            maybe_email(f"{len(new_shown)} new roles · {today}", page)

    print(f"raw={len(raw)} relevant={len(rows)} new={len(new)} shown={len(new_shown)} failures={len(failures)}")
    for s in SECTIONS:
        print(f"  {s}: {len(groups[s])}")
    for f in failures:
        print("  failed:", f)


if __name__ == "__main__":
    main()
