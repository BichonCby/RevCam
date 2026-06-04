# gpio_controller.py
import threading
import time
import os
import RPi.GPIO as GPIO
from datetime import datetime
from config import config

class GPIOController:
    """Gestion des boutons physiques et LEDs"""
    
    # Pins des boutons (à ajuster selon votre câblage)
    PIN_BTN_VOLUME_UP = 17
    PIN_BTN_VOLUME_DOWN = 27
    PIN_BTN_ALARM_SET = 22
    PIN_BTN_MODE = 23
    
    # Pins des LEDs
    PIN_LED_MUSIC = 24
    PIN_LED_CAMERA = 25
    PIN_LED_PROBLEM = 5
    
    # Modes d'affichage pour le bouton MODE
    MODE_NORMAL = 0
    MODE_ALARM_SET = 1
    MODE_INIT = 2
    MODE_ALARM_ACTIVE = 3
    MODE_ALARM_SET_HOUR = 4
    MODE_ALARM_SET_MINUTE = 5
    MODE_MUSIC = 6
    MODE_VOLUME = 7
    MODE_ALARM_ON_OFF = 8
    
    # constantes pour mettre en corelation l'IHM et le GPIO
    BOUTON_PLUS = 1
    BOUTON_MOINS = 0
    BOUTON_SNOOZE = 2
    BOUTON_MODE =3

    
    def __init__(self, audio_manager, camera_manager, display_manager=None,led_callback=None):
        self.audio_manager = audio_manager
        self.camera_manager = camera_manager
        self.display_manager = display_manager
        self.led_callback = led_callback
        
        self.running = False
        self.current_mode = self.MODE_NORMAL
        self.alarm_hour = config.get("alarm", "hour")
        self.alarm_minute = config.get("alarm", "minute")
        self.alarm_enabled = config.get("alarm", "enabled")
        self.cpt_mode = 50
        self.music_mode = False
        self.disk_full = False
        
        # Callbacks pour l'interface graphique
        self.status_callbacks = []
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Configure les pins GPIO"""
        GPIO.setmode(GPIO.BCM)
        
        # Configuration des boutons (entrées avec pull-up)
        GPIO.setup(self.PIN_BTN_VOLUME_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_BTN_VOLUME_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_BTN_ALARM_SET, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_BTN_MODE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Configuration des LEDs (sorties)
        GPIO.setup(self.PIN_LED_MUSIC, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.PIN_LED_CAMERA, GPIO.OUT, initial=GPIO.HIGH)  # ON par défaut
        GPIO.setup(self.PIN_LED_PROBLEM, GPIO.OUT, initial=GPIO.LOW)
        
        # États initiaux des LEDs
        self.led_music_state = False
        self.led_camera_state = True
        self.led_problem_state = False
        
        # Variables anti-rebond
        self.last_press = {
            self.PIN_BTN_VOLUME_UP: 0,
            self.PIN_BTN_VOLUME_DOWN: 0,
            self.PIN_BTN_ALARM_SET: 0,
            self.PIN_BTN_MODE: 0
        }
        self.debounce_time = 0.3  # 300 ms
    
    def manage_led(self):
        #Pour l'instant une Led pour la musique ON, une autre pour un probleme disk        
        GPIO.output(self.PIN_LED_MUSIC, GPIO.HIGH if self.music_mode else GPIO.LOW)
        GPIO.output(self.PIN_LED_PROBLEM, GPIO.HIGH if self.disk_full else GPIO.LOW)
        if self.led_callback:
            self.led_callback(self.music_mode,self.disk_full)
            #print("envoi callback")
        #else:
            #print("PB")
            
    def set_led_camera(self, state):
        """Allume/éteint la LED caméra"""
        self.led_camera_state = state
        GPIO.output(self.PIN_LED_CAMERA, GPIO.HIGH if state else GPIO.LOW)
    
    def set_led_problem(self, state, auto_clear=True):
        """Allume/éteint la LED problème"""
        self.led_problem_state = state
        GPIO.output(self.PIN_LED_PROBLEM, GPIO.HIGH if state else GPIO.LOW)
        
        # Éteindre automatiquement après 5 secondes si auto_clear
        if state and auto_clear:
            threading.Timer(5.0, lambda: self.set_led_problem(False)).start()
    
    def check_disk_space(self):
        """Vérifie l'espace disque et allume la LED problème si nécessaire"""
        try:
            stat = os.statvfs('/')
            free_space = stat.f_bavail * stat.f_frsize
            free_gb = free_space / (1024**3)
            if free_gb < 500:#0.5:  # Moins de 500MB
                self.disk_full = True
                self.set_led_problem(True)
                if self.display_manager:
                    self.display_manager.show_message("LOW", 2)
                return False
            return True
        except:
            return True
    
    def push_button(self,btn):
        if btn == self.BOUTON_MOINS:
            self._volume_down()
        elif btn == self.BOUTON_PLUS:
            self._volume_up()
        elif btn == self.BOUTON_SNOOZE:
            self._alarm_action()
        elif btn == self.BOUTON_MODE:
            self._mode_switch()
        else:
            print("mauvais bouton")
    
    def _on_button_press(self, pin):
        """Callback appelé quand un bouton est pressé"""
        current_time = time.time()
        
        # Anti-rebond
        if current_time - self.last_press[pin] < self.debounce_time:
            return
        
        self.last_press[pin] = current_time
        
        if pin == self.PIN_BTN_VOLUME_UP:
            self._volume_up()
        elif pin == self.PIN_BTN_VOLUME_DOWN:
            self._volume_down()
        elif pin == self.PIN_BTN_ALARM_SET:
            self._alarm_action()
        elif pin == self.PIN_BTN_MODE:
            self._mode_switch()
    
    def _volume_up(self):#BOUTON_PLUS
        match self.current_mode:
            case self.MODE_NORMAL:
                if self.music_mode:# si la musique est OFF, on ne fait rien
                    
                    """Augmente le volume"""
                    current_volume = self.audio_manager.volume
                    new_volume = min(1.0, current_volume + 0.05)
                    self.audio_manager.set_volume(new_volume)
                    config.set("audio", "volume", new_volume)
        
                    # Feedback visuel : clignotement LED musique
                    #self._blink_led(self.PIN_LED_MUSIC, 0.1)
        
                    # Afficher le volume sur TM1637
                    if self.display_manager:
                        volume_percent = int(new_volume * 100)
                        self.display_manager.set_text(f"u{volume_percent}")
                        self.display_manager.set_mode(3)#??
                        self.display_manager.show_message(f"u{volume_percent}", 1)                    
                    self.cpt_mode = 50
                    print(f"Volume: {int(new_volume * 100)}%")
            case self.MODE_MUSIC:
                self.music_mode = not self.music_mode
                txt = "m On" if self.music_mode else "m OF"
                self.display_manager.set_text(txt)
                self.display_manager.set_mode(3)#??
                #self.display_manager.show_message(txt, 1)                    
                self.cpt_mode = 50
            case self.MODE_ALARM_ON_OFF:
                self.alarm_enabled = not self.alarm_enabled
                txt = f"{self.alarm_hour:02d}{self.alarm_minute:02d}" if self.alarm_enabled else "noAl"
                self.display_manager.set_text(txt)
                self.display_manager.set_mode(3)#??
                self.cpt_mode = 50
            case self.MODE_ALARM_SET_HOUR:
                self.alarm_hour=self.alarm_hour+1
                self.display_manager.set_text(f"{self.alarm_hour:02d}  ")
                self.display_manager.set_mode(3)#??
                self.cpt_mode = 50                
            case self.MODE_ALARM_SET_MINUTE:
                self.alarm_minute=self.alarm_minute+1
                self.display_manager.set_text(f"  {self.alarm_minute:02d}")
                self.display_manager.set_mode(3)#??
                self.cpt_mode = 50                
    def _volume_down(self):#BOUTON_MOINS
        """Diminue le volume"""
        current_volume = self.audio_manager.volume
        new_volume = max(0.0, current_volume - 0.05)
        self.audio_manager.set_volume(new_volume)
        config.set("audio", "volume", new_volume)
        
        # Feedback visuel
        self._blink_led(self.PIN_LED_MUSIC, 0.1)
        
        if self.display_manager:
            volume_percent = int(new_volume * 100)
            self.display_manager.set_text(f"U{volume_percent}")
            self.display_manager.set_mode(3)
            self.display_manager.show_message(f"U{volume_percent}", 1)
            self.display_manager.show_message(f"D{volume_percent}", 1)
        
        print(f"Volume: {int(new_volume * 100)}%")
    
    def _alarm_action(self):#BOUTON_SNOOZE
        """Action selon le mode"""
        self.music_mode = not self.music_mode
        print(f"music mode : {self.music_mode}")
        # if self.current_mode == self.MODE_ALARM_SET:
            #Mode réglage alarme : confirmer l'heure
            # self.alarm_enabled = not self.alarm_enabled
            # config.set("alarm", "enabled", self.alarm_enabled)
            # config.set("alarm", "hour", self.alarm_hour)
            # config.set("alarm", "minute", self.alarm_minute)
            
            # if self.display_manager:
                # if self.alarm_enabled:
                    # self.display_manager.show_message(f"A{self.alarm_hour:02d}{self.alarm_minute:02d}", 2)
                # else:
                    # self.display_manager.show_message("OFF", 1)
            
            # self.current_mode = self.MODE_NORMAL
            
        # else:
            #Mode normal : afficher l'heure de l'alarme
            # if self.display_manager:
                # self.display_manager.show_message(f"{self.alarm_hour:02d}{self.alarm_minute:02d}", 2)
    
    def _mode_switch(self):#BOUTON_MODE
        """Change de mode (normal/réglage alarme)"""
        print ("mode swith")
        match self.current_mode:
            case self.MODE_NORMAL:
                self.current_mode = self.MODE_ALARM_ON_OFF
                txt = f"{self.alarm_hour:02d}{self.alarm_minute:02d}" if self.alarm_enabled else "noAl"
                self.display_manager.set_text(txt)
                self.display_manager.set_mode(3)#??
                self.cpt_mode = 40
            case self.MODE_ALARM_ON_OFF:
                self.current_mode = self.MODE_ALARM_SET_HOUR
                txt = f"{self.alarm_hour:02d}  "
                self.display_manager.set_text(txt)
                self.display_manager.set_mode(3)#??
                self.cpt_mode = 40
            case self.MODE_ALARM_SET_HOUR:
                self.current_mode = self.MODE_ALARM_SET_MINUTE
                txt = f"  {self.alarm_minute:02d}"
                self.display_manager.set_text(txt)
                self.display_manager.set_mode(3)#??
                self.cpt_mode = 40
            case self.MODE_ALARM_SET_MINUTE:
                self.current_mode = self.MODE_NORMAL
                self.cpt_mode = 1
        # if self.current_mode == self.MODE_NORMAL:
            # self.current_mode = self.MODE_ALARM_SET
            # if self.display_manager:
                # self.display_manager.show_message("SET", 1)
        # else:
            # self.current_mode = self.MODE_NORMAL
    
    def _blink_led(self, pin, duration=0.2):
        """Fait clignoter une LED"""
        def blink():
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(pin, GPIO.LOW)
        
        threading.Thread(target=blink, daemon=True).start()
    
    def set_alarm_time(self, hour, minute):
        """Définit l'heure du réveil"""
        self.alarm_hour = max(0, min(23, hour))
        self.alarm_minute = max(0, min(59, minute))
        config.set("alarm", "hour", self.alarm_hour)
        config.set("alarm", "minute", self.alarm_minute)
    
    def check_alarm(self):
        """Vérifie si l'alarme doit sonner"""
        if not self.alarm_enabled:
            return False
        
        now = datetime.now()
        if now.hour == self.alarm_hour and now.minute == self.alarm_minute:
            if now.second == 0:  # Une seule fois par minute
                self._trigger_alarm()
                return True
        return False
    
    def _trigger_alarm(self):
        """Déclenche l'alarme"""
        print("⏰ ALARME !")
        self.set_led_problem(True, auto_clear=False)
        
        # Jouer un son d'alarme
        alarm_sound = os.path.join("music", "alarm.mp3")
        if os.path.exists(alarm_sound):
            self.audio_manager.play_music(alarm_sound)
        
        # Afficher sur TM1637
        if self.display_manager:
            self.display_manager.show_message("ALRM", 3)
    
    def run(self):
        """Boucle principale pour la surveillance des boutons"""
        self.running = True
        
        # Ajouter les détections de bord
        GPIO.add_event_detect(self.PIN_BTN_VOLUME_UP, GPIO.FALLING, 
                              callback=self._on_button_press, bouncetime=300)
        GPIO.add_event_detect(self.PIN_BTN_VOLUME_DOWN, GPIO.FALLING, 
                              callback=self._on_button_press, bouncetime=300)
        GPIO.add_event_detect(self.PIN_BTN_ALARM_SET, GPIO.FALLING, 
                              callback=self._on_button_press, bouncetime=300)
        GPIO.add_event_detect(self.PIN_BTN_MODE, GPIO.FALLING, 
                              callback=self._on_button_press, bouncetime=300)
        
        # Boucle pour les vérifications périodiques
        last_alarm_check = 0
        last_disk_check = 0
        
        while self.running:
            #gestion du compteur de modes
            if self.cpt_mode == 1:
                self.current_mode = self.MODE_NORMAL
                self.display_manager.set_mode(self.current_mode) #on envoi le mode NORMAL au display apres la tempo
                print("mode normal")
            self.cpt_mode = max(0,self.cpt_mode-1)
            
            current_time = time.time()
            
            # Vérifier l'alarme toutes les secondes
            if current_time - last_alarm_check >= 1:
                self.check_alarm()
                last_alarm_check = current_time
            
            # Vérifier l'espace disque toutes les 30 secondes
            if current_time - last_disk_check >= 30:
                self.check_disk_space()
                last_disk_check = current_time
            
            # Gestion des Led
            self.manage_led()
            time.sleep(0.1)
    
    def stop(self):
        """Nettoie les GPIO"""
        self.running = False
        GPIO.cleanup([self.PIN_BTN_VOLUME_UP, self.PIN_BTN_VOLUME_DOWN,
                      self.PIN_BTN_ALARM_SET, self.PIN_BTN_MODE,
                      self.PIN_LED_MUSIC, self.PIN_LED_CAMERA, self.PIN_LED_PROBLEM])