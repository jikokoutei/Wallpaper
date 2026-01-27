import os
import re
import urllib.parse
import subprocess
import pathlib
import hashlib
import sys

# =============== CONFIG =================
START_MARKER = "<!-- PREVIEW_START -->"
END_MARKER = "<!-- PREVIEW_END -->"

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".webm", ".avi")

PREVIEW_DIR = "video_previews"
THUMB_WIDTH = 250
MAX_WIDTH = 900
# =======================================

TARGET_DIR = sys.argv[1] if len(sys.argv) > 1 else "."

pathlib.Path(PREVIEW_DIR).mkdir(exist_ok=True)

# ---------- Read README ----------
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

match = re.search(
    rf"{re.escape(START_MARKER)}(.*?){re.escape(END_MARKER)}",
    readme,
    re.S
)

existing_html = match.group(1) if match else ""
existing_keys = set(re.findall(r'data-key="(.*?)"', existing_html))
existing_headers = set(re.findall(r"<h3.*?>(.*?)</h3>", existing_html))

# ---------- Collect repo files ----------
items = []
seen = set()

for root, _, files in os.walk(TARGET_DIR):
    root = root.replace("\\", "/")

    if root.startswith(PREVIEW_DIR):
        continue

    for file in files:
        if file.startswith("."):
            continue

        ext = os.path.splitext(file)[1].lower()
        if ext in IMAGE_EXTS or ext in VIDEO_EXTS:
            path = os.path.join(root, file).replace("\\", "/").lstrip("./")
            key = path.lower()
            if key not in seen:
                seen.add(key)
                items.append(path)

items.sort()

# ---------- Group by folder ----------
groups = {}
for item in items:
    key = item.lower()
    if key in existing_keys:
        continue

    folder = os.path.dirname(item) or "."
    groups.setdefault(folder, []).append(item)

# ---------- Generate README HTML ----------
new_html = ""

for folder in sorted(groups):
    files = groups[folder]
    if not files:
        continue

    heading = " / ".join(folder.split("/"))
    if heading in existing_headers:
        continue  # header already exists → skip whole section

    section_html = f'<h3 align="center">{heading}</h3>\n'
    section_html += (
        f'<div style="max-width:{MAX_WIDTH}px; overflow-x:auto; margin:auto;">\n'
        '<table><tr>\n'
    )

    for file in files:
        ext = os.path.splitext(file)[1].lower()
        raw_name = os.path.splitext(os.path.basename(file))[0]
        name = re.sub(r"[.-]+", " ", raw_name).strip()
        key = file.lower()
        file_url = urllib.parse.quote(file)

        # ---------- GIF (animated → no label) ----------
        if ext == ".gif":
            img_url = urllib.parse.quote(file)
            cell = f"""
<td align="center" data-key="{key}" style="padding:6px;">
  <img src="{img_url}" width="{THUMB_WIDTH}">
</td>
"""

        # ---------- IMAGE ----------
        elif ext in IMAGE_EXTS:
            img_url = urllib.parse.quote(file)
            cell = f"""
<td align="center" data-key="{key}" style="padding:6px;">
  <img src="{img_url}" width="{THUMB_WIDTH}"><br>
  <sub><b>{name}</b></sub>
</td>
"""

        # ---------- VIDEO ----------
        else:
            h = hashlib.md5(file.encode()).hexdigest()[:12]
            preview_path = f"{PREVIEW_DIR}/{h}.png"

            if not os.path.exists(preview_path):
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-ss", "1",
                        "-i", file,
                        "-frames:v", "1",
                        preview_path
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            preview_url = urllib.parse.quote(preview_path)

            cell = f"""
<td align="center" data-key="{key}" style="padding:6px;">
  <a href="{file_url}" style="position:relative; display:inline-block;">
    <img src="{preview_url}" width="{THUMB_WIDTH}">
    <div style="
      position:absolute;
      bottom:0;
      width:100%;
      background:linear-gradient(transparent, rgba(0,0,0,0.7));
      color:white;
      font-size:12px;
      padding:4px 2px;
      text-align:center;
      box-sizing:border-box;">
      <b>{name}</b>
    </div>
  </a>
</td>
"""

        section_html += cell

    section_html += "</tr></table>\n</div>\n<br>\n"
    new_html += section_html

# ---------- Update README ----------
final_html = existing_html + "\n" + new_html if existing_html else new_html

updated_readme = re.sub(
    rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
    f"{START_MARKER}\n{final_html}\n{END_MARKER}",
    readme,
    flags=re.S
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated_readme)

print("✅ GitHub README previews updated")
