#!/usr/bin/env python3
"""
build.py — turns the Markdown in content/ into a finished static website in _site/.

Run it locally to preview:      python3 build.py  &&  python3 -m http.server -d _site 8000
Netlify runs it automatically:  pip install -r requirements.txt && python3 build.py

There is no framework here on purpose. It is ~one file you can read top to bottom.
"""

import os, re, shutil, html, datetime, glob
from urllib.parse import urlsplit
import yaml
import markdown as md_lib

# ---------------------------------------------------------------- paths
ROOT    = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
ASSETS  = os.path.join(ROOT, "assets")
ADMIN   = os.path.join(ROOT, "admin")
OUT     = os.path.join(ROOT, "_site")

MD = md_lib.Markdown(extensions=["extra", "sane_lists", "smarty", "toc"])

# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str(s or ""), quote=True)

def oneline(s):
    """Collapse whitespace/newlines — for use inside HTML attributes."""
    return " ".join(str(s or "").split())

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def load_yaml(path):
    return yaml.safe_load(read(path)) or {}

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)

def parse_md(path):
    """Return (front-matter dict, rendered-html body)."""
    text = read(path)
    m = FM_RE.match(text)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
    else:
        meta, body = {}, text
    MD.reset()
    return meta, MD.convert(body)

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")

def fmt_date(value):
    if not value:
        return ""
    s = str(value)
    m = DATE_RE.match(s)
    if not m:
        return s
    try:
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # Avoid the non-portable %-d flag so local builds work on Windows too.
        return "%s %d, %d" % (d.strftime("%B"), d.day, d.year)
    except ValueError:
        return s

def slugify(name):
    name = re.sub(r"\.md$", "", os.path.basename(name))
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)      # strip date prefix on posts
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return name

def load_collection(folder):
    items, seen = [], {}
    for i, path in enumerate(sorted(glob.glob(os.path.join(CONTENT, folder, "*.md")))):
        meta, body = parse_md(path)
        if meta.get("draft") is True:
            continue
        base = slugify(path) or slugify(str(meta.get("title", ""))) or ("item-%d" % (i + 1))
        # Guarantee a unique slug so two posts never overwrite each other.
        if base in seen:
            seen[base] += 1
            slug = "%s-%d" % (base, seen[base])
        else:
            seen[base] = 1
            slug = base
        meta["_slug"] = slug
        meta["_body"] = body
        items.append(meta)
    return items

def as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    return [v for v in value if v not in (None, "")]

def file_ext_label(path):
    clean = urlsplit(str(path)).path          # drop ?query and #fragment
    ext = os.path.splitext(clean)[1].lstrip(".").upper()
    return ext or "FILE"

# ---------------------------------------------------------------- load everything
SITE  = load_yaml(os.path.join(CONTENT, "site.yml"))
PAGES = {}
for p in ("home", "about", "cv", "contact"):
    fp = os.path.join(CONTENT, "pages", p + ".md")
    PAGES[p] = parse_md(fp) if os.path.exists(fp) else ({}, "")

POSTS = sorted(load_collection("posts"), key=lambda x: str(x.get("date", "")), reverse=True)
STUDENTS = sorted(load_collection("students"), key=lambda x: str(x.get("date", "")), reverse=True)
COLLEAGUES = sorted(load_collection("colleagues"), key=lambda x: str(x.get("date", "")), reverse=True)

BASE_URL = str(SITE.get("base_url", "")).rstrip("/")

# ---------------------------------------------------------------- layout
def nav_html(active):
    links = ['<a href="/" %s>Home</a>' % ('class="active"' if active == "home" else "")]
    for item in SITE.get("nav", []):
        url = item.get("url", "#")
        is_active = active and active != "home" and ("/%s/" % active) == url
        links.append('<a href="%s"%s>%s</a>' % (esc(url), ' class="active"' if is_active else "", esc(item.get("label"))))
    return "".join(links)

def social_html():
    out = []
    for s in SITE.get("social", []):
        if s.get("url"):
            out.append('<li><a href="%s">%s</a></li>' % (esc(s["url"]), esc(s["label"])))
    return "".join(out)

def footer_nav():
    out = []
    for item in SITE.get("nav", []):
        out.append('<li><a href="%s">%s</a></li>' % (esc(item.get("url", "#")), esc(item.get("label"))))
    return "".join(out)

def initials():
    parts = re.sub(r"^(Dr\.?|Prof\.?)\s+", "", str(SITE.get("name", "")), flags=re.I).split()
    return "".join(p[0] for p in parts[:2]).upper() or "SA"

def tags_html(tags):
    items = as_list(tags)
    if not items:
        return ""
    return "".join('<span class="chip tag">%s</span>' % esc(t) for t in items)

def section_head(kicker, title, blurb="", level="h1", center=False):
    cls = "section-head center" if center else "section-head"
    blurb_html = ("<p>%s</p>" % esc(blurb)) if blurb else ""
    return '<div class="%s"><p class="kicker">%s</p><%s>%s</%s>%s</div>' % (
        cls, esc(kicker), level, esc(title), level, blurb_html)

def layout(*, title, description, body, active="", canonical="", og_image="", show_progress=False, article=False):
    site_name = esc(SITE.get("name", "Academic Hub"))
    full_title = "%s — %s" % (esc(title), site_name) if title and title != site_name else site_name
    desc = esc(oneline(description or SITE.get("tagline", "")))
    canon = (BASE_URL + canonical) if (BASE_URL and canonical) else ""
    og = (BASE_URL + og_image) if (BASE_URL and og_image) else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{site_name}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="{'article' if article else 'website'}">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{desc}">
{f'<meta property="og:url" content="{esc(canon)}">' if canon else ''}
{f'<meta property="og:image" content="{esc(og)}">' if og else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{'<div id="progress"></div>' if show_progress else ''}
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="/">
      <span class="mark">{esc(initials())}</span>
      <span class="brand-text"><small>{esc(SITE.get('role',''))}</small><strong>{site_name}</strong></span>
    </a>
    <button class="nav-toggle" aria-label="Open menu" aria-expanded="false" aria-controls="primary-nav"><span></span><span></span><span></span></button>
    <nav class="nav" id="primary-nav" aria-label="Primary">{nav_html(active)}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
{footer_html()}
<script src="/assets/js/site.js"></script>
</body>
</html>
"""

def footer_html():
    return f"""<footer class="site">
  <div class="wrap">
    <div class="foot-brand">
      <strong>{esc(SITE.get('name',''))}</strong>
      <p>{esc(SITE.get('tagline',''))}</p>
    </div>
    <div><h2>Explore</h2><ul>{footer_nav()}</ul></div>
    <div><h2>Elsewhere</h2><ul>{social_html() or '<li>Add links in Site settings</li>'}</ul></div>
    <div class="foot-note">
      <span>{esc(SITE.get('footer_note',''))}</span>
      <span>Edit this site at <a href="/admin/">/admin</a></span>
    </div>
  </div>
</footer>"""

# ---------------------------------------------------------------- shared item renderers
def post_item(post, level="h3"):
    return f"""<li class="post-item">
      <div class="meta"><span>{esc(fmt_date(post.get('date')))}</span>{tags_html(post.get('tags'))}</div>
      <{level}><a href="/writing/{esc(post['_slug'])}/">{esc(post.get('title'))}</a></{level}>
      <p class="summary">{esc(post.get('summary',''))}</p>
      <a class="go" href="/writing/{esc(post['_slug'])}/">Read &rarr;</a>
    </li>"""

def resource_item(item, level="h2"):
    has_file = bool(item.get("file"))
    actions = ""
    if has_file:
        actions += f'<a class="btn btn-solid" href="{esc(item["file"])}" download>Download {esc(file_ext_label(item["file"]))}</a>'
    if item.get("link"):
        actions += f'<a class="btn btn-outline" href="{esc(item["link"])}">Open link &rarr;</a>'
    if not actions:
        actions = '<span class="meta">File coming soon</span>'
    icon = file_ext_label(item["file"]) if has_file else ("LINK" if item.get("link") else "DOC")
    sub = item.get("course") or item.get("category") or ""
    lic = f'<span class="chip">{esc(item.get("license"))}</span>' if item.get("license") else ""
    featured = " res-featured" if item.get("featured") else ""
    body = item.get("_body", "")
    notes = f'<div class="res-notes prose">{body}</div>' if body and body.strip() else ""
    return f"""<li class="res-item{featured}">
      <div class="res-icon" aria-hidden="true">{esc(icon)}</div>
      <div class="res-body">
        <div class="meta">{('<span class="chip">%s</span>' % esc(sub)) if sub else ''}<span>{esc(fmt_date(item.get('date')))}</span>{lic}</div>
        <{level}>{esc(item.get('title'))}</{level}>
        <p>{esc(item.get('description',''))}</p>
        {notes}
        <div class="res-actions">{actions}</div>
      </div>
    </li>"""

# ---------------------------------------------------------------- page builders
def build_home():
    meta, body = PAGES["home"]
    panels = ""
    for p in meta.get("panels", []):
        panels += f"""<a class="card panel" href="{esc(p.get('url','#'))}">
          <h2>{esc(p.get('title'))}</h2>
          <p>{esc(p.get('body'))}</p>
          <span class="go">{esc(p.get('cta','Open'))} &rarr;</span>
        </a>"""

    recent = "".join(post_item(post, level="h3") for post in POSTS[:3])
    recent_block = f"""<section class="section featured-band">
        <div class="wrap">
          <div class="section-head"><p class="kicker">From the blog</p><h2>Recent writing</h2></div>
          <ul class="post-list">{recent}</ul>
          <p style="margin-top:1.5rem"><a class="btn btn-outline" href="/writing/">All posts &rarr;</a></p>
        </div>
      </section>""" if POSTS else ""

    hero = f"""<section class="hero">
      <div class="hero-watermark" aria-hidden="true">{esc(initials())}</div>
      <div class="wrap">
        <p class="eyebrow">{esc(SITE.get('institution',''))}</p>
        <h1>{esc(meta.get('hero_heading', SITE.get('name')))}</h1>
        <p class="role">{esc(meta.get('hero_sub', SITE.get('role','')))}</p>
        <p class="lede">{esc(meta.get('hero_blurb', SITE.get('tagline','')))}</p>
        <div class="cta">
          <a class="btn btn-primary" href="{esc(meta.get('cta_primary_url','/writing/'))}">{esc(meta.get('cta_primary_label','Read my writing'))}</a>
          <a class="btn btn-ghost" href="{esc(meta.get('cta_secondary_url','/about/'))}">{esc(meta.get('cta_secondary_label','About me'))}</a>
        </div>
      </div>
    </section>"""

    intro = f'<section class="section-tight"><div class="wrap narrow"><div class="prose wide">{body}</div></div></section>' if body.strip() else ""

    panels_block = f"""<section class="section">
      <div class="wrap">
        <div class="section-head center"><p class="kicker">What you'll find here</p><h2>Three things, one place</h2></div>
        <div class="grid grid-3">{panels}</div>
      </div>
    </section>"""

    body_html = hero + intro + panels_block + recent_block
    return layout(title=SITE.get("name", "Home"), description=SITE.get("tagline", ""),
                  body=body_html, active="home", canonical="/")

def build_about():
    meta, body = PAGES["about"]
    portrait = meta.get("portrait")
    if portrait:
        pic = f'<img class="portrait" src="{esc(portrait)}" alt="{esc(meta.get("portrait_alt") or SITE.get("name",""))}">'
    else:
        pic = f'<div class="portrait-fallback" aria-hidden="true">{esc(initials())}</div>'
    aside = f"""<div class="about-aside">
        <h2>Contact</h2>
        <ul>
          {'<li><a href="mailto:%s">%s</a></li>' % (esc(SITE.get('email')), esc(SITE.get('email'))) if SITE.get('email') else ''}
          {'<li>%s</li>' % esc(SITE.get('location')) if SITE.get('location') else ''}
        </ul>
        <h2>Elsewhere</h2>
        <ul>{social_html() or '<li>—</li>'}</ul>
      </div>"""
    inner = f"""<section class="section">
      <div class="wrap">
        <div class="section-head"><p class="kicker">About</p><h1>{esc(meta.get('subtitle',''))}</h1></div>
        <div class="about-grid">
          <div>{pic}{aside}</div>
          <div class="prose" style="margin:0">{body}</div>
        </div>
      </div>
    </section>"""
    return layout(title="About", description=meta.get("subtitle", ""), body=inner, active="about", canonical="/about/")

def build_cv():
    meta, body = PAGES["cv"]
    download = ""
    if meta.get("cv_pdf"):
        download = f'<a class="btn btn-solid" href="{esc(meta["cv_pdf"])}" download>Download full CV (PDF)</a>'
    updated = f'<p class="meta">Last updated {esc(fmt_date(meta.get("updated")))}</p>' if meta.get("updated") else ""
    inner = f"""<section class="section">
      <div class="wrap narrow">
        <div class="section-head"><p class="kicker">Curriculum Vitae</p><h1>{esc(meta.get('title','Curriculum Vitae'))}</h1><p>{esc(meta.get('subtitle',''))}</p></div>
        <div style="margin-bottom:1.5rem;display:flex;gap:.8rem;flex-wrap:wrap;align-items:center">{download}{updated}</div>
        <div class="prose" style="margin:0">{body}</div>
      </div>
    </section>"""
    return layout(title="CV", description=meta.get("subtitle", ""), body=inner, active="cv", canonical="/cv/")

def build_contact():
    meta, body = PAGES["contact"]
    email = SITE.get("email", "")
    details = f"""<dl class="contact-details">
      {'<dt>Email</dt><dd><a href="mailto:%s">%s</a></dd>' % (esc(email), esc(email)) if email else ''}
      {'<dt>Location</dt><dd>%s</dd>' % esc(SITE.get('location')) if SITE.get('location') else ''}
      {'<dt>Institution</dt><dd>%s</dd>' % esc(SITE.get('institution')) if SITE.get('institution') else ''}
    </dl>"""
    form = ""
    if meta.get("show_form", True):
        form = f"""<form class="form" name="contact" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/contact/?sent=1">
          <input type="hidden" name="form-name" value="contact">
          <p hidden><label>Don't fill this out: <input name="bot-field"></label></p>
          <label>Your name <input type="text" name="name" required></label>
          <label>Your email <input type="email" name="email" required></label>
          <label>Message <textarea name="message" required></textarea></label>
          <button class="btn btn-solid" type="submit">Send message</button>
        </form>"""
    inner = f"""<section class="section">
      <div class="wrap">
        <div class="section-head"><p class="kicker">Contact</p><h1>{esc(meta.get('subtitle',''))}</h1></div>
        <div class="contact-grid">
          <div><div class="prose" style="margin:0">{body}</div>{form}</div>
          <div class="contact-details">{details}</div>
        </div>
      </div>
    </section>"""
    return layout(title="Contact", description=meta.get("subtitle", ""), body=inner, active="contact", canonical="/contact/")

def build_writing_index():
    if POSTS:
        listing = '<ul class="post-list">%s</ul>' % "".join(post_item(p, level="h2") for p in POSTS)
    else:
        listing = '<div class="empty">No posts yet. Add your first one in <a href="/admin/">the editor</a>.</div>'
    inner = f"""<section class="section">
      <div class="wrap narrow">
        <div class="section-head"><p class="kicker">Writing</p><h1>Essays &amp; notes</h1><p>Thinking-in-progress on literature and the digital humanities.</p></div>
        {listing}
      </div>
    </section>"""
    return layout(title="Writing", description="Essays and notes on literature and the digital humanities.",
                  body=inner, active="writing", canonical="/writing/")

def build_post(post):
    cover = f'<img class="cover" src="{esc(post["cover"])}" alt="">' if post.get("cover") else ""
    inner = f"""<article class="section">
      <div class="wrap">
        <div class="article-head">
          <div class="meta"><a href="/writing/">&larr; All writing</a><span>{esc(fmt_date(post.get('date')))}</span>{tags_html(post.get('tags'))}</div>
          <h1>{esc(post.get('title'))}</h1>
          {'<p class="lede">%s</p>' % esc(post.get('summary')) if post.get('summary') else ''}
        </div>
        {cover}
        <div class="prose">{post['_body']}</div>
        <hr>
        <p class="meta"><a href="/writing/">&larr; Back to all writing</a></p>
      </div>
    </article>"""
    return layout(title=post.get("title", "Post"), description=post.get("summary", ""), body=inner,
                  active="writing", canonical="/writing/%s/" % post["_slug"],
                  og_image=post.get("cover", ""), show_progress=True, article=True)

def build_collection_page(items, *, active, slug, kicker, heading, blurb, empty):
    if items:
        listing = '<ul class="res-list">%s</ul>' % "".join(resource_item(i, level="h2") for i in items)
    else:
        listing = '<div class="empty">%s</div>' % empty
    inner = f"""<section class="section">
      <div class="wrap narrow">
        {section_head(kicker, heading, blurb, level="h1")}
        {listing}
      </div>
    </section>"""
    return layout(title=heading, description=blurb, body=inner, active=active, canonical="/%s/" % slug)

def build_404():
    inner = """<section class="section"><div class="wrap narrow" style="text-align:center;padding:4rem 0">
      <p class="kicker" style="color:var(--gold-ink)">404</p>
      <h1>This page wandered off.</h1>
      <p style="color:var(--ink-soft)">The link may be old or mistyped. Let's get you back.</p>
      <p style="margin-top:1.5rem"><a class="btn btn-solid" href="/">Return home</a></p>
    </div></section>"""
    return layout(title="Not found", description="Page not found", body=inner, canonical="/404.html")

def build_sitemap():
    urls = ["/", "/about/", "/writing/", "/teaching/", "/resources/", "/cv/", "/contact/"]
    urls += ["/writing/%s/" % p["_slug"] for p in POSTS]
    items = "".join("<url><loc>%s%s</loc></url>" % (BASE_URL, u) for u in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % items

def build_feed():
    entries = ""
    for p in POSTS[:20]:
        link = "%s/writing/%s/" % (BASE_URL, p["_slug"])
        entries += f"""<item>
      <title>{esc(p.get('title'))}</title>
      <link>{esc(link)}</link>
      <guid>{esc(link)}</guid>
      <pubDate>{esc(p.get('date',''))}</pubDate>
      <description>{esc(oneline(p.get('summary','')))}</description>
    </item>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{esc(SITE.get('name',''))} — Writing</title>
  <link>{esc(BASE_URL)}/writing/</link>
  <description>{esc(oneline(SITE.get('tagline','')))}</description>
  {entries}
</channel></rss>
"""

# ---------------------------------------------------------------- run
def copy_static():
    if os.path.exists(os.path.join(OUT, "assets")):
        shutil.rmtree(os.path.join(OUT, "assets"))
    shutil.copytree(ASSETS, os.path.join(OUT, "assets"))
    if os.path.isdir(ADMIN):
        shutil.copytree(ADMIN, os.path.join(OUT, "admin"), dirs_exist_ok=True)

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    write("index.html", build_home())
    write("about/index.html", build_about())
    write("cv/index.html", build_cv())
    write("contact/index.html", build_contact())
    write("writing/index.html", build_writing_index())
    for post in POSTS:
        write("writing/%s/index.html" % post["_slug"], build_post(post))
    write("teaching/index.html", build_collection_page(
        STUDENTS, active="teaching", slug="teaching",
        kicker="For students", heading="Teaching materials",
        blurb="Handouts, readings, and lab materials for my current courses — free to download, no login.",
        empty="No materials posted yet. Add handouts in <a href='/admin/'>the editor</a>."))
    write("resources/index.html", build_collection_page(
        COLLEAGUES, active="resources", slug="resources",
        kicker="For colleagues", heading="Resources for teachers",
        blurb="Reusable teaching packs, templates, and syllabi. Adapt them freely for your own classroom.",
        empty="No resources posted yet. Add materials in <a href='/admin/'>the editor</a>."))
    write("404.html", build_404())
    write("sitemap.xml", build_sitemap())
    write("feed.xml", build_feed())
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE_URL)

    copy_static()

    core_pages = 7
    print("Built %d core pages + %d posts + %d teaching + %d resources -> %s"
          % (core_pages, len(POSTS), len(STUDENTS), len(COLLEAGUES), OUT))

if __name__ == "__main__":
    main()
