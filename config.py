import os

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))


class Config:
    feishu_app_token: str
    feishu_table_id: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    sender_name: str
    cv_path: str

    def __init__(self) -> None:
        for key in (
            "FEISHU_APP_TOKEN",
            "FEISHU_TABLE_ID",
            "SMTP_HOST",
            "SMTP_USER",
            "SMTP_PASS",
            "SENDER_NAME",
            "CV_PATH",
        ):
            value = os.getenv(key)
            if not value:
                raise ValueError(f"Missing required environment variable: {key}")
            setattr(self, key.lower(), value)

        _smtp_port_raw = os.getenv("SMTP_PORT")
        if not _smtp_port_raw:
            raise ValueError("Missing required environment variable: SMTP_PORT")
        self.smtp_port = int(_smtp_port_raw)
