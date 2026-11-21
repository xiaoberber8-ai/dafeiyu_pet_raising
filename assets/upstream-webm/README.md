# 上游动作素材库 · 大肥鱼养成项目

> 来源：https://github.com/PC2005-cloud/dsh-pet @ `549fff2ea33c2acfb16612c76912c6137da4a758`
> 许可：**MIT**（见 `LICENSE-upstream-MIT.txt`，转载必须保留）
> 归档日期：2026-11-21
> 所有文件：VP9-alpha WebM / 640×360 / 24fps / 10.042s / 241 帧

---

## 分类说明

本库从上游 106 个动作中筛出**与养成「吃」系统相关**的素材，按用途分为三类，
另有一个「未使用」目录存放当初误归档、实际与进食无关的文件。

| 目录 | 数量 | 用途 | 是否用于养成 |
|---|---|---|---|
| `01-日常饮食/` | 13 | 免费剩饭、零食、三餐、大餐等日常食物 | ✅ 是 |
| `02-节日时令/` | 8 | 6 个时令节令 + 月饼（跨类） | ✅ 是 |
| `03-状态交互/` | 1 | `ext_whattoeat`「吃什么」提示动作 | ✅ 是 |
| `99-未使用（非进食）/` | 3 | 打瞌睡、小憩、刷牙 | ❌ 否（当初误归档） |

**会用到的共 22 个**（13 + 8 + 1）。

---

## 01-日常饮食（13 个）

| 源文件 | 对应 clip id | 养成档位 | 备注 |
|---|---|---|---|
| 吃Token.webm | `eat_token` | 专属 | 唯一可由 manifest 源名直接佐证 |
| 吃白饭.webm | `ext_rice` | 1 免费剩饭 / 3 便当 | 与便当撞车，见台账缺口 2 |
| 偷吃零食被抓住.webm | `ext_snack` | 2 小零食 | 档 2 唯一动作 |
| 吃早餐.webm | `ext_breakfast` | 4 正餐 | |
| 吃午餐.webm | `ext_lunch` | 4 正餐 | |
| 吃晚餐.webm | `ext_dinner` | 4 正餐 | |
| 大口吃零食.webm | `ext_bigsnack` | 5 大餐 | |
| 吃冰淇淋融化.webm | `ext_icecream` | 2 小零食 | 融化机制，与新增巧克力区分 |
| 吃西瓜.webm | `ext_watermelon` | 3 便当 | |
| 吃大闸蟹.webm | `ext_crab` | 5 大餐 | 剥壳机制 |
| 涮火锅.webm | `ext_hotpot` | 5 大餐 | 短版（与新增 15s 丰盛版并存） |
| 吃饺子.webm | `ext_dumpling` | 5 大餐 / 冬至 | 跨类 |
| 吃长寿面.webm | `ext_noodles` | 3 便当 | 长度梗；新增提示词已避开 |

## 02-节日时令（8 个）

| 源文件 | 对应 clip id | 节日 | 养成档位 |
|---|---|---|---|
| 吃汤圆.webm | `ext_tangyuan` | 元宵 | 6 节日特供 |
| 吃粽子.webm | `ext_zongzi` | 端午 | 6 节日特供 |
| 吃年糕.webm | `ext_niangao` | 春节 | 6 节日特供 |
| 吃青团.webm | `ext_qingtuan` | 清明 | 6 节日特供 |
| 吃重阳糕.webm | `ext_chongyangcake` | 重阳 | 6 节日特供 |
| 吃腊八粥.webm | `ext_laba` | 腊八 | 6 节日特供 |
| 中秋赏月吃月饼.webm | `ext_midautumn` | 中秋 | 6 节日特供（在 actions.js 归「节日」组） |
| 吃糖葫芦.webm | `ext_tanghulu` | 小吃/节令 | 2 或 3 |

## 03-状态交互（1 个）

| 源文件 | 对应 clip id | 用途 |
|---|---|---|
| 是啊，吃什么.webm | `ext_whattoeat` | 饥饿提示气泡触发的动作 |

## 99-未使用（非进食）

| 源文件 | 实际性质 |
|---|---|
| 打瞌睡被惊醒.webm | 睡眠行为，属 `ext_doze` |
| 原地小憩沉眠.webm | 睡眠行为，属 `ext_nap` |
| 晨间刷牙.webm | 洗漱行为，属 `ext_brush` |

> 这三个当初因关键词匹配（`crab` 等）被误归入进食资产，**不在养成「吃」系统使用范围**，保留在此仅供参考。

---

## 来源与许可（重要）

1. 这些是上游**已处理完成的播放入库文件**（VP9-alpha WebM），不是原始 AI 生成 mp4。
2. 上游素材由 AI 生成（作者自述使用豆包），经 `scripts/` 四步脚本链处理。本项目仅转载成品。
3. MIT 许可要求保留版权与许可声明：**`LICENSE-upstream-MIT.txt` 必须随素材一同保留**。
4. 上游项目名与角色身份归原作者所有；本项目为个人养成项目，与 DeepSeek、PC2005-cloud 无隶属关系。

## 怎样用这些素材

见 `docs/dafeiyu-workflow.md`。简要流程：

```
webm（本库）→ 抠像/已透明 → webm_to_frames.py → WebP 帧序列
            → register_clip.py → 重启 DSH → /health + /play 验证
```

裁切参数（实测可复现本地资产）：`crop=412:344:100:0`，不做缩放，`frameMs: 42`。
