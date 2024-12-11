Overview
This project includes two Python scripts: build-directories.py and deploy-checklist.py.

build-directories.py:

This script generates a preconfigured set of directories tailored for OSCP challenge labs. It is designed to save time by automating the process of creating the necessary folder structure for your upcoming exam.
deploy-checklist.py:

This script deploys a Flask web server that links to the directories created by the previous script. It generates an interactive Penetration Testing Checklist for each target system.
Additionally, it creates several .json files that allow you to link your favorite bookmarks and GitHub tools to the web server for easy access while working.
An Edit Checklist page is included, enabling you to modify the .json configuration that defines the checklist, allowing you to customize it to suit your specific needs.
A Command-Line Cheat Sheet section is also provided, where you can store and reference your commonly used commands.

Run build-directories.py:
Execute the script to generate the required folder structure. This step should be run using sudo:
```
sudo python3 build-directories.py
```

Run deploy-checklist.py:
After building the directories, run the deploy-checklist.py script to start the Flask web server:
```
python3 deploy-checklist.py
This will set up the interactive checklist and the associated features.
```
