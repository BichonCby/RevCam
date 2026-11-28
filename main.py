#!/usr/bin/env python3
# main.py

import sys
import threading
from PyQt5.QtWidgets import QApplication
from camera_manager import CameraManager
from display_manager import DisplayManager
from audio_manager import AudioManager
from playlist_manager import PlaylistManager 

from gui_manager import GUIManager
from gpio_controller import GPIOController  # NOUVEAU

class SurveillanceSystem:
    def __init__(self):
        self.camera_manager = CameraManager(recording_callback=self.on_recording_status, motion_callback = self.on_motion_status)
        if not self.camera_manager.camera_available:
            print("Mode sans camera")
        self.display_manager = DisplayManager()
        self.audio_manager = AudioManager()
        self.playlist_manager = PlaylistManager(self.audio_manager, music_dir="music")
        
        # Initialisation du contrôleur GPIO (après les autres managers)
        self.gpio_controller = GPIOController(
            audio_manager=self.audio_manager,
            camera_manager=self.camera_manager,
            display_manager=self.display_manager,
            playlist_manager=self.playlist_manager,
            led_callback = self.on_led_status
        )
        
        # Threads
        self.camera_thread = None
        self.display_thread = None
        self.gpio_thread = None
        self.app = None
        self.gui = None
    
    def on_recording_status(self, is_recording):
        if is_recording:
            if self.gui:
                self.gui.status_update_signal.emit(
                    "record",
                    "🔴🔴 ENREGISTREMENT 🔴🔴",
                    "color: red; font-weight: bold;"
                )

        else:
            if self.gui:
                self.gui.status_update_signal.emit(
                    "record",
                    "🟢 PAS D ENREGISTREMENT",
                    "color: green;"
                )

    def on_motion_status(self, is_moving):
        if is_moving:
            if self.gui:
                self.gui.status_update_signal.emit(
                    "motion",
                    "🔴🔴 MOUVEMENT DÉTECTÉ 🔴🔴",
                    "color: red; font-weight: bold;"
                )

        else:
            if self.gui:
                self.gui.status_update_signal.emit(
                    "motion",
                    "🟢 AUCUN MOUVEMENT",
                    "color: green;"
                )

    def on_led_status(self,led1,led2):
        #
        if self.gui:
            self.gui.set_led(led1,led2)
            #print(f"led callback appele {led1} {led2}")
    
    def start_background_tasks(self):
        self.camera_thread = threading.Thread(target=self.camera_manager.run, daemon=True)
        self.camera_thread.start()
        
        self.display_thread = threading.Thread(target=self.display_manager.run, daemon=True)
        self.display_thread.start()
        
        self.gpio_thread = threading.Thread(target=self.gpio_controller.run, daemon=True)
        self.gpio_thread.start()
    
    def start_gui(self):
        self.app = QApplication(sys.argv)
        self.gui = GUIManager(self.camera_manager, self.display_manager, self.audio_manager, self.gpio_controller, self.playlist_manager)
        self.app.aboutToQuit.connect(self.stop)
        self.gui.show()
        sys.exit(self.app.exec_())
    
    def stop(self):
        """Arrête tous les services proprement."""
        print("🛑 Arrêt du système...") 
        # 1. Arrêter la playlist en premier (avant la GUI)
        if hasattr(self, 'playlist_manager'):
            self.playlist_manager.stop()
        print("✅ Playlist arrêtée")
        # 2. Arrêter la caméra
        self.camera_manager.stop()
        print("✅ Caméra arrêtée")
    
        # 3. Arrêter l'afficheur
        self.display_manager.stop()
        self.display_thread.join(timeout=2)
        print("✅ Afficheur arrêté")
        
        # 4. Arrêter le GPIO
        if hasattr(self, 'gpio_controller'):
            self.gpio_controller.stop()
            self.gpio_thread.join(timeout=2)
            print("✅ GPIO arrêté")
        
        # 5. Quitter le mixer Pygame proprement
        if hasattr(self.audio_manager, 'cleanup'):
            self.audio_manager.cleanup()
        
        print("✅ Système arrêté proprement")
        
def main():
    system = SurveillanceSystem()
    system.start_background_tasks()
    system.start_gui()

if __name__ == "__main__":
    main()