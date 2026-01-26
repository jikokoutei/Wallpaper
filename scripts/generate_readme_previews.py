import os, re, urllib.parse

start_marker = "<!-- PREVIEW_START -->"
end_marker = "<!-- PREVIEW_END -->"

# --- Read existing README ---
with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

# Extract existing preview HTML block
match = re.search(
    rf"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
    content,
    re.S
)

existing_html = ""
existing_names = set()

if match:
    existing_html = match.group(1)

    # Extract existing preview names
    existing_names = set(
        re.findall(r"<sub><b>(.*?)</b></sub>", existing_html)
    )

# collect all image files
images = []
for root, _, files in os.walk("."):
    for f in files:
        if re.search(r"\.(png|jpe?g)$", f, re.IGNORECASE):
            path = os.path.join(root, f).replace("\\", "/").lstrip("./")
            images.append(path)

# Force ASCII sort on raw paths
images = sorted(images)

# group by folder
groups = {}
for img in images:
    name = os.path.splitext(os.path.basename(img))[0].replace("-", " ")

    # skip duplicates
    if name in existing_names:
        continue

    folder = os.path.dirname(img) or "."
    groups.setdefault(folder, []).append(img)

# sort folders ASCII
sorted_folders = sorted(groups.keys())

# generate new html only for NEW images
new_html = ""
for folder in sorted_folders:
    imgs = sorted(groups[folder])

    parts = folder.split("/")
    heading = " / ".join(parts)

    new_html += f"<h3 align=\"center\">{heading}</h3>\n"
    new_html += "<table align=\"center\"><tr>\n"

    for i, img in enumerate(imgs):
        name = os.path.splitext(os.path.basename(img))[0].replace("-", " ")
        img_url = urllib.parse.quote(img)

        new_html += f"""<td align="center">
  <img src="{img_url}" width="250"><br>
  <sub><b>{name}</b></sub>
</td>
"""

        if (i + 1) % 3 == 0:
            new_html += "</tr><tr>\n"

    new_html += "</tr></table>\n<br>\n"

# Combine old + new
final_html = existing_html + "\n" + new_html

# Replace section in README
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
