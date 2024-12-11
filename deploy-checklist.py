from flask import Flask, render_template, request, redirect, url_for
import os
import json
from pathlib import Path

app = Flask(__name__)

# File paths for persistent storage
CHEATSHEET_FILE = "cheatsheet.json"
BOOKMARKS_FILE = "bookmarks.json"
GITHUBS_FILE = "githubs.json"
CHECKLIST_TEMPLATE_FILE = "checklist_template.json"
CHECKLIST_PROGRESS_FILE = "checklist_progress.json"
BASE_DIRS = {
    "standalone": "oscp-exam/standalone",
    "active_directory": "oscp-exam/active_directory"
}

# Helper function to load or initialize data files
def load_or_init(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        with open(file_path, "w") as f:
            json.dump(default, f)
        return default

# Initializing the data
cheatsheet_content = load_or_init(CHEATSHEET_FILE, {
    "Full NMAP scan": "sudo nmap -sS -sV -sC -Pn -n -p- -T4 <IP> | sudo tee ip.nmap"
})

bookmarks_content = load_or_init(BOOKMARKS_FILE, {})
githubs_content = load_or_init(GITHUBS_FILE, {})
checklist_template = load_or_init(CHECKLIST_TEMPLATE_FILE, {
    "reconnaissance": ["Identify domain names", "Gather subdomains"],
    "enumeration": ["Port scan", "Identify running services"],
    "exploitation": ["Attempt known exploits"],
    "post_exploitation": ["Extract sensitive data"]
})

checklist_progress = load_or_init(CHECKLIST_PROGRESS_FILE, {})

# Load systems from directory structure
def load_systems():
    systems = {}
    for category, base_dir in BASE_DIRS.items():
        systems[category] = []
        if os.path.exists(base_dir):
            for system in os.listdir(base_dir):
                system_path = os.path.join(base_dir, system)
                if os.path.isdir(system_path):
                    systems[category].append(system)
    return systems

systems = load_systems()

@app.route("/")
def index():
    return render_template("index.html", systems=systems)

# Cheatsheet Route
@app.route("/cheatsheet", methods=["GET", "POST"])
def cheatsheet():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if title and content:
            cheatsheet_content[title] = content
            with open(CHEATSHEET_FILE, "w") as f:
                json.dump(cheatsheet_content, f)
        return redirect(url_for("cheatsheet"))

    return render_template("cheatsheet.html", cheatsheet_content=cheatsheet_content)

# Bookmarks Route
@app.route("/bookmarks", methods=["GET", "POST"])
def bookmarks():
    if request.method == "POST":
        title = request.form.get("title")
        url = request.form.get("url")
        if title and url:
            # Ensure the URL starts with https://
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            bookmarks_content[title] = url
            with open(BOOKMARKS_FILE, "w") as f:
                json.dump(bookmarks_content, f)
        return redirect(url_for("bookmarks"))

    return render_template("bookmarks.html", bookmarks_content=bookmarks_content)

# GitHubs Route
@app.route("/githubs", methods=["GET", "POST"])
def githubs():
    if request.method == "POST":
        title = request.form.get("title")
        url = request.form.get("url")
        if title and url:
            # Ensure the URL starts with https://
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            githubs_content[title] = url
            with open(GITHUBS_FILE, "w") as f:
                json.dump(githubs_content, f)
        return redirect(url_for("githubs"))

    return render_template("githubs.html", githubs_content=githubs_content)

# Edit Checklist Template Route
@app.route("/edit_checklist", methods=["GET", "POST"])
def edit_checklist():
    if request.method == "POST":
        new_template = request.form.get("checklist_template")
        if new_template:
            global checklist_template
            checklist_template = json.loads(new_template)
            with open(CHECKLIST_TEMPLATE_FILE, "w") as f:
                json.dump(checklist_template, f)
        return redirect(url_for("edit_checklist"))

    return render_template("edit_checklist.html", checklist_template=json.dumps(checklist_template, indent=4))

# System Route (Displays the checklist for a specific system)
@app.route("/system/<category>/<system>", methods=["GET", "POST"])
def system(category, system):
    if category not in BASE_DIRS or system not in systems.get(category, []):
        return "System not found", 404

    # Load system-specific checklist from the global template
    system_checklist = checklist_template

    # Load or initialize progress for this system
    system_progress = checklist_progress.get(system, {phase: [False] * len(tasks) for phase, tasks in system_checklist.items()})

    # Handle POST request to update checklist progress
    if request.method == "POST":
        updated_progress = request.form.to_dict()
        for phase, tasks in system_checklist.items():
            for idx, task in enumerate(tasks):
                task_key = f"{phase}_{idx}"
                # Check if the checkbox is checked or not
                if task_key in updated_progress:
                    # Convert 'on' to True (checked) and None to False (unchecked)
                    system_progress[phase][idx] = True if updated_progress[task_key] == 'on' else False

        # Save progress to file
        checklist_progress[system] = system_progress
        with open(CHECKLIST_PROGRESS_FILE, "w") as f:
            json.dump(checklist_progress, f)

        return redirect(url_for("system", category=category, system=system))

    return render_template("system.html", system=system, checklist_template=system_checklist, system_progress=system_progress)


if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    if not os.path.exists("templates"):
        os.makedirs("templates")

    # Only write the templates if they do not already exist
    templates = {
        "index.html": '''<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Penetration Testing Dashboard</title> <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}"> </head> <body> <header>Penetration Testing Dashboard</header> <div class="container"> <div class="section-title">Systems</div> <!-- Insert system links here --> </div> </body> </html>''',
        "cheatsheet.html": '''<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Cheatsheet</title> <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}"> </head> <body> <header>Cheatsheet</header> <div class="container"> <!-- Insert cheatsheet content here --> </div> </body> </html>''',
        "bookmarks.html": '''<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Bookmarks</title> <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}"> </head> <body> <header>Bookmarks</header> <div class="container"> <!-- Insert bookmarks content here --> </div> </body> </html>''',
        "githubs.html": '''<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>GitHub Links</title> <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}"> </head> <body> <header>GitHub Links</header> <div class="container"> <!-- Insert GitHub links here --> </div> </body> </html>''',
        "edit_checklist.html": '''<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Edit Checklist Template</title> <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}"> </head> <body> <header>Edit Checklist Template</header> <div class="container"> <!-- Insert checklist editing content here --> </div> </body> </html>''',
        "system.html": '''<!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>{{ system }} - Penetration Testing Checklist</title> <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}"> </head> <body> <header>{{ system }} - Penetration Testing Checklist</header> <div class="container"> <!-- Insert system checklist here --> </div> </body> </html>'''
    }

    # Write templates to disk if they don't already exist
    for filename, content in templates.items():
        file_path = Path(f"templates/{filename}")
        if not file_path.exists():
            with open(file_path, 'w') as file:
                file.write(content)

    # Start the Flask web service
    app.run(host="0.0.0.0", port=9443, debug=True)

