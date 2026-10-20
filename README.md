# Qoder Usage Statusbar

给 [Qoder](https://qoder.com) / QoderWork 加一条**本地、离线**的额度状态栏：实时显示
当前模型的 **credit 消耗**、**上下文窗口占用率**、**每轮耗时**。数据全部来自本机
Qoder 会话日志，**不联网、不上传任何东西**。

简体中文 · [English](README.en.md) · Windows / macOS / Linux · Python 3.8+ · [MIT](LICENSE)

## 为什么没有 token 数和余额

有些额度工具会显示真实 token 用量、tok/s，以及各家模型的**剩余额度 + 重置倒计时**，
靠的是「本地存真实 token」+「联网查供应商额度 API」。

**这两条在 Qoder 上都不成立**：

- Qoder 落盘会话日志时，把 `input_tokens / output_tokens / cache_*` **一律置零**。
  本机 1900+ 条记录里没有一条非零 —— 所以真实 token 数和 tok/s **算不出来**。
- 本地文件里只有 `plan`（Free/付费），**没有剩余 credit 数字，也没有可查询的公开额度接口**。
  余额只能在 Qoder 网页账户面板看到。

真正可靠、且完全能本地算出来的指标是 `usage.credits`（每次请求消耗的 credit，有值）
和 `context_usage_ratio`（上下文占用率，有值）。所以本项目主打这两项 + 每轮耗时，
把「余额 / 重置」留作后续可选模块（需网页抓取，有 ToS 风险）。

## 能显示什么

| 指标 | 含义 | 来源 |
|---|---|---|
| `context now / peak` | 当前 / 本轮会话峰值的上下文窗口占用百分比（图标颜色随占用从绿到红） | `usage.context_usage_ratio` |
| `session cr` | 当前会话累计消耗的 credit | `usage.credits` 求和 |
| `today cr` | 今日（本地时区）累计消耗的 credit | 同上 |
| `today reqs` | 今日请求次数 | 会话记录计数 |
| `avg turn` | 本轮会话平均每次请求的墙钟间隔（粗略「每轮耗时」） | 相邻时间戳之差 |
| `model` | 当前使用的模型代号 | `message.model` |

## 安装

```bash
# 克隆后
pip install -e .            # 核心引擎（--once / --watch 不需要额外依赖）
pip install -e ".[tray]"    # 额外装 pystray + Pillow 才能用托盘 --tray
```

## 用法

```bash
qoder-usage                 # 打印一次汇总
qoder-usage --watch         # 终端里每 15s 刷新（Ctrl+C 退出）
qoder-usage --tray          # 系统托盘图标，悬停看详情
qoder-usage --interval 10 --watch
```

示例输出：

```
Qoder usage
------------------------
model        : qfmodel
context now  :  6.7%
context peak :  6.7%
session cr   : 7.03
today cr     : 323.36
today reqs   : 1277
avg turn     : 15s
updated      : 22:15:39
```

## 数据在哪

自动扫描（按优先级）：

- `~/.qoderworkcn/projects/**/*.jsonl`  ← QoderWork
- `~/.qoder/projects/**/*.jsonl`        ← Qoder IDE

每条 `type == "assistant"` 的记录里带一个 `usage` 对象即被采集。只读，不写不改。

## 局限

- **不显示真实 token 数 / tok/s** —— Qoder 本地日志里 token 字段被置零（见上）。
- **不显示剩余额度 / 重置倒计时** —— 本地无此数据、无公开接口。
- 「今日」按运行机器的本地时区切分；Qoder 日志时间戳是 UTC，已做换算。

## 许可

MIT
