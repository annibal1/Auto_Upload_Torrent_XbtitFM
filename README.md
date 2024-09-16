Detailed Guide to Installing and Using the Automatic Torrent Creation and Seed Script

This guide will provide you with detailed instructions on how to install and use the Python script that automatically creates torrent files, uploads them to a site, and adds them to qBittorrent for seeding. The script is designed to run on Ubuntu systems, using mktorrent to create torrent files and qbittorrent-nox as a torrent client. The detailed steps for installation and use are listed below.
1. Prerequisites

Before starting, make sure you have access to an Ubuntu server (or a Linux-compatible system) and that you have Python 3 installed. Additionally, you will need the following dependencies:

mktorrent to create torrent files.
qbittorrent-nox as a torrent client.
Python 3 with pip installed.

If you do not have Python 3 and pip, install them using:
sudo apt-get update
sudo apt-get install python3 python3-pip

2. Installing Dependencies
Step 1: Installing mktorrent and qbittorrent-nox

mktorrent is used for creating torrent files, while qbittorrent-nox is a torrent client without a graphical interface. Both software are installed directly from the Ubuntu package manager.

Run the following commands to install them:
sudo apt-get update
sudo apt-get install mktorrent qbittorrent-nox

Step 2: Installing Python Dependencies

To simplify the installation of Python dependencies, the script uses a requirements.txt file. You can install all the necessary dependencies with a single command.
pip install -r requirements.txt

This command will install all the necessary libraries such as beautifulsoup4, qbittorrent-api, requests, lxml and python-dotenv.
3. Configuring the Script
Step 1: Creating the .env file

The script uses a .env file to load the necessary environment variables. This file contains configuration information such as qBittorrent credentials, URLs and API keys.
The epn.env file is in the same directory as the script and has the following content:

BITTORRENT_HOST=http://localhost
QBIT_PORT=8080
QBITTORRENT_USER=il_tuo_username
QBITTORRENT_PASSWORD=la_tua_password
TMDB_APIKEY=la_tua_chiave_api_tmdb
UPLOAD_URL=https://esempio.com/upload
DOWNLOAD_URL_BASE=https://esempio.com/
ANNOUNCE_URL=http://esempio.com:2710/announce
TORRENT_SAVE_DIR=/root/test/file_torrent
POSTER_SAVE_DIR=/root/test/poster_dir

BITTORRENT_HOST: URL of the qBittorrent server (usually http://localhost or the IP address of the server).
QBIT_PORT: The port on which qBittorrent is running (default 8080).
QBITTORRENT_USER and QBITTORRENT_PASSWORD: qBittorrent login credentials.
TMDB_APIKEY: Your API key for TMDB (The Movie Database), used to get movie descriptions.
UPLOAD_URL: URL to upload the torrent file to the site.
DOWNLOAD_URL_BASE: Base URL to download torrent files from the site.
ANNOUNCE_URL: URL of the announcer for the torrent tracker.
TORRENT_SAVE_DIR: Directory where the torrent files will be saved.
POSTER_SAVE_DIR: Directory where the posters downloaded from TMDB will be saved.

Step 2: Creating the categories file
The script uses a categories_config.json file to map category names to their respective IDs on the site. Create a categories_config.json file and enter your site's categories, for example:
{
  "bluray": 40,
  "4k": 42,
  "dvdrip": 15,
  "quotidiani": 36
}
4. Running the Script

After you have everything configured, you can run the script using the python3 command. You need to specify two parameters: the category name (for example, bluray) and the directory of the movie to be converted into a torrent.

Example:
python3 start.py bluray /root/test/Cintura.nera.2024.iTALiAN.WEB-DL
The script will do the following:

Create a torrent file using mktorrent and save it to the directory specified in TORRENT_SAVE_DIR.
Upload the torrent file to the site using the upload API provided in the .env file.
Download the torrent file from the site and add it to qBittorrent for seeding.
Perform a recheck of the files on qBittorrent to make sure the files match the torrent.
Force a second recheck after 2 minutes to make sure everything is configured correctly.

5. Troubleshooting

Authentication error on qBittorrent: Make sure the login credentials in the .env file are correct.
TMDB does not return any results: Verify that your TMDB API key is valid and that the movie name is formatted correctly.
Torrent does not seed: Verify that the save path (TORRENT_SAVE_DIR and POSTER_SAVE_DIR) is correct and that the files are present.
By following these steps, you will be able to install, configure and use the script on Ubuntu to automate torrent creation and seeding.

