import os, re, urllib.parse

start_marker = "<!-- PREVIEW_START -->"
end_marker = "<!-- PREVIEW_END -->"

# --- Read existing README ---
with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

# Extract existing preview names
existing_section = re.search(
    rf"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
    content,
    re.S
)

existing_names = set()
if existing_section:
    # Extract <sub><b>name</b></sub> patterns
    existing_names = set(
        re.findall(r"<sub><b>(.*?)</b></sub>", existing_section.group(1))
    )

# collect all image files
images = []
for root, _, files in os.walk("."):
    for f in files:
        if re.search(r"\.(png|jpe?g)$", f, re.IGNORECASE):
            path = os.path.join(root, f).replace("\\", "/").lstrip("./")
            images.append(path)

# group by folder
groups = {}
for img in sorted(images):
    name = os.path.splitext(os.path.basename(img))[0].replace("-", " ")

    # skip if name already exists in README
    if name in existing_names:
        continue

    folder = os.path.dirname(img) or "."
    groups.setdefault(folder, []).append(img)

# sort images inside each folder
for folder in groups:
    groups[folder].sort()

# sort folders alphabetically
sorted_folders = sorted(groups.keys())

# generate html
html = ""
for folder in sorted_folders:
    imgs = groups[folder]

    parts = folder.split("/")
    heading = " / ".join(parts)

    html += f"<h3 align=\"center\">{heading}</h3>\n"
    html += "<table align=\"center\"><tr>\n"

    for i, img in enumerate(imgs):
        name = os.path.splitext(os.path.basename(img))[0].replace("-", " ")
        img_url = urllib.parse.quote(img)

        html += f"""<td align="center">
  <img src="{img_url}" width="250"><br>
  <sub><b>{name}</b></sub>
</td>
"""

        if (i + 1) % 3 == 0:
            html += "</tr><tr>\n"

    html += "</tr></table>\n<br>\n"

# replace section in README
pattern = re.compile(
    rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
    re.S
)
new_content = pattern.sub(f"{start_marker}\n{html}\n{end_marker}", content)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)
