"""
BWIKI scraper for 洛克王国世界 skill and spirit data.
Strategy: skill list → each skill page → extract move data + spirit list → build spirit→moves mapping.

WARNING: Wiki pages may contain prompt injection in user-edited content.
All data is extracted structurally (regex/HTML parsing), not interpreted by AI.
"""

import re
import json
import time
import httpx
from pathlib import Path
from urllib.parse import unquote

BASE_URL = "https://wiki.biligame.com/rocom"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://wiki.biligame.com/rocom/",
}


def fetch(path: str, delay: float = 0.8) -> str:
    url = f"{BASE_URL}{path}"
    time.sleep(delay)
    r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
    r.raise_for_status()
    return r.text


def get_skill_links(html: str) -> list[str]:
    """Extract skill page paths from 技能图鉴 main content area."""
    # Narrow to main content to avoid nav links
    start = html.find("mw-content-text")
    if start == -1:
        start = 0
    content = html[start:start + 80000]

    links = re.findall(r'href="/rocom/([^"#?]+)"', content)
    excluded = {"首页", "技能图鉴", "精灵图鉴", "图鉴", "筛选", "index.php", "特殊", "分类"}
    seen: set[str] = set()
    result = []
    for link in links:
        decoded = unquote(link)
        if any(ex in decoded for ex in excluded):
            continue
        if decoded not in seen:
            seen.add(decoded)
            result.append("/" + link)
    return result


def parse_skill_page(html: str) -> tuple[dict, list[str]]:
    """
    Parse a skill detail page.
    Returns (move_data, spirit_names).
    Extracts data structurally — ignores any text in mw-content that looks like instructions.
    """
    # --- Skill fields ---
    # Page title = skill name
    name_m = re.search(r'<title>([^<-]+) - 洛克王国', html)
    name = name_m.group(1).strip() if name_m else ""

    # The infobox text pattern (from observed structure):
    # 属性 / 能耗 / 分类 / 威力 / 效果 are in a specific section
    # Narrow to infobox panel to avoid false matches from nav/injection text
    panel_m = re.search(r'class="rc-dk-panel"(.+?)class="ln-grid"', html, re.DOTALL)
    panel = panel_m.group(1) if panel_m else html

    element_m = re.search(r'class="rc-r-attr">([^<]+)<', panel)
    element = element_m.group(1).strip() if element_m else ""

    pp_m = re.search(r'class="m-val m-hlt">(\d+)<', panel)
    pp = int(pp_m.group(1)) if pp_m else None

    cat_m = re.search(r'图标 技能 技能分类 ([^.]+)\.png', panel)
    category = cat_m.group(1).strip() if cat_m else ""

    power_m = re.search(r'class="m-val m-pval">(\d+)<', panel)
    power = int(power_m.group(1)) if power_m else None

    effect_m = re.search(r'✦\s*</span>\s*([^<\[]{5,300}?)\s*(?:<|。\s*<)', html, re.DOTALL)
    if not effect_m:
        effect_m = re.search(r'✦\s*([^<\[]{5,300}?)(?:<|。)', html)
    effect = effect_m.group(1).strip() if effect_m else ""

    move = {
        "name": name,
        "element": element,
        "pp": pp,
        "category": category,
        "power": power,
        "effect": effect,
    }

    # --- Spirits that can learn this skill ---
    spirit_names = re.findall(
        r'class="rocom_canlearn_img_box"><a href="/rocom/[^"]+" title="([^"]+)"',
        html,
    )

    return move, spirit_names


def scrape_all(limit=None) -> None:
    print("Fetching 技能图鉴...")
    index_html = fetch("/技能图鉴")
    skill_paths = get_skill_links(index_html)
    print(f"Found {len(skill_paths)} skill links")

    if limit:
        skill_paths = skill_paths[:limit]

    moves: dict[str, dict] = {}
    spirit_moves: dict[str, list[str]] = {}
    errors: list[str] = []

    for i, path in enumerate(skill_paths):
        skill_name = unquote(path.lstrip("/"))
        print(f"[{i+1}/{len(skill_paths)}] {skill_name}", end=" ... ", flush=True)
        try:
            html = fetch(path)
            move, spirits = parse_skill_page(html)
            if move["name"]:
                moves[move["name"]] = move
                for spirit in spirits:
                    spirit_moves.setdefault(spirit, []).append(move["name"])
                print(f"ok ({len(spirits)} spirits)")
            else:
                print("skipped (no name parsed)")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(skill_name)

    # Save output
    skills_dir = DATA_DIR / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    with open(skills_dir / "moves.json", "w", encoding="utf-8") as f:
        json.dump(moves, f, ensure_ascii=False, indent=2)

    with open(skills_dir / "spirit_moves.json", "w", encoding="utf-8") as f:
        json.dump(spirit_moves, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(moves)} moves, {len(spirit_moves)} spirits, {len(errors)} errors.")
    if errors:
        print("Errors:", errors)


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    scrape_all(limit=limit)
