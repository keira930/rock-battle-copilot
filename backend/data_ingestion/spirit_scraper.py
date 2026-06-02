"""
Scrape skill data directly from each spirit's detail page.
Handles two page templates used by BWIKI:
  - Template A: rocom_sprite_skill_wrap  (older spirits e.g. 魔力猫)
  - Template B: skill-single             (newer spirits e.g. 迪莫)

Output:
  data/spirits/spirit_skills.json  — { spirit_name: [ {name, element, category, pp, power, effect} ] }
  data/skills/all_moves.json       — deduplicated move dict from all spirit pages
"""

import re
import json
import time
import httpx
from pathlib import Path

BASE_URL = "https://wiki.biligame.com/rocom"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://wiki.biligame.com/rocom/",
}


def fetch(slug: str, delay: float = 0.8) -> str:
    url = f"{BASE_URL}/{slug}"
    time.sleep(delay)
    r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
    r.raise_for_status()
    return r.text


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _parse_template_a(html: str) -> list[dict]:
    """Old template: rocom_sprite_skill_wrap blocks."""
    skills = []
    seen = set()
    blocks = re.findall(
        r'class="rocom_sprite_skill_wrap">(.*?)</div>\s*</div>\s*</div>',
        html, re.DOTALL
    )
    for block in blocks:
        name_m = re.search(r'class="rocom_sprite_skillName[^"]*">([^<]+)<', block)
        if not name_m:
            continue
        name = name_m.group(1).strip()
        if name in seen:
            continue
        seen.add(name)

        cat_m = re.search(r'图标 技能 类别 ([^.]+)\.png', block)
        elem_m = re.search(r'图标 宠物 属性 ([^.]+)\.png', block)
        # pp is after the img tag inside rocom_sprite_skillDamage
        pp_m = re.search(r'rocom_sprite_skillDamage[^>]*>(?:<[^>]+>)*(\d+)<', block)
        power_m = re.search(r'rocom_sprite_skill_power[^>]*>(\d+)<', block)
        effect_m = re.search(r'✦\s*([^<]{3,300}?)(?:</|$)', block)

        skills.append({
            "name": name,
            "element": elem_m.group(1).strip() if elem_m else "普通",
            "category": cat_m.group(1).strip() if cat_m else "",
            "pp": int(pp_m.group(1)) if pp_m else None,
            "power": int(power_m.group(1)) if power_m else None,
            "effect": effect_m.group(1).strip() if effect_m else "",
        })
    return skills


def _parse_template_b(html: str) -> list[dict]:
    """New template: skill-single blocks (e.g. 迪莫)."""
    skills = []
    seen = set()

    # Each skill block: skill-single-head-info + skill-single-body
    blocks = re.findall(
        r'class="skill-single-head-info">(.*?)</div>\s*</div>\s*'
        r'(?:<div class="skill-single-body">(.*?)</div>\s*</div>)?',
        html, re.DOTALL
    )
    for head, body in blocks:
        name_m = re.search(r'class="skill-name[^"]*">([^<]+)<', head)
        if not name_m:
            continue
        name = name_m.group(1).strip()
        if name in seen:
            continue
        seen.add(name)

        cat_m = re.search(r'图标 技能 类别 ([^.]+)\.png', head)
        elem_m = re.search(r'图标 宠物 属性 ([^.]+)\.png', head)

        # In typelist: imgtext-row contains pp, last bare <span>N</span> is power
        # pp: number inside imgtext-row span
        pp_m = re.search(r'imgtext-row[^>]*>.*?<span>(\d+)</span>', head, re.DOTALL)
        # power: all bare <span>N</span>, last one is power
        spans = re.findall(r'<span>(\d+)</span>', head)
        power = int(spans[-1]) if spans else None

        effect = ""
        if body:
            eff_m = re.search(r'class="skill-desc-atk">([^<]+)<', body)
            if eff_m:
                effect = eff_m.group(1).strip()

        skills.append({
            "name": name,
            "element": elem_m.group(1).strip() if elem_m else "普通",
            "category": cat_m.group(1).strip() if cat_m else "",
            "pp": int(pp_m.group(1)) if pp_m else None,
            "power": power,
            "effect": effect,
        })
    return skills


def parse_spirit_skills(html: str) -> list[dict]:
    """Auto-detect template and parse skills."""
    if "rocom_sprite_skill_wrap" in html:
        return _parse_template_a(html)
    elif "skill-single-head-info" in html:
        return _parse_template_b(html)
    return []


def scrape_all(limit=None):
    spirits_path = DATA_DIR / "spirits" / "spirits_final.json"
    spirits = json.loads(spirits_path.read_text(encoding="utf-8"))
    if limit:
        spirits = spirits[:limit]

    spirit_skills: dict[str, list[dict]] = {}
    all_moves: dict[str, dict] = {}
    errors = []

    print(f"Scraping {len(spirits)} spirits...")
    for i, spirit in enumerate(spirits):
        name, slug = spirit["name"], spirit["slug"]
        print(f"[{i+1}/{len(spirits)}] {name}", end=" ... ", flush=True)
        try:
            html = fetch(slug)
            skills = parse_spirit_skills(html)
            spirit_skills[name] = skills
            for sk in skills:
                if sk["name"] not in all_moves:
                    all_moves[sk["name"]] = {k: v for k, v in sk.items() if k != "name"}
            template = "A" if "rocom_sprite_skill_wrap" in html else "B"
            print(f"ok ({len(skills)} skills, template {template})")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(name)

    (DATA_DIR / "spirits").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "skills").mkdir(parents=True, exist_ok=True)

    (DATA_DIR / "spirits" / "spirit_skills.json").write_text(
        json.dumps(spirit_skills, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_DIR / "skills" / "all_moves.json").write_text(
        json.dumps(all_moves, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDone: {len(spirit_skills)} spirits, {len(all_moves)} unique moves, {len(errors)} errors")
    if errors:
        print("Errors:", errors)


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    scrape_all(limit=limit)
