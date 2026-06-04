# display_manager.py
import time
import threading
from datetime import datetime
import tm1637

class DisplayManager:
    def __init__(self, clk_pin=18, dio_pin=16):
        # GPIO 18 pour CLK, GPIO 16 pour DIO
        self.display = tm1637.TM1637("/dev/gpiochip0", clk=clk_pin, dio=dio_pin)
        self.brightness_val = 5
        self.display.brightness(self.brightness_val)
        self.running = False
        self.mode = 'init'
        self.texte = "8888"
        self.colon = True
        
    def show_time(self):
        """Affiche l'heure courante"""
        now = datetime.now()
        hours = now.hour
        minutes = now.minute
        self.texte = f"{hours:02d}{minutes:02d}"
        self.colon = now.second % 2 == 0
        self.display.numbers(hours, minutes, self.colon)
    
    def set_mode(self,mode):
        self.mode = mode
        
    def set_text(self,text):
        self.texte = text
        self.colon = False
        
        self.show_message(self.texte)
        
    def show_message(self, text, duration=2):
        """Affiche un message temporaire"""
        if len(text) > 4:
            text = text[:4]
        # La bibliothèque gpiod-tm1637 n'a pas de méthode show() directe
        # On affiche temporairement et on revient à l'heure
        #self.clear()
        self.display.show(text)
        #time.sleep(duration)
        #self.show_time()
    
    def get_display(self):
        return self.texte,self.colon
        
    def get_current_display(self):
        """Retourne l'état actuel de l'affichage pour la GUI"""
        # Cette méthode permet à la GUI de connaître l'état
        return {
            'numbers': (self.current_hours, self.current_minutes),
            'colon': self.current_colon,
            'brightness': self.brightness_val
        }
        
    
    def set_brightness(self, brightness):
        """Règle la luminosité (0-7)"""
        self.brightness_val = max(0, min(7, brightness))
        self.display.brightness(self.brightness_val)
    
    def run(self):
        """Boucle principale d'affichage"""
        self.running = True
        last_second = -1
        
        while self.running:
            if self.mode == 0:
                now = datetime.now()
                if now.second != last_second:
                    self.show_time()
                    last_second = now.second
            else:
                self.show_message(self.texte)
            time.sleep(0.1)
    
    def stop(self):
        """Arrête l'affichage"""
        self.running = False
        #self.clear()