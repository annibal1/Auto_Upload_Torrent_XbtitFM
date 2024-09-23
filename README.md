Detailed Guide to Installing and Using the Automatic Torrent Creation and Seed Script

This guide provides detailed instructions on how to install and use the Python script that automatically creates torrent files, uploads them to a site, and adds them to qBittorrent for seeding. The script is compatible with both Ubuntu and Windows systems, with specific instructions for each environment. Follow the steps below to set up and use the script on your preferred platform.
Prerequisites

Before starting, ensure you have access to your preferred system (either Ubuntu or Windows) and Python 3 installed. The dependencies required are:

    For Ubuntu: mktorrent to create torrent files and qbittorrent-nox as a torrent client without a graphical interface.
    For Windows: Python 3 with torrentool to create torrent files and qbittorrent-api to interact with the qBittorrent client.

If you do not have Python 3 and pip installed, you can set them up as follows:
Installing Python 3 and pip
Ubuntu:

bash

sudo apt-get update
sudo apt-get install python3 python3-pip

Windows:

Download and install Python 3 from the official Python website: Python Downloads. Ensure you select the option to install pip during the setup.
Installing Dependencies
Ubuntu
Step 1: Installing mktorrent and qbittorrent-nox

mktorrent is used for creating torrent files, and qbittorrent-nox is a torrent client without a graphical interface. Install both using the Ubuntu package manager:

bash

sudo apt-get update
sudo apt-get install mktorrent qbittorrent-nox

Step 2: Installing Python Dependencies

Use the requirements.txt file to install the required Python libraries. Run the following command:

bash

pip install -r requirements.txt

This will install libraries like beautifulsoup4, qbittorrent-api, requests, lxml, python-dotenv, and torrentool.
Windows
Step 1: Installing Python Dependencies

For Windows, the script uses a requirements.txt file to simplify dependency installation. Run the following command in your terminal:

bash

pip install -r requirements.txt

This will install all necessary dependencies including beautifulsoup4, qbittorrent-api, requests, lxml, python-dotenv, and torrentool.
Configuring the Script
Step 1: Creating the .env File

The script requires a .env file to load necessary environment variables. This file includes configuration details such as qBittorrent credentials, API keys, and URLs. Create a file named epn.env in the same directory as the script with the following content:

plaintext

# qBittorrent Settings
BITTORRENT_HOST=http://127.0.0.1
QBITTORRENT_USER=your_qbittorrent_username  # Replace with your qBittorrent username
QBITTORRENT_PASSWORD=your_qbittorrent_password  # Replace with your qBittorrent password
QBIT_PORT=8080  # Default port for qBittorrent

# TMDB API Key
TMDB_APIKEY=your_tmdb_api_key  # Replace with your TMDB API key

# Cookies for Site Authentication
COOKIES=uid=your_uid;pass=your_pass  # Replace with your site's authentication cookies

# URLs for Upload and Download
UPLOAD_URL=https://example.com/upload  # Replace with your upload URL
DOWNLOAD_URL_BASE=https://example.com/  # Replace with your site's base download URL
ANNOUNCE_URL=http://example.com:2710/announce  # Replace with your tracker announce URL

# Request Headers
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3
REFERER=https://example.com/upload  # Replace with your referer URL

# Directories for Files and Torrents
POSTER_SAVE_DIR=C:\Path\To\Posters  # Directory where downloaded posters will be saved
TORRENT_SAVE_DIR=C:\Path\To\Torrents  # Directory where created torrent files will be saved
TORRENT_DOWNLOAD_DIR=C:\Path\To\DownloadedTorrents  # Directory where torrents downloaded from the site will be saved

Step 2: Creating the Categories File

The script uses a categories_config.json file to map category names to their respective IDs on the site. Create this file with your site's categories:

json

{
  "bluray": 40,
  "4k": 42,
  "dvdrip": 15,
  "quotidiani": 36
}

Running the Script
Ubuntu

Run the script using Python 3. You need to specify two parameters: the category name (e.g., bluray) and the directory of the movie you want to convert into a torrent.

Example:

bash

python3 start.py bluray /root/test/Cintura.nera.2024.iTALiAN.WEB-DL

Windows

Run the script from the command line. Make sure to specify the paths using double quotes if they contain spaces.

Example:

bash

python start.py bluray "D:\Film\BluRay\Il Gladiatore (10th Anniversary Edition)"

Handling Single Files with the -s Option

To process a single file instead of an entire directory, use the -s option. This option ensures that the script correctly handles individual files.

Example for a Single File:

bash

python start.py serietv -s "C:\Users\Administrator\Desktop\Respira.S01.C0P\Respira.1x08.Goccia.fredda.NF.WEB-DL.DDP5.1.H.264.C0P.mkv"

Handling Paths with Spaces

When using paths that contain spaces, make sure to enclose the entire path in double quotes ("). This applies to both category names and directory paths.

Example with Spaces:

bash

python start.py bluray "C:\Users\Administrator\Desktop\Ragazze interrotte (1999) - BDMux HEVC 1080p - Ita Eng"

Script Workflow

    Create a Torrent File: The script creates a torrent using mktorrent (Ubuntu) or torrentool (Windows) and saves it in the directory specified in TORRENT_SAVE_DIR.
    Upload the Torrent: The script uploads the torrent file to the site using the URL provided in the .env file.
    Download the Torrent: It downloads the newly generated torrent file from the site and adds it to qBittorrent for seeding.
    Recheck the Files: The script performs a recheck on qBittorrent to ensure the files match the torrent.
    Force a Second Recheck: After 2 minutes, it forces a second recheck to verify everything is set up correctly.

Troubleshooting

    Authentication Error on qBittorrent: Verify that the login credentials in the .env file are correct.
    TMDB Search Issues: Check that your TMDB API key is valid and that the movie title is correctly formatted.
    Torrent Does Not Seed: Ensure that the save paths (TORRENT_SAVE_DIR and POSTER_SAVE_DIR) are correct and that the files are present.

By following this guide, you will be able to install, configure, and use the script on either Ubuntu or Windows systems to automate torrent creation and seeding.

This updated guide provides the steps for using the script on both Ubuntu and Windows, ensuring compatibility with different environments.
