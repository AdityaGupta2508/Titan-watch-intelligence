"""Draws a distinct SVG watch for every Titan collection (no image files needed).
Want real photos? Drop PNG/JPG/WEBP files into an  images/  folder named after the model
(e.g. images/Nebula MET-08.png) or the collection (images/Nebula.png) - they replace the drawings automatically.
"""
import os, math, glob, base64

HERE = os.path.dirname(os.path.abspath(__file__))
CX, CY = 130, 200

# case=(light,dark) metal gradient | dial=(centre,edge) | strap colours per strap type
CFG = {
    "Nebula":   dict(shape="tonneau", case=("#F6E7B4", "#B8923A"), dial=("#1B3F95", "#071641"), hand="#F6E7B4", mark="#F6E7B4",
                     style="roman", leather="#1A1A22", silicone="#0E2A6B"),
    "Edge":     dict(shape="round", case=("#EDEFF5", "#8E96AD"), dial=("#3A4663", "#1A2238"), hand="#FFFFFF", mark="#DDE3F2",
                     style="slim", leather="#3A4258", silicone="#3A4663"),
    "Raga":     dict(shape="round", case=("#F6D9CF", "#C98F7D"), dial=("#FFFFFF", "#F2E6E2"), hand="#B87463", mark="#B87463",
                     style="studs", leather="#7C4A3A", silicone="#C98F7D"),
    "Regalia":  dict(shape="round", case=("#F6E7B4", "#B8923A"), dial=("#FFF7DD", "#E8D49A"), hand="#7A5A12", mark="#7A5A12",
                     style="roman", leather="#4A2E1E", silicone="#B8923A"),
    "Octane":   dict(shape="round", case=("#D9DDE8", "#4B536B"), dial=("#1A1F2E", "#080B14"), hand="#FFFFFF", mark="#FFFFFF",
                     style="chrono", leather="#14161D", silicone="#C0392B"),
    "Karishma": dict(shape="round", case=("#EDEFF5", "#8E96AD"), dial=("#FFFFFF", "#E7ECF7"), hand="#0A1F5C", mark="#0A1F5C",
                     style="classic", leather="#3B2A20", silicone="#0A1F5C"),
    "Neo":      dict(shape="round", case=("#DADFEC", "#5C6685"), dial=("#161B2C", "#070A14"), hand="#FFFFFF", mark="#8FB1FF",
                     style="classic", leather="#1B1E2A", silicone="#2E5BFF"),
    "Smart":    dict(shape="square", case=("#E4E8F2", "#3B435C"), dial=("#06080F", "#000000"), hand="#FFFFFF", mark="#5B8DEF",
                     style="smart", leather="#3A4258", silicone="#3B5BDB"),
    "Automatic": dict(shape="round", case=("#EDEFF5", "#7A839D"), dial=("#1F2A4D", "#0B1230"), hand="#F6E7B4", mark="#F6E7B4",
                      style="open", leather="#4A2E1E", silicone="#0A1F5C"),
}
DEFAULT = CFG["Karishma"]

def _p(r, deg):
    a = math.radians(deg)
    return CX + r * math.sin(a), CY - r * math.cos(a)

def find_image(model, collection):
    for name in (model, collection):
        for ext in ("png", "jpg", "jpeg", "webp"):
            path = os.path.join(HERE, "images", f"{name}.{ext}")
            if os.path.exists(path):
                mime = "jpeg" if ext in ("jpg", "jpeg") else ext
                return f"data:image/{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()
    return None

def _strap(kind, color, top, bot, u, metal):
    s = []
    if kind == "Metal":
        for y in range(top - 17, -20, -19):
            s.append(f"<rect x='91' y='{y}' width='78' height='16' rx='5' fill='url(#mt{u})'/>")
        for y in range(bot + 1, 420, 19):
            s.append(f"<rect x='91' y='{y}' width='78' height='16' rx='5' fill='url(#mt{u})'/>")
        return "".join(s)
    s.append(f"<path d='M96 0 L164 0 L169 {top} L91 {top} Z' fill='{color}'/>")
    s.append(f"<path d='M91 {bot} L169 {bot} L163 400 L97 400 Z' fill='{color}'/>")
    if kind == "Leather":
        for x0, x1 in ((101, 104), (159, 156)):
            s.append(f"<path d='M{x0} 4 L{x0 + (4 if x0 < 130 else -4)} {top - 6}' stroke='rgba(255,255,255,.35)' "
                     f"stroke-width='1.4' stroke-dasharray='4 3' fill='none'/>")
            s.append(f"<path d='M{x0 + (4 if x0 < 130 else -4)} {bot + 6} L{x0 + (2 if x0 < 130 else -2)} 396' stroke='rgba(255,255,255,.35)' "
                     f"stroke-width='1.4' stroke-dasharray='4 3' fill='none'/>")
        for i in range(5):
            s.append(f"<circle cx='130' cy='{bot + 38 + i * 21}' r='3.2' fill='rgba(0,0,0,.55)'/>")
    else:  # Silicone
        for y in range(8, top - 4, 13):
            s.append(f"<path d='M{97 + y * 0.03:.1f} {y} L{163 - y * 0.03:.1f} {y}' stroke='rgba(0,0,0,.22)' stroke-width='2'/>")
        for y in range(bot + 10, 396, 13):
            s.append(f"<path d='M97 {y} L163 {y}' stroke='rgba(0,0,0,.22)' stroke-width='2'/>")
        for i in range(4):
            s.append(f"<circle cx='130' cy='{bot + 44 + i * 22}' r='3.4' fill='rgba(0,0,0,.5)'/>")
    s.append(f"<rect x='91' y='0' width='78' height='400' fill='url(#sh{u})' opacity='.35'/>")
    return "".join(s)

def _ticks(cfg, R):
    out, st = [], cfg["style"]
    m = cfg["mark"]
    if st == "smart":
        return ""
    for i in range(12):
        big = i % 3 == 0
        if st == "slim" and not big:
            continue
        r1, r2 = (R - 4, R - (16 if big else 10))
        if st == "roman" and big:
            continue
        x1, y1 = _p(r1, i * 30); x2, y2 = _p(r2, i * 30)
        out.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{m}' "
                   f"stroke-width='{3.2 if big else 1.6}' stroke-linecap='round'/>")
    if st == "roman":
        for label, deg in (("XII", 0), ("III", 90), ("VI", 180), ("IX", 270)):
            x, y = _p(R - 15, deg)
            out.append(f"<text x='{x:.1f}' y='{y + 4:.1f}' font-size='11' font-family='Georgia,serif' font-weight='700' "
                       f"text-anchor='middle' fill='{m}'>{label}</text>")
    return "".join(out)

def watch_svg(collection, strap="Leather", uid="w", animate=True):
    cfg = CFG.get(collection, DEFAULT)
    shape, (cl, cd), (d1, d2) = cfg["shape"], cfg["case"], cfg["dial"]
    hand, m, st = cfg["hand"], cfg["mark"], cfg["style"]
    if shape == "tonneau":   top, bot = 108, 292
    elif shape == "square":  top, bot = 116, 284
    else:                    top, bot = 121, 279
    strap_color = cfg["leather"] if strap == "Leather" else cfg["silicone"]
    defs = (f"<defs><linearGradient id='cg{uid}' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{cl}'/>"
            f"<stop offset='.55' stop-color='{cd}'/><stop offset='1' stop-color='{cl}'/></linearGradient>"
            f"<radialGradient id='dg{uid}' cx='.4' cy='.35' r='.8'><stop offset='0' stop-color='{d1}'/>"
            f"<stop offset='1' stop-color='{d2}'/></radialGradient>"
            f"<linearGradient id='mt{uid}' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='{cd}'/>"
            f"<stop offset='.5' stop-color='{cl}'/><stop offset='1' stop-color='{cd}'/></linearGradient>"
            f"<linearGradient id='sh{uid}' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#000'/>"
            f"<stop offset='.5' stop-color='#fff' stop-opacity='.5'/><stop offset='1' stop-color='#000'/></linearGradient></defs>")
    parts = [defs, _strap(strap, strap_color, top, bot, uid, cl)]
    # crown
    parts.append(f"<rect x='{CX + (80 if shape != 'square' else 72)}' y='{CY - 8}' width='11' height='16' rx='3' fill='url(#cg{uid})'/>")
    if shape == "round":
        parts.append(f"<circle cx='{CX}' cy='{CY}' r='81' fill='url(#cg{uid})'/>")
        parts.append(f"<circle cx='{CX}' cy='{CY}' r='72' fill='none' stroke='rgba(0,0,0,.25)' stroke-width='1.5'/>")
        parts.append(f"<circle cx='{CX}' cy='{CY}' r='67' fill='url(#dg{uid})'/>")
        R = 62
    elif shape == "tonneau":
        parts.append(f"<rect x='52' y='{top - 4}' width='156' height='{bot - top + 8}' rx='54' fill='url(#cg{uid})'/>")
        parts.append(f"<rect x='62' y='{top + 6}' width='136' height='{bot - top - 12}' rx='46' fill='none' stroke='rgba(0,0,0,.25)' stroke-width='1.5'/>")
        parts.append(f"<rect x='67' y='{top + 11}' width='126' height='{bot - top - 22}' rx='42' fill='url(#dg{uid})'/>")
        R = 56
    else:
        parts.append(f"<rect x='56' y='{top - 2}' width='148' height='{bot - top + 4}' rx='34' fill='url(#cg{uid})'/>")
        parts.append(f"<rect x='66' y='{top + 8}' width='128' height='{bot - top - 16}' rx='26' fill='url(#dg{uid})'/>")
        R = 52
    if st == "studs":
        for i in range(12):
            x, y = _p(76.5, i * 30)
            parts.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.6' fill='#fff' opacity='.95'/>")
    parts.append(_ticks(cfg, R))
    if st == "chrono":
        for (x, y) in ((CX, CY - 24), (CX - 30, CY + 14), (CX + 30, CY + 14)):
            parts.append(f"<circle cx='{x}' cy='{y}' r='15' fill='rgba(255,255,255,.06)' stroke='{m}' stroke-width='1.2'/>")
            parts.append(f"<line x1='{x}' y1='{y}' x2='{x + 7}' y2='{y - 8}' stroke='#E5484D' stroke-width='1.6' stroke-linecap='round'/>")
    if st == "open":
        gx, gy = CX, CY + 36
        parts.append(f"<circle cx='{gx}' cy='{gy}' r='19' fill='#05091C' stroke='{m}' stroke-width='1.4'/>")
        spin = " class='gear'" if animate else ""
        spokes = "".join(f"<line x1='{gx}' y1='{gy}' x2='{gx + 13 * math.cos(math.radians(a)):.1f}' y2='{gy + 13 * math.sin(math.radians(a)):.1f}' "
                         f"stroke='{m}' stroke-width='1.6'/>" for a in range(0, 360, 45))
        parts.append(f"<g{spin} style='transform-origin:{gx}px {gy}px'><circle cx='{gx}' cy='{gy}' r='13' fill='none' stroke='{m}' "
                     f"stroke-width='2' stroke-dasharray='3 2.4'/>{spokes}<circle cx='{gx}' cy='{gy}' r='3' fill='{m}'/></g>")
    if st == "smart":
        parts.append(f"<text x='{CX}' y='{CY + 6}' font-size='34' font-family='Arial,sans-serif' font-weight='700' text-anchor='middle' fill='#fff'>10:10</text>")
        parts.append(f"<path d='M{CX - 40} {CY - 38} A44 44 0 0 1 {CX + 40} {CY - 38}' stroke='#5B8DEF' stroke-width='4' fill='none' stroke-linecap='round'/>")
        parts.append(f"<path d='M{CX - 40} {CY + 42} A44 44 0 0 0 {CX + 40} {CY + 42}' stroke='#3DD6A0' stroke-width='4' fill='none' stroke-linecap='round'/>")
        parts.append(f"<text x='{CX}' y='{CY + 30}' font-size='10' font-family='Arial' text-anchor='middle' fill='#9FB4E8'>72 bpm | 6,420 steps</text>")
    else:
        hx, hy = _p(34, 305); mx, my = _p(52, 60)
        parts.append(f"<line x1='{CX}' y1='{CY}' x2='{hx:.1f}' y2='{hy:.1f}' stroke='{hand}' stroke-width='5' stroke-linecap='round'/>")
        parts.append(f"<line x1='{CX}' y1='{CY}' x2='{mx:.1f}' y2='{my:.1f}' stroke='{hand}' stroke-width='3.4' stroke-linecap='round'/>")
        sec_cls = " class='sweep'" if animate else ""
        parts.append(f"<g{sec_cls} style='transform-origin:{CX}px {CY}px'><line x1='{CX}' y1='{CY + 14}' x2='{CX}' y2='{CY - 56}' "
                     f"stroke='#C9A24B' stroke-width='1.5'/><circle cx='{CX}' cy='{CY}' r='4' fill='#C9A24B'/></g>")
        parts.append(f"<circle cx='{CX}' cy='{CY}' r='2.2' fill='#111'/>")
    # glass reflection
    if shape == "round":
        parts.append(f"<path d='M{CX - 56} {CY - 34} A66 66 0 0 1 {CX + 20} {CY - 62} L{CX - 8} {CY - 8} Z' fill='#fff' opacity='.10'/>")
    else:
        parts.append(f"<path d='M70 {top + 14} L190 {top + 14} L140 {CY} L70 {CY - 10} Z' fill='#fff' opacity='.07'/>")
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 260 400' preserveAspectRatio='xMidYMid meet' "
            f"style='width:100%;height:100%'>{''.join(parts)}</svg>")
