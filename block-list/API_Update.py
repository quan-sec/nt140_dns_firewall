"""
updater_api.py

Module để tải/gom nhiều threat feeds (OpenPhish, StevenBlack, URLhaus, ...) và
ghi thành blacklist.txt (atomic). Có thể gọi trực tiếp từ DNS server hoặc chạy
độc lập (cron/Task Scheduler).

Usage:
    # run once
    python updater_api.py --once

    # run as daemon in-process (non-blocking)
    from updater_api import start_periodic
    start_periodic(interval=3600)  # cập nhật mỗi 1 giờ
"""

import requests
import tldextract
import tempfile
import os
import time
import threading
from datetime import datetime
from urllib.parse import urlparse
import shutil

# ---------------- CONFIG ----------------
OUT_FILE = "blacklist.txt"                 # file đầu ra chính
CANDIDATE_FILE = "blacklist.candidate.txt" # nếu muốn QA trước khi replace
BACKUP_DIR = "blacklist_backups"
USER_AGENT = "dns-firewall-updater/1.0 (+your_email@example.com)"
FETCH_TIMEOUT = 20
SOURCES = {
    "stevenblack": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "openphish":  "https://openphish.com/feed.txt",
    "urlhaus":    "https://urlhaus.abuse.ch/downloads/csv/",
}
# ----------------------------------------

HEADERS = {"User-Agent": USER_AGENT}


def fetch_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=FETCH_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] fetch {url} failed: {e}")
        return None


def extract_domain(host_or_url):
    """Trả domain dạng example.com"""
    if not host_or_url:
        return None
    try:
        if "://" in host_or_url:
            host = urlparse(host_or_url).hostname or host_or_url
        else:
            host = host_or_url
    except Exception:
        host = host_or_url

    ext = tldextract.extract(host)
    if ext and ext.suffix:
        return f"{ext.domain}.{ext.suffix}".lower()
    return None


def parse_stevenblack(text):
    results = set()
    if not text:
        return results
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            candidate = parts[1]
        else:
            candidate = parts[0]
        d = extract_domain(candidate)
        if d:
            results.add(d)
    return results


def parse_openphish(text):
    results = set()
    if not text:
        return results
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        d = extract_domain(line)
        if d:
            results.add(d)
    return results


def parse_urlhaus(text):
    results = set()
    if not text:
        return results
    for line in text.splitlines():
        if not line or line.startswith("id,"):
            continue
        parts = line.split(",")
        candidate = None
        for p in parts:
            p = p.strip().strip('"')
            if p.startswith("http") or ("." in p and len(p) < 200):
                candidate = p
                break
        if candidate:
            d = extract_domain(candidate)
            if d:
                results.add(d)
    return results


def collect_from_sources(sources=None):
    if sources is None:
        sources = SOURCES
    all_domains = set()

    sb = fetch_text(sources.get("stevenblack"))
    if sb:
        parsed = parse_stevenblack(sb)
        all_domains.update(parsed)
        print(f"[INFO] StevenBlack -> {len(parsed)} domains")

    op = fetch_text(sources.get("openphish"))
    if op:
        parsed = parse_openphish(op)
        before = len(all_domains)
        all_domains.update(parsed)
        print(f"[INFO] OpenPhish -> {len(parsed)} domains (added {len(all_domains)-before})")

    uh = fetch_text(sources.get("urlhaus"))
    if uh:
        parsed = parse_urlhaus(uh)
        before = len(all_domains)
        all_domains.update(parsed)
        print(f"[INFO] URLhaus -> {len(parsed)} domains (added {len(all_domains)-before})")

    return all_domains


def atomic_write(domains, out_path=OUT_FILE, backup=True, use_candidate=False):
    """
    Ghi atomic trên cùng ổ:
      - backup file cũ nếu có
      - ghi file tạm trong cùng thư mục -> os.replace
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)

    target = CANDIDATE_FILE if use_candidate else out_path
    target_dir = os.path.dirname(os.path.abspath(target)) or os.getcwd()

    # backup
    if backup and os.path.exists(target):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bk_path = os.path.join(BACKUP_DIR, f"blacklist_{stamp}.txt")
        try:
            shutil.copy2(target, bk_path)
            print(f"[INFO] Backup old blacklist -> {bk_path}")
        except Exception as e:
            print(f"[WARN] Backup failed: {e}")

    # tạo file tạm trong cùng thư mục
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_blacklist_", dir=target_dir, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("# blacklist generated by updater_api.py\n")
            f.write(f"# generated: {datetime.utcnow().isoformat()}Z\n")
            f.write("# sources: " + ", ".join(SOURCES.keys()) + "\n\n")
            for d in sorted(domains):
                f.write(d + "\n")
        os.replace(tmp_path, target)
        print(f"[INFO] Wrote {len(domains)} domains -> {target}")
    except Exception as e:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        print(f"[ERROR] atomic_write failed: {e}")
        raise


def update_once(out_path=OUT_FILE, use_candidate=False):
    domains = collect_from_sources()
    atomic_write(domains, out_path=out_path, use_candidate=use_candidate)
    return len(domains)


def start_periodic(interval_seconds=3600, background=True, out_path=OUT_FILE, use_candidate=False):
    def _runner():
        while True:
            try:
                print(f"[INFO] updater: starting collection at {datetime.utcnow().isoformat()}Z")
                n = update_once(out_path=out_path, use_candidate=use_candidate)
                print(f"[INFO] updater: collected {n} domains")
            except Exception as e:
                print(f"[ERROR] updater exception: {e}")
            time.sleep(interval_seconds)

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    if background:
        return t
    else:
        t.join()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Blacklist updater (collect threat feeds -> blacklist.txt)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (background)")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds for daemon")
    parser.add_argument("--candidate", action="store_true", help="Write to candidate file (do not replace main file)")
    args = parser.parse_args()

    if args.once:
        update_once(use_candidate=args.candidate)
    elif args.daemon:
        start_periodic(interval_seconds=args.interval, background=False, use_candidate=args.candidate)
    else:
        update_once(use_candidate=args.candidate)
