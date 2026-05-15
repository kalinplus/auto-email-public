# Auto Email

[中文](README_ZH.md) | English

Automated cold email sender for graduate school applications. Collect advisor info, write to Feishu (optional), and send via SMTP — driven by CLI or GitHub Actions cron.

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

### 2. Prepare Your CV

Place your CV as `CV.pdf` in the project root:

```bash
cp /path/to/your/CV.pdf ./CV.pdf
```

### 3. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description | Example |
|---|---|---|
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `465` |
| `SMTP_USER` | Sender email | `you@gmail.com` |
| `SMTP_PASS` | Email app password | (not your login password) |
| `SENDER_NAME` | Display name | `Your Name` |
| `FEISHU_APP_TOKEN` | Feishu table token *(optional)* | `W8d2bsAz...` |
| `FEISHU_TABLE_ID` | Feishu table ID *(optional)* | `tblJNhhDD...` |
| `CV_PATH` | CV file path | `./CV.pdf` |

If you don't use Feishu, the `FEISHU_APP_TOKEN` and `FEISHU_TABLE_ID` secrets are not required — just don't use the `--write` flag.

### 4. Enable Actions Write Permission

**Settings → Actions → General → Workflow permissions** → Select **Read and write permissions** → Save.

### 5. Add Advisor Entries

Edit `advisors.json` directly, or use the CLI:

```bash
python main.py advisors.json --add '{"name_zh":"...", "name_en":"...", "school_college":"...", "email":"...", "email_subject":"...", "email_body":"..."}'
```

### 6. Push and Send

```bash
git add advisors.json CV.pdf
git commit -m "add advisors"
git push
```

GitHub Actions will send unsent emails on the next cron trigger. You can also manually trigger it from the **Actions** tab.

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

### Writing Effective Cold Emails

Your `email_body` should be concise and personalized:

1. **Who you are**: Your name, current institution, and program
2. **Why this advisor**: Mention a specific paper or research direction that interests you
3. **What you bring**: Your relevant skills, experience, or research background
4. **Call to action**: Ask if they are accepting new students or request a brief meeting

Example (customize to your own background):

```
Dear Professor [Name],

My name is [Your Name] and I am currently a [degree] student at [University]. I have been following your work on [specific topic], particularly your paper "[paper title]".

I am very interested in pursuing [degree] under your supervision. My background in [relevant skill/field] has prepared me well for research in this area. [1-2 sentences about your relevant experience].

Would you be available for a brief call to discuss potential opportunities in your group? I have attached my CV for your reference.

Thank you for your time.

Best regards,
[Your Name]
```

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

Default cron is UTC 23:05 (Beijing 07:05). Adjust in `.github/workflows/send-email.yml`. GitHub Actions cron may delay 5–15 minutes — this is normal platform behavior. Use **Run workflow** in the Actions tab for immediate sending.

## Tech Stack

- Python 3.9+ / smtplib / argparse
- arxiv (paper verification), tenacity (retry), python-dotenv (config)
- lark-cli (Feishu table, local only)
- GitHub Actions (scheduled + manual trigger)

## License

MIT
