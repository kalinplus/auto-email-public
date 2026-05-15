import json
import logging
import subprocess
from datetime import datetime, timezone

from config import Config

logger = logging.getLogger(__name__)


def write_advisors(advisors: list[dict], config: Config) -> list[dict]:
    for advisor in advisors:
        if advisor.get("verified") is False:
            logger.warning("Skipping unverified advisor: %s", advisor.get("name_zh", "N/A"))
            continue

        name_zh = advisor.get("name_zh")
        school_college = advisor.get("school_college")
        email = advisor.get("email")

        if not name_zh or not school_college or not email:
            logger.error("Missing required field(s) for advisor: name_zh=%s, school_college=%s, email=%s", name_zh, school_college, email)
            advisor["error"] = "Missing required field(s): name_zh, school_college, or email"
            continue

        fields = {
            "导师姓名": name_zh,
            "学校-学院": school_college,
            "研究领域": advisor.get("research_field", ""),
            "发信邮箱": email,
            "当前进展": "已发信",
            "初次发信日期": int(datetime.now(timezone.utc).timestamp() * 1000),
        }

        homepage = advisor.get("homepage")
        if homepage:
            fields["个人主页"] = homepage

        payload = json.dumps(fields, ensure_ascii=False)

        cmd = [
            "lark-cli",
            "base",
            "+record-upsert",
            "--base-token",
            config.feishu_app_token,
            "--table-id",
            config.feishu_table_id,
            "--json",
            payload,
        ]

        if advisor.get("feishu_record_id"):
            cmd.extend(["--record-id", advisor["feishu_record_id"]])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            response = json.loads(result.stdout)
            record_id = (
                response.get("data", {})
                .get("record", {})
                .get("record_id_list", [None])[0]
            )
            if record_id:
                advisor["feishu_record_id"] = record_id
                logger.info("Successfully wrote/updated record for %s (record_id=%s)", name_zh, record_id)
        except subprocess.CalledProcessError as e:
            logger.error("lark-cli failed for %s: %s", name_zh, e.stderr or e.stdout or str(e))
            advisor["error"] = f"lark-cli failed: {e.stderr or e.stdout or str(e)}"
        except json.JSONDecodeError as e:
            logger.error("Failed to parse lark-cli output for %s: %s", name_zh, e)
            advisor["error"] = f"Failed to parse lark-cli output: {e}"

    return advisors
