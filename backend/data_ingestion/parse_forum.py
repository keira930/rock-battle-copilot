"""
论坛数据摄入脚本 — 支持两种模式：

  模式 A（推荐）: 用浏览器 Cookie 直接爬取
    python parse_forum.py --url "https://17roco.gamebbs.qq.com/forum.php?mod=viewthread&tid=157476" --cookie "你的Cookie"

  模式 B: 浏览器另存 HTML 后解析
    python parse_forum.py --html saved_page.html

输出: data/counters/forum_<tid>.json  和  data/status/forum_<tid>.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip install beautifulsoup4 requests")
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ── 关键词分类器 ──────────────────────────────────────────────
COUNTER_KEYWORDS = [
    "克制", "弱点", "抵抗", "效果好", "效果不好", "无效",
    "倍伤", "减伤", "属性相克", "天敌", "counter",
]
STATUS_KEYWORDS = [
    "中毒", "灼烧", "麻痹", "冰冻", "睡眠", "混乱", "束缚",
    "封印", "沉默", "减速", "加速", "强化", "弱化",
    "状态", "异常", "buff", "debuff",
]


def classify_paragraph(text: str) -> list[str]:
    """返回该段落的分类标签列表。"""
    tags = []
    tl = text.lower()
    if any(kw in tl for kw in COUNTER_KEYWORDS):
        tags.append("counter")
    if any(kw in tl for kw in STATUS_KEYWORDS):
        tags.append("status")
    return tags


# ── HTML 解析 ────────────────────────────────────────────────
def parse_html(html: str, source_url: str = "") -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # 提取帖子标题
    title_tag = soup.find("h1", id="thread_subject") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "未知帖子"

    # 提取所有楼层内容（Discuz 论坛结构）
    posts = []
    for post_div in soup.select("div.t_f, td.t_f, div[id^='postmessage_']"):
        text = post_div.get_text(separator="\n", strip=True)
        # 过滤太短的楼层（签名档等）
        if len(text) < 20:
            continue
        # 按段落切分
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        posts.append({"paragraphs": paragraphs, "raw": text})

    if not posts:
        # 兜底: 直接按 <p> 和 <div> 提取所有文本块
        for tag in soup.select("p, li, td"):
            text = tag.get_text(strip=True)
            if len(text) > 30:
                posts.append({"paragraphs": [text], "raw": text})

    # 分类提取
    counter_docs = []
    status_docs = []

    for post_idx, post in enumerate(posts):
        for para in post["paragraphs"]:
            tags = classify_paragraph(para)
            doc = {
                "source": source_url,
                "thread_title": title,
                "post_index": post_idx,
                "text": para,
            }
            if "counter" in tags:
                counter_docs.append(doc)
            if "status" in tags:
                status_docs.append(doc)

    return {
        "title": title,
        "total_posts": len(posts),
        "counter_docs": counter_docs,
        "status_docs": status_docs,
    }


# ── 网络爬取 ─────────────────────────────────────────────────
def fetch_with_cookie(url: str, cookie: str) -> str:
    if not HAS_REQUESTS:
        raise RuntimeError("请安装 requests: pip install requests")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": cookie,
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.encoding = resp.apparent_encoding or "utf-8"
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {url}")
    return resp.text


# ── 保存结果 ─────────────────────────────────────────────────
def save_results(result: dict, tid: str) -> None:
    counter_path = DATA_DIR / "counters" / f"forum_{tid}.json"
    status_path = DATA_DIR / "status" / f"forum_{tid}.json"

    counter_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    counter_path.write_text(
        json.dumps(result["counter_docs"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    status_path.write_text(
        json.dumps(result["status_docs"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ 帖子: {result['title']}")
    print(f"   楼层数: {result['total_posts']}")
    print(f"   克制段落: {len(result['counter_docs'])} 条 → {counter_path}")
    print(f"   状态段落: {len(result['status_docs'])} 条 → {status_path}")


# ── 主入口 ───────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="洛克王国论坛数据摄入工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="论坛帖子 URL（需配合 --cookie）")
    group.add_argument("--html", help="已保存的 HTML 文件路径")
    parser.add_argument("--cookie", default="", help="浏览器 Cookie 字符串")
    parser.add_argument("--tid", default="unknown", help="帖子 ID（用于输出文件名）")
    args = parser.parse_args()

    # 提取 tid
    tid = args.tid
    if args.url:
        m = re.search(r"tid=(\d+)", args.url)
        if m:
            tid = m.group(1)

    # 获取 HTML
    if args.url:
        print(f"🌐 正在爬取: {args.url}")
        html = fetch_with_cookie(args.url, args.cookie)
        source_url = args.url
    else:
        html_path = Path(args.html)
        if not html_path.exists():
            print(f"❌ 文件不存在: {args.html}")
            sys.exit(1)
        print(f"📄 正在解析: {args.html}")
        html = html_path.read_text(encoding="utf-8", errors="replace")
        source_url = f"file://{html_path.resolve()}"

    # 解析 + 保存
    result = parse_html(html, source_url)
    save_results(result, tid)


if __name__ == "__main__":
    main()
