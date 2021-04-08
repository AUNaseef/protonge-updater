#!/usr/bin/env python3
# ProtonUp - ProtonGE Downloader and Updater
# Authored by: Naseef Abdullah <aunaseef AT protonmail.com>
import sys
import os
import json
from urllib.request import urlopen, urlretrieve
import requests
import tarfile
from configparser import ConfigParser


version = 0.3
protonge_url = 'https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/'
configdir = os.path.expanduser('~/.config/protonup')
install_directory = '~/.steam/root/compatibilitytools.d'
interactive = True

s_path = os.path.abspath(__file__)
s_installpath = "/usr/bin/protonup"


def readconfig():
    global install_directory
    config = ConfigParser()
    config.read(configdir + "/config.ini")
    if(config.has_option("protonup", "installdir")):
        install_directory = os.path.expanduser(config["protonup"]["installdir"])
        print(f"Custom Location: {install_directory}")
    else:
        install_directory = os.path.expanduser(install_directory)


def help():
    print(f"ProtonUp {version} : Commands",
          "\n[none]   : Update to the latest version",
          "\n[tag]    : Install a specific version",
          "\n-l, list : List installed Proton versions",
          "\n-d, dir  : Set installation directory",
          "\n-y, yes  : Disable prompts and progress",
          "\n-h, help : Show this help",
          "\n--install, --uninstall")


def list_versions():
    # Get the list of folders in install directory
    try:
        installed_versions = os.listdir(install_directory)
    except OSError:
        print("Error: Failed to find proton installations")
        exit()

    found = 0
    output = ""

    # List names of directories with proton
    for i in installed_versions:
        if(os.path.exists(f"{install_directory}/{i}/proton")):
            found += 1
            output += i + '\n'

    print(f"Found {found} Proton installation{'s' if found != 1 else ''}")
    sys.stdout.write(output)


def install(version='latest'):
    if version == 'latest':
        print("Cheking for updates ...")
        url = protonge_url + 'latest'
    else:
        if os.path.exists(install_directory + "/Proton-" + version):
            print("Proton " + version + " is already installed")
            if(input("Delete and re-install? (y/n) : ") in ['y', 'Y']):
                os.rmdir(install_directory + "/Proton-" + version)
            else:
                exit()
        print("Preparing to install ...")
        url = protonge_url + "tags/" + version

    # Load information about the release from github api
    try:
        data = json.load(urlopen(url))
    except OSError:
        print("Failed to retrieve data",
              "\nNetwork error or invalid release tag")
        exit()

    download_version = data['tag_name']
    download_link = data['assets'][0]['browser_download_url']

    # Check if this version already exists
    if os.path.exists(install_directory + "/Proton-" + download_version):
        print("Proton " + download_version + " is already installed")

    else:
        # Download and store the file temporarily in /tmp
        download_location = '/tmp/' + download_link.split('/')[-1]

        # Show download progress when not running in silent mode
        if (interactive):
            download = requests.get(download_link, stream=True)
            size = int(download.headers.get('content-length'))
            size_mb = round(size / 1048576, 2)
            chunk_count = size / 32768

            print("Ready to install Proton " + download_version)
            print("Size      : ", size_mb, "MB")
            print("Published : ", data['published_at'].split('T')[0])

            if(not input("Continue? (y/n) : ") in ['y', 'Y']):
                print("Installation Cancelled")
                exit()

            with open(download_location, 'wb') as f:
                x = 1
                for chunk in download.iter_content(chunk_size=32768):
                    progress = round((x / chunk_count) * 100, 2)
                    downloaded = round((x * 32768) / 1048576, 2)
                    sys.stdout.write(f"\rDownloaded {progress}% - {downloaded} MB/{size_mb}MB")
                    x += 1
                    if chunk:
                        f.write(chunk)
                        f.flush()
                print()
        else:
            print("Downloading", download_version, "...")
            urlretrieve(download_link, filename=download_location)

        # Extract the download file into installation directory
        print("Installing ...")
        tarfile.open(download_location, "r:gz").extractall(install_directory)
        os.remove(download_location)
        print("Successfully installed")


def main(argv):
    global interactive
    argc = len(argv)

    try:
        if(argc > 1):
            if(argv[1] in ['-y', '-yes']):
                interactive = False
                if(argc > 2):
                    install(argv[2])
                else:
                    install()

            elif(argv[1] in ['-h', '-help']):
                help()

            elif(argv[1] in ['-l', '-list']):
                list_versions()

            elif(argv[1] in ['-d', '-dir']):
                if(argc > 2):
                    # Add custom directory to configuration file
                    print(f"changing install directory to {argv[2]}")
                    config = ConfigParser()
                    config.read(configdir + "/config.ini")
                    if(not config.has_section('protonge-updater')):
                        config.add_section('protonge-updater')
                    config['protonge-updater']['installdir'] = argv[2]

                    if(not os.path.exists(configdir)):
                        os.mkdir(configdir)
                        config['protonge-updater']['installdir'] = argv[2]

                    with open(configdir + "/config.ini", 'w') as output:
                        config.write(output)
                else:
                    readconfig()
                    print(f"current install directory: {install_directory}",
                           "\nUse -d [custom directory] to change")

            elif(argv[1] in ['--install']):
                # Installing to bin
                if(s_path == s_installpath):
                    print("Already installed")
                    exit()
                elif(not os.system(f"sudo cp '{s_path}' {s_installpath}")):
                    print("Install successful",
                          "\nCommand: protonup")
                    exit()
                print()
                print("Install failed")
                exit()

            elif(argv[1] in ['--uninstall']):
                # Uninstalling
                if(not s_path == s_installpath):
                    print("Not installed")
                    exit()
                elif(not os.system(f"sudo rm '{s_path}'")):
                    print("Uninstall successful")
                    exit()
                print("Uninstall failed")
                exit()

            else:
                readconfig()
                if(argc > 2):
                    if(argv[2] in ['-y', '-yes']):
                        interactive = False
                install(argv[1])

        else:
            readconfig()
            install()

    except KeyboardInterrupt:
        print("\nExiting ...")


if __name__ == '__main__':
    main(sys.argv)
