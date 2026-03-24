import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

async def send_email(to: str, subject: str, html_body: str) -> bool:
    if not settings.smtp_host or not settings.smtp_user:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))
        await aiosmtplib.send(msg, hostname=settings.smtp_host, port=settings.smtp_port, username=settings.smtp_user, password=settings.smtp_password, use_tls=True)
        return True
    except Exception:
        return False

def build_content_email(contents: list[dict], task_name: str) -> str:
    items_html = ""
    for c in contents:
        items_html += f'<div style="border:1px solid #eee;padding:12px;margin:8px 0;border-radius:8px;"><strong>[{c.get("platform","")}]</strong> {c.get("title","无标题")}<br><small style="color:#666;">{(c.get("body",""))[:100]}...</small></div>'
    return f"<h2>ContentFlow - {task_name} 已完成</h2><p>以下内容已自动生成：</p>{items_html}"
