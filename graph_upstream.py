import codecs
import os
import re
import time
from base64 import b64decode

import github3
import networkx as nx
import yaml
from jinja2 import UndefinedError, Template
import requests


def source_location(meta_yaml):
    try:
        if 'github.com' in meta_yaml['url']:
            return 'github'
        elif 'pypi.python.org' in meta_yaml['url']:
            return 'pypi'
        else:
            return None
    except KeyError:
        return None


def pypi_version(meta_yaml, package_name, gh):
    r = requests.get('https://pypi.python.org/pypi/{}/json'.format(
        package_name))
    if not r.ok:
        print('Could not find version on pypi', package_name)
        return False
    return r.json()['info']['version'].strip()


def gh_version(meta_yaml, package_name, gh):
    split_url = meta_yaml['url'].lower().split('/')
    package_owner = split_url[split_url.index('github.com') + 1]

    # get all the tags
    repo = gh.repository(package_owner, package_name)
    if not repo:
        print("could not find repo", package_name)
        return False

    rels = [r.tag_name for r in repo.iter_releases()]
    if len(rels) == 0:
        print("no releases found", package_name)
        return False

    return max(rels)


sl_map = {'pypi': {'version': pypi_version},
          'github': {'version': gh_version}}


def get_latest_version(meta_yaml, gh):
    sl = source_location(meta_yaml)
    if sl is None:
        print('Not on GitHub or pypi', meta_yaml['name'])
        return False
    rv = sl_map[sl]['version'](meta_yaml, meta_yaml['name'], gh)
    return rv


gh = github3.login(os.environ['USERNAME'], os.environ['PASSWORD'])

gx = nx.read_gpickle('graph.pkl')

try:
    for node, attrs in gx.node.items():
        attrs['new_version'] = get_latest_version(attrs, gh)

except github3.GitHubError:
    pass

nx.write_gpickle(gx, 'graph2.pkl')
