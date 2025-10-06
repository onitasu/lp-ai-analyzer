import os, re, time

def slugify(s: str):
    return re.sub(r"[^a-zA-Z0-9\-]+", "-", s)[:50].strip("-").lower()

def make_run_dir(url: str):
    ts = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join("runs", f"{ts}_{slugify(url)}")
    os.makedirs(d, exist_ok=True)
    return d

def write_text(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def write_bytes(path: str, b: bytes):
    with open(path, "wb") as f:
        f.write(b)

def read_text(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()