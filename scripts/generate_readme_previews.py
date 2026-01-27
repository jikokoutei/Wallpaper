import os, re, urllib.parse, subprocess, pathlib

start_marker = "<!-- PREVIEW_START -->"
end_marker = "<!-- PREVIEW_END -->"

VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")
IMAGE_EXTS = (".png", ".jpg", ".jpeg")
PREVIEW_DIR = "video_previews"

pathlib.Path(PREVIEW_DIR).mkdir(exist_ok=True)

# --- Read existing README ---
with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(
    rf"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
    content,
    re.S
)

existing_html = ""
existing_names = set()

if match:
    existing_html = match.group(1)
    existing_names = set(
        re.findall(r"<sub><b>(.*?)</b></sub>", existing_html)
    )

items = []

# --- Collect images + videos ---
for root, _, files in os.walk("."):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in IMAGE_EXTS or ext in VIDEO_EXTS:
            path = os.path.join(root, f).replace("\\", "/").lstrip("./")
            items.append(path)

items = sorted(items)

groups = {}

for item in items:
    name = os.path.splitext(os.path.basename(item))[0].replace("-", " ")

    if name in existing_names:
        continue

    folder = os.path.dirname(item) or "."
    groups.setdefault(folder, []).append(item)

sorted_folders = sorted(groups.keys())

new_html = ""

for folder in sorted_folders:
    files = sorted(groups[folder])
    heading = " / ".join(folder.split("/"))

    new_html += f'<h3 align="center">{heading}</h3>\n'
    new_html += '<table align="center"><tr>\n'

    for i, file in enumerate(files):
        name = os.path.splitext(os.path.basename(file))[0].replace("-", " ")
        ext = os.path.splitext(file)[1].lower()

        file_url = urllib.parse.quote(file)

        # --- IMAGE ---
        if ext in IMAGE_EXTS:
            thumb_url = urllib.parse.quote(file)

            cell = f"""
<td align="center">
  <img src="{thumb_url}" width="250"><br>
  <sub><b>{name}</b></sub>
</td>
"""

        # --- VIDEO ---
        else:
            preview_path = f"{PREVIEW_DIR}/{os.path.basename(file)}.png"

            if not os.path.exists(preview_path):
                subprocess.run([
                    "ffmpeg",
                    "-y",
                    "-ss", "1",
                    "-i", file,
                    "-frames:v", "1",
                    preview_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            preview_url = urllib.parse.quote(preview_path)

            cell = f"""
<td align="center">
  <a href="{file_url}">
    <img src="{preview_url}" width="250">
  </a><br>
  <sub><b>{name}</b></sub>
</td>
"""

        new_html += cell

        if (i + 1) % 3 == 0:
            new_html += "</tr><tr>\n"

    new_html += "</tr></table>\n<br>\n"

final_html = existing_html + "\n" + new_html

pattern = re.compile(
    rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
    re.S
)

new_content = pattern.sub(
    f"{start_marker}\n{final_html}\n{end_marker}",
    content
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)
