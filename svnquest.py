#!/usr/bin/env python3

import subprocess
import os
import json
import string
import re
import random
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader


CONFIG = 'config.yaml'
TEMPLATES_DIR = 'templates'
REMOTES_DIR = 'remotes'
HTML_DIR = 'html'

def remove_contents(path):
    for c in os.listdir(path):
        full_path = os.path.join(path, c)
        if os.path.isfile(full_path):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)

def is_file(part: str, splitted: list) -> bool:
    """Check if substring is not a directory.
    In case of directory the last item
    in splitted path is empty (because we split by '/'):
    ['Registrars', 'BR-226', 'trunk', '']
    So we check that part is last in splitted list
    and last part is not empty.
    """
    return part == splitted[-1] and part != ""


def jsoned_tree(paths: list) -> list:
    def stage1(paths: list):
        """Convert paths to dict.
        Example return:
        {
            'root_directory': {
                'child1_directory': {
                    'file1_directory': {},
                    'file2_directory': {}
                },
                'child2_directory': {
                    'file1_directory': {}
                }
            }
        }
        """
        results = {}
        for path in paths:
            splitted = path.split('/')
            current = results
            for part in splitted:
                if not part:
                    continue
                # TODO: create better way to filter files and directories
                if is_file(part, splitted):
                    part = part + '_file'
                else:
                    part = part + '_directory'

                current.setdefault(part, {})
                current = current[part]
        return results

    def stage2(dct: dict):
        """ Modify dict with right keys and values.
        Example return:
            {
                "text": "root",
                "children": [
                    {
                        "text": "child1",
                        "children": [
                            {
                                "text": "file1",
                                "children": []
                            },
                            {
                                "text": "file2",
                                "children": []
                            }
                        ]
                    }
        """
        return [
            {
                'text': re.sub('_directory$|_file$', '', key),
                'children': stage2(value),
                'icon': "jstree-file" if key.endswith('_file') else ''
            }
            for key, value in dct.items() if (key)
        ]

    items = stage1(paths)
    json_paths = stage2(items)
    return json_paths


def get_svn_listing(url: str) -> list:
    print('Listing url: %s' % url)
    with subprocess.Popen(['svn', 'ls', '-R', url],
                          stdout=subprocess.PIPE) as process:
            output, err = process.communicate()
    if err:
        print(err)
        return None

    return output.decode('utf-8').splitlines()


def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def main():

    config = yaml.load(open(CONFIG).read())

    remove_contents(REMOTES_DIR)
    remove_contents(HTML_DIR)

    results = list()

    for remote in config['remotes']:
        repo_url = remote.get('url')
        repo_alias = remote.get('alias')

        listing = get_svn_listing(repo_url)
        if not listing:
            print('Cannot list url: %s' % URL)
            continue

        jsoned_listing = jsoned_tree(listing)
        remote_id = generate_id()
        with open(os.path.join(REMOTES_DIR, remote_id + '.json'),
                  'w') as f:
            f.write(json.dumps(jsoned_listing,
                               ensure_ascii=False))

        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template('page.html.template')
        html_filename = remote_id + '.html'
        with open(os.path.join(HTML_DIR, html_filename), 'w') as f:
            f.write(template.render(id=remote_id,
                                    repo_url=repo_url,
                                    repo_alias=repo_alias,
                                    remotes_dir=REMOTES_DIR))

        results.append({'id': remote_id, 'repo_url': repo_url, 'repo_alias': repo_alias})


    if results:
        template = env.get_template('index.html.template')
        html_filename = template.name.replace('.template', '')
        with open(os.path.join(HTML_DIR, html_filename), 'w') as f:
            f.write(template.render(results=results))

if __name__ == '__main__':
    main()
