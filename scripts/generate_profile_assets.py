#!/usr/bin/env python3
"""Generate the reproducible SVG system used by the SergiGTAr profile README."""

from __future__ import annotations

import base64
import io
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
AVATAR = ASSETS / "cybersec-avatar.png"
MONO_BOLD = Path("C:/Windows/Fonts/consolab.ttf")

NOW = datetime.now()
MONTH_TAG = f"{NOW.strftime('%b').upper()}.{NOW.year}"
REFRESH_TAG = f"{NOW.strftime('%B').upper()} {NOW.day}, {NOW.year}"


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    bg2: str
    panel: str
    panel2: str
    fg: str
    muted: str
    accent: str
    accent2: str
    warn: str
    line: str
    grid: str
    shadow: str


DARK = Palette(
    "dark", "#010503", "#03150A", "#041B0D", "#082817", "#E5FFEE",
    "#7DCB98", "#00FF66", "#6DFFA6", "#FFCA55", "#1D9D53", "#0B3F23", "#000000"
)
LIGHT = Palette(
    "light", "#F4F1DF", "#E7ECD8", "#EEF2E3", "#DCE8D5", "#102C1E",
    "#416C55", "#007A3D", "#009B50", "#9A6200", "#4E8B67", "#B7CDBB", "#C3CEBE"
)


def esc(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def cut_path(x: float, y: float, w: float, h: float, cut: float) -> str:
    return (
        f"M{x + cut},{y} H{x + w - cut} L{x + w},{y + cut} "
        f"V{y + h - cut} L{x + w - cut},{y + h} H{x + cut} "
        f"L{x},{y + h - cut} V{y + cut} Z"
    )


def contrast(hex_a: str, hex_b: str) -> float:
    def luminance(value: str) -> float:
        rgb = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    a, b = luminance(hex_a), luminance(hex_b)
    return round((max(a, b) + 0.05) / (min(a, b) + 0.05), 2)


def fitted_size(text: str, max_width: int, maximum: int, minimum: int = 12) -> int:
    if not MONO_BOLD.exists():
        return maximum
    lo, hi = minimum, maximum
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = ImageFont.truetype(str(MONO_BOLD), mid)
        width = font.getbbox(text)[2]
        if width <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return lo


def avatar_data_uri() -> str:
    image = Image.open(AVATAR).convert("RGB")
    image.thumbnail((420, 420), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90, optimize=True, progressive=True, subsampling=0)
    return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def waveform(x0: float, y0: float, width: float, amplitude: float, points: int = 180) -> str:
    coords = []
    for index in range(points):
        t = index / (points - 1)
        envelope = 0.34 + 0.66 * math.sin(math.pi * t) ** 2
        signal = (
            math.sin(t * math.tau * 6.0)
            + 0.42 * math.sin(t * math.tau * 15.0 + 0.7)
            + 0.18 * math.sin(t * math.tau * 31.0 + 1.1)
        )
        coords.append(f"{x0 + t * width:.1f},{y0 + signal * amplitude * envelope:.1f}")
    return " ".join(coords)


def wave_path(points: str) -> str:
    """Convert waveform polyline points into an animateMotion path."""
    return "M" + points.replace(" ", " L")


def svg_defs(p: Palette, uid: str, portrait_uri: str | None = None) -> str:
    portrait = ""
    if portrait_uri:
        portrait = (
            f'<clipPath id="portrait-{uid}"><path d="{cut_path(866, 142, 240, 250, 28)}"/></clipPath>'
        )
    portrait_block = f"      {portrait}\n" if portrait else ""
    return f"""
    <defs>
      <linearGradient id="bg-{uid}" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="{p.bg}"/>
        <stop offset="0.55" stop-color="{p.bg2}"/>
        <stop offset="1" stop-color="{p.bg}"/>
      </linearGradient>
      <radialGradient id="radar-{uid}" cx="50%" cy="50%" r="58%">
        <stop offset="0" stop-color="{p.accent}" stop-opacity=".16"/>
        <stop offset=".55" stop-color="{p.accent}" stop-opacity=".04"/>
        <stop offset="1" stop-color="{p.accent}" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="sweep-{uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{p.accent}" stop-opacity="0"/>
        <stop offset=".5" stop-color="{p.accent}" stop-opacity=".25"/>
        <stop offset="1" stop-color="{p.accent}" stop-opacity="0"/>
      </linearGradient>
      <pattern id="grid-{uid}" width="30" height="30" patternUnits="userSpaceOnUse">
        <path d="M30 0H0V30" fill="none" stroke="{p.grid}" stroke-width="1" opacity=".55"/>
      </pattern>
      <pattern id="scan-{uid}" width="4" height="4" patternUnits="userSpaceOnUse">
        <path d="M0 3.5H4" stroke="{p.shadow}" stroke-width="1" opacity=".20"/>
      </pattern>
      <filter id="glow-{uid}" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="4" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="soft-{uid}" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="1.4"/>
      </filter>
{portrait_block}    </defs>
    <style>
      .mono {{ font-family: Consolas, "SFMono-Regular", Menlo, monospace; }}
      .label {{ font-size: 15px; font-weight: 700; letter-spacing: 3px; }}
      .micro {{ font-size: 12px; font-weight: 700; letter-spacing: 1.8px; }}
      .body {{ font-size: 17px; letter-spacing: .5px; }}
      .scan-sweep {{ animation: scan-{uid} 8s linear infinite; }}
      .pulse {{ animation: pulse-{uid} 3.4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
      .blink {{ animation: blink-{uid} 1.05s steps(1) infinite; }}
      .flow {{ stroke-dasharray: 12 8; animation: flow-{uid} 2.8s linear infinite; }}
      .radar-sweep {{ animation: rotate-{uid} 5.5s linear infinite; transform-box: fill-box; transform-origin: center; }}
      .glitch {{ animation: glitch-{uid} 7s steps(1) infinite; }}
      .boot-1 {{ animation: boot-{uid} .4s .10s both; }}
      .boot-2 {{ animation: boot-{uid} .4s .35s both; }}
      .boot-3 {{ animation: boot-{uid} .4s .60s both; }}
      .boot-4 {{ animation: boot-{uid} .4s .85s both; }}
      @keyframes scan-{uid} {{ from {{ transform: translateY(-90px); }} to {{ transform: translateY(690px); }} }}
      @keyframes pulse-{uid} {{ 0%,100% {{ opacity:.28; transform:scale(.94); }} 50% {{ opacity:.9; transform:scale(1.04); }} }}
      @keyframes blink-{uid} {{ 0%,48% {{ opacity:1; }} 49%,100% {{ opacity:0; }} }}
      @keyframes flow-{uid} {{ to {{ stroke-dashoffset:-40; }} }}
      @keyframes rotate-{uid} {{ to {{ transform:rotate(360deg); }} }}
      @keyframes glitch-{uid} {{ 0%,92%,96%,100% {{ transform:translate(0); }} 93% {{ transform:translate(2px,-1px); }} 94% {{ transform:translate(-2px,1px); }} 95% {{ transform:translate(1px,0); }} }}
      @keyframes boot-{uid} {{ from {{ opacity:0; transform:translateX(-10px); }} to {{ opacity:1; transform:translateX(0); }} }}
      @media (prefers-reduced-motion: reduce) {{ .scan-sweep,.pulse,.blink,.flow,.radar-sweep,.glitch,.boot-1,.boot-2,.boot-3,.boot-4 {{ animation:none!important; opacity:1!important; transform:none!important; }} .motion-ball {{ display:none; }} }}
    </style>
    """


def universal_hero_svg(p: Palette, portrait_uri: str) -> str:
    uid = f"universal-hero-{p.name}"
    security_size = fitted_size("SECURITY-FIRST", 405, 53)
    engineering_size = fitted_size("ENGINEERING", 390, 64)
    wave = waveform(34, 695, 650, 12, 130)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="760" viewBox="0 0 720 760" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr tactical security terminal</title>
  <desc id="desc-{uid}">Responsive Pip-Boy inspired profile terminal with operator portrait, security-first engineering mission and live system modules.</desc>
  {svg_defs(p, uid)}
  <defs><clipPath id="portrait-{uid}"><path d="{cut_path(487, 87, 188, 207, 22)}"/></clipPath></defs>
  <rect width="720" height="760" fill="url(#bg-{uid})"/>
  <rect width="720" height="760" fill="url(#grid-{uid})" opacity=".38"/>
  <path d="{cut_path(8, 8, 704, 744, 24)}" fill="{p.panel}" stroke="{p.accent}" stroke-width="3"/>
  <path d="{cut_path(22, 22, 676, 716, 18)}" fill="none" stroke="{p.line}" stroke-width="1.5"/>
  <path d="M22 62H698M22 330H698M22 650H698" stroke="{p.line}"/>
  <g class="mono">
    <text x="36" y="44" class="label" fill="{p.accent}">◆ SERGIGTAR OS // PUBLIC NODE</text>
    <text x="684" y="44" text-anchor="end" class="micro" fill="{p.muted}">{MONTH_TAG}</text>
    <text x="38" y="96" class="micro" fill="{p.warn}">SYS://SECURITY_OPERATOR</text>
    <text x="34" y="157" fill="{p.fg}" font-size="{security_size}" font-weight="800" letter-spacing="1">SECURITY-FIRST</text>
    <text x="34" y="220" fill="{p.accent}" font-size="{engineering_size}" font-weight="800" letter-spacing="2" class="glitch" filter="url(#glow-{uid})">ENGINEERING</text>
    <path d="M36 237H438" stroke="{p.accent}" stroke-width="3"/>
    <g class="body">
      <g class="boot-1"><text x="38" y="270" fill="{p.accent}">[OK]</text><text x="92" y="270" fill="{p.fg}">trust mapped</text></g>
      <g class="boot-2"><text x="38" y="300" fill="{p.accent}">[OK]</text><text x="92" y="300" fill="{p.fg}">defaults hardened</text></g>
    </g>
  </g>
  <g>
    <circle cx="581" cy="190" r="110" fill="url(#radar-{uid})" stroke="{p.grid}"/>
    <g class="radar-sweep" style="transform-box: view-box; transform-origin: 581px 190px"><path d="M581 190L581 76A114 114 0 0 1 662 109Z" fill="{p.accent}" opacity=".12"/><path d="M581 190V76" stroke="{p.accent}" stroke-width="2"/></g>
    <image href="{portrait_uri}" x="480" y="80" width="202" height="222" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait-{uid})"/>
    <path d="{cut_path(487, 87, 188, 207, 22)}" fill="none" stroke="{p.accent}" stroke-width="3"/>
    <path d="M581 72V308M463 190H699" stroke="{p.line}" opacity=".38"/>
  </g>
  <g class="mono">
    <text x="36" y="365" class="label" fill="{p.warn}">ACTIVE SYSTEMS // 04</text>
    <g class="body">
      <path d="{cut_path(34, 390, 316, 102, 14)}" fill="{p.bg}" fill-opacity=".45" stroke="{p.line}"/>
      <text x="55" y="425" class="micro" fill="{p.muted}">APPSEC</text><text x="55" y="463" fill="{p.accent}">ACTIVE</text>
      <text x="198" y="425" class="micro" fill="{p.muted}">PRIVACY</text><text x="198" y="463" fill="{p.accent}">ENFORCED</text>
      <path d="{cut_path(370, 390, 316, 102, 14)}" fill="{p.bg}" fill-opacity=".45" stroke="{p.line}"/>
      <text x="391" y="425" class="micro" fill="{p.muted}">RESEARCH</text><text x="391" y="463" fill="{p.warn}">ONGOING</text>
      <text x="534" y="425" class="micro" fill="{p.muted}">UPLINK</text><text x="534" y="463" fill="{p.accent}">READY</text>
      <path d="{cut_path(34, 512, 652, 108, 14)}" fill="{p.bg}" fill-opacity=".45" stroke="{p.line}"/>
      <text x="55" y="550" class="micro" fill="{p.muted}">COMMAND</text>
      <text x="55" y="588" fill="{p.fg}" font-size="20">&gt; build --harden --verify</text>
      <rect class="blink" x="356" y="568" width="12" height="22" fill="{p.accent}"/>
      <text x="656" y="550" text-anchor="end" class="micro" fill="{p.muted}">OPERATOR</text>
      <text x="656" y="588" text-anchor="end" fill="{p.accent}" font-size="18">SGT-06 // AUTH</text>
    </g>
  </g>
  <polyline points="{wave}" fill="none" stroke="{p.accent}" stroke-width="2" class="flow"/>
  <g class="motion-ball"><circle r="5" fill="{p.warn}"><animateMotion dur="3s" repeatCount="indefinite" path="{wave_path(wave)}"/></circle></g>
  <g class="mono micro"><text x="34" y="731" fill="{p.muted}">VERIFY BEFORE TRUST</text><text x="686" y="731" text-anchor="end" fill="{p.accent}">SERGIGTAR.DEV // ENTER</text></g>
  <rect class="scan-sweep" x="22" y="-30" width="676" height="90" fill="url(#sweep-{uid})" opacity=".45"/>
  <rect width="720" height="760" fill="url(#scan-{uid})" opacity=".25" pointer-events="none"/>
</svg>
"""


def universal_systems_svg(p: Palette) -> str:
    uid = f"universal-systems-{p.name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="850" viewBox="0 0 720 850" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr active system map</title>
  <desc id="desc-{uid}">Responsive readout of cybersecurity focus, engineering tools and the responsible open-source protocol.</desc>
  {svg_defs(p, uid)}
  <rect width="720" height="850" fill="url(#bg-{uid})"/><rect width="720" height="850" fill="url(#grid-{uid})" opacity=".3"/>
  <path d="{cut_path(8, 8, 704, 834, 24)}" fill="none" stroke="{p.accent}" stroke-width="3"/>
  <g class="mono"><text x="32" y="52" class="label" fill="{p.accent}">◆ ACTIVE MODULES // SYSTEM MAP</text><circle class="pulse" cx="600" cy="46" r="4" fill="{p.accent}"/><text x="612" y="52" class="micro" fill="{p.muted}">03 ONLINE</text></g>
  <g>
    <path d="{cut_path(24, 76, 672, 226, 18)}" fill="{p.panel}" stroke="{p.line}" stroke-width="1.5"/>
    <path d="{cut_path(24, 318, 672, 226, 18)}" fill="{p.panel}" stroke="{p.line}" stroke-width="1.5"/>
    <path d="{cut_path(24, 560, 672, 226, 18)}" fill="{p.panel}" stroke="{p.line}" stroke-width="1.5"/>
  </g>
  <g class="mono">
    <text x="50" y="116" class="label" fill="{p.warn}">01 // SECURITY TRACK</text><text x="50" y="145" class="micro" fill="{p.muted}">CURRENT VECTOR</text>
    <g class="body" fill="{p.fg}"><text x="50" y="184">◆ application security</text><text x="50" y="218">◆ secure architecture</text><text x="50" y="252">◆ privacy-aware engineering</text><text x="385" y="184">◆ defensive automation</text><text x="385" y="218">◆ threat-aware development</text><text x="385" y="252">◆ reproducible research</text></g>
    <text x="50" y="358" class="label" fill="{p.warn}">02 // ENGINEERING CORE</text><text x="50" y="387" class="micro" fill="{p.muted}">INTEROPERABLE TOOLCHAIN</text>
    <g class="body"><text x="50" y="430" fill="{p.accent}">.NET / C#</text><text x="235" y="430" fill="{p.fg}">PYTHON</text><text x="420" y="430" fill="{p.accent}">TYPESCRIPT</text><text x="50" y="478" fill="{p.fg}">KOTLIN</text><text x="235" y="478" fill="{p.accent}">SQL</text><text x="420" y="478" fill="{p.fg}">DOCKER / AZURE</text></g>
    <path d="M50 448H670" stroke="{p.line}" opacity=".5"/>
    <text x="50" y="600" class="label" fill="{p.warn}">03 // OSS PROTOCOL</text><text x="50" y="629" class="micro" fill="{p.muted}">LEAVE A SAFE TRAIL</text>
    <g class="body"><text x="50" y="675" fill="{p.accent}">01</text><text x="102" y="675" fill="{p.fg}">REPRODUCE</text><text x="370" y="675" fill="{p.accent}">02</text><text x="422" y="675" fill="{p.fg}">SANITISE</text><text x="50" y="727" fill="{p.accent}">03</text><text x="102" y="727" fill="{p.fg}">DOCUMENT</text><text x="370" y="727" fill="{p.accent}">04</text><text x="422" y="727" fill="{p.fg}">IMPROVE</text></g>
  </g>
  <g class="mono micro"><text x="28" y="821" fill="{p.muted}">ASSUME LESS · EVIDENCE &gt; VIBES</text><text x="692" y="821" text-anchor="end" fill="{p.accent}">SECURE BY DEFAULT</text></g>
  <rect class="scan-sweep" x="10" y="-40" width="700" height="80" fill="url(#sweep-{uid})" opacity=".35"/><rect width="720" height="850" fill="url(#scan-{uid})" opacity=".2"/>
</svg>
"""


def universal_brief_svg(p: Palette) -> str:
    uid = f"universal-brief-{p.name}"
    chips = [
        ("CLEAR TRUST BOUNDARIES", 32, 236),
        ("SECURE DEFAULTS", 284, 148),
        ("REPRODUCIBLE EVIDENCE", 448, 210),
    ]
    chip_markup = "".join(
        f'<path d="{cut_path(x, 226, w, 42, 8)}" fill="none" stroke="{p.line}" stroke-width="1.5"/>'
        f'<text x="{x + w / 2}" y="252" text-anchor="middle" font-size="15" font-weight="700" letter-spacing="1" fill="{p.accent}">{label}</text>'
        for label, x, w in chips
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="300" viewBox="0 0 720 300" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr operator brief</title>
  <desc id="desc-{uid}">Security-first software engineer: clear trust boundaries, secure defaults and reproducible evidence.</desc>
  {svg_defs(p, uid)}
  <rect width="720" height="300" fill="url(#bg-{uid})"/><rect width="720" height="300" fill="url(#grid-{uid})" opacity=".3"/>
  <path d="{cut_path(8, 8, 704, 284, 24)}" fill="none" stroke="{p.accent}" stroke-width="3"/>
  <g class="mono">
    <text x="32" y="52" class="label" fill="{p.accent}">◆ SYS://OPERATOR_BRIEF</text>
    <text x="688" y="52" text-anchor="end" class="micro" fill="{p.muted}">AUTH: OPERATOR</text>
    <text x="32" y="108" font-size="19" fill="{p.fg}">Software engineer moving deeper into cybersecurity,</text>
    <text x="32" y="140" font-size="19" fill="{p.fg}">combining a security-first mindset with product-aware</text>
    <text x="32" y="172" font-size="19" fill="{p.fg}">engineering and systems that remain understandable</text>
    <text x="32" y="204" font-size="19" fill="{p.fg}">under pressure.</text>
    <rect class="blink" x="189" y="186" width="10" height="18" fill="{p.accent}"/>
  </g>
  {chip_markup}
  <rect class="scan-sweep" x="10" y="-40" width="700" height="80" fill="url(#sweep-{uid})" opacity=".35"/>
  <rect width="720" height="300" fill="url(#scan-{uid})" opacity=".2" pointer-events="none"/>
</svg>
"""


def universal_nav_svg(p: Palette, kind: str, code: str, title: str) -> str:
    uid = f"universal-nav-{kind}-{p.name}"
    glyph = {"portfolio": "⌁", "linkedin": "in", "orcid": "iD"}[kind]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="140" viewBox="0 0 360 140" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">{esc(title)}</title><desc id="desc-{uid}">Responsive navigation control for {esc(title)}.</desc>
  {svg_defs(p, uid)}
  <path d="{cut_path(4, 4, 352, 132, 14)}" fill="{p.panel}" stroke="{p.accent}" stroke-width="2"/>
  <circle cx="58" cy="70" r="34" fill="none" stroke="{p.line}" stroke-width="2"/><text x="58" y="81" text-anchor="middle" class="mono" font-size="29" font-weight="800" fill="{p.accent}">{glyph}</text>
  <g class="mono"><text x="108" y="46" class="micro" fill="{p.muted}">{esc(code)}</text><text x="108" y="82" font-size="26" font-weight="800" letter-spacing="1" fill="{p.fg}">{esc(title)}</text></g>
  <circle class="pulse" cx="290" cy="32" r="4" fill="{p.accent}"/><text x="302" y="36" class="micro" fill="{p.muted}">ONLINE</text>
  <path d="M322 56L338 70 322 84" fill="none" stroke="{p.accent}" stroke-width="3" class="pulse"/>
  <path d="{cut_path(4, 4, 352, 132, 14)}" fill="none" stroke="{p.accent2}" stroke-width="2" stroke-dasharray="60 320" class="flow"/>
</svg>
"""


def universal_footer_svg(p: Palette) -> str:
    uid = f"universal-footer-{p.name}"
    wave = waveform(34, 92, 652, 11, 130)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="180" viewBox="0 0 720 180" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr public profile status</title><desc id="desc-{uid}">Public profile online: learn, build, harden, share and disclose responsibly.</desc>
  {svg_defs(p, uid)}
  <path d="{cut_path(8, 8, 704, 164, 20)}" fill="{p.panel}" stroke="{p.line}" stroke-width="2"/>
  <g class="mono"><text x="34" y="42" class="micro" fill="{p.muted}">PUBLIC PROFILE // STATUS ONLINE</text><text x="34" y="72" font-size="20" font-weight="800" letter-spacing="2" fill="{p.accent}">LEARN · BUILD · HARDEN · SHARE</text></g>
  <polyline points="{wave}" fill="none" stroke="{p.accent}" stroke-width="2" class="flow"/><g class="motion-ball"><circle r="5" fill="{p.warn}"><animateMotion dur="3.2s" repeatCount="indefinite" path="{wave_path(wave)}"/></circle></g>
  <g class="mono"><text x="34" y="135" class="micro" fill="{p.muted}">SANITISED PUBLIC OUTPUT</text><text x="686" y="135" text-anchor="end" font-size="16" font-weight="800" letter-spacing="2" fill="{p.fg}">DISCLOSE RESPONSIBLY</text><text x="686" y="158" text-anchor="end" class="micro" fill="{p.accent}">NO TRACKERS // NO VIEW COUNTERS</text></g>
</svg>
"""


def validate_svg(path: Path) -> dict[str, object]:
    tree = ET.parse(path)
    root = tree.getroot()
    xml = path.read_text(encoding="utf-8")
    forbidden = [name for name in ("<script", "<foreignObject", "javascript:") if name in xml]
    external_links = [token for token in ("http://", "https://") if token in xml.replace("http://www.w3.org/2000/svg", "")]
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "width": root.attrib.get("width"),
        "height": root.attrib.get("height"),
        "title": "<title" in xml,
        "desc": "<desc" in xml,
        "forbidden": forbidden,
        "external_links": external_links,
    }


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    portrait_uri = avatar_data_uri()
    generated: dict[str, str] = {}
    for palette in (DARK, LIGHT):
        # GitHub's live themed-picture element preserves colour-scheme sources but
        # discards width conditions. A single tall composition therefore scales
        # reliably in both the desktop README column and the mobile profile view.
        generated[f"pipboy-terminal-{palette.name}.svg"] = universal_hero_svg(palette, portrait_uri)
        generated[f"operator-brief-{palette.name}.svg"] = universal_brief_svg(palette)
        generated[f"systems-map-{palette.name}.svg"] = universal_systems_svg(palette)
        generated[f"nav-portfolio-{palette.name}.svg"] = universal_nav_svg(palette, "portfolio", "UPLINK // 01", "PORTFOLIO")
        generated[f"nav-linkedin-{palette.name}.svg"] = universal_nav_svg(palette, "linkedin", "CHANNEL // 02", "LINKEDIN")
        generated[f"nav-orcid-{palette.name}.svg"] = universal_nav_svg(palette, "orcid", "IDENTITY // 03", "ORCID")
        generated[f"footer-status-{palette.name}.svg"] = universal_footer_svg(palette)

    for name, contents in generated.items():
        (ASSETS / name).write_text(contents, encoding="utf-8", newline="\n")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    updated = re.sub(r"LAST REFRESH: [A-Z]+(?: \d{1,2},)? \d{4}", f"LAST REFRESH: {REFRESH_TAG}", text)
    if updated != text:
        readme.write_text(updated, encoding="utf-8", newline="\n")

    metrics = {
        "palette_contrast": {
            palette.name: {
                "fg_on_bg": contrast(palette.fg, palette.bg),
                "accent_on_bg": contrast(palette.accent, palette.bg),
                "muted_on_bg": contrast(palette.muted, palette.bg),
            }
            for palette in (DARK, LIGHT)
        },
        "portrait_embedded_bytes": len(base64.b64decode(portrait_uri.split(",", 1)[1])),
        "assets": [validate_svg(ASSETS / name) for name in sorted(generated)],
    }
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
