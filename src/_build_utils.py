#!/usr/bin/env python
"""
Contains the ananke module building utility tools. Credit to
https://github.com/GalacticDynamics-Oxford/Agama/blob/master/setup.py.
"""
import os
import importlib.util
import sys
import pathlib
import subprocess
import ssl
import urllib.request
import urllib.parse
import json
import configparser
from distutils.errors import CompileError
from packaging import version

from ._builtin_utils import import_source_file
from ._constants import *
from .__metadata__ import *
from . import _version, versioneer

__all__ = ['make_package_data', 'check_submodules', 'append_install_requires_with_submodules', 'make_cmdclass']

ROOT_DIR = pathlib.Path(__file__).parent.parent

# Check if we're in a build workflow
IS_BUILD = any(
    cmd in sys.argv 
    for cmd in ('sdist', 'bdist_wheel', 'bdist_egg')
)


# force printing to the terminal even if stdout was redirected
def say(text):
    text += ' '
    sys.stdout.write(text)
    sys.stdout.flush()
    if not sys.stdout.isatty():
        # output was redirected, but we still try to send the message to the terminal
        try:
            if pathlib.Path('/dev/tty').exists():
                with open('/dev/tty', 'w') as out:
                    out.write(text)
                    out.flush()
        except (OSError, PermissionError):
            # /dev/tty may not exist or may not be writable!
            pass


# get the list of all files in the given directories (including those in nested directories)
def all_files(*paths, basedir='.'):
    basedir = pathlib.Path(basedir)
    return [str(pathlib.Path(dirpath, f).relative_to(basedir))
            for path in paths
            for dirpath, dirnames, files in os.walk(basedir / path)
            for f in files]


def make_package_data():
    for_all_files = ('__license__', )
    return {NAME: all_files(*for_all_files,
                            basedir=pathlib.Path(SRC_DIR, NAME))}


def get_submodule_commit(repo_owner, repo_name, commit_sha, submodule_path):
    """
    Get submodule commit hash for a specific GitHub repository commit.

    Args:
        repo_owner: Repository owner
        repo_name: Repository name
        commit_sha: Commit SHA in the main repository
        submodule_path: Relative path to the submodule

    Returns:
        Submodule commit SHA string
    """
    # Create SSL context (bypass verification if needed)
    ctx = ssl.create_default_context()
    # Uncomment below line if you encounter certificate errors
    # ctx.check_hostname = False
    # ctx.verify_mode = ssl.CERT_NONE
    # Step 1: Get repository tree recursively for the specific commit
    tree_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/trees/{commit_sha}?recursive=1"
    ################################################################
    try:
        # Make HTTP request
        req = urllib.request.Request(tree_url)
        with urllib.request.urlopen(req, context=ctx) as response:
            # Check rate limit headers
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining == '0':
                reset_time = response.headers.get('X-RateLimit-Reset')
                raise RuntimeError(f"GitHub API rate limit exceeded. Reset at {reset_time}")
            # Parse JSON response
            data = response.read()
            encoding = response.info().get_content_charset('utf-8')
            tree_data = json.loads(data.decode(encoding))
    except urllib.error.HTTPError as e:
        if e.code == 403 and 'rate limit' in e.reason.lower():
            raise RuntimeError("GitHub API rate limit exceeded. Try again later.")
        raise  # Re-raise other HTTP errors
    ################################################################
    # response = requests.get(tree_url)
    # if response.status_code == 403 and 'rate limit' in response.text.lower():
    #     raise RuntimeError("GitHub API rate limit exceeded. Try again later.")
    # response.raise_for_status()
    # tree_data = response.json()
    ################################################################
    # Step 2: Find the submodule entry in the tree
    for item in tree_data.get('tree', []):
        if item['path'] == submodule_path:
            if item['type'] == 'commit':
                return item['sha']
            raise ValueError(f"Path '{submodule_path}' is not a submodule (type: {item['type']})")
    raise FileNotFoundError(f"Submodule path '{submodule_path}' not found in repository")


def clone_and_checkout_submodules(root_dir, submodule_names):
    parsed_url = urllib.parse.urlparse(__url__)
    url_path = pathlib.Path(parsed_url.path)
    gitmodules = configparser.ConfigParser()
    gitmodules.read(root_dir / '.gitmodules')
    for submodule_name in submodule_names:
        galaxia_url = parsed_url._replace(path=str((url_path / gitmodules[f'submodule "{submodule_name}"']['url']).resolve())).geturl()
        galaxia_commit = get_submodule_commit(
            *(url_path.parts[-2:] + (_version.get_versions()['full-revisionid'], submodule_name))
            )
        try:
            _temp = subprocess.Popen(['git', 'clone', galaxia_url], cwd=root_dir,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in iter(_temp.stdout.readline, ""):
                say(line)
            _temp.wait()
        except RuntimeError as e:
            raise CompileError(str(e) + f"\nError cloning {submodule_name}, aborting...\n")
        _temp = subprocess.call(['git', 'checkout', galaxia_commit], cwd=root_dir / submodule_name)
        # git archive -vvv --remote=<REPO_URL> <REF> | tar -xvf -


def check_submodules(root_dir):
    root_dir = pathlib.Path(root_dir)
    # if not pathlib.os.listdir(PYENBID) or not pathlib.os.listdir(PYGALAXIA):
    say("\nChecking submodules, running git...")
    try:
        _temp = subprocess.call(['git', 'submodule', 'update', '--init', '--recursive'], cwd=root_dir)
    except FileNotFoundError:
        raise OSError("Your system does not have git installed. Please install git before proceeding")
    if _temp == 128:
        say("\n\tFailed to git submodule init submodules, attempting to clone...")
        clone_and_checkout_submodules(root_dir, [PYENBID, PYGALAXIA])
        say("\n\tClone was successful")
        # raise OSError(f"The repository from which you are attempting to install this package is not a git repository.\nPlease follow the online instructions for proper installation ({__url__}/#installation).")
    #
    EnBiD_src_root = root_dir / PYENBID / SRC_DIR
    EnBiD_src = import_source_file("EnBiD_src", EnBiD_src_root / '__init__.py')
    EnBiD_meta = import_source_file("EnBiD_src.__metadata__", EnBiD_src_root / '__metadata__.py')
    #
    Galaxia_src_root = root_dir / PYGALAXIA / SRC_DIR
    Galaxia_src = import_source_file("Galaxia_src", Galaxia_src_root / '__init__.py')
    Galaxia_meta = import_source_file("Galaxia_src.__metadata__", Galaxia_src_root / '__metadata__.py')
    #### TODO: below's fix is ugly, there must be something better to do!
    if pathlib.Path(sys.argv[0]).name == 'setup.py' and (sys.argv[1] == 'egg_info' if len(sys.argv)>1 else False) and 'pip' in sys.argv[-1]:
        subprocess.call(['pip', 'cache', 'remove', '*_ananke'])
    ####
    return EnBiD_meta, Galaxia_meta


def append_install_requires_with_submodules(install_requires):
    EnBiD_meta, Galaxia_meta = check_submodules(ROOT_DIR)
    if IS_BUILD:
        submodule_dependencies = [
            f"enbid_ananke=={version.Version(EnBiD_meta.__version__).public}",
            f"galaxia_ananke=={version.Version(Galaxia_meta.__version__).public}"
            ]
    else:
        submodule_dependencies = [
            f"enbid_ananke @ file://{pathlib.Path(EnBiD_meta.__file__).parent.parent}",
            f"galaxia_ananke @ file://{pathlib.Path(Galaxia_meta.__file__).parent.parent}"
            ]
    return install_requires + submodule_dependencies


make_cmdclass = versioneer.get_cmdclass
