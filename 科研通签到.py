"""
科研通自动签到脚本
环境变量 ABLESCI_AUTH 格式：账号#密码

Author: cjy
"""

import importlib.util
import json
import os
import random
import re
import time
from datetime import datetime
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36",
]

LOG_PATH = "ablesci_sign.log"
NOTIFY_TITLE = "科研通签到"


def build_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.ablesci.com/",
        "X-Requested-With": "XMLHttpRequest",
    }


def read_auth(raw: str) -> tuple[str, str]:
    if "#" not in raw:
        raise ValueError("ABLESCI_AUTH 格式应为 账号#密码")
    email, password = raw.split("#", 1)
    email = email.strip()
    password = password.strip()
    if not email or not password:
        raise ValueError("账号或密码不能为空")
    return email, password


def json_from_response(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"code": -1, "msg": "响应不是 JSON", "raw": raw[:300]}



def extract_user_points(html: str) -> str:
    """Extract current points from AbleSci home HTML."""
    patterns = [
        r'id=["\']user-point-now["\'][^>]*>\s*([^<\s]+)\s*<',
        r'<[^>]+id=["\']user-point-now["\'][^>]*>\s*([^<]+?)\s*</[^>]+>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.I | re.S)
        if match:
            return re.sub(r"\s+", "", match.group(1))
    return ""


def fetch_user_points(opener) -> str:
    """Fetch current points from home page with logged-in opener."""
    home_req = Request("https://www.ablesci.com/", headers=build_headers())
    with opener.open(home_req, timeout=15) as resp:
        home_html = resp.read().decode("utf-8", errors="replace")
    return extract_user_points(home_html)


def format_points_delta(points_before: str, points_after: str) -> str:
    """Format points delta between before and after sign-in."""
    if not points_before or not points_after:
        return ""
    try:
        delta = int(points_after) - int(points_before)
    except ValueError:
        return ""
    return f"{delta:+d}"


def extract_csrf(html: str) -> str:
    patterns = [
        r'<meta name="csrf-token" content="([^"]+)"',
        r'<input type="hidden" id="g_csrf_token" value="([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.I)
        if match:
            return match.group(1)
    raise ValueError("未找到 CSRF token")


def login_and_sign(email: str, password: str) -> dict:
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))

    req_home = Request("https://www.ablesci.com/site/login", headers=build_headers())
    with opener.open(req_home, timeout=15) as resp:
        login_html = resp.read().decode("utf-8", errors="replace")

    csrf = extract_csrf(login_html)
    time.sleep(random.uniform(0.8, 1.8))

    post_data = urlencode(
        {
            "_csrf": csrf,
            "email": email,
            "password": password,
            "remember": "on",
        }
    ).encode("utf-8")

    login_headers = build_headers()
    login_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    login_headers["Referer"] = "https://www.ablesci.com/site/login"
    login_req = Request("https://www.ablesci.com/site/login", data=post_data, headers=login_headers)
    with opener.open(login_req, timeout=15) as resp:
        login_raw = resp.read().decode("utf-8", errors="replace")

    login_result = json_from_response(login_raw)
    if login_result.get("code") != 0:
        return login_result

    try:
        points_before = fetch_user_points(opener)
    except Exception:
        points_before = ""

    time.sleep(random.uniform(0.8, 1.8))

    sign_req = Request("https://www.ablesci.com/user/sign", headers=build_headers())
    with opener.open(sign_req, timeout=15) as resp:
        sign_raw = resp.read().decode("utf-8", errors="replace")

    sign_result = json_from_response(sign_raw)

    try:
        points_after = fetch_user_points(opener)
    except Exception:
        points_after = ""

    sign_result["points_before"] = points_before
    sign_result["points_after"] = points_after
    sign_result["points_delta"] = format_points_delta(points_before, points_after)
    return sign_result


def extract_sign_time(msg: str) -> str:
    patterns = [
        r"已于\s*\[(\d{2}:\d{2}:\d{2})\]\s*签到",
        r"\[(\d{2}:\d{2}:\d{2})\]",
    ]
    for pattern in patterns:
        match = re.search(pattern, msg)
        if match:
            return match.group(1)
    return ""


def format_result_status(result: dict) -> str:
    msg = str(result.get("msg", ""))
    code = result.get("code")
    if code == 0:
        return "签到成功"
    if "已于" in msg and "签到" in msg:
        return "今日已签到"
    return "签到失败"


def format_message(timestamp: str, email: str, result: dict) -> str:
    msg = str(result.get("msg", ""))
    sign_time = extract_sign_time(msg) or timestamp.split(" ", 1)[-1]
    lines = [
        f"账号: {email}",
        f"结果: {format_result_status(result)}",
        f"签到时间: [{sign_time}]",
    ]
    points_before = result.get("points_before")
    points_after = result.get("points_after")
    points_delta = result.get("points_delta") or format_points_delta(str(points_before or ""), str(points_after or ""))
    if points_before:
        lines.append(f"签到前积分: {points_before}")
    if points_after:
        lines.append(f"签到后积分: {points_after}")
    if points_delta:
        lines.append(f"积分变化: {points_delta}")
    return "\n".join(lines)


def format_log_line(timestamp: str, result: dict) -> str:
    line = f"[{timestamp}] code={result.get('code', -1)} msg={result.get('msg', '无消息')}"
    points_before = result.get("points_before")
    points_after = result.get("points_after")
    points_delta = result.get("points_delta") or format_points_delta(str(points_before or ""), str(points_after or ""))
    if points_before:
        line += f" 签到前积分={points_before}"
    if points_after:
        line += f" 签到后积分={points_after}"
    if points_delta:
        line += f" 积分变化={points_delta}"
    return line


def load_qinglong_sender():
    candidates = [
        Path("/ql/scripts/sendNotify.py"),
        Path("/ql/scripts/notify.py"),
        Path("/ql/data/scripts/sendNotify.py"),
        Path("/ql/data/scripts/notify.py"),
    ]

    for path in candidates:
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location(f"ql_notify_{path.stem}", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            continue
        for func_name in ("send", "notify"):
            func = getattr(module, func_name, None)
            if callable(func):
                return func
    return None


def send_qinglong_notification(title: str, content: str) -> None:
    sender = load_qinglong_sender()
    if sender is None:
        return
    try:
        sender(title, content)
    except TypeError:
        try:
            sender(title=title, content=content)
        except Exception:
            pass
    except Exception:
        pass


def write_log(line: str) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    auth = os.environ.get("ABLESCI_AUTH", "").strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not auth:
        line = f"[{timestamp}] 缺少环境变量 ABLESCI_AUTH，格式为 账号#密码"
        print(line)
        write_log(line)
        send_qinglong_notification(NOTIFY_TITLE, f"时间: {timestamp}\n状态: 失败\n原因: 缺少 ABLESCI_AUTH")
        return

    if random.random() < 0.25:
        delay = random.randint(60, 180)
        print(f"随机延迟 {delay} 秒后执行")
        time.sleep(delay)

    try:
        email, password = read_auth(auth)
        result = login_and_sign(email, password)
        line = format_log_line(timestamp, result)
        print(line)
        write_log(line)
        send_qinglong_notification(NOTIFY_TITLE, format_message(timestamp, email, result))
    except Exception as exc:
        line = f"[{timestamp}] ERROR {exc}"
        print(line)
        write_log(line)
        send_qinglong_notification(NOTIFY_TITLE, f"时间: {timestamp}\n状态: 异常\n错误: {exc}")


if __name__ == "__main__":
    main()
