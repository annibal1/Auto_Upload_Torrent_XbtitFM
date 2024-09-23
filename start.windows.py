import qbittorrentapi
import time
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import argparse
import re
from pathlib import Path
from torrentool.api import Torrent
import json

# Carica variabili d'ambiente dal file epn.env
load_dotenv('epn.env')

# Parametri qBittorrent dal file epn.env
QBITTORRENT_HOST = os.getenv('BITTORRENT_HOST')
QBITTORRENT_PORT = os.getenv('QBIT_PORT')
QBITTORRENT_USER = os.getenv('QBITTORRENT_USER')
QBITTORRENT_PASSWORD = os.getenv('QBITTORRENT_PASSWORD')
QBITTORRENT_URL = f"{QBITTORRENT_HOST}:{QBITTORRENT_PORT}"

# Ottieni i percorsi di salvataggio dal file epn.env
TORRENT_SAVE_DIR = Path(os.getenv('TORRENT_SAVE_DIR'))
POSTER_SAVE_DIR = Path(os.getenv('POSTER_SAVE_DIR'))
TORRENT_DOWNLOAD_DIR = Path(os.getenv('TORRENT_DOWNLOAD_DIR'))

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

# Funzione per verificare e creare directory
def ensure_directory_exists(directory):
    path = Path(directory)
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Directory creata: {path}")
        elif not os.access(path, os.W_OK):
            print(f"Errore: Permessi di scrittura mancanti per la directory {path}")
            return False
        return True
    except Exception as e:
        print(f"Errore durante la gestione della directory {path}: {e}")
        return False

# Verifica le directory configurate
if not ensure_directory_exists(POSTER_SAVE_DIR):
    print("Errore: Directory POSTER_SAVE_DIR non disponibile.")
if not ensure_directory_exists(TORRENT_SAVE_DIR):
    print("Errore: Directory TORRENT_SAVE_DIR non disponibile.")
if not ensure_directory_exists(TORRENT_DOWNLOAD_DIR):
    print("Errore: Directory TORRENT_DOWNLOAD_DIR non disponibile.")

# Connessione a qBittorrent
client = qbittorrentapi.Client(host=QBITTORRENT_URL, username=QBITTORRENT_USER, password=QBITTORRENT_PASSWORD)

try:
    client.auth_log_in()
    print("Connesso a qBittorrent!")
except qbittorrentapi.LoginFailed as e:
    print(f"Errore di login a qBittorrent: {e}")
    exit(1)

# Funzione per pulire il titolo del film o della serie TV, separando il nome dall'anno e riconoscendo le stagioni
def clean_title(file_name):
    # Rimuove codec, risoluzioni, lingue, formati e altre informazioni non rilevanti
    file_name = re.sub(r'\b(1080p|720p|4k|FullHD|x264|x265|AC3|DTS|BluRay|BDRip|WEBRip|WEB-DL|HDRip|HDTV|iTALiAN|ENG|MULTI|HEVC|H\.264|AAC|BDMux|ITA|ENG|SUB|Mux|DVD|MP3|FLAC|DOLBY|ATMOS|HD|NF|DDP5\.1|C0P|DDP|AAC|MKV)\b', '', file_name, flags=re.IGNORECASE)
    file_name = re.sub(r'\(|\)|\d{3,4}p|-\w*| - |_', ' ', file_name)  # Rimuove parentesi, tag, e trattini
    # Separa stagioni ed episodi se presenti (es. S01, 1x08)
    match = re.search(r'(.*?)(S\d+|E\d+|\d+x\d+)', file_name, re.IGNORECASE)
    if match:
        title = match.group(1).strip().replace('.', ' ')
        is_series = True
    else:
        title = re.sub(r'[._]', ' ', file_name).strip()  # Rimuove solo punti e underscore, mantenendo il titolo corretto
        is_series = False
    
    # Rimuove ulteriori dettagli dell'episodio dopo il titolo
    title = re.split(r'[\.\-]\s*', title)[0]  # Spezza il titolo al primo delimitatore comune
    title = re.sub(r'(\d+x\d+|\bE\d+\b|\bS\d+\b).*', '', title).strip()  # Rimuove riferimenti a stagioni o episodi
    title = re.sub(r'\s+', ' ', title).strip()  # Rimuove spazi extra
    return title, is_series

# Funzione per cercare i dettagli su TMDB, distinguendo tra film e serie TV
def fetch_tmdb_info(movie_title):
    title, is_series = clean_title(movie_title)
    print(f"Cercando su TMDB: {title}")

    # Usa endpoint di ricerca per film e serie TV
    if is_series:
        search_url_it = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={title}&language=it-IT"
        search_url_en = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={title}&language=en-US"
    else:
        search_url_it = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&language=it-IT"
        search_url_en = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&language=en-US"

    try:
        # Prova la ricerca in italiano
        response = requests.get(search_url_it)
        data = response.json()

        # Verifica i risultati della ricerca
        if 'results' in data and data['results']:
            for item in data['results']:
                print(f"Trovato su TMDB: {item['name' if is_series else 'title']}")
                description = item.get('overview', 'Descrizione non disponibile.')
                poster_path = item.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None
                return {'description': description, 'poster_url': poster_url}

        # Se non trovato in italiano, prova in inglese
        print("Film o serie TV non trovato in italiano, provo in inglese...")
        response = requests.get(search_url_en)
        data = response.json()

        if 'results' in data and data['results']:
            for item in data['results']:
                print(f"Trovato su TMDB in inglese: {item['name' if is_series else 'title']}")
                description = item.get('overview', 'Description not available.')
                poster_path = item.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else None
                return {'description': description, 'poster_url': poster_url}

    except Exception as e:
        print(f"Errore durante la ricerca su TMDB: {e}")

    print(f"Titolo non trovato su TMDB. Uso il nome del file: {movie_title}")
    return {'description': f"{movie_title}<br>Descrizione non disponibile.", 'poster_url': None}

# Funzione per scaricare il poster da TMDB
def download_poster(poster_url, movie_title):
    if not ensure_directory_exists(POSTER_SAVE_DIR):
        return None

    poster_path = POSTER_SAVE_DIR / f"{movie_title}.jpg"
    try:
        response = requests.get(poster_url)
        with open(poster_path, 'wb') as f:
            f.write(response.content)
        print(f"Poster scaricato correttamente in: {poster_path}")
        return poster_path
    except Exception as e:
        print(f"Errore durante il download del poster: {e}")
        return None
        
# Funzione per creare un file torrent con torrentool
def create_torrent(directory, is_single_file):
    path = Path(directory)
    if not path.exists():
        print(f"Errore: Il percorso '{directory}' non esiste.")
        return None


    # Se il percorso è un file singolo, crea il torrent nella directory impostata in TORRENT_SAVE_DIR
    if is_single_file:
        save_dir = TORRENT_SAVE_DIR
        torrent_name = path.stem  # Usa il nome del file senza estensione
    else:
        # Se è una cartella, salva nel percorso configurato
        save_dir = TORRENT_SAVE_DIR
        torrent_name = path.name  # Usa il nome della cartella

    # Percorso completo del file torrent da creare
    torrent_file_path = save_dir / f"{torrent_name}.torrent"
    print(f"Creazione del torrent in: {torrent_file_path}")

    try:
        # Crea il torrent utilizzando torrentool
        torrent = Torrent.create_from(directory)
        torrent.announce_urls = [[ANNOUNCE_URL]]
        torrent.to_file(str(torrent_file_path))
        print(f"Torrent creato correttamente: {torrent_file_path}")
        return torrent_file_path
    except Exception as e:
        print(f"Errore durante la creazione del torrent con torrentool: {e}")
        return None

# Funzione per aggiungere il torrent a qBittorrent e avviare il seeding
def add_torrent_to_qbittorrent(torrent_file_path, save_path):
    try:
        print(f"Tentativo di aggiungere il torrent: {torrent_file_path} a qBittorrent")

        torrent_params = {
            'save_path': str(save_path),      # Percorso di salvataggio che corrisponde ai file esistenti
            'is_paused': False,               # Aggiungi subito e non in pausa
            'skip_checking': True,            # Salta il controllo dei file, presuppone che siano completi
            'seed_mode': True,                # Avvia direttamente in modalità seed
            'autoTMM': False,                 # Disattiva la gestione automatica dei torrent
        }

        # Aggiunta del torrent a qBittorrent con i parametri definiti
        with open(torrent_file_path, 'rb') as f:
            response = client.torrents_add(torrent_files=[f], **torrent_params)

        if not response:
            print("Errore: Non è stato possibile aggiungere il torrent a qBittorrent.")
        else:
            print(f"Torrent aggiunto correttamente a qBittorrent dalla cartella: {save_path}")

    except Exception as e:
        print(f"Errore durante l'aggiunta del torrent a qBittorrent: {e}")

# Funzione per estrarre il link del torrent dal testo della risposta HTML
def extract_torrent_link(response_text, expected_filename):
    soup = BeautifulSoup(response_text, 'html.parser')
    torrent_link = None
    expected_filename = expected_filename.replace(' ', '+').replace('.', '+').lower()  # Prepara il nome del file

    # Cerca tutti i tag <a> con href e filtra i possibili link torrent
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].lower()
        print(f"Link trovato: {href}")

        # Modifica i controlli per adattarsi meglio ai link torrent
        if 'download.php?id=' in href and (expected_filename in href or '.torrent' in href):
            torrent_link = href
            break

    # Restituisci il link se trovato
    if torrent_link:
        print(f"Trovato link del torrent: {torrent_link}")
        return torrent_link.replace("&amp;", "&")
    else:
        print("Errore: Non sono riuscito a trovare il link del torrent.")
        return None


# Funzione per scaricare il torrent dal sito, avviare il seed e successivamente eliminare il torrent
def download_torrent_and_seed(download_link, torrent_name, save_path, single_file_mode=False):
    if not download_link:
        print("Errore: Link del torrent non valido.")
        return

    # Imposta il percorso di salvataggio in base alla modalità (singolo file o cartella)
    if single_file_mode:
        # Se è un file singolo, salva il torrent nella stessa cartella del file
        save_path = Path(save_path).parent
    else:
        # Se è una cartella, salva il torrent nella cartella superiore (una sola cartella sopra)
        save_path = Path(save_path).parent

    download_url = f"{DOWNLOAD_URL_BASE}{download_link}"
    print(f"Scaricamento del torrent da: {download_url}")

    try:
        response = requests.get(download_url, cookies=cookies_dict, headers=headers, allow_redirects=True)
        print(f"Risposta del server: {response.status_code}")

        if 'application/x-bittorrent' not in response.headers.get('Content-Type', ''):
            print(f"Errore: Il server ha restituito {response.headers.get('Content-Type')} invece di un file torrent.")
            return

        if response.status_code == 200:
            # Salva il file torrent nella cartella appropriata
            torrent_file_path = save_path / f"{Path(torrent_name).stem}.torrent"
            with open(torrent_file_path, 'wb') as torrent_file:
                torrent_file.write(response.content)
            print(f"Torrent scaricato correttamente in: {torrent_file_path}")

            # Aggiungi il torrent scaricato dal sito a qBittorrent
            add_torrent_to_qbittorrent(torrent_file_path, save_path)

            # Attendere alcuni secondi per assicurarsi che qBittorrent elabori correttamente il torrent
            time.sleep(10)

            torrent_hash = None
            attempts = 3  # Numero di tentativi per trovare l'hash del torrent
            for attempt in range(attempts):
                print(f"Tentativo {attempt + 1} di trovare l'hash del torrent...")
                torrents = client.torrents_info()
                for torrent in torrents:
                    if torrent.name.lower() == Path(torrent_name).name.lower():
                        torrent_hash = torrent.hash
                        break
                if torrent_hash:
                    break
                time.sleep(5)  # Attendere un po' prima di ritentare

            if torrent_hash:
                print(f"Forzando il primo reannounce e recheck per il torrent {torrent_hash}...")
                client.torrents_reannounce(torrent_hashes=torrent_hash)
                client.torrents_recheck(torrent_hashes=torrent_hash)

                time.sleep(120)
                print(f"Secondo recheck dopo 2 minuti per il torrent {torrent_hash}...")
                client.torrents_recheck(torrent_hashes=torrent_hash)

                # Attendi ulteriori 30 secondi dopo il secondo recheck per garantire che qBittorrent abbia finito di utilizzare il file
                time.sleep(30)
                print("Attesa di 30 secondi dopo il secondo recheck completata.")

            else:
                print("Errore: Non sono riuscito a trovare l'hash del torrent più recente.")

            # Tentativo di eliminazione del file torrent dopo l'attesa di 30 secondi
            try:
                if torrent_file_path.exists():
                    torrent_file_path.unlink()  # Rimuove il file torrent
                    print(f"File torrent eliminato: {torrent_file_path}")
            except Exception as e:
                print(f"Errore durante l'eliminazione del file torrent: {e}")

        else:
            print(f"Errore durante il download del torrent: {response.status_code}")
    except Exception as e:
        print(f"Errore durante il download del torrent: {e}")


# Funzione per caricare i file sul sito e scaricare il torrent generato dal sito
def upload_torrent(directory, category_name, is_single_file):
    with open('categorie_config.json', 'r') as file:
        categories = json.load(file)

    category_id = categories.get(category_name)
    if not category_id:
        print(f"Errore: Categoria '{category_name}' non trovata.")
        return

    print(f"Categoria '{category_name}' ha ID '{category_id}'")

    movie_title = Path(directory).name
    tmdb_info = fetch_tmdb_info(movie_title)

    poster_path = None
    if tmdb_info:
        description = tmdb_info['description'] or f"{movie_title}<br>Descrizione non trovata su TMDB."
        poster_url = tmdb_info['poster_url']
        if poster_url:
            poster_path = download_poster(poster_url, movie_title)
    else:
        description = f"{movie_title}<br>Film di genere sconosciuto."

    torrent_file = create_torrent(directory, is_single_file)

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
        'req': 'false',
        'nuk': 'false'
    }

    try:
        response = requests.post(UPLOAD_URL, files=files, data=data, cookies=cookies_dict)
        print(f"Risposta del server: {response.status_code}")
        if response.status_code == 200:
            print("Upload completato con successo!")
            download_link = extract_torrent_link(response.text, f"{movie_title}.torrent")
            if download_link:
                download_torrent_and_seed(download_link, movie_title, directory)
        else:
            print(f"Errore durante l'upload: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Errore durante l'upload: {e}")

# Gestione degli argomenti da riga di comando
def main():
    parser = argparse.ArgumentParser(description='Crea e carica un torrent utilizzando torrentool e autoupload su sito.')
    parser.add_argument('category', help='Nome della categoria (es: bluray, dvdrip, ecc.)')
    parser.add_argument('directory', help='Il percorso della cartella o file da trasformare in torrent')
    parser.add_argument('-s', '--single', action='store_true', help='Se specificato, tratta il percorso come un singolo file invece di una cartella')

    args = parser.parse_args()

    upload_torrent(args.directory, args.category, args.single)

if __name__ == "__main__":
    main()
