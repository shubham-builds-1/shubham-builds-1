#!/usr/bin/env python3
"""
Rebuilds the whole GitHub profile from one file: profile.json

    python build.py

Writes (next to this script):
    banner.svg    animated header
    stats.svg     animated numbers + tools
    showcase.svg  animated carousel that cycles through EVERY project, one by one
    README.md     the profile page (with a table of all projects)

To add a project: add a block to "projects" in profile.json, then run this
(or just commit profile.json and let the GitHub Action run it for you).
No other file needs to be edited by hand.
"""
import html
import json
import math
import os
import random
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "profile.json")

SANS = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'SF Mono', Consolas, Menlo, 'DejaVu Sans Mono', monospace"
TEAL, VIOLET, BLUE, AMBER = "#2ee6d0", "#7a5cff", "#2d7dff", "#ffc15a"
INK, MUTED = "#f2f8fa", "#8fb0bd"
ACCENTS = [TEAL, "#b9a8ff", "#8ad0ff", "#ffd37a"]

SLIDE_SECONDS = 6.0      # how long each project stays on screen
FADE_SECONDS = 0.5

esc = lambda s: html.escape(str(s), quote=False)
attr = lambda s: html.escape(str(s), quote=True)


def die(msg):
    print(f"\nERROR in profile.json: {msg}\n", file=sys.stderr)
    sys.exit(1)


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


# ----------------------------------------------------------------------------- load + check
def load():
    try:
        with open(DATA, encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        die("profile.json was not found next to build.py")
    except json.JSONDecodeError as e:
        die(f"{e.msg} (line {e.lineno}, column {e.colno}). Usual causes: a missing comma between "
            f"two items, a comma after the LAST item in a list, or a missing quote.")

    for key in ("name", "projects"):
        if key not in d:
            die(f'the "{key}" field is missing')
    if not isinstance(d["projects"], list) or not d["projects"]:
        die('"projects" must be a list with at least one project')

    d.setdefault("eyebrow", "")
    d.setdefault("tagline", "")
    d.setdefault("badge", "")
    d.setdefault("intro", "")
    d.setdefault("linkedin", "")
    d.setdefault("stats", [])
    d.setdefault("tools", [])

    if not 1 <= len(d["stats"]) <= 5 and d["stats"]:
        warn('"stats" works best with 3 to 5 items; using the first 5')
        d["stats"] = d["stats"][:5]

    for i, p in enumerate(d["projects"], 1):
        if not isinstance(p, dict) or not p.get("name"):
            die(f'project number {i} has no "name"')
        p["status"] = str(p.get("status", "shipped")).strip().lower()
        p.setdefault("description", "")
        p["stack"] = list(p.get("stack") or [])
        p["metrics"] = list(p.get("metrics") or [])
        p.setdefault("code", "")
        p.setdefault("demo", "")
        p.setdefault("note", "")
        for k in ("code", "demo"):
            if p[k] and not str(p[k]).startswith("http"):
                die(f'project "{p["name"]}": "{k}" must start with https:// (or be empty "")')
        if len(p["metrics"]) > 3:
            warn(f'project "{p["name"]}" has more than 3 metrics; only the first 3 are shown')
            p["metrics"] = p["metrics"][:3]
        for m in p["metrics"]:
            if "value" not in m or "label" not in m:
                die(f'project "{p["name"]}": every metric needs "value" and "label"')
            if len(str(m["label"])) > 28:
                warn(f'metric label "{m["label"]}" is long ({len(str(m["label"]))} chars); keep it under 28')
    return d


# ----------------------------------------------------------------------------- shared look
def aurora(p, w, h, strength=1.0):
    defs = (f'<filter id="{p}blur" x="-40%" y="-40%" width="180%" height="180%">'
            f'<feGaussianBlur stdDeviation="46"/></filter>')

    def blob(cx, cy, rx, ry, col, op, dx, dy, dur, begin):
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{col}" opacity="{op}">'
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0;{dx} {dy};{-dx*0.4:.0f} {-dy*0.8:.0f};0 0" dur="{dur}s" begin="-{begin}s" repeatCount="indefinite"/>'
                f'<animate attributeName="rx" values="{rx};{rx*1.25:.0f};{rx*0.85:.0f};{rx}" '
                f'dur="{dur*0.8:.1f}s" begin="-{begin}s" repeatCount="indefinite"/></ellipse>')

    body = (f'<g filter="url(#{p}blur)" opacity="{strength}">'
            + blob(w*.18, h*.85, w*.34, h*.34, TEAL, .55, w*.16, -h*.22, 15, 0)
            + blob(w*.62, h*.12, w*.30, h*.42, VIOLET, .6, -w*.14, h*.2, 19, 5)
            + blob(w*.92, h*.9, w*.26, h*.30, BLUE, .55, -w*.18, -h*.2, 17, 9)
            + blob(w*.45, h*.55, w*.18, h*.2, "#19b6ff", .28, w*.1, -h*.1, 13, 3)
            + '</g>')
    return defs, body


def card_open(p, w, h, strength=1.0, r=18):
    d, b = aurora(p, w, h, strength)
    head = (f'<defs><linearGradient id="{p}base" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#050a12"/><stop offset="1" stop-color="#0a1228"/></linearGradient>'
            f'<pattern id="{p}dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="1.5" cy="1.5" r="1" fill="#ffffff" opacity=".10"/></pattern>'
            f'<linearGradient id="{p}vig" x1="0" y1="0" x2="0" y2="1"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".45"/></linearGradient>'
            f'<linearGradient id="{p}ldark" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#050a12" stop-opacity=".6"/>'
            f'<stop offset=".62" stop-color="#050a12" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="{p}card"><rect width="{w}" height="{h}" rx="{r}"/></clipPath>{d}</defs>')
    inner = (f'<g clip-path="url(#{p}card)"><rect width="{w}" height="{h}" fill="url(#{p}base)"/>{b}'
             f'<rect width="{w}" height="{h}" fill="url(#{p}ldark)"/>'
             f'<rect width="{w}" height="{h}" fill="url(#{p}dots)"/>'
             f'<rect width="{w}" height="{h}" fill="url(#{p}vig)"/>')
    tail = (f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="{r}" fill="none" '
            f'stroke="#ffffff" stroke-opacity=".12" stroke-width="1.5"/></g>')
    return head, inner, tail


def svg_wrap(w, h, label, title, parts):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{attr(label)}"><title>{esc(title)}</title>{"".join(parts)}</svg>')


def kt(*a):
    return ";".join(f"{v:.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v) for v in a)


# ----------------------------------------------------------------------------- banner
def make_banner(d):
    W, H = 1000, 320
    head, inner, tail = card_open("b", W, H, .85)
    rnd = random.Random(11)
    nodes, tries = [], 0
    while len(nodes) < 30 and tries < 4000:
        tries += 1
        x, y = rnd.randint(520, 975), rnd.randint(70, 205)
        if all((x-a)**2 + (y-b)**2 > 40**2 for a, b in nodes):
            nodes.append((x, y))
    edges = [(i, j) for i in range(len(nodes)) for j in range(i+1, len(nodes))
             if (nodes[i][0]-nodes[j][0])**2 + (nodes[i][1]-nodes[j][1])**2 < 118**2]
    net = "".join(f'<line x1="{nodes[i][0]}" y1="{nodes[i][1]}" x2="{nodes[j][0]}" y2="{nodes[j][1]}" '
                  f'stroke="#8fe9ff" stroke-opacity=".2" stroke-width="1"/>' for i, j in edges)
    for (x, y) in nodes:
        dd = round(rnd.uniform(2.2, 5), 1)
        b = round(rnd.uniform(0, 4), 1)
        net += (f'<circle cx="{x}" cy="{y}" r="2.6" fill="#d9fbff"><animate attributeName="opacity" '
                f'values=".35;1;.35" dur="{dd}s" begin="-{b}s" repeatCount="indefinite"/></circle>')
    pulses = ""
    for k, (i, j) in enumerate(rnd.sample(edges, min(16, len(edges)))):
        a, b2 = (nodes[i], nodes[j]) if k % 2 else (nodes[j], nodes[i])
        dd = round(rnd.uniform(1.8, 3.6), 1)
        bg = round(rnd.uniform(0, 5), 1)
        col = rnd.choice([TEAL, "#b9a8ff", "#8ad0ff"])
        pulses += (f'<g><circle r="7" fill="{col}" opacity=".28"/><circle r="2.6" fill="{col}"/>'
                   f'<animateMotion path="M{a[0]} {a[1]} L{b2[0]} {b2[1]}" dur="{dd}s" begin="-{bg}s" repeatCount="indefinite"/></g>')

    rc = random.Random(5)

    def yv(x, k=0.0):
        return 288 - 0.046*(x-40) - 11*math.sin((x-40)/34) - 5*math.sin((x-40)/9.5) + k

    hist = [(x, yv(x, rc.uniform(-3.2, 3.2))) for x in range(40, 641, 12)]
    fore = [(x, yv(x)) for x in range(640, 961, 12)]
    path = lambda pts: "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    hp, fp = path(hist), path([hist[-1]] + fore[1:])
    band_top = [(x, y - (3 + (x-640)*0.07)) for x, y in fore]
    band_bot = [(x, y + (3 + (x-640)*0.07)) for x, y in reversed(fore)]
    bp = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in band_top + band_bot) + "Z"
    LOOP = 12
    chart = f'''
<defs><linearGradient id="bhl" x1="0" x2="1"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>
<linearGradient id="bband" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".05"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".45"/></linearGradient>
<filter id="bglow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="4"/></filter></defs>
<g>
 <path d="{bp}" fill="url(#bband)" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0,.36,.5,.9,.96,1)}" dur="{LOOP}s" repeatCount="indefinite"/></path>
 <path d="{hp}" pathLength="1" fill="none" stroke="url(#bhl)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" filter="url(#bglow)" opacity=".7" stroke-dasharray="1" stroke-dashoffset="1">
   <animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="{kt(0,.3,1)}" dur="{LOOP}s" repeatCount="indefinite"/>
   <animate attributeName="opacity" values=".7;.7;0;0" keyTimes="{kt(0,.9,.96,1)}" dur="{LOOP}s" repeatCount="indefinite"/></path>
 <path d="{hp}" pathLength="1" fill="none" stroke="url(#bhl)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
   <animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="{kt(0,.3,1)}" dur="{LOOP}s" repeatCount="indefinite"/>
   <animate attributeName="opacity" values="1;1;0;0" keyTimes="{kt(0,.9,.96,1)}" dur="{LOOP}s" repeatCount="indefinite"/></path>
 <path d="{fp}" fill="none" stroke="#c9b8ff" stroke-width="2.4" stroke-dasharray="7 7" stroke-linecap="round" opacity="0">
   <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0,.32,.46,.9,.96,1)}" dur="{LOOP}s" repeatCount="indefinite"/></path>
 <g opacity="0"><circle r="9" fill="{TEAL}" opacity=".35"/><circle r="3.6" fill="#fff"/>
   <animateMotion path="{hp}" dur="{LOOP}s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="{kt(0,.3,1)}" calcMode="linear"/>
   <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="{kt(0,.02,.3,.34,1)}" dur="{LOOP}s" repeatCount="indefinite"/></g>
 <text x="44" y="312" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{MUTED}" opacity=".9">ACTUAL</text>
 <text x="900" y="312" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="2" fill="#c9b8ff">FORECAST + BAND</text>
</g>'''

    name = d["name"]
    fsize = 82 if len(name) <= 8 else max(36, int(82 * 8 / len(name)))
    badge = ""
    if d["badge"]:
        bw = int(len(d["badge"]) * 9.2 + 52)
        badge = (f'<g transform="translate({W-24-bw},24)"><rect width="{bw}" height="34" rx="17" fill="#ffffff" fill-opacity=".07" stroke="#ffffff" stroke-opacity=".22"/>'
                 f'<circle cx="20" cy="17" r="5" fill="{TEAL}"><animate attributeName="opacity" values="1;.25;1" dur="1.8s" repeatCount="indefinite"/></circle>'
                 f'<text x="36" y="22" font-family="{MONO}" font-size="12.5" letter-spacing="1.6" fill="{INK}">{esc(d["badge"].upper())}</text></g>')
    text = f'''
<defs><linearGradient id="bname" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">
 <stop offset="0" stop-color="#fff"/><stop offset=".42" stop-color="#fff"/><stop offset=".5" stop-color="#7ff3e6"/><stop offset=".58" stop-color="#fff"/><stop offset="1" stop-color="#fff"/>
 <animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="1000 0" dur="6s" repeatCount="indefinite"/></linearGradient></defs>
<text x="44" y="70" font-family="{SANS}" font-size="13.5" letter-spacing="4" fill="{MUTED}">{esc(d["eyebrow"].upper())}</text>
<text x="40" y="150" font-family="{SANS}" font-size="{fsize}" font-weight="300" letter-spacing="9" fill="url(#bname)">{esc(name.upper())}</text>
<rect x="44" y="166" width="92" height="3" rx="1.5" fill="{TEAL}"><animate attributeName="width" values="92;230;92" dur="6s" repeatCount="indefinite"/></rect>
<text x="44" y="204" font-family="{SANS}" font-size="19" letter-spacing="1" fill="#cfe7ee">{esc(d["tagline"])}</text>
{badge}'''
    return svg_wrap(W, H, f'{name}: {d["tagline"]}', name, [head, inner, net, pulses, chart, text, tail])


# ----------------------------------------------------------------------------- stats + tools
def make_stats(d):
    SW, SH = 1000, 250
    head, inner, tail = card_open("s", SW, SH, .8)
    tiles = d["stats"]
    n = max(len(tiles), 1)
    GAP = 20
    TWD = (SW - 80 - GAP * (n - 1)) / n
    tsvg = ""
    for i, t in enumerate(tiles):
        col = ACCENTS[i % len(ACCENTS)]
        v, lab = str(t.get("value", "")), str(t.get("label", "")).upper()
        fs = 44 if len(v) <= 5 else 36 if len(v) <= 7 else 28
        x0 = 40 + i * (TWD + GAP)
        tsvg += f'''<g transform="translate({x0:.1f},34)">
 <rect width="{TWD:.1f}" height="112" rx="16" fill="#ffffff" fill-opacity=".06" stroke="#ffffff" stroke-opacity=".16"/>
 <rect x="0" y="0" width="{TWD:.1f}" height="3" rx="1.5" fill="{col}" opacity=".9"><animate attributeName="opacity" values=".4;1;.4" dur="{3+i*0.7:.1f}s" repeatCount="indefinite"/></rect>
 <text x="{TWD/2:.1f}" y="68" text-anchor="middle" font-family="{SANS}" font-size="{fs}" font-weight="600" fill="{col}">{esc(v)}</text>
 <text x="{TWD/2:.1f}" y="94" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MUTED}">{esc(lab)}</text>
 <clipPath id="tc{i}"><rect width="{TWD:.1f}" height="112" rx="16"/></clipPath>
 <g clip-path="url(#tc{i})"><rect x="-80" y="-10" width="46" height="140" fill="#fff" opacity=".07" transform="skewX(-20)"><animateTransform attributeName="transform" type="translate" values="0 0;{TWD+160:.0f} 0;{TWD+160:.0f} 0" keyTimes="0;.35;1" dur="{6+i}s" begin="{i*0.8}s" repeatCount="indefinite" additive="sum"/></rect></g>
</g>'''

    chips, x = "", 0
    for t in d["tools"]:
        w = int(len(t) * 8.4 + 34)
        chips += (f'<g transform="translate({x},0)"><rect width="{w}" height="34" rx="17" fill="#ffffff" fill-opacity=".07" stroke="#ffffff" stroke-opacity=".2"/>'
                  f'<text x="{w/2}" y="22" text-anchor="middle" font-family="{MONO}" font-size="13.5" fill="{INK}">{esc(t)}</text></g>')
        x += w + 10
    TW = max(x - 10, 0)
    tools_svg = ""
    if d["tools"]:
        if TW > SW - 80:
            warn("too many tools to fit on one row in stats.svg; remove a few from \"tools\"")
        tools_svg = (f'<text x="40" y="186" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{MUTED}">TOOLS</text>'
                     f'<g transform="translate({(SW-TW)/2 if TW < SW-80 else 40:.0f},198)">{chips}</g>')
    label = "At a glance: " + ", ".join(f'{t.get("value")} {str(t.get("label","")).lower()}' for t in tiles)
    if d["tools"]:
        label += ". Tools: " + ", ".join(d["tools"]) + "."
    return svg_wrap(SW, SH, label, "At a glance", [head, inner, tsvg, tools_svg, tail])


# ----------------------------------------------------------------------------- project showcase
def pretty_url(u):
    for pre in ("https://github.com/", "https://www.", "https://", "http://"):
        if u.startswith(pre):
            return u[len(pre):].rstrip("/")
    return u


def opacity_keys(i, n, T, fade):
    """keyTimes/values for 'visible only during slide i, with a short fade at each end'."""
    s, e, f = i / n, (i + 1) / n, fade / T
    pts = [(0.0, 0.0)] if i else []
    if i:
        pts += [(s, 0.0)]
    pts += [(s + f, 1.0), (e - f, 1.0)]
    if i == 0:
        pts = [(0.0, 0.0)] + pts
    pts += [(e, 0.0)]
    if e < 1.0:
        pts += [(1.0, 0.0)]
    seen, clean = set(), []
    for t, v in pts:
        t = round(t, 5)
        if t in seen:
            continue
        seen.add(t)
        clean.append((t, v))
    return clean


def make_showcase(d):
    W, H = 1000, 380
    P = d["projects"]
    N = len(P)
    T = N * SLIDE_SECONDS
    head, inner, tail = card_open("p", W, H, .8)

    slides = []
    for i, pr in enumerate(P):
        accent = TEAL if pr["status"] == "shipped" else AMBER if pr["status"] == "building" else "#b9a8ff"
        status_txt = pr["status"].upper()
        chip_w = int(len(status_txt) * 9.2 + 46)

        keys = opacity_keys(i, N, T, FADE_SECONDS)
        ktimes = ";".join(f"{t:g}" for t, _ in keys)
        kvals = ";".join(f"{v:g}" for _, v in keys)
        s, f = i / N, FADE_SECONDS / T
        if i == 0:
            slide_kt, slide_kv = f"0;{2*f:g};1", "24 0;0 0;0 0"
        else:
            slide_kt, slide_kv = f"0;{s:g};{s+2*f:g};1", "24 0;24 0;0 0;0 0"

        g = [f'<g opacity="0"><animate attributeName="opacity" values="{kvals}" keyTimes="{ktimes}" dur="{T:g}s" repeatCount="indefinite"/>',
             f'<g><animateTransform attributeName="transform" type="translate" values="{slide_kv}" keyTimes="{slide_kt}" dur="{T:g}s" repeatCount="indefinite"/>']

        # status chip + note + index
        g.append(f'<g transform="translate(44,34)"><rect width="{chip_w}" height="30" rx="15" fill="{accent}" fill-opacity=".14" stroke="{accent}" stroke-opacity=".7"/>'
                 f'<circle cx="18" cy="15" r="4.5" fill="{accent}">'
                 + ('<animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/>' if pr["status"] == "building" else "")
                 + f'</circle><text x="32" y="20" font-family="{MONO}" font-size="12" letter-spacing="1.6" fill="{accent}">{esc(status_txt)}</text></g>')
        if pr["note"]:
            g.append(f'<text x="{44+chip_w+14}" y="54" font-family="{SANS}" font-size="13" fill="{MUTED}">{esc(pr["note"])}</text>')
        g.append(f'<text x="956" y="54" text-anchor="end" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{MUTED}">{i+1:02d} / {N:02d}</text>')

        # title
        title_lines = textwrap.wrap(pr["name"], width=36) or [pr["name"]]
        if len(title_lines) > 2:
            warn(f'project name "{pr["name"]}" is very long; shortening it on the slide')
            title_lines = title_lines[:2]
            title_lines[1] = title_lines[1][:33] + "…"
        y = 108
        for k, line in enumerate(title_lines):
            g.append(f'<text x="44" y="{y}" font-family="{SANS}" font-size="28" font-weight="600" fill="#ffffff">{esc(line)}</text>')
            if k < len(title_lines) - 1:
                y += 36

        # description
        desc_lines = textwrap.wrap(pr["description"], width=64) if pr["description"] else []
        if len(desc_lines) > 4:
            warn(f'description of "{pr["name"]}" is too long for the slide; cut after 4 lines')
            desc_lines = desc_lines[:4]
            desc_lines[3] = desc_lines[3].rstrip(" .,;")[:61] + "…"
        y += 34
        for line in desc_lines:
            g.append(f'<text x="44" y="{y}" font-family="{SANS}" font-size="15" fill="#cfe7ee">{esc(line)}</text>')
            y += 23

        # stack chips
        cx, cy, shown = 44, y - 23 + 18, 0
        for t in pr["stack"]:
            w = int(len(t) * 7.6 + 28)
            if cx + w > 600:
                warn(f'too many stack chips for "{pr["name"]}"; extras are hidden')
                break
            g.append(f'<g transform="translate({cx},{cy})"><rect width="{w}" height="28" rx="14" fill="#ffffff" fill-opacity=".07" stroke="#ffffff" stroke-opacity=".2"/>'
                     f'<text x="{w/2}" y="18.5" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{INK}">{esc(t)}</text></g>')
            cx += w + 8
            shown += 1

        # links
        ly = H - 68
        if pr["code"]:
            g.append(f'<text x="44" y="{ly}" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{MUTED}">CODE</text>'
                     f'<text x="100" y="{ly}" font-family="{MONO}" font-size="12.5" fill="{TEAL}">{esc(pretty_url(pr["code"]))}</text>')
        else:
            g.append(f'<text x="44" y="{ly}" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{MUTED}">CODE</text>'
                     f'<text x="100" y="{ly}" font-family="{MONO}" font-size="12.5" fill="{MUTED}">coming soon</text>')
        if pr["demo"]:
            g.append(f'<text x="44" y="{ly+22}" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{MUTED}">DEMO</text>'
                     f'<text x="100" y="{ly+22}" font-family="{MONO}" font-size="12.5" fill="#8ad0ff">{esc(pretty_url(pr["demo"]))}</text>')

        # metric tiles (right column)
        ms = pr["metrics"]
        if ms:
            gap = 12
            avail = H - 84 - 62
            th = min(78, (avail - gap * (len(ms) - 1)) / len(ms))
            for k, m in enumerate(ms):
                col = ACCENTS[k % len(ACCENTS)]
                v, lab = str(m["value"]), str(m["label"]).upper()
                fs = 30 if len(v) <= 6 else 24 if len(v) <= 9 else 19
                ty = 84 + k * (th + gap)
                g.append(f'<g transform="translate(650,{ty:.1f})"><rect width="306" height="{th:.1f}" rx="14" fill="#ffffff" fill-opacity=".06" stroke="#ffffff" stroke-opacity=".16"/>'
                         f'<rect x="0" y="14" width="3" height="{th-28:.1f}" rx="1.5" fill="{col}"/>'
                         f'<text x="22" y="{th*0.52:.1f}" font-family="{SANS}" font-size="{fs}" font-weight="600" fill="{col}">{esc(v)}</text>'
                         f'<text x="22" y="{th*0.52+20:.1f}" font-family="{MONO}" font-size="10.5" letter-spacing="1.4" fill="{MUTED}">{esc(lab)}</text></g>')

        # progress bar for this slide
        bar_kt = f"0;{s:g};{(i+1)/N:g};1" if i else f"0;{1/N:g};1"
        bar_kv = "0;0;912;912" if i else "0;912;912"
        if i == N - 1 and i:
            bar_kt = f"0;{s:g};1"
            bar_kv = "0;0;912"
        g.append(f'<rect x="44" y="{H-30}" width="0" height="3" rx="1.5" fill="{accent}">'
                 f'<animate attributeName="width" values="{bar_kv}" keyTimes="{bar_kt}" dur="{T:g}s" repeatCount="indefinite"/></rect>')
        g.append('</g></g>')
        slides.append("".join(g))

    # dots (always on top, highlight the active slide)
    dots, spacing = "", 18
    x0 = W / 2 - (N - 1) * spacing / 2
    for i in range(N):
        keys = opacity_keys(i, N, T, 0.01)
        dots += (f'<circle cx="{x0+i*spacing:.1f}" cy="{H-14}" r="3.6" fill="#ffffff" opacity=".25"/>'
                 f'<circle cx="{x0+i*spacing:.1f}" cy="{H-14}" r="3.6" fill="{TEAL}" opacity="0">'
                 f'<animate attributeName="opacity" values="{";".join(f"{v:g}" for _, v in keys)}" '
                 f'keyTimes="{";".join(f"{t:g}" for t, _ in keys)}" dur="{T:g}s" repeatCount="indefinite"/></circle>')
    track = f'<rect x="44" y="{H-30}" width="912" height="3" rx="1.5" fill="#ffffff" opacity=".1"/>'
    names = "; ".join(p["name"] for p in P)
    label = f"Project showcase, {N} projects shown one after another: {names}."
    return svg_wrap(W, H, label, "Projects", [head, inner, track, "".join(slides), dots, tail])


# ----------------------------------------------------------------------------- README
def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def make_readme(d):
    L = ["<!-- Generated by build.py from profile.json. Edit profile.json, not this file. -->",
         '<div align="center">',
         f'  <img src="banner.svg" alt="{attr(d["name"])}: {attr(d["tagline"])}" width="100%">',
         "</div>", "", "<br>", ""]
    if d["intro"]:
        L += [d["intro"], ""]
    names = ", ".join(p["name"] for p in d["projects"])
    L += ['<div align="center">',
          '  <img src="stats.svg" alt="At a glance numbers and tools" width="100%">',
          "  <br><br>",
          f'  <img src="showcase.svg" alt="Projects, shown one after another: {attr(names)}" width="100%">',
          "</div>", "", "## Projects", "",
          "| Project | Status | Details | Links |", "|---|---|---|---|"]
    for p in d["projects"]:
        status = "In progress" if p["status"] == "building" else p["status"].capitalize()
        det = cell(p["description"])
        if p["stack"]:
            det += f'<br><sub>{cell(" · ".join(p["stack"]))}</sub>'
        if p["note"]:
            det += f'<br><sub><i>{cell(p["note"])}</i></sub>'
        links = []
        if p["code"]:
            links.append(f'[Code]({p["code"]})')
        if p["demo"]:
            links.append(f'[Live demo]({p["demo"]})')
        L.append(f'| **{cell(p["name"])}** | {status} | {det} | {" · ".join(links) if links else "Code coming soon"} |')
    if d["linkedin"]:
        L += ["", "## Find me", "", f'[LinkedIn]({d["linkedin"]})']
    return "\n".join(L) + "\n"


def main():
    d = load()
    out = {
        "banner.svg": make_banner(d),
        "stats.svg": make_stats(d),
        "showcase.svg": make_showcase(d),
        "README.md": make_readme(d),
    }
    for name, content in out.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"Built {len(out)} files for {len(d['projects'])} projects: " + ", ".join(out))


if __name__ == "__main__":
    main()
