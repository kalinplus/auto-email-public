# Auto Email

[中文](README_ZH.md) | English

Automated graduate application cold-email sender. With the skill + Claude Code workflow, you can run one-click Feishu archiving (optional) and scheduled SMTP batch sending (GitHub Actions).

## Workflow

```
Provide advisor info (JSON) → Write to Feishu table (optional, local) → Append to advisors.json → git push → GitHub Actions sends unsent emails on schedule
```

- **Local**: Use the `/advisor-mailer` Claude Code skill to write advisor info to Feishu and append to `advisors.json`
- **Remote**: GitHub Actions triggers `--send` on cron, skips already-sent entries

## Project Structure

```
├── main.py              # CLI entry point (--add / --write / --send / --all)
├── config.py            # .env config loader
├── verify.py            # arxiv paper verification (temporarily disabled)
├── feishu_writer.py     # Feishu table writer (depends on lark-cli)
├── mailer.py            # SMTP email sender (connection reuse + rate limiting)
├── advisors.json        # Advisor data (email queue)
├── .env.template        # Environment variable template
├── .claude/skills/      # advisor-mailer skill
└── .github/workflows/   # GitHub Actions scheduled sender
```

## Quick Start

### 1. Clone

```bash
git clone <repo-url>
cd auto-email
```

It is recommended to keep your GitHub repository private to avoid leaking personal information, so clone is recommended over fork.

### 2. Prepare Your CV

Place your CV as `CV.pdf` in the project root:

```bash
cp /path/to/your/CV.pdf ./CV.pdf
```

### 3. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description | Example |
|---|---|---|
| `SMTP_HOST` | SMTP server | `smtp.163.com` |
| `SMTP_PORT` | SMTP port | `465` |
| `SMTP_USER` | Sender email | `you@163.com` |
| `SMTP_PASS` | Email app password | (usually 16 characters, not your login password) |
| `SENDER_NAME` | Display name | `Zhang San` |
| `FEISHU_APP_TOKEN` | Feishu table token *(optional)* | `...` |
| `FEISHU_TABLE_ID` | Feishu table ID *(optional)* | `...` |
| `CV_PATH` | CV file path | `./CV.pdf` |

For details on how to obtain these values, search online by yourself.

If you do not use Feishu, `FEISHU_APP_TOKEN` and `FEISHU_TABLE_ID` are not required. When using the skill to add pending entries, choose the corresponding option.

### 4. Enable Actions Write Permission

**Settings → Actions → General → Workflow permissions** → Select **Read and write permissions** → Save.

### 5. Add Advisor Entries

It is recommended to use CLI tools like Claude Code with the `advisor-mailer` skill in `.claude` and provide the structured JSON described in [Advisor Data Format](#advisor-data-format). It will ask for confirmations, then automatically complete Feishu writing (optional), `advisors.json` update, and reminders.

### 6. Push and Send

```bash
git add advisors.json CV.pdf
git commit -m "add advisors"
git push
```

GitHub Actions will send unsent emails on the next cron trigger. You can also manually trigger it from the **Actions** tab.

After triggering, existing entries in `advisors.json` will have `sent` set to `true` (meaning already sent). You should run `git pull` to get the latest changes and avoid conflicts.

## Advisor Data Format

Each entry in `advisors.json`:

```json
{
  "name_zh": "Advisor Chinese Name",
  "name_en": "Advisor English Name",
  "school_college": "University-Department",
  "research_field": "Brief research description (optional)",
  "homepage": "https://homepage.url (optional)",
  "email": "advisor@university.edu",
  "bridge_paper": {
    "arxiv_query": "Paper title or arxiv ID for verification (optional)"
  },
  "email_subject": "Email subject line",
  "email_body": "Email body text — write your cold email content here"
}
```

How to get these fields? It is recommended to use AI products with stronger web search capabilities (such as Tabbit), and let them search by school and advisor name to generate this structured output.

## Internal Fields (auto-managed)

These fields are added automatically — you don't need to set them:

| Field | Purpose |
|---|---|
| `sent` | `true` = already sent, will be skipped |
| `sent_at` | ISO timestamp of when the email was sent |
| `verified` | arxiv verification result (temporarily disabled) |
| `feishu_record_id` | Feishu record ID for upsert |
| `error` | Failure reason (doesn't affect other entries) |

## Local Usage (Optional)

If you prefer not to use GitHub Actions:

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your real credentials

# Add advisor
python main.py advisors.json --add '{"name_zh":"...", ...}'

# Write to Feishu (requires lark-cli)
python main.py advisors.json --write

# Send emails
python main.py advisors.json --send

# Run all steps
python main.py advisors.json --all
```

## Scheduled Sending

Default cron is Beijing time 07:05. You can change it in `.github/workflows/send-email.yml`.

GitHub Actions cron may delay 60-120 minutes (in practice, setting 07:05 may trigger around 08:05). This is normal platform behavior. If you need immediate sending, run it manually from the Actions page.

## Tech Stack

- Python 3.9+ / smtplib / argparse
- tenacity (retry), python-dotenv (config)
- lark-cli (Feishu table, local only)
- GitHub Actions (scheduled + manual trigger)

## TODO

arxiv (paper verification): verify papers in upstream JSON and ensure the target advisor name appears in the paper.

## License

MIT
