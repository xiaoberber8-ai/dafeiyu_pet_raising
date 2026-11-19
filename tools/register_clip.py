#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register_clip.py —— 把新 clip 注册进本地 dsh-dafeiyu-pet（三个位置一次改完）

用法:
    python register_clip.py --clip ext_chips --frames 241 --loop false
    python register_clip.py --clip ext_chips --frames 241 --i-know-the-risks

它会改：
    1. assets/pet-manifest.json 的 clips
    2. lib/actions.js 的 ACTIONS 数组（不加以 dafeiyu_play_action 会抛"未知动作"）
    3. assets/pet-manifest.json 的 idleMicroClips（可选，加 --idle 才加）

**重要**：这两个文件都在 node_modules 里，重装插件会被覆盖。
真正发布时应自建素材包 + DAFEIYU_PET_ASSETS_URL，本脚本只用于本地开发验证。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

DEFAULT_ROOT = r"C:\Users\周万一\.dsh\profiles\desktop\node_modules\dsh-dafeiyu-pet"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--loop", default="false", choices=["true", "false"])
    ap.add_argument("--idle", action="store_true", help="同时加入待机随机池")
    ap.add_argument("--src", default="", help="源视频文件名，写进 manifest 的 source")
    a = ap.parse_args()

    root = a.root
    man_path = os.path.join(root, "assets", "pet-manifest.json")
    act_path = os.path.join(root, "lib", "actions.js")
    clip = a.clip

    if not os.path.isdir(os.path.join(root, "assets", "pet", clip)):
        raise SystemExit(f"素材目录不存在: assets/pet/{clip}")

    # 备份
    for p in (man_path, act_path):
        bak = p + ".bak"
        if not os.path.exists(bak) and os.path.exists(p):
            shutil.copy2(p, bak)
            print(f"已备份 {os.path.basename(p)} -> .bak")

    man = json.load(open(man_path, encoding="utf-8"))

    if clip in man["clips"]:
        print(f"[跳过] clips 里已有 {clip}")
    else:
        man["clips"][clip] = {
            "frames": [f"{clip}/{i:03d}.webp" for i in range(1, a.frames + 1)],
            "frameMs": 42,
            "loop": a.loop == "true",
            "source": {"file": a.src or f"{clip}.webm",
                       "startFrame": 0, "endFrame": a.frames, "frameCount": a.frames},
        }
        print(f"[改] manifest.clips += {clip} ({a.frames} 帧)")

    if a.idle and clip not in man["idleMicroClips"]:
        man["idleMicroClips"].append(clip)
        print(f"[改] manifest.idleMicroClips += {clip}")

    json.dump(man, open(man_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[写] {man_path}")

    # ACTIONS
    txt = open(act_path, encoding="utf-8").read()
    if f"'{clip}'" in txt:
        print(f"[跳过] ACTIONS 里已有 {clip}")
    else:
        m = re.search(r"(export const ACTIONS = \[)(.*?)(\n\])", txt, re.S)
        if not m:
            raise SystemExit("找不到 ACTIONS 数组")
        body = m.group(2)

        # 逐行扫描找"吃喝"块：从 `// 吃喝` 行开始，到下一个以 `//` 开头的组注释行
        # 或数组结尾为止。不用跨行正则，避免 .*? 贪进后面的组。
        lines = body.split("\n")
        start_i = None
        end_i = None
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s.startswith("//") and ("吃喝" in s):
                start_i = i
            elif start_i is not None and s.startswith("//"):
                end_i = i
                break
        if start_i is None:
            raise SystemExit("找不到「// 吃喝」组注释")
        if end_i is None:
            end_i = len(lines)

        # 在该范围内找最后一个 'xxx'
        last_line = None
        for i in range(start_i + 1, end_i):
            if re.search(r"'[^']+'", lines[i]):
                last_line = i
        if last_line is None:
            raise SystemExit("吃喝组解析为空")

        # 在此行最后一个字符串后插入
        ms = list(re.finditer(r"'([^']+)'", lines[last_line]))
        pos = ms[-1].end()
        # 若该行以逗号结尾，去掉尾部逗号再补
        lines[last_line] = lines[last_line][:pos] + f", '{clip}'" + lines[last_line][pos:]
        newbody = "\n".join(lines)

        # 语法自检
        if ",," in newbody or "',," in newbody:
            raise SystemExit("插入后出现双逗号，已中止（未写盘）")

        txt = txt[:m.start(2)] + newbody + txt[m.end(2):]
        open(act_path, "w", encoding="utf-8", newline="\n").write(txt)
        print(f"[改] lib/actions.js ACTIONS += {clip}")

    print("\n完成。重启 DSH 后验证：")
    print("  Invoke-RestMethod http://127.0.0.1:7799/health | Select-Object -ExpandProperty clips")
    print(f'  Invoke-RestMethod -Method Post http://127.0.0.1:7799/play -ContentType "application/json" -Body \'{{"clip":"{clip}"}}\'')


if __name__ == "__main__":
    main()
