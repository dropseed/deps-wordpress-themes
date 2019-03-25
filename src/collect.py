import re
import os
import sys
import logging
from subprocess import run

import requests

from utils import write_json_to_temp_file


def collect():
    themes_path = sys.argv[1]
    themes_contents = os.listdir(themes_path)
    theme_directories = [x for x in themes_contents if os.path.isdir(os.path.join(themes_path, x))]

    run(['deps', 'hook', 'before_update'], check=True)

    collected_themes = {}

    for theme in theme_directories:

        print(f'Collecting {theme}')

        theme_style_path = os.path.join(themes_path, theme, "style.css")
        installed_version = None

        with open(theme_style_path, 'rb') as f:
            contents = f.read()
            version_match = re.search(b'^\s*\**\s*Version:\s*(.*)\s*$', contents, re.MULTILINE)
            if version_match:
                installed_version = version_match.groups(0)[0]

        if not installed_version:
            logging.error(f'Could not detect installed version of {theme}')
            continue

        installed_version = installed_version.decode('utf-8').strip()

        try:
            response = requests.get(f'https://api.wordpress.org/themes/info/1.1/?action=theme_information&request[slug]={theme}')
            available = [response.json()["version"]]
            print(available)
        except Exception:
            logging.error(f'Unable to find available versions of {theme} in API.')
            available = [installed_version]

        collected_themes[theme] = {
            'constraint': installed_version,
            'available': [{'name': x} for x in available],
            'source': 'wordpress-theme',
        }

    schema_output = {
        'manifests': {
            themes_path: {
                'current': {
                    'dependencies': collected_themes
                }
            }
        }
    }
    run(['deps', 'collect', write_json_to_temp_file(schema_output)], check=True)
