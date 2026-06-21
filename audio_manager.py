# audio_manager.py
import pygame
import os
from config import config

class AudioManager:
    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()
        self.volume = config.get("audio", "volume")
        self.set_volume(self.volume)
#        self.is_playing = False
    
    @property
    def is_playing(self):
        """Retourne True si Pygame est en train de jouer un morceau."""
        return pygame.mixer.music.get_busy()
        
    def play_music(self, filepath):
        """Joue un fichier musical"""
        if not os.path.exists(filepath):
            print(f"Fichier non trouvé: {filepath}")
            return False
        
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            #self.is_playing = True
            return True
        except Exception as e:
            print(f"Erreur audio: {e}")
            return False
    
    def stop_music(self):
        """Arrête la musique"""
        pygame.mixer.music.stop()
        #self.is_playing = False
    
    def pause_music(self):
        """Met en pause"""
        pygame.mixer.music.pause()
    
    def unpause_music(self):
        """Reprend la lecture"""
        pygame.mixer.music.unpause()
    
    def set_volume(self, volume):
        """Règle le volume (0.0 à 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def play_alert(self):
        """Joue une alerte"""
        if config.get("audio", "play_on_motion"):
            alert_file = config.get("audio", "motion_sound")
            alert_path = os.path.join("music", alert_file)
            if os.path.exists(alert_path):
                pygame.mixer.Sound(alert_path).play()
                
    # 2. Méthode pour "réinitialiser" le mixer en cas de problème
    def reset_mixer(self):
        """Réinitialise le mixer pour éviter les crashes et saccades"""
        if self.is_playing:
            self.stop_music()
        pygame.mixer.quit()
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()
        self.set_volume(self.volume)
        print("Mixer audio réinitialisé")