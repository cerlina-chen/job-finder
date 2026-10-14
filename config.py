"""Everything you are likely to tweak lives here. No code changes needed to adjust filters."""

GRAD_TERM = "May 2029"

# Community repos (raw files). These already poll thousands of companies.
REPO_SOURCES = {
    "simplify": "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json",
    "zshah": "https://raw.githubusercontent.com/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/main/data/internships.csv",
    "vansh": "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/README.md",
    "vansh_off": "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/OFFSEASON_README.md",
    "speedy_swe": "https://raw.githubusercontent.com/speedyapply/2027-SWE-College-Jobs/main/README.md",
    "speedy_ai": "https://raw.githubusercontent.com/speedyapply/2027-AI-College-Jobs/main/README.md",
    "under_zapply": "https://raw.githubusercontent.com/zapplyjobs/underclassmen-internships/main/README.md",
    "under_jose": "https://raw.githubusercontent.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities/main/README.md",
}

# Design roles barely appear in the repos, so we read these company boards directly.
# Format: (ats, board slug, display name). Slug = the part after the domain in the careers URL:
#   boards.greenhouse.io/<slug>, jobs.lever.co/<slug>, jobs.ashbyhq.com/<slug>
# Add companies here. A wrong slug just shows up as "failed" in the digest footer.
ATS_WATCHLIST = [
    ("greenhouse", "figma", "Figma"),
    ("greenhouse", "databricks", "Databricks"),
    ("greenhouse", "roblox", "Roblox"),
    ("greenhouse", "duolingo", "Duolingo"),
    ("greenhouse", "airbnb", "Airbnb"),
    ("greenhouse", "pinterest", "Pinterest"),
    ("greenhouse", "discord", "Discord"),
    ("greenhouse", "stripe", "Stripe"),
    ("ashby", "notion", "Notion"),
    ("ashby", "linear", "Linear"),
    ("ashby", "ramp", "Ramp"),
    ("lever", "spotify", "Spotify"),
    ("lever", "palantir", "Palantir"),
]

# Role categories, checked in this order. Patterns are case-insensitive regex.
DESIGN = r"\b(ux|ui/ux|ux/ui|user experience|product design(er)?|interaction design|experience design|user research|ux research|design technologist|ux engineer|content design|ux writ\w*|service design|digital experience|visual design)\b"
DESIGN_EXCLUDE = r"\b(industrial|interior|mechanical|hardware|circuit|chip|asic|fpga|furniture|fashion|apparel|customer experience|employee experience|patient experience)\b"
SWE = r"\b(software|swe|developer|full[- ]?stack|front[- ]?end|back[- ]?end|web|mobile|ios|android|platform engineer|engineering intern)\b"
SWE_EXCLUDE = r"\b(mechanical|electrical|civil|chemical|hardware|fpga|asic|manufacturing|quant\w*|trad(ing|er))\b"
DATA = r"\b(data|analytics|analyst|machine learning|ml|ai|business intelligence)\b"
DATA_EXCLUDE = r"\b(quant\w*|trad(ing|er)|phd)\b"

# Drop roles that are not for undergrads like you.
LEVEL_EXCLUDE = r"\b(phd|ph\.d|master'?s|ms|m\.s\.|mba|graduate student|new grad|full[- ]?time|senior|staff|principal|manager|director)\b"

# Only keep these postings from company boards (they list every job, not just internships).
EARLY_TALENT = r"\b(intern(ship)?|co-?op|apprentice|early career|university|student|summer 20\d\d)\b"

# You can't do fall. Spring/winter only if remote (you are in classes).
DROP_FALL = True
SPRING_REQUIRES_REMOTE = True
MIN_TERM_YEAR = 2027  # drops stale "Summer 2026"-style labels

# Ranking boosts (higher = shown first within a section).
BOOST = {
    "underclassmen": (r"\b(sophomore|second[- ]year|first[- ]year|underclass\w*|freshman|explore|discover\w*|ignite|early insight|class of 2029)\b", 3),
    "new_york": (r"\b(new york|nyc|ny)\b", 1),
    "remote": (r"\bremote\b", 1),
}

# Sophomore program lists cover finance and other schools too. Keep tech/design/data/prep ones.
PROGRAM_KEEP = r"\b(software|swe|engineer\w*|tech\w*|computer|cs|data|design|ux|product|developer|career prep|fellowship|accelerate|program)\b"
PROGRAM_DROP = r"\b(investment bank\w*|equity research|private equity|wealth|trad(ing|er)|quant\w*|insight day|banking|bible|humanities|biomedical|biotech|civil|mechanical|chemical|2024|2025)\b"
PROGRAM_RESCUE = r"\b(software|swe|developer|design|ux|data)\b"  # keeps a dropped program if it is clearly your field
PROGRAM_SCHOOL_ONLY = r"\b(university|college)\b"  # program run by another school; dropped unless it mentions Wisconsin

PER_SECTION_LIMIT = 15
