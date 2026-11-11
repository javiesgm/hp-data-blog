#!/usr/bin/env python3
"""
One-off migration of the GBIF Data Blog (Hugo, gbif/data-blog) into this
hosted-portal Jekyll site.

Usage:
    python3 scripts/migrate_from_hugo.py <path-to-data-blog-clone> <path-to-hugo-build>

<path-to-hugo-build> is a `hugo -d <dir>` build of the data blog. It is used as
the source of truth for post URLs and for every image/data file that posts link
to, so that all existing /post/... addresses keep working.

What it does
- writes one file per post to _posts/YYYY-MM-DD-<slug>.md with Jekyll front matter
- copies post assets (images, data files, htmlwidgets) to /post/... at the same paths
- maps the ~100 Hugo tags to a short list of categories used by the archive filter
- keeps the original tags so nothing is lost
"""
import os, re, shutil, sys, pathlib, yaml

SRC, HUGO_OUT = map(pathlib.Path, sys.argv[1:3])
DEST = pathlib.Path(__file__).resolve().parent.parent
POSTS_IN = SRC / "content" / "post"

# --------------------------------------------------------------------------
# Tag -> category. First matching rule wins; a post gets at most 2 categories.
# --------------------------------------------------------------------------
CATEGORY_RULES = [
    ("Survey and monitoring", {"sam", "humboldt", "survey", "monitoring"}),
    ("Publishing data", {"publishing", "publish", "darwin core", "dwc-a", "dwc-dp", "sampling-event",
                         "sam", "humboldt", "ipt", "metadata", "dataset", "dataset type", "dataset classes",
                         "frictionless data", "dublin core", "protocols", "target", "location", "date",
                         "time", "installation", "hosting", "earthcape", "symbiota", "biocase"}),
    ("Molecular data", {"dna", "edna", "sequence", "molecular", "otu", "ggbn", "ebi", "metagenomics", "mixs"}),
    ("Collections", {"grscicoll", "collections", "collection", "institution", "specimen", "latimer core",
                     "ih", "idigbio", "collection descriptors", "registry"}),
    ("Taxonomy", {"taxonomy", "backbone", "catalogue of life", "catalogue-of-life", "col", "checklist",
                  "checklists", "species matching tool", "taxon match none", "taxon match higherrank",
                  "taxon match fuzzy", "species api", "tree list", "wikidata"}),
    ("Data quality", {"data quality", "quality", "flags", "issues", "outliers", "dbscan", "centroids",
                      "ingestion history", "user feedback", "spatial filtering", "annotations"}),
    ("APIs and downloads", {"api", "downloads", "sql", "rgbif", "rstats", "r", "cloud computing", "aws",
                            "azure", "parquet", "github", "tools", "shiny", "leaflet", "shapefile"}),
    ("Analysis and maps", {"maps", "gridded data", "statistics", "data gaps", "hunger maps", "es50",
                           "gbif regions", "arctic", "custom metrics", "rollup metrics", "derived datasets"}),
    ("Citation and data use", {"citation", "citethedoi", "doi", "data use", "use", "users", "release notes", "lod"}),
    ("Citizen science", {"citizen science", "citizen"}),
    ("Multimedia", {"multimedia", "media", "image", "sound", "video"}),
]

# Posts without tags: categorise by a keyword in the title (first match wins)
TITLE_RULES = [
    ("license processing", ["Data quality"]),
    ("post-processing", ["APIs and downloads", "Data quality"]),
    ("arrow and parquet", ["APIs and downloads"]),
    ("checklist of vascular plants", ["Taxonomy"]),
    ("data landscape", ["Analysis and maps"]),
    ("data gaps in the gbif backbone", ["Taxonomy", "Analysis and maps"]),
    ("can be shared through gbif", ["Publishing data"]),
    ("related records", ["Data quality"]),
    ("extinct species", ["Taxonomy"]),
    ("fish trees", ["Analysis and maps"]),
    ("google earth engine", ["Analysis and maps", "APIs and downloads"]),
    ("accumulation curves", ["Analysis and maps", "APIs and downloads"]),
    ("sql downloads", ["APIs and downloads"]),
    ("sampling bias", ["Analysis and maps"]),
    ("sustainability", ["Citation and data use"]),
    ("annotations", ["Data quality"]),
    ("community metrics", ["Citation and data use"]),
]

# Duplicate tags merged into one spelling (the Hugo blog had several variants)
TAG_MAP = {"checklists": "checklist", "publish": "publishing", "citizen": "citizen science",
           "catalogue-of-life": "Catalogue of Life", "catalogue of life": "Catalogue of Life", "col": "Catalogue of Life",
           "collection": "collections", "r": "rstats", "media": "multimedia", "image": "multimedia",
           "quality": "data quality", "darwin core": "Darwin Core", "institution": "institution"}

def categories_for(tags, title=""):
    if not tags:
        for key, cats in TITLE_RULES:
            if key in title.lower():
                return cats
    low = [t.lower() for t in tags]
    cats = []
    for t in low:                       # tag order = author's priority
        for name, keys in CATEGORY_RULES:
            if t in keys and name not in cats:
                cats.append(name)
                break
        if len(cats) == 2:
            break
    return cats or ["General"]

def hugo_urlize(s):
    s = s.strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s

def jekyll_slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def truthy(v):
    return v in (True, "yes", "true", "True", "Yes")

def split_authors(a):
    if not a:
        return []
    if isinstance(a, list):
        return [x.strip() for x in a if str(x).strip()]
    parts = re.split(r"\s*(?:,| and | & )\s*", str(a).strip())
    return [p for p in parts if p]

def first_image(body, url):
    """First real image in the post (skips map-tile templates such as .../{z}/{x}/{y}.png)."""
    # the Markdown URL may contain one level of balanced parentheses, e.g. images/plot%20(1).jpg
    for m in re.finditer(r"!\[[^\]]*\]\(((?:[^()\s]|\([^()\s]*\))+)|<img[^>]+src=[\"']([^\"']+)", body):
        src = m.group(1) or m.group(2)
        if "{" in src or src.startswith("data:"):
            continue
        if src.startswith(("http://", "https://")):
            return src
        if not src.startswith("/"):
            src = url + src.lstrip("./")
        return src
    return None

# --------------------------------------------------------------------------
posts = sorted(list(POSTS_IN.glob("*.md")) + list(POSTS_IN.glob("*/index*.md")))
out_dir = DEST / "_posts"
for f in out_dir.glob("20*.md"):
    f.unlink()

report = []
post_urls = set()
for f in posts:
    text = f.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    fm = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]

    date = str(fm.get("date"))[:10]
    y, mo, d = date.split("-")
    if int(mo) > 12:                    # a few posts have YYYY-DD-MM
        date = f"{y}-{d}-{mo}"
    slug = fm.get("slug")
    if not slug or isinstance(slug, list):
        # Hugo page bundle without a slug: URL is the folder name
        slug = f.parent.name if f.name.startswith("index") else f.stem
    slug = str(slug)
    url_slug = hugo_urlize(slug)
    url = f"/post/{url_slug}/"
    if not (HUGO_OUT / "post" / url_slug / "index.html").exists() and not truthy(fm.get("draft")):
        report.append(f"WARN no Hugo page for {f.name} -> {url}")
    post_urls.add(url_slug)

    tags = []
    for t in fm.get("tags") or []:
        t = str(t).strip()
        t = TAG_MAP.get(t.lower(), t)
        if t and t.lower() != "gbif" and t.lower() not in [x.lower() for x in tags]:
            tags.append(t)

    authors = split_authors(fm.get("author"))
    h2 = len(re.findall(r"^##\s", body, re.M)) + len(re.findall(r"<h2[\s>]", body))

    new = {"title": fm.get("title")}
    if fm.get("description"):
        new["description"] = fm["description"]
    if authors:
        new["author"] = authors[0] if len(authors) == 1 else authors
    new["date"] = date
    if fm.get("lastmod"):
        new["last_modified_at"] = str(fm["lastmod"])
    new["slug"] = slug
    if jekyll_slugify(slug) != url_slug:
        new["permalink"] = url          # keep the exact old address
    new["categories"] = categories_for(tags, str(fm.get("title") or ""))
    new["tags"] = tags
    if not fm.get("series") and url_slug.startswith("sam-"):
        fm["series"] = "Good SAMaritans"   # the SAM posts are a series; Hugo had no field for it
    if fm.get("series"):
        new["series"] = fm["series"][0] if isinstance(fm["series"], list) else fm["series"]
    img = first_image(body, url)
    if img:
        new["thumbnail"] = img
    if h2 >= 3:
        new["toc"] = True
    if truthy(fm.get("hiddenFromHomePage")):
        new["excludeFromArchive"] = True
    if truthy(fm.get("draft")):
        new["published"] = False
    if truthy(fm.get("mathjax")):
        new["mathjax"] = True
    if "<!--more-->" in body:
        new["excerpt_separator"] = "<!--more-->"

    # Hugo shortcodes -> plain HTML
    body = re.sub(r"\{\{<\s*vimeo\s+(\d+)\s*>\}\}",
                  r'<div class="video-embed"><iframe src="https://player.vimeo.com/video/\1" '
                  r'allow="fullscreen; picture-in-picture" allowfullscreen loading="lazy" '
                  r'title="Video"></iframe></div>', body)
    body = re.sub(r"\{\{<\s*youtube\s+([\w-]+)\s*>\}\}",
                  r'<div class="video-embed"><iframe src="https://www.youtube-nocookie.com/embed/\1" '
                  r'allowfullscreen loading="lazy" title="Video"></iframe></div>', body)
    if re.search(r"\{\{<|\{\{%", body):
        report.append(f"WARN unconverted shortcode in {f.name}")

    # Markdown that Hugo's goldmark accepts but Jekyll's kramdown reads differently
    body = re.sub(r"([^\n])\n(\|[^\n]*\|[ \t]*\n\|[ \t:|-]+\|)", r"\1\n\n\2", body)  # blank line before tables
    body = re.sub(r"<details(?![^>]*markdown=)", '<details markdown="1"', body)        # Markdown inside <details>
    body = re.sub(r"^(\s*```)\s*\{(\w+)[^}\n]*\}", r"\1\2", body, flags=re.M)          # ```{r} -> ```r
    # Code like R glue strings or SQL templates can contain {{ or {% -> skip Liquid
    if "{{" in body or "{%" in body:
        new["render_with_liquid"] = False

    name = f"{date}-{re.sub(r'^\d{4}-\d{2}-\d{2}-', '', jekyll_slugify(slug))}.md"
    front = yaml.safe_dump(new, sort_keys=False, allow_unicode=True, width=1000).strip()
    (out_dir / name).write_text(f"---\n{front}\n---\n{body.lstrip()}", encoding="utf-8")

# --------------------------------------------------------------------------
# Assets: copy every non-generated file under Hugo's /post/ output
# --------------------------------------------------------------------------
asset_root = DEST / "post"
if asset_root.exists():
    shutil.rmtree(asset_root)
copied = 0
for p in (HUGO_OUT / "post").rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(HUGO_OUT / "post")
    parts = rel.parts
    if parts[0] == "page" or rel.as_posix() in ("index.html", "index.xml"):
        continue
    if len(parts) == 2 and parts[0] in post_urls and parts[1] in ("index.html", "index.xml"):
        continue
    target = asset_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
    copied += 1

print(f"{len(posts)} posts, {copied} asset files")

# Give unlabelled code blocks a language (colours, line numbers, label)
import subprocess
subprocess.run([sys.executable, str(DEST / "scripts" / "label_code_blocks.py")], check=True)
print("\n".join(report) or "no warnings")
