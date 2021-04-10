#!/usr/bin/env python3
"""Manage Proton Installations"""
import sys
import os
from configparser import ConfigParser
import shutil
import argparse
import requests

# Constant values
CONFIG_DIR = os.path.expanduser('~/.config/protonup/')
CONFIG_FILE = 'config.ini'
DEFAULT_INSTALL_DIR = '~/.steam/root/compatibilitytools.d/'
TEMP_DIR = '/tmp/protonup/'
PROTONGE_URL = 'https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/'


# --- GENERAL FUNCTIONS --- #
def download(url, destination, show_progress=True):
    """Download files"""
    file = requests.get(url, stream=True)
    f_size = int(file.headers.get('content-length'))
    f_size_mib = round(f_size / 1048576, 2)
    c_size = 65536
    c_count = f_size / c_size
    c_current = 1

    with open(destination, 'wb') as dest:
        for chunk in file.iter_content(chunk_size=c_size):
            if chunk:
                dest.write(chunk)
                dest.flush()
            if show_progress:
                progress = round((c_current / c_count) * 100, 2)
                downloaded = round((c_current * c_size) / 1048576, 2)
                sys.stdout.write(f'\rDownloaded {progress}% - {downloaded} MiB/{f_size_mib} MiB')
                c_current += 1


def folder_size(folder):
    """Calculate the size of a folder"""
    size = 0
    for root, dirs, files in os.walk(folder, onerror=None):
        for file in files:
            size += os.path.getsize(os.path.join(root, file))
    return size


def fetch_release(github_url, quiet=True):
    """Fetch release information from github"""
    values = dict()

    try:
        data = requests.get(github_url).json()
    except OSError:
        if not quiet:
            print("Failed to fetch release ", "\nNetwork error or invalid release tag")
        return None

    for asset in data['assets']:
        if asset['name'].endswith('sha512sum'):
            values['checksum'] = asset['browser_download_url']
        elif asset['name'].endswith('tar.gz'):
            values['download'] = asset['browser_download_url']
    values['date'] = data['published_at'].split('T')[0]
    values['version'] = data['tag_name']
    return values


# --- PROTONUP-SPECIFIC FUNCTIONS --- #
def install_directory(target=None):
    """Custom install directory"""
    config = ConfigParser()
    config.read(CONFIG_DIR + CONFIG_FILE)

    if target is None:
        if config.has_option('protonup', 'installdir'):
            installdir = os.path.expanduser(config['protonup']['installdir'])
        else:
            installdir = DEFAULT_INSTALL_DIR
    else:
        if not target.endswith('/'):
            target += '/'
        if not config.has_section('protonup'):
            config.add_section('protonup')
        config['protonup']['installdir'] = installdir = target
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_DIR + CONFIG_FILE, 'w') as file:
            config.write(file)

    return installdir


def installed_versions():
    """List of proton installations"""
    installdir = install_directory()
    versions_found = []

    if os.path.exists(installdir):
        folders = os.listdir(installdir)
        # Find names of directories with proton
        for folder in folders:
            if os.path.exists(f"{installdir}/{folder}/proton"):
                versions_found.append(folder)

    return versions_found


def get_proton(version=None, quiet=True, yes=True, dl_only=False, output=None):
    """Download and (optionally) install Proton"""
    if not quiet:
        print(version)
    if yes or input("Continue?( y/n) : ") in ['y', 'Y']:
        print("Let's move on!")
    if dl_only:
        if not quiet:
            print(f"downloading to {output}")


def remove_proton(version=None, yes=True, quiet=True):
    """Uninstall existing proton installation"""
    target = install_directory() + "Proton-" + version
    if os.path.exists(target):
        if yes or input(f"Do you want to remove {version}? (y/n) : ") in ['y', 'Y']:
            if not quiet:
                print(f"Removing {version}")
            shutil.rmtree(install_directory() + "Proton-" + version)
    else:
        if not quiet:
            print(f"Proton-{version} not installed")
        return False
    return True


def parse_arguments():
    """Parse commandline arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', type=str, default=None, help='proton-ge version tag')
    parser.add_argument('-l', '--list', action='store_true', help='list installed version')
    parser.add_argument('-r', '--rem', type=str, default=None, metavar='TAG',
                        help='remove existing installations')
    parser.add_argument('-o', '--output', type=str, default=None, help='set download directory')
    parser.add_argument('-d', '--dir', type=str, default=None, help='set installation directory')
    parser.add_argument('-y', '--yes', action='store_true', help='disable prompts')
    parser.add_argument('-q', '--quiet', action='store_true', help='disable logging')
    parser.add_argument('--download', action='store_true', help='download only')
    return parser.parse_args()


def main():
    """Start here"""
    args = parse_arguments()
    if args.dir:
        print(f"Changed install directory to \"{install_directory(args.dir)}\"")
    if args.tag:
        get_proton(version=args.tag, quiet=args.quiet, yes=args.yes, dl_only=args.download,
                   output=args.out)
    if args.rem:
        remove_proton(version=args.rem, yes=args.yes, quiet=args.quiet)
    if args.list:
        installdir = install_directory()
        for item in installed_versions():
            print(f"{item} - {round(folder_size(installdir + item)/1048576, 2)} MiB")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == '__main__':
    main()
