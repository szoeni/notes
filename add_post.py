#!/usr/bin/env python3
"""
add_post.py – Neuen Blogbeitrag aus Zotero-Notizen erstellen.

Verwendung:
  python3 add_post.py --key ZOTERO_KEY --title "Titel des Beitrags" --slug "url-slug"
  python3 add_post.py --author "Parsons" --title "Titel" --slug "parsons-carbon"
  python3 add_post.py --list   (alle verfügbaren Einträge mit Notizen anzeigen)

Optionale Argumente:
  --intro "Einleitungstext"   Kursiv gesetzter Einleitungsabsatz
"""

import json, os, re, argparse, sys
from datetime import date

BLOG_DIR   = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR  = os.path.join(BLOG_DIR, "posts")
CACHE_FILE = os.path.join(BLOG_DIR, "notes_cache.json")
POSTS_FILE = os.path.join(BLOG_DIR, "posts.json")

BLOG_TITLE    = "Lektürenotizen"
BLOG_SUBTITLE = "Gedanken aus der Forschung zu Globalisierung, Ungleichheit und ökologischer Transformation"
BLOG_AUTHOR   = "Philipp Schöneberg"

os.makedirs(POSTS_DIR, exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────────────
with open(CACHE_FILE) as f:
    data = json.load(f)
entries_by_key = {e['key']: e for e in data['entries']}

# ── Date helpers ─────────────────────────────────────────────────────────────
_MONTHS = {"January":"Januar","February":"Februar","March":"März","April":"April",
           "May":"Mai","June":"Juni","July":"Juli","August":"August",
           "September":"September","October":"Oktober","November":"November","December":"Dezember"}

def german_date(d=None):
    d = d or date.today()
    s = d.strftime("%-d. %B %Y")
    for en, de in _MONTHS.items():
        s = s.replace(en, de)
    return s

TODAY = german_date()

# ── CSS (same as in build script) ───────────────────────────────────────────
CSS = r"""
:root {
  --ink:#1a1a1a;--mid:#555;--faint:#888;--rule:#ddd;
  --accent:#2d5a27;--accent-light:#e8f0e6;
  --interp-bg:#f5f0e8;--interp-border:#b89a5a;
  --bg:#fafaf8;--max:720px;
  --serif:Georgia,'Times New Roman',serif;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--serif);background:var(--bg);color:var(--ink);line-height:1.8;font-size:18px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.site-header{border-bottom:2px solid var(--ink);padding:2.5rem 1.5rem 1.5rem;text-align:center}
.site-header h1{font-family:var(--sans);font-size:1.9rem;font-weight:700;letter-spacing:-.5px}
.site-header h1 a{color:inherit;text-decoration:none}
.subtitle{font-size:.88rem;color:var(--mid);margin-top:.4rem;font-style:italic}
.site-header nav{margin-top:1rem;font-family:var(--sans);font-size:.82rem}
.site-header nav a{margin:0 .75rem;color:var(--mid);text-transform:uppercase;letter-spacing:.06em}
.container{max-width:var(--max);margin:0 auto;padding:3rem 1.5rem 5rem}
.post-list{list-style:none}
.post-list li{padding:2.2rem 0;border-bottom:1px solid var(--rule)}
.post-list li:first-child{padding-top:0}
.post-meta{font-family:var(--sans);font-size:.75rem;color:var(--faint);text-transform:uppercase;letter-spacing:.07em;margin-bottom:.35rem}
.post-list h2{font-size:1.3rem;line-height:1.3;margin-bottom:.45rem}
.post-list h2 a{color:var(--ink)}
.post-list h2 a:hover{color:var(--accent);text-decoration:none}
.post-excerpt{font-size:.93rem;color:var(--mid);margin-bottom:.7rem}
.source-tag{display:inline-block;background:var(--accent-light);color:var(--accent);font-family:var(--sans);font-size:.72rem;padding:.18rem .55rem;border-radius:2px;font-weight:600;letter-spacing:.04em}
.read-more{font-family:var(--sans);font-size:.8rem;font-weight:700;color:var(--accent);letter-spacing:.03em;margin-top:.5rem;display:inline-block}
.back-link{font-family:var(--sans);font-size:.8rem;color:var(--mid);display:inline-block;margin-bottom:2rem}
.post-header{margin-bottom:2.5rem;padding-bottom:1.5rem;border-bottom:1px solid var(--rule)}
.post-header h1{font-size:1.85rem;line-height:1.25;margin:.6rem 0 .6rem}
.post-body h2{font-size:1.05rem;font-family:var(--sans);font-weight:700;margin:2.2rem 0 .65rem;border-bottom:1px solid var(--rule);padding-bottom:.3rem}
.post-body p{margin-bottom:1.1rem}
.post-body blockquote{border-left:3px solid var(--accent);margin:1.4rem 0;padding:.7rem 1.2rem;background:var(--accent-light);font-style:italic}
.post-body blockquote cite{display:block;font-style:normal;font-family:var(--sans);font-size:.76rem;color:var(--faint);margin-top:.35rem}
.interp{border-left:3px solid var(--interp-border);margin:1.4rem 0;padding:.7rem 1.2rem;background:var(--interp-bg)}
.interp-label{font-family:var(--sans);font-size:.72rem;font-weight:700;color:var(--interp-border);text-transform:uppercase;letter-spacing:.07em;margin-bottom:.35rem}
.interp p{margin-bottom:.5rem;color:#3a3020}
.interp p:last-child{margin-bottom:0}
.cite-line{font-family:var(--sans);font-size:.8rem;color:var(--faint);display:block;margin-bottom:.6rem;margin-top:-.4rem}
.post-references{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--rule);font-family:var(--sans);font-size:.82rem;color:var(--mid)}
.post-references h3{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.65rem;color:var(--faint)}
.intro{font-size:.96rem;color:var(--mid);font-style:italic;border-bottom:1px solid var(--rule);padding-bottom:1.5rem;margin-bottom:1.8rem}
footer{border-top:1px solid var(--rule);text-align:center;padding:1.5rem;font-family:var(--sans);font-size:.76rem;color:var(--faint)}
"""

# ── Note parser ──────────────────────────────────────────────────────────────
def parse_note_content(content):
    lines    = [l.rstrip() for l in content.split('\n')]
    parts    = []
    ibuf     = []
    in_interp = False
    cite_re  = re.compile(r'^\(([^)]+(?:19|20)\d\d[^)]*)\)\s*$')
    interp_re = re.compile(r'^(Eigene Interpretation|Weiterführende Frage|Resultierende Fragestellung):?\s*(.*)', re.DOTALL)
    zitat_re  = re.compile(r'^Zitat:\s*(.+)$', re.DOTALL)

    def flush():
        if ibuf:
            inner = '\n'.join(f'<p>{l}</p>' for l in ibuf if l.strip())
            parts.append(f'<div class="interp"><div class="interp-label">Eigene Interpretation</div>{inner}</div>')
            ibuf.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line: i += 1; continue

        m = cite_re.match(line)
        if m:
            flush(); in_interp = False
            parts.append(f'<span class="cite-line">({m.group(1)})</span>')
            i += 1; continue

        m = interp_re.match(line)
        if m:
            if not in_interp: flush(); in_interp = True
            label = m.group(1); rest = m.group(2).strip()
            ibuf.append(f'<strong>{label}:</strong> {rest}' if rest else f'<strong>{label}</strong>')
            i += 1; continue

        if in_interp:
            ibuf.append(line); i += 1; continue

        m = zitat_re.match(line)
        if m:
            flush(); in_interp = False
            q = m.group(1)
            j = i + 1
            while j < len(lines) and lines[j].strip() and not cite_re.match(lines[j].strip()) and not interp_re.match(lines[j].strip()):
                q += ' ' + lines[j].strip(); j += 1
            cite_str = ""
            if j < len(lines):
                cm = cite_re.match(lines[j].strip())
                if cm: cite_str = f'<cite>({cm.group(1)})</cite>'; j += 1
            q = re.sub(r'^[„"\u201c"]+|["\u201d"]+$', '', q.strip())
            parts.append(f'<blockquote>{q}{cite_str}</blockquote>')
            i = j; continue

        flush(); in_interp = False
        parts.append(f'<p>{line}</p>')
        i += 1

    flush()
    return '\n'.join(parts)

def build_body(entry):
    out = []
    for note in entry['notes']:
        if note['heading'].strip():
            out.append(f'<h2>{note["heading"].strip()}</h2>')
        out.append(parse_note_content(note['content']))
    return '\n'.join(out)

# ── HTML templates ────────────────────────────────────────────────────────────
def post_html(entry, title, slug, intro=""):
    src = f"{entry['author']} ({entry['year']})"
    if entry.get('publication'): src += f" — <em>{entry['publication']}</em>"
    short = entry['title'][:90] + ("…" if len(entry['title'])>90 else "")
    intro_html = f'<p class="intro">{intro}</p>' if intro else ""
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {BLOG_TITLE}</title><style>{CSS}</style></head>
<body>
<header class="site-header">
  <h1><a href="../index.html">{BLOG_TITLE}</a></h1>
  <p class="subtitle">{BLOG_SUBTITLE}</p>
  <nav><a href="../index.html">Alle Beiträge</a></nav>
</header>
<main class="container">
<a class="back-link" href="../index.html">← Alle Beiträge</a>
<article>
<header class="post-header">
  <div class="source-tag">Lektürenotiz</div>
  <h1>{title}</h1>
  <div class="post-meta">{TODAY} &ensp;·&ensp; {BLOG_AUTHOR}</div>
</header>
{intro_html}
<div class="post-body">
{build_body(entry)}
</div>
<div class="post-references">
  <h3>Quelle</h3>
  <p>{src}<br><em>{short}</em></p>
</div>
</article>
</main>
<footer><p>© {date.today().year} {BLOG_AUTHOR}</p></footer>
</body></html>"""

def index_html(posts):
    items = ""
    for p in reversed(posts):
        items += f"""
  <li>
    <div class="post-meta">{p['date']}</div>
    <h2><a href="posts/{p['slug']}.html">{p['title']}</a></h2>
    <p class="post-excerpt">{p['excerpt']}</p>
    <span class="source-tag">{p['author_source']}</span><br>
    <a class="read-more" href="posts/{p['slug']}.html">Weiterlesen →</a>
  </li>"""
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{BLOG_TITLE}</title><style>{CSS}</style></head>
<body>
<header class="site-header">
  <h1>{BLOG_TITLE}</h1>
  <p class="subtitle">{BLOG_SUBTITLE}</p>
  <nav><a href="index.html">Alle Beiträge</a></nav>
</header>
<main class="container"><ul class="post-list">{items}</ul></main>
<footer><p>© {date.today().year} {BLOG_AUTHOR}</p></footer>
</body></html>"""

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Blog-Beitrag aus Zotero-Notizen erstellen")
    parser.add_argument('--key',    help='Zotero-Key des Eintrags')
    parser.add_argument('--author', help='Autorenname (Suche, wenn kein Key angegeben)')
    parser.add_argument('--title',  help='Titel des Blogbeitrags', required=False)
    parser.add_argument('--slug',   help='URL-Slug (z.B. gramsci-hegemonie)', required=False)
    parser.add_argument('--intro',  help='Einleitungstext', default="")
    parser.add_argument('--list',   action='store_true', help='Alle Einträge mit Notizen anzeigen')
    args = parser.parse_args()

    if args.list:
        print(f"\n{'Nr':>3}  {'Key':<12} {'Notizen':>7}  Autor (Jahr) — Titel")
        print("─" * 80)
        for i, e in enumerate(data['entries']):
            print(f"{i:>3}  {e['key']:<12} {len(e['notes']):>7}  {e['author']} ({e['year']}) — {e['title'][:45]}")
        return

    # Find entry
    if args.key:
        if args.key not in entries_by_key:
            print(f"Fehler: Key '{args.key}' nicht gefunden. --list zeigt alle Keys.", file=sys.stderr)
            sys.exit(1)
        entry = entries_by_key[args.key]
    elif args.author:
        matches = [e for e in data['entries'] if args.author.lower() in e['author'].lower()]
        if not matches:
            print(f"Kein Eintrag mit Autor '{args.author}' gefunden.", file=sys.stderr)
            sys.exit(1)
        if len(matches) > 1:
            print(f"Mehrere Treffer – bitte --key verwenden:")
            for m in matches:
                print(f"  {m['key']}  {m['author']} ({m['year']}) — {m['title'][:50]}")
            sys.exit(1)
        entry = matches[0]
    else:
        parser.print_help(); sys.exit(1)

    title = args.title or f"Notizen zu {entry['author']} ({entry['year']})"
    slug  = args.slug  or re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]

    # Generate excerpt
    excerpt = ""
    for n in entry['notes']:
        for l in n['content'].split('\n'):
            l = l.strip()
            if l and not l.startswith('(') and not l.startswith('Eigene') and not l.startswith('Zitat'):
                excerpt = l[:200] + "…"; break
        if excerpt: break

    # Write post file
    html = post_html(entry, title, slug, args.intro)
    post_path = os.path.join(POSTS_DIR, f"{slug}.html")
    with open(post_path, 'w') as f:
        f.write(html)

    # Update posts registry
    with open(POSTS_FILE) as f:
        posts = json.load(f)

    # Remove existing entry with same slug if updating
    posts = [p for p in posts if p['slug'] != slug]
    posts.append({"slug": slug, "title": title,
                  "author_source": f"{entry['author']} ({entry['year']})",
                  "date": TODAY, "excerpt": excerpt})
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # Regenerate index
    with open(os.path.join(BLOG_DIR, "index.html"), 'w') as f:
        f.write(index_html(posts))

    print(f"✓ Beitrag erstellt: {post_path}")
    print(f"✓ index.html aktualisiert ({len(posts)} Beiträge)")
    print(f"\nTitel:  {title}")
    print(f"Quelle: {entry['author']} ({entry['year']})")
    print(f"Datei:  posts/{slug}.html")

if __name__ == '__main__':
    main()
