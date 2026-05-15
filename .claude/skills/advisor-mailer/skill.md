---
name: advisor-mailer
description: |
  Write advisor data to Feishu and queue email for GitHub Actions to send. Trigger when user provides an advisor JSON object and wants to send email or write to Feishu. Triggers on phrases like: 发邮件, 发送邮件, 发给导师, send email, 发信, 套磁邮件, 写入飞书, 同步飞书.
---

# Advisor Mailer

帮用户将套磁信息归档到飞书，并更新 `advisors.json` 推送到 GitHub，由 GitHub Actions 定时发送邮件。

## 流程概述

```
写入飞书 (--write) → 更新 advisors.json → 提醒用户 git push → Actions 定时发送
```

本地只做飞书写入和状态更新，邮件发送由 GitHub Actions cron 完成。

## 输入格式

用户提供一个 JSON 对象（单条），包含以下字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `name_zh` | 是 | 导师中文名 |
| `name_en` | 否 | 英文名 |
| `school_college` | 是 | 学校-学院 |
| `email` | 是 | 导师邮箱 |
| `email_subject` | 是 | 邮件主题 |
| `email_body` | 是 | 邮件正文 |
| `homepage` | 否 | 个人主页 |
| `research_field` | 否 | 研究方向 |
| `bridge_paper` | 否 | 桥接论文信息 |

用户可能直接粘贴 JSON，也可能通过对话描述导师信息。如果缺少必填字段，先问用户补全。

## 工作流程

### Step 1: 确认信息 + 选择操作范围

收到 JSON 后，展示关键信息，并用选择题让用户确认操作范围：

```
发信目标:
  导师: {name_zh} ({name_en})
  学校: {school_college}
  邮箱: {email}
  主题: {email_subject}
  正文: {email_body 前 50 字}...
```

然后通过 AskUserQuestion 让用户选择（单选）：
- "仅写入 JSON" — 只追加 advisors.json，不写飞书
- "写入 JSON + 飞书" — 追加 advisors.json 并写入飞书表格（推荐）
- "写入 JSON + 飞书 + 立即发信" — 全部执行，不等 Actions 定时

如果用户在消息中已明确表达了意图（如"不写飞书"/"只写 json"/"立即发"），则跳过确认，直接按用户要求执行。

### Step 2: 写入 advisors.json（必做）

将新导师追加到 `advisors.json`（自动初始化 `sent: false`、`verified: null`）：

```bash
python main.py advisors.json --add '<用户的 JSON 字符串>'
```

这一步无条件执行。`--add` 会保留已有记录，仅追加新条目。

### Step 3: 写入飞书（按用户选择）

仅在 Step 1 用户选择了包含飞书的选项时执行：

```bash
python main.py advisors.json --write
```

执行后检查最后一条记录的状态：
- `feishu_record_id` 存在 → 飞书写入成功
- `error` 字段存在 → 出错，展示错误信息

### Step 4: 立即发信（按用户选择）

仅在 Step 1 用户选择了"立即发信"时执行：

```bash
python main.py advisors.json --all
```

### Step 5: 提醒用户推送

提醒用户推送以触发 GitHub Actions 定时发送：

> 已更新 advisors.json。请推送到 GitHub：
> ```
> git add advisors.json && git commit -m "add advisor: {name_zh}" && git push
> ```

如果用户希望立即发送（不等定时），可以去 GitHub Actions 页手动 Run workflow。

## 项目路径

工作目录: 当前仓库根目录

所有命令在该目录下执行。
