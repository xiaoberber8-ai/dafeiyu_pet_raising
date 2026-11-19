# 大肥鱼 · 新增视频动作的完整流程

> 适用：给 `dsh-dafeiyu-pet` 新增一个动画动作（吃饭、饮品、节日、特效皆可）
> 本文所有参数与命令**均经实测验证**，不是推测
> 更新日期：2026-11-19

---

## 〇、先看这张图

```
[1] 写提示词 ──> [2] AI 生成 ──> [3] 绿幕抠像 ──> [4] 逐帧转 WebP ──> [5] 注册 ──> [6] 验证
     ↓              ↓               ↓                ↓                  ↓           ↓
 已有 17 条      10s 绿幕 mp4    透明 webm       412×344 帧序列       三处配置    能播会说
```

**两条路线**：

| 路线 | 何时用 | 第 3 步怎么做 |
|---|---|---|
| **A 自动** | AI 生成的绿幕视频 | HSV 色相抠像（`chroma_step02.py` 思路） |
| **B 手动** | 含复杂透明边缘/第三方物品 | 剪映或 PR 手抠，导出带 alpha 的 mov |

> 上游作者自述「**全部采用路线 B**」——自动抠像对复杂边缘容易残边。新手建议先跑 A，不行再上 B。

---

## 一、写提示词

### 现成素材

已有 **17 条**，直接取用：

- [dafeiyu-video-prompts-ALL.md](dafeiyu-video-prompts-ALL.md)（总集，含全部 17 条）
- 单条结构：通用前缀 → 动作概述 → 按秒分割画面 → 动作结束后状态

### 新写一条时

复制任一现有条目的 ```` ```markdown ```` 代码块，只改：

| 改什么 | 注意 |
|---|---|
| 动作名 | `## 吃东西-具体笑点` |
| 动作概述 | 说清道具形态、核心笑点、情绪曲线 |
| 按秒分割 | 每段一个时间区间 + ⚠️ 强调项 |
| 结束状态 | 必须写「最终帧＝标准正面站立，无残留」 |

**通用前缀一字不改**。唯一例外：L/XL 长片段把末句「第 10 秒」改成实际秒数。

### 时长怎么定

| 档位 | 时长 | 帧数 | 用在哪 |
|---|---|---|---|
| S | 8 s | 192 | 喝一口、咬一口 |
| M | 10 s | 241 | **默认**，与既有 112 个 clip 对齐 |
| L | 14 s | 336 | 多阶段表演 |
| XL | 18 s | 432 | 宴席级 |

> 播放器按帧数组长度播完即停，**长片段不需要改任何代码**。

---

## 二、AI 生成源视频

### 工具

| 工具 | 推荐度 | 理由 |
|---|---|---|
| **豆包 / 即梦（Seedance）** | ★★★ | 作者原用工具；单次最长 30s；支持绿幕参考 |
| **可灵 Kling** | ★★★ | 支持**首尾帧**，可强制"第 N 秒回到标准站立" |
| Sora 2 | ✗ | 只有 4/8/12 秒固定档，做不出 10 秒 |
| Veo 3.1 | ✗ | 8 秒封顶 |

### 操作

1. 模式选**图生视频**（不要文生视频）
2. 首帧上传 `ref/ref_standing_640x360.png`
3. 粘贴提示词
4. 负面提示词（若支持）：
   ```
   3D渲染, 写实, 真人, 阴影, 渐变背景, 镜头移动, 跟拍, 平移, 走出画面, 多余手指, 文字, 水印
   ```

### 出片验收

- [ ] 背景纯净 `#00FF00`
- [ ] 首帧＝标准正面站立，无道具
- [ ] 末帧＝标准正面站立，无残留
- [ ] 角色无平移
- [ ] 时长符合档位

不过就重抽。**别指望一次过**——作者 106 个动作也是挑出来的。

---

## 三、绿幕抠像

### 路线 A：自动（HSV 色相判定）

上游 `scripts/chroma_step02.py` 的核心参数，可直接照抄：

```python
W, H, FPS = 1280, 720, 24
GREEN_HUE_MIN = 70.0    # 绿色色相下界
GREEN_HUE_MAX = 170.0   # 绿色色相上界
SAT_MIN = 0.15
VAL_MIN = 0.15
HUE_FEATHER = 6.0       # 边界渐变（度）
```

输出：VP9 + `yuva420p`，`-crf 30`。

用 ffmpeg 一行实现的简化版：

```bash
ffmpeg -y -i input.mp4 \
  -vf "chromakey=0x00FF00:0.20:0.06,format=yuva420p" \
  -c:v libvpx-vp9 -pix_fmt yuva420p -crf 30 -b:v 0 -an \
  output.webm
```

> ⚠️ 两个必踩的坑：
> 1. **解码端必须显式 `-c:v libvpx-vp9`**，否则 ffmpeg 自选解码器会丢 alpha → 黑底
> 2. **`scale` 滤镜默认丢 alpha**，需 `format=yuva420p` 强制保留

### 路线 B：手动

1. 剪映或 Premiere 里手工抠像
2. 导出**带 alpha 的 mov**（ProRes 4444 with Alpha，或 PNG 序列封装）
3. 转回 webm：
   ```bash
   ffmpeg -y -i keyed.mov -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 32 -row-mt 1 -an out.webm
   ```

### 抠像后自检

```bash
# 确认 alpha 真的存在：应看到 ALPHA_MODE=1
ffprobe -v error -show_streams out.webm | findstr /C:"ALPHA_MODE"

# 抽一帧看四角是否透明
ffmpeg -y -c:v libvpx-vp9 -i out.webm -vf "select=eq(n\,0)" -frames:v 1 -pix_fmt rgba frame0.png
```

---

## 四、逐帧转 WebP（本文档核心）

### 用现成脚本

[tools/webm_to_frames.py](dafeiyu_pet_raising/tools/webm_to_frames.py)

```powershell
$py = "C:\Users\周万一\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
$env:FFMPEG  = "D:\bin\ffmpeg.exe"
$env:FFPROBE = "D:\bin\ffprobe.exe"
$env:PYTHONUTF8 = "1"

# 先干跑看测量结果
& $py tools\webm_to_frames.py "吃白饭.webm" "ext_rice" --dry

# 正式转换
& $py tools\webm_to_frames.py "吃白饭.webm" "output\ext_rice" --clip ext_rice
```

### 关键参数（**已实测验证可复现本地资产**）

| 参数 | 值 | 依据 |
|---|---|---|
| 画布 | **412 × 344** | 本地 112 个 clip 全部一致 |
| 裁切窗 | **crop=412:344:100:0** | 上游 `assetSource.crop = [100,0,412,344]` |
| 缩放 | **不做缩放** | 上游已归一化过 |
| 帧率 | 24 fps（源），输出 `frameMs: 42` | 全库统一 |
| 编码 | WebP `quality=68`，RGBA | 上游 `webpQuality: 68` |

### 验证结果

用上游 `吃白饭.webm` 跑一遍，与本地已有 `ext_rice` 逐帧比对：

| 帧 | 我的 bbox | 本地 bbox | 一致 |
|---|---|---|---|
| 1 | (111, 63, 321, 323) | (111, 63, 321, 323) | ✅ |
| 61 | (111, 64, 324, 323) | (111, 64, 324, 323) | ✅ |
| 121 | (119, 67, 328, 323) | (119, 67, 328, 323) | ✅ |
| 181 | (110, 63, 326, 323) | (110, 63, 326, 323) | ✅ |
| 241 | (111, 63, 322, 337) | (111, 63, 322, 337) | ✅ |

像素平均误差 **1.12/255**，明显差异像素占比 **0.01%**。体积 3.53 MB vs 本地 4.97 MB（quality 略有差异，不影响观感）。

> **结论：这套参数能精确复现本地资产**，不是猜的。

### 三个必须知道的坑

**坑 1：ffmpeg 写 .webp 序列会只出 1 帧**
`.webp` 默认走 animated-webp 复用器，把整段动画塞进一个文件。
→ 脚本采用**两步法**：先导 PNG 序列（`%05d.png`），再用 Pillow 转 WebP。稳。

**坑 2：image2 无法从 `001.webp` 推断序列**
报 `Cannot write more than one file with the same name`。
→ 同上，走 PNG 中转。

**坑 3：慢**
241 帧约 **3~4 分钟**（PNG 导出 + WebP 编码）。18 秒的 XL 档（432 帧）约 6~7 分钟。建议后台跑。

---

## 五、注册到插件

### 用现成脚本

[tools/register_clip.py](dafeiyu_pet_raising/tools/register_clip.py)

```powershell
& $py tools\register_clip.py --clip ext_chips --frames 241 --loop false --idle --src "薯片.webm"
```

它会改三处（**缺一不生效**）：

| 位置 | 内容 | 不做的后果 |
|---|---|---|
| `assets/pet-manifest.json` 的 `clips` | 帧清单、`frameMs:42`、`loop` | helper 不认识这个动作 |
| `lib/actions.js` 的 `ACTIONS` | 加入数组 | **工具抛「未知动作」** |
| `manifest` 的 `idleMicroClips` | 加入待机池（加 `--idle`） | 不会自动出现 |

### 手动改的话

**manifest 条目**：
```json
"ext_chips": {
  "frames": ["ext_chips/001.webp", "...", "ext_chips/241.webp"],
  "frameMs": 42,
  "loop": false,
  "source": { "file": "薯片.webm", "startFrame": 0, "endFrame": 241, "frameCount": 241 }
}
```

**actions.js**：
```js
  // 吃喝
  'ext_rice', ..., 'ext_chongyangcake', 'ext_chips',
```

> ⚠️ 改 `actions.js` 时**不要用跨行正则**找插入点。我实测踩过：`// 吃喝(.*?)// 玩乐` 会贪进后面的组，插到数组末尾并产生 `,,` 语法错误。脚本已改为**逐行扫描**，并加了双逗号自检。

### 命名规范

| 项 | 规则 | 示例 |
|---|---|---|
| clip id | 全小写、`ext_` 前缀、多词连写 | `ext_chips`、`ext_bubbletea` |
| 目录 | `assets/pet/<clip_id>/` | `assets/pet/ext_chips/` |
| 文件名 | 3 位零填充 | `001.webp` … `241.webp` |

---

## 六、验证

### 重启后查

```powershell
# 1. 动作是否被认到（总数应从 104 变 105）
Invoke-RestMethod http://127.0.0.1:7799/health | Select-Object -ExpandProperty clips

# 2. 直接试播
Invoke-RestMethod -Method Post http://127.0.0.1:7799/play `
  -ContentType "application/json" -Body '{"clip":"ext_chips"}'
```

### 肉眼验收

- [ ] 能正常播放、不卡在某一帧
- [ ] 从 `idle` 切进来时角色**不跳位**（这条最能暴露裁切错误）
- [ ] 播完能回到 idle
- [ ] 气泡不遮挡角色

---

## 七、⚠️ 最重要的一条：别改 node_modules

新增的素材和配置都在：

```
C:\Users\周万一\.dsh\profiles\desktop\node_modules\dsh-dafeiyu-pet\
```

**`dsh plugin add` 重装插件会全部覆盖**。三个可行方案：

### 方案 1（推荐）：自建素材包

1. 把改好的 `assets/` 打包
2. 传到你的 GitHub Release
3. 设环境变量指向它：
   ```powershell
   $env:DAFEIYU_PET_ASSETS_URL = "https://github.com/xiaoberber8-ai/dafeiyu_pet_raising/releases/download/v1/assets.tar.gz"
   ```
4. 重装插件后自动下载你的版本

这是插件**原生支持**的机制（见 `lib/assets.js`）。

### 方案 2：fork 一份插件

把 `dsh-dafeiyu-pet` 完整复制出来，改 `package.json` 的 `dsh.assets.url`，作为独立插件安装。

### 方案 3（最省事但最脆弱）：定期备份

```powershell
Copy-Item "C:\Users\周万一\.dsh\profiles\desktop\node_modules\dsh-dafeiyu-pet\assets\pet-manifest.json" `
          "你的仓库\backup\pet-manifest.json" -Force
Copy-Item "C:\Users\周万一\.dsh\profiles\desktop\node_modules\dsh-dafeiyu-pet\lib\actions.js" `
          "你的仓库\backup\actions.js" -Force
```

> `register_clip.py` 会自动生成 `.bak` 备份，算是多一层保险。

---

## 八、一次性检查清单

新动作从 0 到能播，逐项打勾：

**写**
- [ ] 提示词沿用通用前缀，一字未改
- [ ] 写清道具形态、核心笑点、情绪曲线
- [ ] 每段有 ⚠️ 强调项
- [ ] 结束状态写明「最终帧＝标准正面站立」

**生成**
- [ ] 图生视频，首帧用 `ref_standing_640x360.png`
- [ ] 背景纯净 `#00FF00`
- [ ] 首末帧都是标准站立
- [ ] 全程无平移
- [ ] 时长符合 S/M/L/XL 档位

**抠像**
- [ ] 边缘无绿边白边
- [ ] `ffprobe` 能看到 `ALPHA_MODE=1`
- [ ] 四角透明

**转帧**
- [ ] 412×344
- [ ] 帧数 = 时长 × 24
- [ ] 体积在 3.5~10 MB（241 帧参考值）
- [ ] 命名 `001.webp` 起

**注册**
- [ ] `assets/pet/<clip>/` 存在
- [ ] manifest `clips` 有条目
- [ ] `actions.js` 的 `ACTIONS` 有 id
- [ ] 想进待机池则加了 `idleMicroClips`

**验证**
- [ ] `/health` 的 clips 数组里有它
- [ ] `POST /play` 返回 ok
- [ ] 实际播放不跳位、能回 idle

**保护**
- [ ] 已备份或已走 Release 方案

---

## 九、常见故障

| 现象 | 原因 | 处理 |
|---|---|---|
| 转出来只有 1 帧 | ffmpeg 用了 animated-webp | 用 `webm_to_frames.py` 的两步法 |
| `Cannot write more than one file with the same name` | image2 推断不出序列 | 同上 |
| 播出来是黑底 | 解码时丢了 alpha | 解码加 `-c:v libvpx-vp9` |
| 切动作时角色跳位 | 裁切窗不对 | 确认 `crop=412:344:100:0` |
| 工具报「未知动作」 | 没加进 `ACTIONS` | 改 `lib/actions.js` |
| 右键菜单里没动作 | helper 没重启 | 完全退出 DSH 再开 |
| `,,` 语法错误 | 正则插入点错误 | 用 `register_clip.py`（已修） |
| 重装插件后动作没了 | node_modules 被覆盖 | 见第七节 |

---

## 十、相关文件

| 文件 | 用途 |
|---|---|
| [dafeiyu-video-prompts-ALL.md](dafeiyu-video-prompts-ALL.md) | 17 条提示词总集 |
| [dafeiyu-food-drink-inventory.md](dafeiyu-food-drink-inventory.md) | 吃喝动作台账、缺口、映射表 |
| [webm_to_frames.py](dafeiyu_pet_raising/tools/webm_to_frames.py) | webm → WebP 帧序列 |
| [register_clip.py](dafeiyu_pet_raising/tools/register_clip.py) | 三处配置一次改完 |
| `assets/upstream-webm/food-drink/` | 上游 25 个源视频（风格基准） |
