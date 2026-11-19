#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dsh-pet webm/绿幕视频  →  dsh-dafeiyu-pet WebP 帧序列

用法:
    python webm_to_frames.py <输入视频> <输出目录> [--clip 名字] [--dry]

做三件事:
    1. 归一化：按首帧角色站立高度缩放，脚底对齐、水平居中，落到 412x344 透明画布
    2. 逐帧导出：WebP quality 68，RGBA
    3. 打印可直接粘贴进 pet-manifest.json 的片段

归一化目标（与本地 112 个 clip 实测一致）:
    画布 412x344 / 站立高 266px / 脚底 y=330 / 水平中心 x=219
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

# ---- 目标规格（取自本地 dsh-dafeiyu-pet v1.0.4 实测） ----
CANVAS_W, CANVAS_H = 412, 344
TARGET_STAND_H = 266      # 实测 idle bbox 高度
TARGET_FEET_Y = 330       # 实测脚底
TARGET_CENTER_X = 219     # 实测水平中心
FPS = 24
WEBP_QUALITY = 68
ALPHA_THRESHOLD = 10      # 判定"不透明"的 alpha 阈值
CROP_X, CROP_Y = 100, 0   # 上游 assetSource.crop = [100, 0, 412, 344]

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")


def run(cmd, capture=False):
    return subprocess.run(cmd, capture_output=capture, text=True, encoding="utf-8", errors="replace")


def probe(path):
    r = run([FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate",
             "-show_entries", "format=duration", "-of", "json", path], capture=True)
    j = json.loads(r.stdout or "{}")
    st = (j.get("streams") or [{}])[0]
    num, den = (st.get("r_frame_rate") or "24/1").split("/")
    return {
        "width": int(st.get("width") or 0),
        "height": int(st.get("height") or 0),
        "fps": float(num) / float(den or 1),
        "duration": float((j.get("format") or {}).get("duration") or 0),
    }


def measure_first_frame(path):
    """解第一帧为 RGBA，量角色包围盒。首帧按约定应是标准正面站立。"""
    r = run([FFMPEG, "-v", "error", "-c:v", "libvpx-vp9", "-i", path,
             "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
            capture=True)
    if r.returncode != 0:
        raise SystemExit(f"解码首帧失败: {r.stderr[:300]}")
    raw = r.stdout
    # capture_output 是 text 模式，这里改用字节重取
    p = subprocess.run([FFMPEG, "-v", "error", "-c:v", "libvpx-vp9", "-i", path,
                        "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                       capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"解码首帧失败: {p.stderr.decode('utf-8', 'replace')[:300]}")
    info = probe(path)
    w, h = info["width"], info["height"]
    buf = p.stdout
    need = w * h * 4
    if len(buf) < need:
        raise SystemExit(f"首帧字节不足: {len(buf)} < {need}")
    alpha_off = 3
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        row = y * w * 4
        for x in range(w):
            if buf[row + x * 4 + alpha_off] > ALPHA_THRESHOLD:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx < 0:
        raise SystemExit("首帧全透明，无法测量角色位置")
    return {
        "bbox": (minx, miny, maxx, maxy),
        "height": maxy - miny + 1,
        "feet_y": maxy,
        "center_x": (minx + maxx) / 2.0,
        "canvas": (w, h),
    }


def build_filter_crop(out_w=CANVAS_W, out_h=CANVAS_H):
    """纯裁剪（对齐上游 dsh-pet 的既有素材）。

    上游 640x360 已经过 normalize_step03 统一过角色大小与位置，
    所以这里只需在固定窗口裁一刀，**不做任何缩放**。
    实测验证：上游吃白饭首帧 bbox(211,63,421,323) - (100,0) = (111,63,321,323)，
    与本地 dsh-dafeiyu-pet 的 ext_rice 首帧 bbox 完全一致。
    """
    return f"crop={CANVAS_W}:{CANVAS_H}:{CROP_X}:{CROP_Y},format=yuva420p[v]"


def build_filter_normalize(m, out_w=CANVAS_W, out_h=CANVAS_H):
    """归一化（用于自制的 AI 新视频，角色大小/位置不保证与上游一致）。"""
    s = TARGET_STAND_H / m["height"]
    ox = TARGET_CENTER_X - m["center_x"] * s
    oy = TARGET_FEET_Y - m["feet_y"] * s
    sw = int(m["canvas"][0] * s) // 2 * 2
    sh = int(m["canvas"][1] * s) // 2 * 2
    return (
        f"color=c=black@0:s={out_w}x{out_h}:r={FPS}[bg];"
        f"[0:v]scale={sw}:{sh}:flags=lanczos,format=yuva420p[sc];"
        f"[bg][sc]overlay={ox:.2f}:{oy:.2f}:shortest=1,format=yuva420p[v]"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("outdir")
    ap.add_argument("--clip", default=None, help="clip id（默认取输出目录名）")
    ap.add_argument("--dry", action="store_true", help="只测量与打印，不写文件")
    a = ap.parse_args()

    info = probe(a.src)
    print(f"输入: {a.src}")
    print(f"  编码尺寸 {info['width']}x{info['height']}  {info['fps']:.2f}fps  {info['duration']:.2f}s")

    m = measure_first_frame(a.src)
    print(f"  首帧 bbox={m['bbox']}  站立高={m['height']}  脚底y={m['feet_y']}  中心x={m['center_x']:.1f}")

    f = build_filter_crop()
    print(f"  预计输出帧数: {round(info['duration'] * FPS)}")

    if a.dry:
        return

    os.makedirs(a.outdir, exist_ok=True)
    clip = a.clip or os.path.basename(os.path.normpath(a.outdir))

    # 分两步：先导 PNG 序列（image2 对 %05d.png 可靠），再转 WebP。
    # 直接让 ffmpeg 写 .webp 序列会被 animated-webp / image2 命名规则坑到，
    # 实测会只出 1 帧或报 "Cannot write more than one file with the same name"。
    tmpdir = os.path.join(a.outdir, "_png_tmp")
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)

    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-c:v", "libvpx-vp9", "-i", a.src,
           "-filter_complex", f, "-map", "[v]",
           "-r", str(FPS), "-an",
           "-pix_fmt", "rgba",
           os.path.join(tmpdir, "%05d.png")]
    r = run(cmd)
    if r.returncode != 0:
        raise SystemExit("转 PNG 失败:\n" + (r.stderr or "")[:800])

    pngs = sorted(x for x in os.listdir(tmpdir) if x.endswith(".png"))
    if not pngs:
        raise SystemExit("没有产出任何帧")

    from PIL import Image
    for i, name in enumerate(pngs, 1):
        with Image.open(os.path.join(tmpdir, name)) as im:
            im.convert("RGBA").save(
                os.path.join(a.outdir, f"{i:03d}.webp"),
                "WEBP", quality=WEBP_QUALITY, method=6,
            )
    shutil.rmtree(tmpdir, ignore_errors=True)

    files = sorted(x for x in os.listdir(a.outdir) if x.endswith(".webp"))
    total = sum(os.path.getsize(os.path.join(a.outdir, x)) for x in files)
    print(f"\n完成: {len(files)} 帧, {total/1048576:.2f} MB, 输出 {a.outdir}")

    entry = {
        clip: {
            "frames": [f"{clip}/{i:03d}.webp" for i in range(1, len(files) + 1)],
            "frameMs": 42,
            "loop": False,
            "source": {
                "file": os.path.basename(a.src),
                "startFrame": 0,
                "endFrame": len(files),
                "frameCount": len(files),
            },
        }
    }
    print("\n--- 粘贴进 pet-manifest.json 的 clips ---")
    txt = json.dumps(entry, ensure_ascii=False, indent=2)
    print(txt if len(txt) < 2000 else txt[:2000] + " ...(已截断)")


if __name__ == "__main__":
    main()
