#!/usr/bin/env python3
# main.py

import sys
import threading
from PyQt5.QtWidgets import QApplication
from camera_manager import CameraManager
from display_manager import DisplayManager
from audio_manager import AudioManager
from gui_manager import GUIManager
from gpio_controller import GPIOController  # NOUVEAU

class SurveillanceSystem:
    def __init__(self):
        self.camera_manager = CameraManager(recording_callback=self.on_recording_status)
        self.display_manager = DisplayManager()
        self.audio_manager = AudioManager()
        
        # Initialisation du contrôleur GPIO (après les autres managers)
        self.gpio_controller = GPIOController(
            audio_manager=self.audio_manager,
            camera_manager=self.camera_manager,
            display_manager=self.display_manager,
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
            #self.display_manager.show_message("REC", 1)
            if self.gui:
                self.gui.motion_status.setText("🔴🔴 MOUVEMENT DÉTECTÉ 🔴🔴")
                self.gui.motion_status.setStyleSheet("color: red; font-weight: bold;")
            # Clignotement LED caméra pendant l'enregistrement
            if self.gpio_controller:
                self.gpio_controller._blink_led(self.gpio_controller.PIN_LED_CAMERA, 0.5)

        else:
            print("recording status false")
            if self.gui:
                print("recording status false 2")
                self.gui.motion_status.setText("🟢 Aucun mouvement")
                print("recording status false 3")
                self.gui.motion_status.setStyleSheet("color: green;")
                print("recording status false 4")
            # Rallumer LED caméra fixe
            if self.gpio_controller:
                self.gpio_controller.set_led_camera(True)
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
        self.gui = GUIManager(self.camera_manager, self.display_manager, self.audio_manager, self.gpio_controller)
        self.gui.show()
        sys.exit(self.app.exec_())
    
    def stop(self):
        print("stop surveillance systeme")
        self.camera_manager.stop()
        self.display_manager.stop()
        self.gpio_controller.stop()
        
def main():
    system = SurveillanceSystem()
    system.start_background_tasks()
    system.start_gui()

if __name__ == "__main__":
    main()