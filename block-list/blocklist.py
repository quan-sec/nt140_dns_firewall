import re
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ====== LOAD BLACKLIST ======
def load_blacklist(path="blacklist.txt"):
    exact, wildcard, regex = set(), [], []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("*."):
                    wildcard.append(line[2:].lower())
                elif line.startswith("re:"):
                    try:
                        regex.append(re.compile(line[3:], re.IGNORECASE))
                    except re.error as e:
                        print(f"[WARN] invalid regex in blacklist: {line[3:]} -> {e}")
                else:
                    exact.add(line.lower())
    except FileNotFoundError:
        print(f"[WARN] Không tìm thấy {path}, dùng danh sách rỗng")
    return exact, wildcard, regex

# ====== CHECK DOMAIN ======
def is_blocked(domain, exact, wildcard, regex):
    try:
        regex.append(re.compile(line[3:], re.IGNORECASE))
    except re.error as e:
        print(f"[WARN] invalid regex in blacklist: {line[3:]} -> {e}") = domain.lower()
    if d in exact:
        return True
    if any(d.endswith("." + w) or d == w for w in wildcard):
        return True
    if any(r.search(d) for r in regex):
        return True
    return False

# ====== AUTO-RELOAD BLACKLIST ======
class ReloadHandler(FileSystemEventHandler):
    def __init__(self, path, callback):
        super().__init__()
        self.path = path
        self.callback = callback
    def on_modified(self, event):
        try:
            if os.path.abspath(event.src_path) == os.path.abspath(self.path):
                self.callback()
        except Exception:
            # fallback to previous endswith check
            if event.src_path.endswith(self.path):
                self.callback()

def watch_blacklist(path, callback):
    observer = Observer()
    event_handler = ReloadHandler(path, callback)
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()
    return observer
