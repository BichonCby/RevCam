# playlist_manager.py
import os
import json
import glob
import random
from threading import Thread, Event
import time
from audio_manager import AudioManager

class PlaylistManager:
    def __init__(self, audio_manager, music_dir="music"):
        """
        Initialise le gestionnaire de playlist.
        :param audio_manager: Instance de AudioManager pour jouer les sons.
        :param music_dir: Chemin du répertoire contenant les fichiers audio.
        """
        self.audio = audio_manager
        self.music_dir = music_dir
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.stop_event = Event()
        self.current_thread = None
        self.state_file = os.path.join(self.music_dir, "playlist_state.json")
        os.makedirs(self.music_dir, exist_ok=True)

        self._load_playlist()
        self._load_state()

    def _load_playlist(self):
        """Charge la playlist depuis le répertoire (extensions supportées)."""
        extensions = ['*.mp3', '*.wav', '*.ogg', '*.flac']
        self.playlist = []
        for ext in extensions:
            self.playlist.extend(glob.glob(os.path.join(self.music_dir, ext)))
        self.playlist.sort()  # Ordonne par nom de fichier
        print(f"📂 Playlist chargée : {len(self.playlist)} morceaux trouvés.")

    def _load_state(self):
        """Charge l'état (dernier morceau joué)."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    last_file = data.get('last_file')
                    if last_file in self.playlist:
                        self.current_index = self.playlist.index(last_file)
                        print(f"🔁 Reprise du dernier morceau : {os.path.basename(last_file)}")
            except Exception as e:
                print(f"⚠️ Erreur chargement état : {e}")

    def _save_state(self):
        """Sauvegarde le dernier morceau joué."""
        try:
            data = {'last_file': self.playlist[self.current_index] if self.current_index >= 0 else None}
            with open(self.state_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde état : {e}")

    def _play_next(self):
        """Joue le morceau suivant dans la playlist."""
        if not self.playlist:
            print("❌ Playlist vide.")
            self.is_playing = False
            return

        # Passe au morceau suivant (ou revient au début)
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self._play_current()

    def _play_current(self):
        """Joue le morceau courant et planifie le suivant."""
        if not self.playlist or self.current_index < 0 or self.current_index >= len(self.playlist):
            self.is_playing = False
            return

        filepath = self.playlist[self.current_index]
        print(f"🎵 Lecture : {os.path.basename(filepath)}")
        self.audio.play_music(filepath)

        # Sauvegarde l'état pour une reprise ultérieure
        self._save_state()

        # Attend la fin du morceau dans un thread séparé
        def wait_and_play_next():
            # L'événement stop_event permet d'interrompre l'attente
            while self.audio.is_playing and not self.stop_event.wait(0.1):
                pass
            #while self.audio.is_playing and not self.stop_event.is_set():
            #    time.sleep(0.1)

            if self.stop_event.is_set():
                print("⏹️ Lecture interrompue.")
                #self.is_playing = False
                return

            # Si le morceau est terminé et que la lecture est toujours active
            #if self.is_playing:
            print("➡️ Morceau terminé, passage au suivant.")
            self._play_next()

        self.stop_event.clear()
        self.current_thread = Thread(target=wait_and_play_next, daemon=True)
        self.current_thread.start()

    def start(self):
        """Démarre ou reprend la lecture de la playlist."""
        if self.is_playing:
            print("⏸️ Lecture déjà en cours.")
            return

        self._load_playlist()
        if not self.playlist:
            print("❌ Aucun morceau trouvé dans le dossier 'music'.")
            return

        # Si aucun morceau n'est sélectionné, commence par le premier
        if self.current_index < 0:
            self.current_index = 0

        self.is_playing = True
        self.stop_event.clear()
        self._play_current()

    def stop(self):
        """Arrête la lecture et la playlist."""
        if not self.is_playing:
            return

        print("⏹️ Arrêt de la playlist.")
        self.is_playing = False
        self.stop_event.set()
        self.audio.stop_music()

        # Attend que le thread de lecture se termine proprement
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=1.0)

    def skip(self):
        """Passe au morceau suivant (interrompt la lecture en cours)."""
        if not self.is_playing:
            self.start()
            return

        print("⏭️ Passer au morceau suivant.")
        # Interrompt la lecture en cours
        self.audio.stop_music()
        self.stop_event.set()
        self._play_next()
        # Le thread de lecture déclenchera automatiquement le suivant

    def shuffle(self):
        """Mélange la playlist."""
        if not self.playlist:
            return
        random.shuffle(self.playlist)
        self.current_index = 0
        self._save_state()
        print("🔀 Playlist mélangée.")

    def add_music(self, filepath):
        """Ajoute un morceau à la playlist et recharge."""
        if os.path.exists(filepath):
            # Copie le fichier dans le répertoire music
            import shutil
            dest = os.path.join(self.music_dir, os.path.basename(filepath))
            shutil.copy2(filepath, dest)
            self._load_playlist()
            print(f"✅ Fichier ajouté : {os.path.basename(filepath)}")
        else:
            print(f"❌ Fichier introuvable : {filepath}")

    def get_current_music(self):
        """Retourne le nom du morceau en cours (ou None)."""
        if self.current_index >= 0 and self.current_index < len(self.playlist):
            return os.path.basename(self.playlist[self.current_index])
        return None