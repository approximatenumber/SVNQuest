#!/usr/bin/env python3

import subprocess
import os
import sys
import json
import string
import re
import random
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader


CONFIG_FILE = 'config.yaml'
TEMPLATES_DIR = 'templates'
REMOTES_DIR = 'remotes'
HTML_DIR = 'html'

os.makedirs(REMOTES_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)


class SVNRequest():
    def __init__(self):
        """Constructor."""
        self.config = yaml.load(open(CONFIG_FILE).read())
        self.env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        # it will be not needed in future
        self.remove_contents(REMOTES_DIR)
        self.remove_contents(HTML_DIR)

    def generate(self) -> bool:
        """Main function to generate all files."""
        generated = list()
        for remote in self.config['remotes']:

            remote_url = remote.get('url')
            remote_alias = remote.get('alias')
            remote_id = self.get_id(remote_alias)
            remote_username = remote.get('username')
            remote_password = remote.get('password')

            if not self.generate_remote_json(remote_id,
                                             remote_url,
                                             username=remote_username,
                                             password=remote_password):
                print(
                    'Cannot generate json for url: %s' % remote_url)
                return False

            if not self.generate_remote_html(remote_id,
                                             remote_url,
                                             remote_alias):
                print(
                    'Cannot generate html for url: %s' % remote_url)
                return False

        generated.append(
            {'id': remote_id,
             'remote_url': remote_url,
             'remote_alias': remote_alias})

        if not generated:
            print('Generation failed: nothing to do.')
            return False
        self.generate_index_html(generated)
        return True

    def remove_contents(self, path: str) -> None:
        """Remove directory content recursively."""
        for c in os.listdir(path):
            full_path = os.path.join(path, c)
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)

    def is_file(self, part: str, splitted: list) -> bool:
        """Check if substring is not a directory.
        In case of directory the last item
        in splitted path is empty (because split by '/'):
        ['site', 'html', 'css', '']
        So check that part is last in splitted list
        and last part is not empty.
        """
        return part == splitted[-1] and part != ""

    def json_listing(self, paths: list) -> list:
        def stage1(paths: list) -> dict:
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
                    if self.is_file(part, splitted):
                        part = part + '_file'
                    else:
                        part = part + '_directory'

                    current.setdefault(part, {})
                    current = current[part]
            return results

        def stage2(dct: dict) -> list:
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

    def svn_command_line(self, url: str, **parameters: dict) -> list:
        """Create command line for 'svn ls' with optional parametes.
        """
        command = ['svn', 'ls', '-R']
        if parameters.get('username'):
            command.append('--username')
            command.append(parameters['username'])
        if parameters.get('password'):
            command.append('--password')
            command.append(parameters['password'])
        command.append(url)
        return command

    def svn_list(self, url: str, **parameters: dict) -> list:
        """Exectute 'svn ls' and returns listing."""
        print('Listing url: %s' % url)
        command_line = self.svn_command_line(url, **parameters)
        with subprocess.Popen(command_line,
                              stdout=subprocess.PIPE) as process:
                output, err = process.communicate()
        if err:
            print(err)
            return None

        return output.decode('utf-8').splitlines()

    def get_id(self,
                remote_alias: str,
                size=6,
                chars=string.ascii_lowercase + string.digits) -> str:
        """Generate uniq id if no alias is set."""
        if not remote_alias:
            return ''.join(random.choice(chars) for _ in range(size))
        return remote_alias.lower()\
                           .replace('\s:-', '_')

    def generate_remote_json(self,
                              remote_id: str,
                              remote_url: str,
                              **parameters) -> bool:
        listing = self.svn_list(remote_url, **parameters)
        if not listing:
            print('Cannot list url: %s' % remote_url)
            return False
        jsoned_listing = self.json_listing(listing)
        with open(os.path.join(REMOTES_DIR, remote_id + '.json'),
                  'w') as f:
            f.write(json.dumps(jsoned_listing,
                               ensure_ascii=False))
        return True

    def generate_remote_html(self,
                              remote_id: str,
                              remote_url: str,
                              remote_alias: str) -> bool:
        template = self.env.get_template('page.html.template')
        html_filename = remote_id + '.html'
        with open(os.path.join(HTML_DIR, html_filename), 'w') as f:
            f.write(template.render(id=remote_id,
                                    remote_url=remote_url,
                                    remote_alias=remote_alias,
                                    remotes_dir=REMOTES_DIR))
        return True

    def generate_index_html(self, generated: dict) -> None:
        template = self.env.get_template('index.html.template')
        html_filename = template.name.replace('.template', '')
        with open(os.path.join(HTML_DIR, html_filename), 'w') as f:
            f.write(template.render(ready_remotes=generated,
                                    remotes_dir=REMOTES_DIR))


def main():
    """Main."""
    svnrequest = SVNRequest()
    if not svnrequest.generate():
        sys.exit(1)

if __name__ == '__main__':
    main()
