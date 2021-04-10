#!/usr/bin/env python3
# ProtonUp - ProtonGE Downloader and Updater
# Authored by: Naseef Abdullah <aunaseef AT protonmail.com>
"""Update/Install/Uninstall Proton GE Versions"""
import sys
import os
import json
from urllib.request import urlopen, urlretrieve
import tarfile
from configparser import ConfigParser
import shutil
import requests


version = 0.4
HELP = """ProtonUp {version} (GPLv3)
URL: https://github.com/AUNaseef/protonup
Basic Commands
[none]   : Update to the latest version
[tag]    : Install a specific version
-l, list : List installed Proton versions
-d, dir  : Set installation directory
-y, yes  : Disable prompts and progress
-h, help : Show this help

Meta Commands:
--install, --uninstall, --update"""

protonge_url = 'https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/'
configdir = os.path.expanduser('~/.config/protonup')
install_directory = '~/.steam/root/compatibilitytools.d'
interactive = True

s_path = os.path.abspath(__file__)
s_installpath = "/usr/bin/protonup"
s_dlink = "https://github.com/AUNaseef/protonge-updater/raw/main/protonup.py"


def readconfig(install_directory):
    """Read current config"""
    config = ConfigParser()
    config.read(configdir + "/config.ini")
    if config.has_option("protonup", "installdir"):
        install_directory = os.path.expanduser(config["protonup"]["installdir"])
    else:
        install_directory = os.path.expanduser(install_directory)
    return install_directory


def list_versions():
    """get list of installated versions of Proton"""
    """Get the list of folders in install directory"""
    installdir = readconfig(install_directory)
    try:
        installed_versions = os.listdir(installdir)
    except OSError:
        print("Error: Failed to find proton installations")
        return []

    output = []

    # List names of directories with proton
    for i in installed_versions:
        if os.path.exists(installdir + "/" + i + "/proton"):
            output.append(i)
    return output


def _print_versions():
    versions = list_versions()
    print("Found %s Proton installation" % len(versions), end="")
    if len(versions) != 1:
        print("s", end="")
    print()
    if versions == []:
        sys.exit()
    for each in versions:
        print(each)


def uninstall_proton(version):
    """Uninstall given Proton version"""
    installed_versions = os.listdir(install_directory)
    for each in enumerate(installed_versions):
        installed_versions[each[0]] = installed_versions[each[0]][7:]
    if version not in installed_versions:
        print("Not a valid version")
    else:
        shutil.rmtree(install_directory + "/Proton-" + version)
        print("Uninstall successful")


def download(version="latest", just_download=False, interactive=True):
    """Download a specific version of Proton GE"""
    if version == "latest":
        url = protonge_url + "latest"
    else:
        url = protonge_url + "tags/" + version
    # Load information about the release from github api
    try:
        data = json.load(urlopen(url))
    except OSError:
        print("Failed to retrieve data",
              "\nNetwork error or invalid release tag")
        sys.exit()

    download_version = data['tag_name']
    download_link = data['assets'][0]['browser_download_url']

    if just_download is True:
        download_location = os.getcwd() + "/" + download_link.split('/')[-1]
    else:
        download_location = '/tmp/' + download_link.split('/')[-1]

    if interactive is True:
        download = requests.get(download_link, stream=True)
        size = int(download.headers.get('content-length'))
        size_mb = round(size / 1048576, 2)
        chunk_count = size / 32768

        print("Ready to download Proton " + download_version)
        print("Size      : ", size_mb, "MB")
        print("Published : ", data['published_at'].split('T')[0])

        if not input("Continue? (y/n) : ") in ['y', 'Y']:
            print("Download Cancelled")
            return False

        with open(download_location, 'wb') as f:
            x = 1
            for chunk in download.iter_content(chunk_size=32768):
                progress = int(round((x / chunk_count) * 100, 2))
                downloaded = int(round((x * 32768) / 1048576, 2))
                sys.stdout.write(f"\rDownloaded {progress}% - {downloaded} MB/{size_mb}MB")
                x += 1
                if chunk:
                    f.write(chunk)
                    f.flush()
            print()
    else:
        print("Downloading", download_version, "...")
        urlretrieve(download_link, filename=download_location)
    return download_location


def install(version='latest', interactive=True):
    """Download and install a specific version of Proton"""
    installdir = readconfig(install_directory)
    if version == 'latest':
        print("Checking for updates ...")
        url = protonge_url + 'latest'
    else:
        if os.path.exists(installdir + "/Proton-" + version):
            print("Proton " + version + " is already installed")
            if input("Delete and re-install? (y/n) : ") in ['y', 'Y']:
                os.rmdir(installdir + "/Proton-" + version)
            else:
                sys.exit()
        print("Preparing to install ...")
        url = protonge_url + "tags/" + version

    # Load information about the release from github api
    try:
        data = json.load(urlopen(url))
    except OSError:
        print("Failed to retrieve data",
              "\nNetwork error or invalid release tag")
        sys.exit()

    download_version = data['tag_name']
    download_link = data['assets'][0]['browser_download_url']

    # Check if this version already exists
    if os.path.exists(installdir + "/Proton-" + download_version):
        print("Proton " + download_version + " is already installed")

    else:
        download_location = download(version=version)
        if download_location is False:
            print("Installation Canceled")
        # Extract the download file into installation directory
        print("Installing ...")
        tarfile.open(download_location, "r:gz").extractall(installdir)
        os.remove(download_location)
        print("Successfully installed")


def _post_install_cleanup():
    """Post install cleanup"""
    try:
        os.chmod("/tmp/protonup", 0o776)
        os.remove(s_path)
        shutil.copytree("/tmp/protonup", s_path)
    except (FileNotFoundError, PermissionError):
        return False
    return True


def _main(argv):
    """Main function"""
    readconfig(install_directory)
    argc = len(argv)
    try:
        if argc > 1:
            if argv[1] in ['-y', '-yes']:
                if argc > 2:
                    install(argv[2], interactive=False)
                else:
                    install(interactive=False)

            elif argv[1] in ['-h', '-help', '--help']:
                print(HELP)

            elif argv[1] in ['-l', '-list', "--list"]:
                _print_versions()

            elif argv[1] in ['-d', '-dir']:
                if argc > 2:
                    # Add custom directory to configuration file
                    print(f"changing install directory to {argv[2]}")
                    config = ConfigParser()
                    config.read(configdir + "/config.ini")
                    if not config.has_section('protonup'):
                        config.add_section('protonup')
                    config['protonup']['installdir'] = argv[2]

                    if not os.path.exists(configdir):
                        os.mkdir(configdir)
                        config['protonup']['installdir'] = argv[2]

                    with open(configdir + "/config.ini", 'w') as output:
                        config.write(output)
                else:
                    print(f"current install directory: {install_directory}",
                          "\nUse -d [custom directory] to change")

            elif argv[1] in ['--install']:
                # Installing to bin
                if s_path == s_installpath:
                    print("Already installed")
                    sys.exit()
                elif not shutil.copytree(s_path, s_installpath):
                    print("Install successful",
                          "\nCommand: protonup")
                    sys.exit()
                print()
                print("Install failed")
                sys.exit()

            elif argv[1] in ['--uninstall']:
                # Uninstalling
                if s_path != s_installpath:
                    print("Not installed")
                    sys.exit()
                elif not os.remove(s_path):
                    print("Uninstall successful")
                    sys.exit()
                print("Uninstall failed")
                sys.exit()

            elif argv[1] in ['--update']:
                # Updating
                urlretrieve(s_dlink, filename="/tmp/protonup")
                if s_path == s_installpath:
                    # When installed
                    if _post_install_cleanup():
                        print("Update successful")
                        sys.exit()
                elif _post_install_cleanup():
                    # Portable
                    print("Update successful")
                    sys.exit()

                print("Update failed")
                sys.exit()
            elif argv[1] in ["--download"]:
                if argc >= 3:
                    download(version=argv[2], just_download=True)
                else:
                    download(just_download=True)
            elif argv[1] in ["-r", "--remove"]:
                if argc > 2:
                    uninstall_proton(argv[2])
                else:
                    print("No version provided.")
            else:
                if argc > 2:
                    if argv[2] in ['-y', '-yes']:
                        install(version=argv[1], interactive=False)
                else:
                    install(version=argv[1])

        else:
            install()

    except KeyboardInterrupt:
        print("\nExiting ...")


if __name__ == '__main__':
    _main(sys.argv)
