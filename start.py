import qbittorrentapi
import time
import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import argparse
import re
import subprocess

# Carica variabili d'ambiente dal file epn.env
load_dotenv('epn.env')

# Parametri qBittorrent dal file epn.env
QBITTORRENT_HOST = os.getenv('BITTORRENT_HOST')
QBITTORRENT_PORT = os.getenv('QBIT_PORT')
QBITTORRENT_USER = os.getenv('QBITTORRENT_USER')
QBITTORRENT_PASSWORD = os.getenv('QBITTORRENT_PASSWORD')
QBITTORRENT_URL = f"{QBITTORRENT_HOST}:{QBITTORRENT_PORT}"

# Ottieni il percorso per salvare i file torrent e poster dal file epn.env
TORRENT_SAVE_DIR = os.getenv('TORRENT_SAVE_DIR', '/root/test/file_torrent')
POSTER_SAVE_DIR = os.getenv('POSTER_SAVE_DIR', '/root/test/poster_dir')
TORRENT_SAVE_PATH = os.getenv('TORRENT_SAVE_PATH', '/root/test')  # Nuova variabile per il percorso di salvataggio

# TMDB API Key dal file epn.env
TMDB_API_KEY = os.getenv('TMDB_APIKEY')

# URL per upload e download
UPLOAD_URL = os.getenv('UPLOAD_URL')
DOWNLOAD_URL_BASE = os.getenv('DOWNLOAD_URL_BASE')
ANNOUNCE_URL = os.getenv('ANNOUNCE_URL')
USER_AGENT = os.getenv('USER_AGENT')
REFERER = os.getenv('REFERER')

# Headers per le richieste
headers = {
    'User-Agent': USER_AGENT,
    'Referer': REFERER,
}

# Recupera i cookie dal file epn.env
COOKIES = os.getenv('COOKIES')

# Converte i cookie in un dizionario
def parse_cookies(cookie_str):
    cookies_dict = {}
    if cookie_str:
        cookie_pairs = cookie_str.split(';')
        for cookie in cookie_pairs:
            key, value = cookie.split('=', 1)
            cookies_dict[key.strip()] = value.strip()
    return cookies_dict

cookies_dict = parse_cookies(COOKIES)

# Connessione a qBittorrent
client = qbittorrentapi.Client(host=QBITTORRENT_URL, username=QBITTORRENT_USER, password=QBITTORRENT_PASSWORD)

try:
    client.auth_log_in()
    print("Connesso a qBittorrent!")
except qbittorrentapi.LoginFailed as e:
    print(f"Errore di login a qBittorrent: {e}")
    exit(1)

# Funzione per pulire il titolo del film, separando il nome dall'anno
def clean_movie_title(file_name):
    pattern = r"(.+?)\.(\d{4})"
    match = re.search(pattern, file_name)
    if match:
        title = match.group(1).replace('.', ' ')
        year = match.group(2)
        return title, year
    else:
        return file_name.replace('.', ' '), None

# Funzione per cercare i dettagli su TMDB
def fetch_tmdb_info(movie_title):
    title, year = clean_movie_title(movie_title)
    print(f"Cercando su TMDB: {title}")
    
    # Prova a ottenere la descrizione in italiano
    search_url_it = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&language=it-IT"
    search_url_en = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&language=en-US"

    try:
        # Primo tentativo in italiano
        response = requests.get(search_url_it)
        data = response.json()

        if 'results' in data and data['results']:
            if year:
                for movie in data['results']:
                    if str(movie.get('release_date', '')).startswith(year):
                        description = movie.get('overview', 'Descrizione non disponibile.')
                        poster_path = movie.get('poster_path')
                        poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None
                        print(f"Trovato su TMDB in italiano: {movie['title']} ({year})")
                        return {'description': description, 'poster_url': poster_url}

            movie = data['results'][0]
            description = movie.get('overview', 'Descrizione non disponibile.')
            poster_path = movie.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None
            print(f"Trovato su TMDB in italiano: {movie['title']}")
            return {'description': description, 'poster_url': poster_url}
        else:
            print("Film non trovato in italiano, provo in inglese...")

            # Se non trovato in italiano, prova in inglese
            response = requests.get(search_url_en)
            data = response.json()

            if 'results' in data and data['results']:
                if year:
                    for movie in data['results']:
                        if str(movie.get('release_date', '')).startswith(year):
                            description = movie.get('overview', 'Description not available.')
                            poster_path = movie.get('poster_path')
                            poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None
                            print(f"Trovato su TMDB in inglese: {movie['title']} ({year})")
                            return {'description': description, 'poster_url': poster_url}

                movie = data['results'][0]
                description = movie.get('overview', 'Description not available.')
                poster_path = movie.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None
                print(f"Trovato su TMDB in inglese: {movie['title']}")
                return {'description': description, 'poster_url': poster_url}

    except Exception as e:
        print(f"Errore durante la ricerca su TMDB: {e}")
    
    # Se nessuna descrizione è trovata, usa il nome del file
    print(f"Film non trovato su TMDB. Uso il nome del file: {movie_title}")
    return {'description': f"{movie_title}<br>Descrizione non disponibile.", 'poster_url': None}

# Funzione per scaricare il poster da TMDB
def download_poster(poster_url, movie_title):
    if not os.path.exists(POSTER_SAVE_DIR):
        os.makedirs(POSTER_SAVE_DIR)
    
    poster_path = os.path.join(POSTER_SAVE_DIR, f"{movie_title}.jpg")
    try:
        response = requests.get(poster_url)
        with open(poster_path, 'wb') as f:
            f.write(response.content)
        print(f"Poster scaricato correttamente in: {poster_path}")
        return poster_path
    except Exception as e:
        print(f"Errore durante il download del poster: {e}")
        return None

# Funzione per creare un file torrent tramite mktorrent
def create_torrent(directory):
    if not os.path.exists(directory):
        print(f"Errore: La cartella '{directory}' non esiste.")
        return None

    if not os.path.exists(TORRENT_SAVE_DIR):
        os.makedirs(TORRENT_SAVE_DIR)

    torrent_name = os.path.basename(directory)
    torrent_file_path = os.path.join(TORRENT_SAVE_DIR, f"{torrent_name}.torrent")
    print(f"Creazione del torrent in: {torrent_file_path}")

    # Verifica se il file torrent esiste già e lo sovrascrive
    if os.path.exists(torrent_file_path):
        print(f"Il file torrent '{torrent_file_path}' esiste già. Sovrascrivo...")
        os.remove(torrent_file_path)  # Rimuove il file esistente

    try:
        # Usa mktorrent per creare il torrent
        command = [
            'mktorrent',
            '-a', ANNOUNCE_URL,  # URL tracker
            '-o', torrent_file_path,  # Percorso file torrent
            directory  # Directory con i file
        ]
        subprocess.run(command, check=True)
        print(f"Torrent creato correttamente: {torrent_file_path}")
        return torrent_file_path
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la creazione del torrent: {e}")
        return None

# Funzione per estrarre il link del file torrent utilizzando BeautifulSoup
def extract_torrent_link(response_text):
    soup = BeautifulSoup(response_text, 'lxml')

    print("Link trovati nella risposta HTML:")
    for a_tag in soup.find_all('a', href=True):
        print(f"Link trovato: {a_tag['href']}")

    # Cerca un link che contenga ".torrent" o "download.php"
    torrent_link = None
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if ".torrent" in href or "download.php" in href:
            torrent_link = href
            break

    if torrent_link:
        print(f"Trovato link del torrent: {torrent_link}")
        return torrent_link.replace("&amp;", "&")
    else:
        print("Errore: Non sono riuscito a trovare il link del torrent.")
        return None

# Funzione per scaricare il torrent dal sito e avviare il seed
def download_torrent_and_seed(download_link, directory, torrent_name):
    if not download_link:
        print("Errore: Link del torrent non valido.")
        return

    download_url = f"{DOWNLOAD_URL_BASE}{download_link}"
    print(f"Scaricamento del torrent da: {download_url}")

    try:
        response = requests.get(download_url, cookies=cookies_dict, headers=headers, allow_redirects=True)
        print(f"Risposta del server: {response.status_code}")
        if 'application/x-bittorrent' not in response.headers.get('Content-Type', ''):
            print(f"Errore: Il server ha restituito {response.headers.get('Content-Type')} invece di un file torrent.")
            return

        if response.status_code == 200:
            torrent_file_path = os.path.join(TORRENT_SAVE_DIR, f"{torrent_name}.torrent")
            with open(torrent_file_path, 'wb') as torrent_file:
                torrent_file.write(response.content)
            print(f"Torrent scaricato correttamente in: {torrent_file_path}")

            # Aggiungi il torrent a qBittorrent e fai il recheck su /root/test
            torrent_params = {
                'save_path': '/root/test',  # Percorso per il recheck
                'paused': False,
                'auto_managed': False,
                'seed_mode': True,
            }

            with open(torrent_file_path, 'rb') as f:
                client.torrents_add(
                    torrent_files=[f],
                    save_path='/root/test',  # Forza qBittorrent a controllare in /root/test
                    torrent_params=torrent_params,
                    is_paused=False,
                    skip_checking=False  # Disattiva lo skip del recheck automatico
                )
            print(f"Torrent scaricato dal sito aggiunto a qBittorrent per il seed nel percorso: /root/test")

            # Aspetta per assicurarsi che il torrent sia stato aggiunto
            time.sleep(10)

            # Forza il recheck solo per il torrent più recente
            torrents = client.torrents_info()
            torrent_hash = None
            for torrent in torrents:
                if torrent.name == torrent_name and '/root/test' in torrent.save_path:
                    torrent_hash = torrent.hash
                    break

            if torrent_hash:
                print(f"Forzando il primo reannounce e recheck per il torrent {torrent_hash}...")
                client.torrents_reannounce(torrent_hashes=torrent_hash)
                client.torrents_recheck(torrent_hashes=torrent_hash)

                # Attendi 2 minuti e fai un secondo recheck
                time.sleep(120)
                print(f"Secondo recheck dopo 2 minuti per il torrent {torrent_hash}...")
                client.torrents_recheck(torrent_hashes=torrent_hash)
            else:
                print("Errore: Non sono riuscito a trovare l'hash del torrent più recente.")

        else:
            print(f"Errore durante il download del torrent: {response.status_code}")
    except Exception as e:
        print(f"Errore durante il download del torrent: {e}")

# Funzione per caricare i file sul sito e scaricare il torrent generato dal sito
def upload_torrent(directory, category_name):
    with open('categorie_config.json', 'r') as file:
        categories = json.load(file)

    category_id = categories.get(category_name)
    if not category_id:
        print(f"Errore: Categoria '{category_name}' non trovata.")
        return
    
    print(f"Categoria '{category_name}' ha ID '{category_id}'")

    movie_title = os.path.basename(directory)
    tmdb_info = fetch_tmdb_info(movie_title)

    poster_path = None
    if tmdb_info:
        description = tmdb_info['description'] or f"{movie_title}<br>Descrizione non trovata su TMDB."
        poster_url = tmdb_info['poster_url']
        if poster_url:
            poster_path = download_poster(poster_url, movie_title)
    else:
        description = f"{movie_title}<br>Film di genere sconosciuto."

    torrent_file = create_torrent(directory)

    if not torrent_file:
        print("Errore durante la creazione del torrent.")
        return

    files = {'torrent': ('file.torrent', open(torrent_file, 'rb'), 'application/x-bittorrent')}
    if poster_path:
        files['userfile'] = ('poster.jpg', open(poster_path, 'rb'), 'image/jpeg')

    data = {
        'Send': 'Carica',
        'category': category_id,
        'info': description,
        'filename': movie_title,
        'req': 'false',  # Imposta req (richiesta) su false
        'nuk': 'false'   # Imposta nuk (nuked) su false
    }

    try:
        response = requests.post(UPLOAD_URL, files=files, data=data, cookies=cookies_dict)
        print(f"Risposta del server: {response.status_code}")
        if response.status_code == 200:
            print("Upload completato con successo!")
            download_link = extract_torrent_link(response.text)
            # Passa anche 'movie_title' come torrent_name
            download_torrent_and_seed(download_link, directory, movie_title)
        else:
            print(f"Errore durante l'upload: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Errore durante l'upload: {e}")

# Gestione degli argomenti da riga di comando
def main():
    parser = argparse.ArgumentParser(description='Crea e carica un torrent utilizzando qBittorrent e autoupload su sito.')
    parser.add_argument('category', help='Nome della categoria (es: bluray, dvdrip, ecc.)')
    parser.add_argument('directory', help='Il percorso della cartella da trasformare in torrent')

    args = parser.parse_args()

    upload_torrent(args.directory, args.category)

if __name__ == "__main__":
    main()
