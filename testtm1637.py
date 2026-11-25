import threading
import time
import RPi.GPIO as GPIO

from display_manager import DisplayManager
from gpio_controller import GPIOController

# Initialisation de l'afficheur
display = DisplayManager()
display.set_mode(0)

# Initialisation du contrôleur GPIO
# Les autres managers ne sont pas nécessaires pour ce test.
gpio_controller = GPIOController(
    audio_manager=None,
    camera_manager=None,
    display_manager=display,
    playlist_manager=None,
    led_callback=None
)

# Démarrage des deux threads
display_thread = threading.Thread(
    target=display.run,
    daemon=True
)

gpio_thread = threading.Thread(
    target=gpio_controller.run,
    daemon=True
)

display_thread.start()
gpio_thread.start()

print("Test C : TM1637 + GPIOController")
print("Observation pendant 2 minutes...")
print("CTRL+C pour arrêter")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Arrêt du test...")
    display.running = False
    gpio_controller.running = False

    display_thread.join(timeout=2)
    gpio_thread.join(timeout=2)

    GPIO.cleanup()