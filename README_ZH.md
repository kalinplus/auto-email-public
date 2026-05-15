# Auto Email

中文 | [English](README.md)

自动化研究生申请套磁邮件发送，通过 skill 配合 claude code 完成一键：飞书归档（可选）和 SMTP 定时 (GitHub Actions) 批量发送。

## 工作流程

```
上游（如 tabbit 等联网搜索能力较强的 AI 产品）提供导师信息（JSON）→ 写入飞书表格（可选，本地操作）→ 追加到 advisors.json → git push → GitHub Actions 定时发送邮件
```

- **本地**：通过 `/advisor-mailer` skill 将导师信息写入飞书并追加到 `advisors.json`
- **远程**：GitHub Actions cron 触发 `--send`，跳过已发送条目

## 项目结构

```
├── main.py              # CLI 入口（--add / --write / --send / --all）
├── config.py            # .env 配置读取
├── verify.py            # arxiv 论文校验（暂时禁用）
├── feishu_writer.py     # 写入飞书多维表格（依赖 lark-cli）
├── mailer.py            # SMTP 邮件发送（复用连接 + 间隔防限流）
├── advisors.json        # 导师数据（邮件队列）
├── .env.template        # 环境变量模板
├── .claude/skills/      # advisor-mailer skill
└── .github/workflows/   # GitHub Actions 定时发送
```

## 快速开始

### 1. Clone

```bash
git clone <repo-url>
cd auto-email
```

推荐将自己 GitHub 上的该仓库设置为私有，防止隐私信息泄露。所以推荐 clone 而非 fork

### 2. 放入 CV

```bash
cp /path/to/你的CV.pdf ./CV.pdf
```

### 3. 配置 GitHub Secrets

仓库 → Settings → Secrets and variables → Actions，添加以下 Secret：

| Secret | 说明 | 示例 |
|---|---|---|
| `SMTP_HOST` | SMTP 服务器 | `smtp.163.com` |
| `SMTP_PORT` | 端口 | `465` |
| `SMTP_USER` | 发件邮箱 | `you@163.com` |
| `SMTP_PASS` | 邮箱授权码 | （一般是 16 位的，不是登录密码） |
| `SENDER_NAME` | 发件人显示名 | `张三` |
| `FEISHU_APP_TOKEN` | 飞书多维表格 token *（可选）* | `...` |
| `FEISHU_TABLE_ID` | 飞书表 ID *（可选）* | `...` |
| `CV_PATH` | CV 文件路径 | `./CV.pdf` |

上述字段的获取详情，自己上网搜。

不使用飞书的话，`FEISHU_APP_TOKEN` 和 `FEISHU_TABLE_ID` 可以不配。在使用 skill 的时候新增待发送条目时，选择相应选项就行。

如果使用飞书表格对套磁的老师进行归档，需要新建一个飞书多维表格，获取其 Token 和 Table ID（这两个值对应填入上方的 `FEISHU_APP_TOKEN` 和 `FEISHU_TABLE_ID`）。表格中至少（当然可以有更多字段方便记录复盘）需要包含以下字段：

| 字段名 | 类型 | 说明 |
|---|---|---|
| 导师姓名 | 文本 | 必填 |
| 学校-学院 | 文本 | 必填 |
| 研究领域 | 文本 | 可选 |
| 发信邮箱 | 文本 | 必填 |
| 当前进展 | 文本 | 固定写为"已发信" |
| 初次发信日期 | 日期 | Unix 毫秒时间戳，自动填入 |
| 个人主页 | URL | 可选 |

### 4. 开启 Actions 写入权限

仓库 → Settings → Actions → General → Workflow permissions → 选 **Read and write permissions** → Save。

### 5. 添加导师

推荐让 Claude Code 等 CLI 工具使用 `.claude` 目录下的 `advisor-mailer` skill, 输入为 [导师数据格式](#导师数据格式) 中给出的结构化 json 字段，它会向你询问，自动完成写入飞书表格（可选）- 更改 `advisors.json` 文件并提醒你等操作

### 6. 推送发送

```bash
git add advisors.json CV.pdf
git commit -m "add advisors"
git push
```

Actions 会在下一个 cron 时间点自动读取 `advisors.json` 并发送邮件，也可去 Actions 页手动 **Run workflow** 立即触发。

触发之后 `advisors.json` 里已有的条目的 `sent` 字段会被改为 `true` （代表已经发送过邮件了），因此需要 `git pull` 最新的更改，防止冲突。

## 导师数据格式

`advisors.json` 中每条记录：

```json
{
  "name_zh": "导师中文名",
  "name_en": "导师英文名",
  "school_college": "学校-学院",
  "research_field": "研究方向简述（可选）",
  "homepage": "https://homepage.url（可选）",
  "email": "advisor@university.edu",
  "bridge_paper": {
    "arxiv_query": "论文标题或 arxiv id（可选）"
  },
  "email_subject": "套磁邮件主题",
  "email_body": "邮件正文内容"
}
```

如何获取呢？推荐使用 Tabbit 等具有较强联网搜索能力的 AI 产品，让它根据学校和老师名搜索并生成这样结构化的字段。


## 内部字段（自动管理）

以下字段由系统自动添加，不需要手动设置：

| 字段 | 作用 |
|---|---|
| `sent` | `true` = 已发送，永远跳过 |
| `sent_at` | 发送时间（ISO 格式） |
| `verified` | arxiv 校验结果（暂时禁用） |
| `feishu_record_id` | 飞书记录 ID，已有则更新而非新增 |
| `error` | 失败原因，不影响其他条目 |

## 本地使用（可选）

不使用 GitHub Actions 也可以本地直接发送：

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.template .env
# 编辑 .env 填入真实配置

# 追加导师
python main.py advisors.json --add '{"name_zh":"...", ...}'

# 写入飞书（需要 lark-cli）
python main.py advisors.json --write

# 发送邮件
python main.py advisors.json --send

# 一键全跑（飞书 + 发送）
python main.py advisors.json --all
```

## 定时发送

默认 cron 为北京时间 07:05，可在 `.github/workflows/send-email.yml` 中修改。

GitHub Actions cron 可能延迟 60–120 分钟(个人体验是设置 7:05，会在 8:05 左右触发)，这是平台正常行为。如需立即发送，去 Actions 页手动触发。

## 技术栈

- Python 3.9+ / smtplib / argparse
- tenacity（重试）、python-dotenv（配置）
- lark-cli（飞书多维表格，仅本地使用）
- GitHub Actions（定时发送 + 手动触发）

## TODO
arxiv（论文校验）：对上游 JSON 里的论文进行校验，确保这个论文里有目标这个导师的名字。

## License

MIT

