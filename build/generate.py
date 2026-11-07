"""Generates the animated SVG assets for the GitHub profile README.

GitHub strips CSS/JS/fonts from Markdown, but SVGs loaded via <img> keep their
own <style>, CSS keyframes, SMIL animation and base64-embedded fonts.
Run:  python build/generate.py   (writes into ../assets)
"""
import base64
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)


def font(name, file, style="normal", weight="300 700"):
    data = base64.b64encode(open(os.path.join(HERE, "fonts", file), "rb").read()).decode()
    return (f"@font-face{{font-family:'{name}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")


F_SANS = font("Grotesk", "grotesk.woff2")
F_MONO = font("Mono", "mono.woff2", weight="400 700")
F_SERIF = font("Serif", "serif.woff2", style="italic", weight="400")

# palette
BG = "#09090B"
SURFACE = "#111114"
LINE = "#27272A"
TEXT = "#FAFAFA"
MUTED = "#A1A1AA"
DIM = "#8B8B95"
VIOLET = "#8B5CF6"
CYAN = "#22D3EE"
GREEN = "#34D399"
PINK = "#F472B6"

BASE_CSS = f"""
.sans{{font-family:'Grotesk',ui-sans-serif,system-ui,sans-serif}}
.mono{{font-family:'Mono',ui-monospace,monospace}}
.serif{{font-family:'Serif',Georgia,serif;font-style:italic;font-weight:400}}
.fade{{animation:fadeUp .9s cubic-bezier(.2,.7,.2,1) both}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes drift1{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(140px,50px)}}}}
@keyframes drift2{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-160px,-30px)}}}}
@keyframes drift3{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(80px,-60px)}}}}
@keyframes pulse{{0%{{r:5;opacity:.9}}100%{{r:16;opacity:0}}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(w, h, body, fonts=(F_SANS, F_MONO), extra_css="", defs="", title=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>{''.join(fonts)}{BASE_CSS}{extra_css}</style>
<defs>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .5 0"/></filter>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#fff" stroke-opacity=".05"/></pattern>
<radialGradient id="gridfade" cx="50%" cy="40%" r="65%"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="gridmask"><rect width="100%" height="100%" fill="url(#gridfade)"/></mask>
<clipPath id="frame"><rect width="{w}" height="{h}" rx="20"/></clipPath>
{defs}
</defs>
{body}
</svg>"""


def backdrop(w, h, blobs, grid=True, intensity=.55):
    out = [f'<rect width="{w}" height="{h}" rx="20" fill="{BG}"/>', '<g clip-path="url(#frame)">',
           f'<g filter="url(#blur)" opacity="{intensity}">']
    for i, (cx, cy, r, color) in enumerate(blobs):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" '
                   f'style="animation:drift{i % 3 + 1} {16 + i * 4}s ease-in-out infinite"/>')
    out.append('</g>')
    if grid:
        out.append(f'<rect width="{w}" height="{h}" fill="url(#grid)" mask="url(#gridmask)"/>')
    out.append(f'<rect width="{w}" height="{h}" filter="url(#grain)" opacity=".07"/>')
    out.append('</g>')
    return "\n".join(out)


def border(w, h, gid="sheen", dur=6):
    """Hairline border with a light sheen travelling around it."""
    return f'''<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="{h}">
<stop offset="0" stop-color="{LINE}"/><stop offset=".45" stop-color="{LINE}"/>
<stop offset=".5" stop-color="{VIOLET}"/><stop offset=".55" stop-color="{CYAN}"/>
<stop offset=".6" stop-color="{LINE}"/><stop offset="1" stop-color="{LINE}"/>
<animateTransform attributeName="gradientTransform" type="translate" values="-{w} -{h};{w} {h}" dur="{dur}s" repeatCount="indefinite"/>
</linearGradient>''', f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="19.5" fill="none" stroke="url(#{gid})"/>'


def wrap(text, size, max_w, cw=.53):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if len(trial) * size * cw > max_w and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    lines.append(cur)
    return lines


def chips(items, x, y, size=15, gap=10, pad=14, h=32, color=MUTED, max_w=None):
    out, cx, cy = [], x, y
    for it in items:
        w = len(it) * size * .6 + pad * 2
        if max_w and cx + w > x + max_w:
            cx, cy = x, cy + h + gap
        out.append(f'<rect x="{cx}" y="{cy}" width="{w:.0f}" height="{h}" rx="{h / 2}" fill="#fff" fill-opacity=".04" stroke="#fff" stroke-opacity=".1"/>'
                   f'<text x="{cx + w / 2:.0f}" y="{cy + h / 2 + size * .36:.0f}" text-anchor="middle" class="mono" font-size="{size}" fill="{color}">{escape(it)}</text>')
        cx += w + gap
    return "".join(out)


# ---------------------------------------------------------------- hero
def hero():
    W, H = 1280, 560
    phrases = ["RAG pipelines with FastAPI", "end-to-end encrypted chat @ Lupyd",
               "real-time apps with WebSockets", "clean React + TypeScript UIs"]
    cyc, slot = 16, 4
    px, py, fs = 128, 392, 24
    typing = []
    for i, p in enumerate(phrases):
        wpx = len(p) * fs * .6
        kt = "0;0.3;0.75;0.9;1"
        typing.append(f'''<clipPath id="tc{i}"><rect x="{px}" y="{py - 30}" height="44" width="0">
<animate attributeName="width" values="0;{wpx:.0f};{wpx:.0f};0;0" keyTimes="{kt}" dur="{slot}s" begin="{i * slot}s;tc{i}a.end+{cyc - slot}s" id="tc{i}a" fill="freeze"/></rect></clipPath>
<text x="{px}" y="{py}" class="mono" font-size="{fs}" fill="{TEXT}" clip-path="url(#tc{i})">{escape(p)}</text>
<rect x="{px}" y="{py - 22}" width="12" height="28" fill="{CYAN}" opacity="0">
<animate attributeName="x" values="{px};{px + wpx:.0f};{px + wpx:.0f};{px};{px}" keyTimes="{kt}" dur="{slot}s" begin="{i * slot}s;tc{i}b.end+{cyc - slot}s" id="tc{i}b"/>
<set attributeName="opacity" to="1" begin="tc{i}b.begin" dur="{slot}s"/></rect>''')

    dot_x, dot_y = 128, 470
    body = backdrop(W, H, [(180, 120, 220, VIOLET), (1050, 140, 240, CYAN), (760, 520, 200, PINK)]) + f'''
<g class="fade" style="animation-delay:.05s">
  <text x="128" y="120" class="mono" font-size="16" letter-spacing="3" fill="{DIM}">SOFTWARE ENGINEER  /  FULL-STACK  /  APPLIED AI</text>
</g>
<g class="fade" style="animation-delay:.2s">
  <text x="122" y="222" class="sans" font-size="92" font-weight="600" letter-spacing="-3" fill="{TEXT}">Mohammed Fawaz</text>
  <text x="122" y="316" class="sans" font-size="92" font-weight="600" letter-spacing="-3" fill="{TEXT}">Haneef<tspan class="serif" font-size="96" letter-spacing="0" fill="url(#ink)"> — builds.</tspan></text>
</g>
<g class="fade" style="animation-delay:.45s">
  <text x="{px - 30}" y="{py}" class="mono" font-size="{fs}" fill="{GREEN}">›</text>
  {"".join(typing)}
</g>
<g class="fade" style="animation-delay:.65s">
  <circle cx="{dot_x + 6}" cy="{dot_y}" r="5" fill="{GREEN}"/>
  <circle cx="{dot_x + 6}" cy="{dot_y}" r="5" fill="none" stroke="{GREEN}" stroke-width="2" style="animation:pulse 2s ease-out infinite"/>
  <text x="{dot_x + 24}" y="{dot_y + 6}" class="mono" font-size="17" fill="{MUTED}">Open to entry-level &amp; new-grad SWE roles</text>
</g>
<g class="fade" style="animation-delay:.8s" text-anchor="end">
  <text x="{W - 112}" y="438" class="sans" font-size="40" font-weight="600" fill="{TEXT}">100+</text>
  <text x="{W - 112}" y="464" class="mono" font-size="13" letter-spacing="1.5" fill="{DIM}">COMMITS @ LUPYD</text>
  <text x="{W - 312}" y="438" class="sans" font-size="40" font-weight="600" fill="{TEXT}">10+</text>
  <text x="{W - 312}" y="464" class="mono" font-size="13" letter-spacing="1.5" fill="{DIM}">PROJECTS BUILT</text>
</g>
'''
    g, b = border(W, H, dur=7)
    defs = g + f'''<linearGradient id="ink" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}"/><stop offset=".5" stop-color="{CYAN}"/><stop offset="1" stop-color="{GREEN}"/>
<animateTransform attributeName="gradientTransform" type="translate" values="-.3 0;.3 0;-.3 0" dur="8s" repeatCount="indefinite"/></linearGradient>'''
    return svg(W, H, body + b, fonts=(F_SANS, F_MONO, F_SERIF), defs=defs,
               title="Mohammed Fawaz Haneef, Software Engineer (Full-stack and Applied AI). Open to entry-level and new-grad SWE roles.")


# ---------------------------------------------------------------- section header
def section(num, title, accent, kicker):
    W, H = 1280, 120
    body = f'''<g class="fade">
<text x="8" y="40" class="mono" font-size="16" letter-spacing="3" fill="{DIM}">{num}  /  {escape(kicker.upper())}</text>
<text x="4" y="98" class="sans" font-size="52" font-weight="600" letter-spacing="-1.5" fill="url(#txt)">{escape(title)} <tspan class="serif" font-size="56" letter-spacing="0" fill="url(#acc)">{escape(accent)}</tspan></text>
</g>'''
    defs = f'''<linearGradient id="acc" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
<linearGradient id="txt" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#F4F4F5"/><stop offset="1" stop-color="#A1A1AA"/></linearGradient>'''
    return svg(W, H, body, fonts=(F_SANS, F_MONO, F_SERIF), defs=defs, title=f"{title} {accent}")


# ---------------------------------------------------------------- project / experience cards
def card(num, kicker, title, desc, tech, link_label, accent, W=630, H=360, metrics=None, gid="c"):
    blobs = [(W - 60, 40, 150, accent)]
    lines = wrap(desc, 19, W - 96)
    desc_svg = "".join(f'<tspan x="48" dy="{0 if i == 0 else 29}">{escape(l)}</tspan>' for i, l in enumerate(lines))
    ty = 178 + 29 * (len(lines) - 1) + 44
    met = ""
    if metrics:
        mx = W - 48
        for val, lab in reversed(metrics):
            met += (f'<text x="{mx}" y="112" text-anchor="end" class="sans" font-size="38" font-weight="600" fill="{TEXT}">{escape(val)}</text>'
                    f'<text x="{mx}" y="136" text-anchor="end" class="mono" font-size="12" letter-spacing="1.5" fill="{DIM}">{escape(lab)}</text>')
            mx -= 190
    body = backdrop(W, H, blobs, grid=False, intensity=.35) + f'''
<g class="fade">
<text x="48" y="64" class="mono" font-size="14" letter-spacing="2.5" fill="{DIM}">{num}  ·  {escape(kicker.upper())}</text>
<text x="46" y="122" class="sans" font-size="40" font-weight="600" letter-spacing="-1" fill="{TEXT}">{escape(title)}</text>
{met}
<text y="178" class="sans" font-size="19" fill="{MUTED}">{desc_svg}</text>
{chips(tech, 48, ty, size=13, h=28, gap=8, pad=12, max_w=W - 96)}
<text x="48" y="{H - 36}" class="mono" font-size="14" fill="{accent}">{escape(link_label)} ↗</text>
</g>'''
    g, b = border(W, H, gid=gid, dur=5 + (hash(title) % 4))
    return svg(W, H, body + b, defs=g, title=f"{title}: {desc} Tech: {', '.join(tech)}")


# ---------------------------------------------------------------- stack
def stack():
    W = 1280
    rows = [("LANGUAGES", ["Python", "TypeScript", "JavaScript", "SQL", "Rust"], VIOLET),
            ("FRONTEND", ["React", "Next.js", "Tailwind CSS", "shadcn/ui", "Vite", "Tauri"], CYAN),
            ("BACKEND", ["FastAPI", "Django", "Node.js", "Express", "REST", "WebSockets"], GREEN),
            ("DATA & AI", ["PostgreSQL", "MongoDB", "Supabase", "Redis", "RAG", "LLM APIs", "PyTorch"], PINK),
            ("TOOLING", ["Git", "Docker", "GitHub Actions", "pytest", "Vercel", "Linux"], "#FBBF24")]
    H = 80 + len(rows) * 66
    out = []
    for i, (lab, items, col) in enumerate(rows):
        y = 64 + i * 66
        out.append(f'<g class="fade" style="animation-delay:{i * .08:.2f}s">'
                   f'<circle cx="56" cy="{y + 18}" r="5" fill="{col}"/>'
                   f'<text x="76" y="{y + 24}" class="mono" font-size="15" letter-spacing="2.5" fill="{DIM}">{escape(lab)}</text>'
                   f'{chips(items, 280, y, size=16, h=36, pad=16, color=TEXT)}</g>')
        if i < len(rows) - 1:
            out.append(f'<line x1="48" x2="{W - 48}" y1="{y + 52}" y2="{y + 52}" stroke="#fff" stroke-opacity=".05"/>')
    body = backdrop(W, H, [(1100, 60, 180, VIOLET), (200, H, 160, CYAN)], intensity=.25) + "".join(out)
    g, b = border(W, H, dur=8)
    alt = "; ".join(f"{l}: {', '.join(i)}" for l, i, _ in rows)
    return svg(W, H, body + b, defs=g, title="Tech stack. " + alt)


# ---------------------------------------------------------------- footer
def footer():
    W, H = 1280, 340
    body = backdrop(W, H, [(300, 300, 220, VIOLET), (980, 60, 220, CYAN), (640, 380, 160, GREEN)], intensity=.5) + f'''
<g class="fade" text-anchor="middle">
<text x="{W / 2}" y="92" class="mono" font-size="15" letter-spacing="3" fill="{DIM}">HAVE AN INTERESTING PROBLEM?</text>
<text x="{W / 2}" y="186" class="sans" font-size="76" font-weight="600" letter-spacing="-2.5" fill="{TEXT}">Let’s build something <tspan class="serif" font-size="82" letter-spacing="0" fill="url(#ink)">real.</tspan></text>
<text x="{W / 2}" y="248" class="sans" font-size="21" fill="{MUTED}">Looking for entry-level / new-grad roles in full-stack, backend &amp; AI engineering.</text>
<text x="{W / 2}" y="296" class="mono" font-size="14" fill="{DIM}">mohdfawaz2004@gmail.com  ·  linkedin.com/in/fawaz-devs</text>
</g>'''
    g, b = border(W, H, dur=7)
    defs = g + f'<linearGradient id="ink" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>'
    return svg(W, H, body + b, fonts=(F_SANS, F_MONO, F_SERIF), defs=defs,
               title="Let's build something real. Open to entry-level and new-grad roles.")


FILES = {
    "hero.svg": hero(),
    "sec-experience.svg": section("01", "Where I", "work.", "experience"),
    "sec-projects.svg": section("02", "Things I’ve", "built.", "selected projects"),
    "sec-stack.svg": section("03", "Tools I", "use.", "tech stack"),
    "sec-activity.svg": section("04", "Shipping", "lately.", "github activity"),
    "card-lupyd.svg": card("CO-FOUNDER", "Software engineer", "Lupyd",
                           "Privacy-first alternative to Discord & Slack: end-to-end encrypted chat (Signal Protocol + MLS), workspaces and voice/video, on desktop and mobile. I build product features in the cross-platform Tauri client.",
                           ["React", "TypeScript", "Tauri", "Rust", "E2EE", "Vite"], "lupyd.com", GREEN,
                           W=1280, H=330, metrics=[("100+", "COMMITS"), ("5", "PLATFORMS")], gid="cl"),
    "card-atlas.svg": card("01", "AI engineering · RAG", "ATLAS AI",
                           "Enterprise knowledge assistant. Upload company documents, ask questions in plain English, and get grounded answers with source citations — powered by semantic search over a vector database.",
                           ["Python", "FastAPI", "React", "TypeScript", "RAG", "Embeddings", "Vector DB", "LLMs"],
                           "atlasaibyfawaz.vercel.app  ·  live demo", VIOLET, W=1280, H=330, gid="ca"),
    "card-ecom.svg": card("02", "Backend", "E-Commerce API",
                          "Production-style REST API: JWT auth, role-based admin, cart & order processing with inventory checks, OpenAPI docs and a pytest suite.",
                          ["FastAPI", "PostgreSQL", "SQLAlchemy", "Docker", "pytest"], "view source", CYAN, gid="ce"),
    "card-testing.svg": card("03", "Quality · CI/CD", "API Test Automation",
                             "pytest framework for REST regression testing with a reusable HTTP client, shared fixtures, HTML reports — run on every push by GitHub Actions.",
                             ["Python", "pytest", "requests", "GitHub Actions"], "view source", GREEN, gid="ct"),
    "card-polling.svg": card("04", "Real-time", "Live Polling",
                             "Classroom polling app: teachers launch polls, students answer live, and results stream back instantly over WebSockets.",
                             ["Node.js", "Express", "Socket.io", "React"], "view source", PINK, gid="cp"),
    "card-feedback.svg": card("05", "Full-stack · NLP", "Smart Feedback",
                              "Feedback platform with role-based access, automatic sentiment classification and admin dashboards that chart trends over time.",
                              ["React", "TypeScript", "PostgreSQL", "NLP", "Chart.js"], "view source", "#FBBF24", gid="cf"),
    "stack.svg": stack(),
    "footer.svg": footer(),
}

for name, content in FILES.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"{name:22s} {len(content) // 1024:4d} KB")
