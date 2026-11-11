"""Generate local, daily-refreshed GitHub telemetry SVGs (stdlib only)."""
import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

USER = "bhavesh-kalluru"
OUT = Path(__file__).resolve().parents[1] / "assets"
DATE = dt.datetime.now(dt.timezone.utc).date().isoformat()
CYAN, LILAC, LIGHT, MUTED = "#79E7FC", "#BDA4FF", "#E5EFFF", "#9AAFD0"


def get(url, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-telemetry",
               "X-GitHub-Api-Version": "2022-11-28"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def esc(v):
    return html.escape(str(v), quote=True)


def text(x, y, v, size=13, color=LIGHT, weight=500, align="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{align}" font-family="Inter,system-ui,Arial,sans-serif">{esc(v)}</text>')


def svg(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title>'
            '<defs><linearGradient id="grad" x2="1" y2="1"><stop stop-color="#091627"/>'
            '<stop offset="1" stop-color="#18203B"/></linearGradient></defs>'
            f'<rect width="{w}" height="{h}" rx="16" fill="url(#grad)"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="15" '
            'fill="none" stroke="#344868"/>')


def save(name, content):
    content += "</svg>\n"
    ET.fromstring(content)
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(content, encoding="utf8")
    print("Created", name)


def repos():
    all_repos = []
    for page in range(1, 16):
        batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        all_repos.extend(r for r in batch if not r["private"])
        if len(batch) != 100:
            break
    return all_repos


def stats(data, profile):
    counts = [
        (len(data), "PUBLIC REPOSITORIES"),
        (sum(x["stargazers_count"] for x in data), "STARS EARNED"),
        (profile["followers"], "FOLLOWERS"),
        (sum(x["forks_count"] for x in data), "FORKS"),
    ]
    s = svg(580, 242, "GitHub statistics for public repositories")
    s += text(26, 35, "OPEN SOURCE / GITHUB STATS", 13, CYAN, 700)
    s += text(554, 35, f"UPDATED {DATE}", 10, MUTED, align="end")
    for i, (n, label) in enumerate(counts):
        x, y = 25 + (i % 2) * 276, 52 + (i // 2) * 92
        s += f'<rect x="{x}" y="{y}" width="254" height="80" rx="11" fill="#18273F" stroke="#344963"/>'
        s += text(x + 16, y + 42, f"{n:,}", 29, CYAN if i % 2 == 0 else LILAC, 800)
        s += text(x + 16, y + 64, label, 10, MUTED, 700)
    s += text(27, 236, "GitHub public API · Automatically updated daily", 10, MUTED)
    save("telemetry-stats.svg", s)


def languages(data):
    top = collections.Counter(r["language"] for r in data if r.get("language")).most_common(6)
    s = svg(580, 242, "Primary languages across public repositories")
    s += text(26, 34, "TOP REPOSITORY LANGUAGES", 13, CYAN, 700)
    s += text(554, 34, f"UPDATED {DATE}", 10, MUTED, align="end")
    colors = [CYAN, LILAC, "#70E1BC", "#6A9FFA", "#F1B77B", "#E58AB7"]
    high = max((v for _, v in top), default=1)
    for i, (name, count) in enumerate(top):
        y = 58 + i * 28
        s += text(25, y + 12, name[:20], 12, LIGHT, 600)
        s += f'<rect x="187" y="{y}" rx="5" width="318" height="14" fill="#233451"/>'
        s += f'<rect x="187" y="{y}" rx="5" width="{max(6, int(318*count/high))}" height="14" fill="{colors[i]}"/>'
        s += text(551, y + 12, count, 12, LIGHT, 700, "end")
    s += text(25, 234, "Primary language by repository count, not code volume", 10, MUTED)
    save("telemetry-languages.svg", s)


def calendar():
    q = ("query($u: String!) { user(login:$u) { contributionsCollection { "
         "contributionCalendar { totalContributions weeks { contributionDays "
         "{ date contributionCount } } } } } }")
    data = get("https://api.github.com/graphql", {"query": q, "variables": {"u": USER}})
    if data.get("errors"):
        raise RuntimeError("GitHub GraphQL errors: " + str([e["message"] for e in data["errors"]]))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def activity(data):
    s = svg(1150, 254, "GitHub daily contribution graph for the past year")
    s += text(34, 37, "CONTRIBUTION ACTIVITY / LAST 12 MONTHS", 15, CYAN, 800)
    s += text(1116, 37, f"UPDATED {DATE}", 11, MUTED, align="end")
    colors = ["#24344E", "#265878", "#327E9E", "#34BDD1", "#91EEFF"]
    seen = set()
    for wi, week in enumerate(data["weeks"]):
        for day in week["contributionDays"]:
            when = dt.date.fromisoformat(day["date"])
            dow = (when.weekday() + 1) % 7
            count = day["contributionCount"]
            ix = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 5 else 3 if count <= 10 else 4
            x, y = 42 + wi * 19, 72 + dow * 19
            s += (f'<rect x="{x}" y="{y}" width="14" height="14" rx="3" fill="{colors[ix]}">'
                  f'<title>{when}: {count} contributions</title></rect>')
            key = (when.year, when.month)
            if key not in seen and when.day <= 7:
                seen.add(key)
                s += text(x, 61, when.strftime("%b"), 11, MUTED)
    s += text(42, 232, f"{data['totalContributions']:,} contributions over the last 12 months", 13, LIGHT, 650)
    s += text(1112, 232, "LESS  ▪ ▪ ▪ ▪ ▪  MORE", 10, MUTED, align="end")
    s += text(42, 248, "Source: GitHub contribution calendar, not a fabricated activity estimate", 9, MUTED)
    save("telemetry-activity.svg", s)


if __name__ == "__main__":
    r = repos()
    p = get(f"https://api.github.com/users/{USER}")
    c = calendar()
    stats(r, p)
    languages(r)
    activity(c)
    print(f"Complete: {len(r)} public repos, {c['totalContributions']} contributions")
