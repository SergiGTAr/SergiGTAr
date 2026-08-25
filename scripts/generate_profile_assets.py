#!/usr/bin/env python3
"""Generate the reproducible SVG system used by the SergiGTAr profile README."""

from __future__ import annotations

import base64
import io
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
AVATAR = ASSETS / "cybersec-avatar.png"
WIDTH = 1200
MONO = Path("C:/Windows/Fonts/consola.ttf")
MONO_BOLD = Path("C:/Windows/Fonts/consolab.ttf")


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


def texture_points(seed: int, count: int, width: int, height: int, color: str) -> str:
    rng = random.Random(seed)
    points = []
    for _ in range(count):
        x, y = rng.randrange(width), rng.randrange(height)
        radius = rng.choice((0.45, 0.55, 0.7, 0.9))
        opacity = rng.uniform(0.08, 0.30)
        points.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" opacity="{opacity:.2f}"/>')
    return "".join(points)


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


def ticks(cx: float, cy: float, r1: float, r2: float, count: int, color: str) -> str:
    lines = []
    for i in range(count):
        angle = math.tau * i / count - math.pi / 2
        a = (cx + math.cos(angle) * r1, cy + math.sin(angle) * r1)
        b = (cx + math.cos(angle) * r2, cy + math.sin(angle) * r2)
        opacity = 0.85 if i % 4 == 0 else 0.35
        lines.append(
            f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
            f'stroke="{color}" stroke-width="{2 if i % 4 == 0 else 1}" opacity="{opacity}"/>'
        )
    return "".join(lines)


def svg_defs(p: Palette, uid: str, portrait_uri: str | None = None) -> str:
    portrait = ""
    if portrait_uri:
        portrait = (
            f'<clipPath id="portrait-{uid}"><path d="{cut_path(866, 142, 240, 250, 28)}"/></clipPath>'
        )
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
      {portrait}
    </defs>
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
      @media (prefers-reduced-motion: reduce) {{ .scan-sweep,.pulse,.blink,.flow,.radar-sweep,.glitch,.boot-1,.boot-2,.boot-3,.boot-4 {{ animation:none!important; opacity:1!important; transform:none!important; }} }}
    </style>
    """


def hero_svg(p: Palette, portrait_uri: str) -> str:
    uid = f"hero-{p.name}"
    security_size = fitted_size("SECURITY-FIRST", 760, 77)
    engineering_size = fitted_size("ENGINEERING", 760, 92)
    frame = cut_path(8, 8, 1184, 604, 30)
    inner = cut_path(27, 27, 1146, 566, 22)
    wave = waveform(60, 548, 760, 10)
    particles = texture_points(20260825, 115, 1200, 620, p.accent)
    tick_marks = ticks(986, 268, 142, 152, 48, p.accent)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr tactical security engineering terminal</title>
  <desc id="desc-{uid}">Pip-Boy inspired public profile terminal for a security-first software engineer, with operator portrait, secure engineering principles and a portfolio uplink.</desc>
  {svg_defs(p, uid, portrait_uri)}
  <rect width="1200" height="620" fill="url(#bg-{uid})"/>
  <rect width="1200" height="620" fill="url(#grid-{uid})" opacity=".46"/>
  <g>{particles}</g>
  <path d="{frame}" fill="{p.panel}" stroke="{p.accent}" stroke-width="3"/>
  <path d="{inner}" fill="none" stroke="{p.line}" stroke-width="1.5" opacity=".85"/>
  <path d="M28 72H1172 M28 492H1172" stroke="{p.line}" stroke-width="1.5"/>
  <path d="M54 83H784V468H54Z" fill="{p.bg}" fill-opacity=".58" stroke="{p.line}"/>
  <path d="{cut_path(804, 83, 342, 385, 18)}" fill="url(#radar-{uid})" stroke="{p.line}" stroke-width="1.5"/>
  <g class="mono label" fill="{p.accent}">
    <text x="56" y="55">◆ SERGIGTAR OS // TACTICAL SECURITY TERMINAL</text>
    <text x="1144" y="55" text-anchor="end">PUBLIC NODE · AUG.2026</text>
  </g>
  <g class="mono">
    <text x="78" y="117" fill="{p.warn}" class="label">SYS://OPERATOR_PROFILE</text>
    <text x="78" y="151" fill="{p.muted}" class="micro">IDENTITY VERIFIED // UPLINK STABLE // MODE: SECURITY-FIRST</text>
    <text x="72" y="226" fill="{p.fg}" font-size="{security_size}" font-weight="800" letter-spacing="2">SECURITY-FIRST</text>
    <text x="72" y="310" fill="{p.accent}" font-size="{engineering_size}" font-weight="800" letter-spacing="6" filter="url(#glow-{uid})" class="glitch">ENGINEERING</text>
    <path d="M76 329H748" stroke="{p.accent}" stroke-width="3"/>
    <path d="M76 336H426" stroke="{p.line}"/>
    <g class="body">
      <g class="boot-1"><text x="78" y="374" fill="{p.accent}">[OK]</text><text x="132" y="374" fill="{p.fg}">trust boundaries mapped</text></g>
      <g class="boot-2"><text x="78" y="405" fill="{p.accent}">[OK]</text><text x="132" y="405" fill="{p.fg}">secure defaults armed</text></g>
      <g class="boot-3"><text x="78" y="436" fill="{p.accent}">[OK]</text><text x="132" y="436" fill="{p.fg}">evidence pipeline live</text></g>
      <text x="438" y="374" fill="{p.muted}">APPSEC</text><text x="548" y="374" fill="{p.accent}">ACTIVE</text>
      <text x="438" y="405" fill="{p.muted}">PRIVACY</text><text x="548" y="405" fill="{p.accent}">ENFORCED</text>
      <text x="438" y="436" fill="{p.muted}">RESEARCH</text><text x="548" y="436" fill="{p.warn}">ONGOING</text>
      <g class="boot-4"><text x="78" y="463" fill="{p.fg}">&gt; build --harden --verify</text><rect class="blink" x="350" y="447" width="11" height="20" fill="{p.accent}"/></g>
    </g>
  </g>
  <g>
    <circle cx="986" cy="268" r="157" fill="none" stroke="{p.grid}" stroke-width="1"/>
    <circle class="pulse" cx="986" cy="268" r="142" fill="none" stroke="{p.accent}" stroke-width="2" opacity=".5"/>
    {tick_marks}
    <path d="M826 268H1146M986 108V428" stroke="{p.line}" opacity=".45"/>
    <path d="M843 176L1128 360M843 360L1128 176" stroke="{p.grid}" opacity=".38"/>
    <g class="radar-sweep" opacity=".65">
      <path d="M986 268L986 116A152 152 0 0 1 1093 160Z" fill="{p.accent}" opacity=".10"/>
      <path d="M986 268L986 116" stroke="{p.accent}" stroke-width="2" filter="url(#glow-{uid})"/>
    </g>
    <image href="{portrait_uri}" x="858" y="134" width="256" height="256" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait-{uid})"/>
    <path d="{cut_path(866, 142, 240, 250, 28)}" fill="none" stroke="{p.accent}" stroke-width="3"/>
    <path d="{cut_path(877, 153, 218, 228, 20)}" fill="none" stroke="{p.accent2}" stroke-width="1" opacity=".75"/>
    <rect x="866" y="142" width="240" height="250" fill="url(#scan-{uid})" clip-path="url(#portrait-{uid})" opacity=".5"/>
    <g class="mono" text-anchor="middle">
      <text x="986" y="420" class="label" fill="{p.fg}">SERGIGTAR // SGT-08</text>
      <text x="986" y="444" class="micro" fill="{p.accent}">OPERATOR LINK: AUTHENTICATED</text>
    </g>
  </g>
  <g class="mono">
    <polyline points="{wave}" fill="none" stroke="{p.accent}" stroke-width="2" class="flow"/>
    <circle r="4" fill="{p.warn}" filter="url(#glow-{uid})"><animateMotion dur="3.2s" repeatCount="indefinite" path="M60 548 H812"/></circle>
    <text x="838" y="531" class="micro" fill="{p.muted}">PORTFOLIO UPLINK</text>
    <text x="838" y="557" class="label" fill="{p.accent}">SERGIGTAR.DEV</text>
    <text x="1140" y="531" text-anchor="end" class="micro" fill="{p.muted}">CHANNEL</text>
    <text x="1140" y="557" text-anchor="end" font-size="13" font-weight="700" letter-spacing="2" fill="{p.warn}">OPEN // ENTER</text>
    <text x="56" y="596" class="micro" fill="{p.muted}">VERIFY BEFORE TRUST</text>
    <text x="600" y="596" text-anchor="middle" class="micro" fill="{p.accent}">セキュリティ端末 // SECURITY CONSOLE</text>
    <text x="1144" y="596" text-anchor="end" class="micro" fill="{p.muted}">NO TRACKERS · NO VIEW COUNTERS</text>
  </g>
  <rect class="scan-sweep" x="28" y="0" width="1144" height="90" fill="url(#sweep-{uid})" opacity=".5" pointer-events="none"/>
  <rect width="1200" height="620" fill="url(#scan-{uid})" opacity=".30" pointer-events="none"/>
  <g fill="{p.accent}"><circle cx="32" cy="32" r="4"/><circle cx="1168" cy="32" r="4"/><circle cx="32" cy="588" r="4"/><circle cx="1168" cy="588" r="4"/></g>
</svg>
"""


def mobile_hero_svg(p: Palette, portrait_uri: str) -> str:
    uid = f"mobile-hero-{p.name}"
    security_size = fitted_size("SECURITY-FIRST", 405, 53)
    engineering_size = fitted_size("ENGINEERING", 405, 64)
    wave = waveform(34, 695, 650, 12, 130)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="760" viewBox="0 0 720 760" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr mobile tactical security terminal</title>
  <desc id="desc-{uid}">Mobile Pip-Boy inspired profile terminal with operator portrait, security-first engineering mission and live system modules.</desc>
  {svg_defs(p, uid)}
  <defs><clipPath id="portrait-{uid}"><path d="{cut_path(487, 87, 188, 207, 22)}"/></clipPath></defs>
  <rect width="720" height="760" fill="url(#bg-{uid})"/>
  <rect width="720" height="760" fill="url(#grid-{uid})" opacity=".38"/>
  <path d="{cut_path(8, 8, 704, 744, 24)}" fill="{p.panel}" stroke="{p.accent}" stroke-width="3"/>
  <path d="{cut_path(22, 22, 676, 716, 18)}" fill="none" stroke="{p.line}" stroke-width="1.5"/>
  <path d="M22 62H698M22 330H698M22 650H698" stroke="{p.line}"/>
  <g class="mono">
    <text x="36" y="44" class="label" fill="{p.accent}">◆ SERGIGTAR OS // MOBILE NODE</text>
    <text x="684" y="44" text-anchor="end" class="micro" fill="{p.muted}">AUG.2026</text>
    <text x="38" y="96" class="micro" fill="{p.warn}">SYS://SECURITY_OPERATOR</text>
    <text x="34" y="157" fill="{p.fg}" font-size="{security_size}" font-weight="800" letter-spacing="1">SECURITY-FIRST</text>
    <text x="34" y="220" fill="{p.accent}" font-size="{engineering_size}" font-weight="800" letter-spacing="4" class="glitch" filter="url(#glow-{uid})">ENGINEERING</text>
    <path d="M36 237H438" stroke="{p.accent}" stroke-width="3"/>
    <g class="body">
      <g class="boot-1"><text x="38" y="270" fill="{p.accent}">[OK]</text><text x="92" y="270" fill="{p.fg}">trust mapped</text></g>
      <g class="boot-2"><text x="38" y="300" fill="{p.accent}">[OK]</text><text x="92" y="300" fill="{p.fg}">defaults hardened</text></g>
    </g>
  </g>
  <g>
    <circle cx="581" cy="190" r="110" fill="url(#radar-{uid})" stroke="{p.grid}"/>
    <g class="radar-sweep"><path d="M581 190L581 76A114 114 0 0 1 662 109Z" fill="{p.accent}" opacity=".12"/><path d="M581 190V76" stroke="{p.accent}" stroke-width="2"/></g>
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
      <text x="656" y="588" text-anchor="end" fill="{p.accent}" font-size="18">SGT-08 // AUTH</text>
    </g>
  </g>
  <polyline points="{wave}" fill="none" stroke="{p.accent}" stroke-width="2" class="flow"/>
  <circle r="5" fill="{p.warn}"><animateMotion dur="3s" repeatCount="indefinite" path="M34 695 H684"/></circle>
  <g class="mono micro"><text x="34" y="731" fill="{p.muted}">VERIFY BEFORE TRUST</text><text x="686" y="731" text-anchor="end" fill="{p.accent}">SERGIGTAR.DEV // ENTER</text></g>
  <rect class="scan-sweep" x="22" y="-30" width="676" height="90" fill="url(#sweep-{uid})" opacity=".45"/>
  <rect width="720" height="760" fill="url(#scan-{uid})" opacity=".25" pointer-events="none"/>
</svg>
"""


def mobile_systems_svg(p: Palette) -> str:
    uid = f"mobile-systems-{p.name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="850" viewBox="0 0 720 850" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr mobile active system map</title>
  <desc id="desc-{uid}">Large mobile readout of cybersecurity focus, engineering tools and the responsible open-source protocol.</desc>
  {svg_defs(p, uid)}
  <rect width="720" height="850" fill="url(#bg-{uid})"/><rect width="720" height="850" fill="url(#grid-{uid})" opacity=".3"/>
  <path d="{cut_path(8, 8, 704, 834, 24)}" fill="none" stroke="{p.accent}" stroke-width="3"/>
  <g class="mono"><text x="32" y="52" class="label" fill="{p.accent}">◆ ACTIVE MODULES // MOBILE MAP</text><text x="688" y="52" text-anchor="end" class="micro" fill="{p.muted}">03 ONLINE</text></g>
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


def systems_svg(p: Palette) -> str:
    uid = f"systems-{p.name}"
    panels = [(30, 86, 352, 260), (424, 86, 352, 260), (818, 86, 352, 260)]
    particles = texture_points(20260826, 52, 1200, 400, p.accent)
    panel_markup = "".join(
        f'<path d="{cut_path(x, y, w, h, 18)}" fill="{p.panel}" fill-opacity=".88" stroke="{p.line}" stroke-width="1.5"/>'
        for x, y, w, h in panels
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400" viewBox="0 0 1200 400" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr active security and engineering system map</title>
  <desc id="desc-{uid}">Three terminal modules showing cybersecurity focus areas, engineering tools and a reproducible open-source protocol.</desc>
  {svg_defs(p, uid)}
  <rect width="1200" height="400" fill="url(#bg-{uid})"/>
  <rect width="1200" height="400" fill="url(#grid-{uid})" opacity=".34"/>
  <g>{particles}</g>
  <path d="{cut_path(8, 8, 1184, 384, 26)}" fill="none" stroke="{p.accent}" stroke-width="2"/>
  <g class="mono">
    <text x="36" y="54" class="label" fill="{p.accent}">◆ ACTIVE MODULES // SYSTEM MAP</text>
    <text x="1164" y="54" text-anchor="end" class="micro" fill="{p.muted}">3 MODULES ONLINE · READ-ONLY PUBLIC OUTPUT</text>
  </g>
  {panel_markup}
  <g class="mono">
    <text x="55" y="120" class="label" fill="{p.warn}">01 // SECURITY TRACK</text>
    <text x="55" y="153" class="micro" fill="{p.muted}">CURRENT VECTOR</text>
    <g class="body" fill="{p.fg}">
      <text x="55" y="190">◆ application security</text>
      <text x="55" y="224">◆ secure architecture</text>
      <text x="55" y="258">◆ privacy-aware engineering</text>
      <text x="55" y="292">◆ defensive automation</text>
      <text x="55" y="326">◆ reproducible research</text>
    </g>

    <text x="449" y="120" class="label" fill="{p.warn}">02 // ENGINEERING CORE</text>
    <text x="449" y="153" class="micro" fill="{p.muted}">INTEROPERABLE TOOLCHAIN</text>
    <g class="body">
      <text x="449" y="194" fill="{p.accent}">.NET / C#</text><text x="615" y="194" fill="{p.fg}">PYTHON</text>
      <text x="449" y="236" fill="{p.fg}">TYPESCRIPT</text><text x="615" y="236" fill="{p.accent}">KOTLIN</text>
      <text x="449" y="278" fill="{p.accent}">SQL</text><text x="615" y="278" fill="{p.fg}">DOCKER</text>
      <text x="449" y="320" fill="{p.fg}">AZURE</text><text x="615" y="320" fill="{p.accent}">OWASP</text>
    </g>
    <g stroke="{p.line}" opacity=".65"><path d="M449 207H738M449 249H738M449 291H738"/></g>

    <text x="843" y="120" class="label" fill="{p.warn}">03 // OSS PROTOCOL</text>
    <text x="843" y="153" class="micro" fill="{p.muted}">LEAVE A SAFE TRAIL</text>
    <g class="body">
      <text x="843" y="194" fill="{p.accent}">01</text><text x="890" y="194" fill="{p.fg}">REPRODUCE</text>
      <text x="843" y="236" fill="{p.accent}">02</text><text x="890" y="236" fill="{p.fg}">SANITISE</text>
      <text x="843" y="278" fill="{p.accent}">03</text><text x="890" y="278" fill="{p.fg}">DOCUMENT</text>
      <text x="843" y="320" fill="{p.accent}">04</text><text x="890" y="320" fill="{p.fg}">IMPROVE</text>
    </g>
    <path d="M1058 186V314" stroke="{p.line}" stroke-width="2" class="flow"/>
    <g fill="{p.accent}"><circle cx="1058" cy="190" r="5"/><circle cx="1058" cy="232" r="5"/><circle cx="1058" cy="274" r="5"/><circle cx="1058" cy="316" r="5"/></g>
  </g>
  <g class="mono micro">
    <text x="34" y="375" fill="{p.muted}">ASSUME LESS</text>
    <text x="426" y="375" fill="{p.muted}">EVIDENCE &gt; VIBES</text>
    <text x="779" y="375" fill="{p.muted}">SECURE BY DEFAULT</text>
    <text x="1164" y="375" text-anchor="end" fill="{p.accent}">BUILD → HARDEN → VERIFY → IMPROVE</text>
  </g>
  <rect class="scan-sweep" x="10" y="-40" width="1180" height="70" fill="url(#sweep-{uid})" opacity=".35" pointer-events="none"/>
  <rect width="1200" height="400" fill="url(#scan-{uid})" opacity=".22" pointer-events="none"/>
</svg>
"""


def nav_svg(p: Palette, kind: str, code: str, title: str, subtitle: str) -> str:
    uid = f"nav-{kind}-{p.name}"
    frame = cut_path(3, 3, 354, 86, 12)
    if kind == "portfolio":
        icon = f'<path d="M31 26L53 15 75 26V58L53 69 31 58Z" fill="none" stroke="{p.accent}" stroke-width="2"/><path d="M43 34L53 44 63 34M53 44V57" fill="none" stroke="{p.accent2}" stroke-width="2"/>'
    elif kind == "linkedin":
        icon = f'<circle cx="53" cy="25" r="6" fill="{p.accent}"/><path d="M47 39V67M60 67V48C60 38 75 38 75 50V67M32 39V67" fill="none" stroke="{p.accent}" stroke-width="4"/>'
    else:
        icon = f'<circle cx="53" cy="43" r="27" fill="none" stroke="{p.accent}" stroke-width="2"/><text x="53" y="50" text-anchor="middle" class="mono" font-size="19" font-weight="800" fill="{p.accent}">iD</text>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="92" viewBox="0 0 360 92" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">{esc(title)}</title><desc id="desc-{uid}">{esc(subtitle)}</desc>
  {svg_defs(p, uid)}
  <path d="{frame}" fill="{p.panel}" stroke="{p.line}" stroke-width="1.5"/>
  <path d="M91 13V79" stroke="{p.grid}"/>{icon}
  <g class="mono"><text x="109" y="31" class="micro" fill="{p.muted}">{esc(code)}</text><text x="109" y="55" font-size="18" font-weight="800" letter-spacing="1" fill="{p.fg}">{esc(title)}</text><text x="109" y="74" font-size="11" letter-spacing="1" fill="{p.accent}">{esc(subtitle)}</text></g>
  <path d="M318 34L332 46 318 58" fill="none" stroke="{p.accent}" stroke-width="2" class="pulse"/>
  <path d="{frame}" fill="none" stroke="{p.accent}" stroke-width="2" stroke-dasharray="70 300" class="flow"/>
</svg>
"""


def mobile_nav_svg(p: Palette, kind: str, code: str, title: str) -> str:
    uid = f"mobile-nav-{kind}-{p.name}"
    glyph = {"portfolio": "⌁", "linkedin": "in", "orcid": "iD"}[kind]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="120" viewBox="0 0 360 120" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">{esc(title)}</title><desc id="desc-{uid}">Mobile navigation control for {esc(title)}.</desc>
  {svg_defs(p, uid)}
  <path d="{cut_path(4, 4, 352, 112, 14)}" fill="{p.panel}" stroke="{p.accent}" stroke-width="2"/>
  <circle cx="56" cy="60" r="31" fill="none" stroke="{p.line}" stroke-width="2"/><text x="56" y="70" text-anchor="middle" class="mono" font-size="27" font-weight="800" fill="{p.accent}">{glyph}</text>
  <g class="mono"><text x="102" y="43" class="micro" fill="{p.muted}">{esc(code)}</text><text x="102" y="78" font-size="25" font-weight="800" letter-spacing="1" fill="{p.fg}">{esc(title)}</text></g>
  <path d="M323 46L338 60 323 74" fill="none" stroke="{p.accent}" stroke-width="3" class="pulse"/>
  <path d="{cut_path(4, 4, 352, 112, 14)}" fill="none" stroke="{p.accent2}" stroke-width="2" stroke-dasharray="60 320" class="flow"/>
</svg>
"""


def footer_svg(p: Palette) -> str:
    uid = f"footer-{p.name}"
    wave = waveform(420, 45, 360, 8, 110)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="112" viewBox="0 0 1200 112" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr public profile status</title><desc id="desc-{uid}">Learning continuously, building deliberately and disclosing responsibly.</desc>
  {svg_defs(p, uid)}
  <path d="{cut_path(8, 8, 1184, 96, 20)}" fill="{p.panel}" stroke="{p.line}" stroke-width="1.5"/>
  <g class="mono"><text x="38" y="39" class="micro" fill="{p.muted}">PUBLIC PROFILE // SANITISED OUTPUT</text><text x="38" y="70" class="label" fill="{p.accent}">LEARN · BUILD · HARDEN · SHARE</text></g>
  <polyline points="{wave}" fill="none" stroke="{p.accent}" stroke-width="2" class="flow"/>
  <g class="mono" text-anchor="end"><text x="1162" y="39" class="micro" fill="{p.muted}">STATUS // ONLINE</text><text x="1162" y="70" class="label" fill="{p.fg}">DISCLOSE RESPONSIBLY</text></g>
  <circle class="pulse" cx="810" cy="54" r="7" fill="{p.accent}"/>
</svg>
"""


def mobile_footer_svg(p: Palette) -> str:
    uid = f"mobile-footer-{p.name}"
    wave = waveform(34, 92, 652, 11, 130)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="180" viewBox="0 0 720 180" role="img" aria-labelledby="title-{uid} desc-{uid}">
  <title id="title-{uid}">SergiGTAr mobile profile status</title><desc id="desc-{uid}">Public profile online: learn, build, harden, share and disclose responsibly.</desc>
  {svg_defs(p, uid)}
  <path d="{cut_path(8, 8, 704, 164, 20)}" fill="{p.panel}" stroke="{p.line}" stroke-width="2"/>
  <g class="mono"><text x="34" y="42" class="micro" fill="{p.muted}">PUBLIC PROFILE // STATUS ONLINE</text><text x="34" y="72" font-size="20" font-weight="800" letter-spacing="2" fill="{p.accent}">LEARN · BUILD · HARDEN · SHARE</text></g>
  <polyline points="{wave}" fill="none" stroke="{p.accent}" stroke-width="2" class="flow"/><circle r="5" fill="{p.warn}"><animateMotion dur="3.2s" repeatCount="indefinite" path="M34 92 H686"/></circle>
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
        generated[f"pipboy-terminal-{palette.name}.svg"] = hero_svg(palette, portrait_uri)
        generated[f"pipboy-terminal-mobile-{palette.name}.svg"] = mobile_hero_svg(palette, portrait_uri)
        generated[f"systems-map-{palette.name}.svg"] = systems_svg(palette)
        generated[f"systems-map-mobile-{palette.name}.svg"] = mobile_systems_svg(palette)
        generated[f"nav-portfolio-{palette.name}.svg"] = nav_svg(palette, "portfolio", "UPLINK // 01", "ENTER PORTFOLIO", "SERGIGTAR.DEV")
        generated[f"nav-linkedin-{palette.name}.svg"] = nav_svg(palette, "linkedin", "CHANNEL // 02", "PROFESSIONAL LINK", "LINKEDIN")
        generated[f"nav-orcid-{palette.name}.svg"] = nav_svg(palette, "orcid", "IDENTITY // 03", "RESEARCH ID", "ORCID")
        generated[f"nav-portfolio-mobile-{palette.name}.svg"] = mobile_nav_svg(palette, "portfolio", "UPLINK // 01", "PORTFOLIO")
        generated[f"nav-linkedin-mobile-{palette.name}.svg"] = mobile_nav_svg(palette, "linkedin", "CHANNEL // 02", "LINKEDIN")
        generated[f"nav-orcid-mobile-{palette.name}.svg"] = mobile_nav_svg(palette, "orcid", "IDENTITY // 03", "ORCID")
        generated[f"footer-status-{palette.name}.svg"] = footer_svg(palette)
        generated[f"footer-status-mobile-{palette.name}.svg"] = mobile_footer_svg(palette)

    for name, contents in generated.items():
        (ASSETS / name).write_text(contents, encoding="utf-8", newline="\n")

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
