import re
import os
import sys
import logging
from subprocess import run
import json

import requests


def collect(input_path, output_path):
    themes_path = input_path
    themes_contents = os.listdir(themes_path)
    theme_directories = [
        x for x in themes_contents if os.path.isdir(os.path.join(themes_path, x))
    ]

    current_themes = {}
    updated_themes = {}

    for theme in theme_directories:

        print(f"Collecting {theme}")

        theme_style_path = os.path.join(themes_path, theme, "style.css")
        installed_version = None

        with open(theme_style_path, "rb") as f:
            contents = f.read()
            version_match = re.search(
                b"^\s*\**\s*Version:\s*(.*)\s*$", contents, re.MULTILINE
            )
            if version_match:
                installed_version = version_match.groups(0)[0]

        if not installed_version:
            logging.error(f"Could not detect installed version of {theme}")
            continue

        installed_version = installed_version.decode("utf-8").strip()
        latest = None

        try:
            response = requests.get(
                f"https://api.wordpress.org/themes/info/1.1/?action=theme_information&request[slug]={theme}"
            )
            latest = response.json()["version"]
        except Exception:
            logging.error(f"Unable to find available versions of {theme} in API.")

        current_themes[theme] = {
            "constraint": installed_version,
            "source": "wordpress-theme",
        }
        if latest and latest != installed_version:
            updated_themes[theme] = {"constraint": latest, "source": "wordpress-theme"}

    schema_output = {
        "manifests": {themes_path: {"current": {"dependencies": current_themes}}}
    }

    if updated_themes:
        schema_output["manifests"][themes_path]["updated"] = {
            "dependencies": updated_themes
        }

    with open(output_path, "w+") as f:
        json.dump(schema_output, f)


if __name__ == "__main__":
    collect(sys.argv[1], sys.argv[2])
