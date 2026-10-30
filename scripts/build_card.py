"""
Builds the neofetch-style profile card (assets/dark_mode.svg + assets/light_mode.svg).

Run locally:   python scripts/build_card.py
In Actions:    GH_TOKEN + GH_USER env vars are set, so live GitHub stats are fetched
               and cached in assets/stats.json. Without a token the cached values are used.

To change any line on the card, edit INFO below.
"""
import json
import os
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
USER = os.environ.get("GH_USER", "eklvy")

# ───────────────────────── card content ─────────────────────────
HEADER = "eklavya@gogia"
INFO = [
    ("Status", "● Online · building (stable)"),
    ("OS", "Eklavya Gogia"),
    ("Host", "The NorthCap University, IN"),
    ("Kernel", "B.Tech AI/ML · Class of 2028"),
    ("Focus", "Local AI, Offline-first Systems"),
    ("Languages.Programming", "Python, TypeScript, JS, C++"),
    ("Languages.Real", "English, Hindi"),
    ("ML.Frameworks", "PyTorch, TensorFlow"),
    ("LLM.Systems", "RAG, GraphRAG, LangGraph, llama.cpp"),
    ("Web.Data", "React, FastAPI, PostgreSQL, Neo4j"),
    ("Tools", "Git, Docker, Figma"),
    ("Interests", "Model Drift, Edge AI, Human-in-loop"),
    ("- Achievements -", None),
    ("Winner", "August Tinkering Lab Challenge"),
    ("1st.Place", "SIH Internal Round"),
    ("1st.Place", "GfG DSA Summer Contest"),
    ("- Contact -", None),
    ("Timezone", "IST (UTC+5:30)"),
    ("Email", "ext.eklavya@gmail.com"),
    ("Website", "eklavyagogia.me"),
    ("LinkedIn", "in/eklavya-gogia-67b00a321"),
    ("X", "@Eklavyaxgogia"),
    ("- GitHub Stats -", "STATS"),
]
FOOTER = [
    "// AI systems for real-world constraints.",
    "// Building projects, one commit at a time.",
]

# ───────────────────────── live stats ─────────────────────────
QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100, isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions }
    }
  }
}"""


def fetch_stats():
    cache = ASSETS / "stats.json"
    stats = json.loads(cache.read_text()) if cache.exists() else {}
    token = os.environ.get("GH_TOKEN")
    if not token:
        return stats
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    try:
        u = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]
        c = u["contributionsCollection"]
        stats = {
            "repos": u["repositories"]["totalCount"],
            "contributed": u["repositoriesContributedTo"]["totalCount"],
            "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
            "followers": u["followers"]["totalCount"],
            "commits": c["totalCommitContributions"],
            "prs": c["totalPullRequestContributions"],
            "contributions": c["contributionCalendar"]["totalContributions"],
        }
        cache.write_text(json.dumps(stats, indent=2) + "\n")
    except Exception as e:  # keep the last good numbers if the API hiccups
        print("stats fetch failed:", e)
    return stats


# ───────────────────────── svg building ─────────────────────────
W = 62            # characters in the info column
FS, LH = 15, 20   # info font-size / line-height
CW = FS * 0.602   # monospace advance
ART_FS, ART_LH, ART_CW = 8, 9.4, 8 * 0.602

THEMES = {
    "dark": dict(bg="#161b22", border="#30363d", text="#c9d1d9", key="#d2a8ff",
                 dots="#484f58", art="#c9d1d9", green="#3fb950", comment="#6e7681", head="#79c0ff"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", text="#24292f", key="#8250df",
                  dots="#afb8c1", art="#24292f", green="#1a7f37", comment="#6e7781", head="#0969da"),
}


def kv(key, value, width):
    """'. Key: ........ value' as (text, class) segments, padded to width chars."""
    fill = width - len(key) - len(value) - 5
    segs = [(". ", "d"), (key, "k"), (":", "t"), (" " + "." * max(fill, 2) + " ", "d")]
    if value.startswith("● "):
        segs += [("● ", "g"), (value[2:], "t")]
    else:
        segs.append((value, "t"))
    return segs


def rule(title, width):
    if title is None:
        return [("—" * width, "d")]
    head = f"{title} "
    return [(head, "h"), ("—" * (width - len(head) - 3), "d"), ("-—-", "d")]


def stat_lines(s):
    g = lambda k: str(s.get(k, "—"))
    a = 37
    b = W - a - 3
    return [
        kv("Repos", f"{g('repos')} {{Contributed: {g('contributed')}}}", a)
        + [(" | ", "d")] + kv("Stars", g("stars"), b),
        kv("Commits (1y)", g("commits"), a) + [(" | ", "d")] + kv("Followers", g("followers"), b),
        kv("Contributions (1y)", g("contributions"), a) + [(" | ", "d")] + kv("PRs", g("prs"), b),
    ]


def build(theme, stats):
    t = THEMES[theme]
    art = (ASSETS / "ascii.txt").read_text().rstrip("\n").split("\n")
    if theme == "light":  # dark ink on light paper: flip the shading so the face stays bright
        ramp = ".:░▒▓█"
        flip = str.maketrans(ramp, ramp[::-1])
        art = [l.translate(flip) for l in art]

    lines = [rule(HEADER, W)]
    for key, val in INFO:
        if val is None or val == "STATS":
            lines.append(rule(key, W))
            if val == "STATS":
                lines += stat_lines(stats)
        else:
            lines.append(kv(key, val, W))
    lines.append(rule(None, W))

    pad = 28
    art_w = max(len(l) for l in art) * ART_CW
    info_x = pad + art_w + 36
    info_h = (len(lines) + len(FOOTER) + 1) * LH
    height = int(pad * 2 + info_h)
    width = int(info_x + W * CW + pad)
    art_y = pad + (info_h - len(art) * ART_LH) / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ConsolasFallback,Consolas,\'SF Mono\',Menlo,\'DejaVu Sans Mono\',monospace">',
        "<style>",
        f".k{{fill:{t['key']}}}.t{{fill:{t['text']}}}.d{{fill:{t['dots']}}}"
        f".g{{fill:{t['green']}}}.h{{fill:{t['head']};font-weight:600}}.c{{fill:{t['comment']}}}",
        "text{white-space:pre}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="{pad}" y="{art_y:.1f}" font-size="{ART_FS}" fill="{t["art"]}" xml:space="preserve">',
    ]
    for i, l in enumerate(art):
        out.append(f'<tspan x="{pad}" dy="{ART_LH if i else ART_LH}">{escape(l)}</tspan>')
    out.append("</text>")

    out.append(f'<text x="{info_x:.1f}" y="{pad}" font-size="{FS}" xml:space="preserve">')
    for i, segs in enumerate(lines):
        spans = "".join(f'<tspan class="{c}">{escape(s)}</tspan>' for s, c in segs)
        out.append(f'<tspan x="{info_x:.1f}" dy="{LH}">{spans}</tspan>')
    out.append(f'<tspan x="{info_x:.1f}" dy="{LH}"> </tspan>')
    for f in FOOTER:
        pad_left = " " * (W - len(f))
        out.append(f'<tspan x="{info_x:.1f}" dy="{LH}" class="c">{escape(pad_left + f)}</tspan>')
    out.append("</text></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    s = fetch_stats()
    for theme in THEMES:
        (ASSETS / f"{theme}_mode.svg").write_text(build(theme, s))
    print("built cards with", s)
