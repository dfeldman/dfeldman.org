import os
from pathlib import Path
import subprocess

# Define folders for the files
diagrams_folder = Path("diagrams")
output_folder = Path("output")
logos_folder = Path("logos")
output_folder.mkdir(exist_ok=True)

# HTML template for each protocol page
protocol_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{protocol_name}</title>
    <style>
        body {{
            color: #ffffff;
            background-color: #1e1e1e;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        h1 {{
            margin-top: 20px;
        }}
        img {{
            margin: 20px 0;
            max-width: 80%;
            height: auto;
        }}
        .source-link {{
            color: #4ea8de;
            text-decoration: none;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    {protocol_text}
    <img src="../diagrams/output/{protocol_image}" alt="{protocol_name} diagram">
    <a href="{protocol_source}" class="source-link">View Source (.puml)</a>
</body>
</html>
"""

# HTML template for the index page
index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auth Protocols</title>
    <style>
        body {{
            color: #ffffff;
            background-color: #1e1e1e;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        h1 {{
            margin-top: 20px;
        }}
        .protocol-button {{
            background-color: #333;
            color: #ffffff;
            text-decoration: none;
            padding: 15px;
            margin: 10px;
            display: flex;
            align-items: center;
            width: 300px;
            border-radius: 8px;
            transition: background-color 0.3s;
        }}
        .protocol-button:hover {{
            background-color: #555;
        }}
        img {{
            width: 40px;
            height: 40px;
            margin-right: 15px;
        }}
    </style>
</head>
<body>
    <h1>Auth Protocols</h1>
    {protocol_buttons}
</body>
</html>
"""

# Create the individual protocol pages and compile diagrams
protocol_buttons_html = ""
for puml_file in diagrams_folder.glob("*.plantuml"):
    protocol_name = puml_file.stem
    png_file = output_folder / f"{protocol_name}.svg"
    html_file = output_folder / f"{protocol_name}.html"
    logo_file = logos_folder / f"{protocol_name}.png"

    # Compile the PlantUML file into a PNG
    subprocess.run(["plantuml", "-tsvg", "-darkmode", "-o", str(output_folder), str(puml_file)], check=True)

    # Create the protocol HTML page
    protocol_html = protocol_template.format(
        protocol_name=protocol_name.capitalize(),
        protocol_image=png_file.name,
        protocol_source=puml_file.name,
        protocol_text="This is a placeholder for the protocol text."
    )
    with open(html_file, "w") as f:
        f.write(protocol_html)

    # Add a button for this protocol to the index page
    protocol_buttons_html += f"""
    <a href="{html_file.name}" class="protocol-button">
        <img src="../logos/{logo_file.name}" alt="{protocol_name} logo">
        {protocol_name.capitalize()}
    </a>
    """

# Create the index page
index_html = index_template.format(protocol_buttons=protocol_buttons_html)
with open(output_folder / "index.html", "w") as f:
    f.write(index_html)

print("Static site generated successfully.")
