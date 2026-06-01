"""
批量摄入多个论坛帖子。

使用方法：在 ingestion_config.json 中配置帖子列表，然后运行：
  python batch_ingest.py --cookie "你的Cookie"

ingestion_config.json 示例：
[
  {"url": "https://17roco.gamebbs.qq.com/forum.php?mod=viewthread&tid=157476", "tags": ["counter", "status"]},
  {"url": "https://17roco.gamebbs.qq.com/forum.php?mod=viewthread&tid=XXXXX", "tags": ["skills"]}
]
"""

import argparse
import json
import re
import time
from pathlib import Path
from parse_forum import fetch_with_cookie, parse_html, save_results

CONFIG_PATH = Path(__file__).parent / "ingestion_config.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookie", required=True, help="浏览器 Cookie 字符串")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="配置文件路径")
    parser.add_argument("--delay", type=float, default=2.0, help="请求间隔秒数（防封号）")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        print("请创建 ingestion_config.json，格式见文件顶部注释")
        return

    urls = json.loads(config_path.read_text(encoding="utf-8"))
    print(f"📋 共 {len(urls)} 个帖子待摄入\n")

    for i, entry in enumerate(urls):
        url = entry["url"]
        m = re.search(r"tid=(\d+)", url)
        tid = m.group(1) if m else f"post_{i}"

        print(f"[{i+1}/{len(urls)}] {url}")
        try:
            html = fetch_with_cookie(url, args.cookie)
            result = parse_html(html, url)
            save_results(result, tid)
        except Exception as e:
            print(f"  ❌ 失败: {e}")

        if i < len(urls) - 1:
            time.sleep(args.delay)

    print("\n✅ 批量摄入完成")


if __name__ == "__main__":
    main()
