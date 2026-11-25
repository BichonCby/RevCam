# gpio_controller.py
import threading
import time
import os
import RPi.GPIO as GPIO
from datetime import datetime
from config import config

class GPIOController:
    """Gestion des boutons physiques et LEDs"""
    
    # # Pins des boutons (à ajuster selon votre câblage)
    # PIN_BTN_VOLUME_UP = 7
    # PIN_BTN_VOLUME_DOWN = 1
    # PIN_BTN_ALARM_SET = 8
    # PIN_BTN_MODE = 25
    
    # # Pins des LEDs
    # PIN_LED_MUSIC = 16
    # PIN_LED_PROBLEM = 20
    
    # Modes d'affichage pour le bouton MODE
    MODE_AFF_NORMAL = 0
    MODE_AFF_ALARM_SET = 1
    MODE_AFF_INIT = 2 #?
    MODE_AFF_ALARM_ACTIVE = 3 #?
    MODE_AFF_ALARM_SET_HOUR = 4
    MODE_AFF_ALARM_SET_MINUTE = 5
    MODE_AFF_MUSIC = 6
    MODE_AFF_VOLUME = 7
    MODE_AFF_ALARM_ON_OFF = 8
    
    # constantes pour mettre en corelation l'IHM et le GPIO
    BOUTON_PLUS = 1
    BOUTON_MOINS = 0
    BOUTON_SNOOZE = 2
    BOUTON_MODE = 3
    BOUTON_LOVE = 4

    
    def __init__(self, audio_manager, camera_manager, display_manager=None,playlist_manager=None,led_callback=None):
        self.audio_manager = audio_manager
        self.camera_manager = camera_manager
        self.display_manager = display_manager
        self.playlist_manager = playlist_manager
        self.led_callback = led_callback
        
        self.pin_btn_volume_up = config.get("GPIO", "PIN_BTN_VOLUME_UP")
        self.pin_btn_volume_down = config.get("GPIO", "PIN_BTN_VOLUME_DOWN")
        self.pin_btn_alarm_set = config.get("GPIO", "PIN_BTN_ALARM_SET")
        self.pin_btn_mode = config.get("GPIO", "PIN_BTN_MODE")
        self.pin_btn_love = config.get("GPIO", "PIN_BTN_LOVE")
        self.pin_led_music = config.get("GPIO", "PIN_LED_MUSIC")
        self.pin_led_problem = config.get("GPIO", "PIN_LED_PROBLEM")
        #etat synthetise des bouton IHM et GPIO
        self.bplus = False
        self.bmoins = False
        self.bsnooze = False
        self.bmode = False
        self.blove = False

        self.pushed_IHM ={
            self.pin_btn_volume_up : False,
            self.pin_btn_volume_down : False,
            self.pin_btn_alarm_set : False,
            self.pin_btn_mode : False,
            self.pin_btn_love : False
            }
        self.pushed_cpt ={
            self.pin_btn_volume_up : 0,
            self.pin_btn_volume_down : 0,
            self.pin_btn_alarm_set : 0,
            self.pin_btn_mode : 0,
            self.pin_btn_love : 0
            }
        self.pushed_GPIO ={
            self.pin_btn_volume_up : False,
            self.pin_btn_volume_down : False,
            self.pin_btn_alarm_set : False,
            self.pin_btn_mode : False,
            self.pin_btn_love : False
            }
        self.running = False
        self.current_mode = self.MODE_AFF_INIT
        self.alarm_hour = config.get("alarm", "hour")
        self.alarm_minute = config.get("alarm", "minute")
        self.alarm_enabled = config.get("alarm", "enabled")
        self.cpt_mode = 50
        self.music_mode = False
        self.disk_full = False
        self.cpt_run = 0
        
        # Callbacks pour l'interface graphique
        self.status_callbacks = []
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Configure les pins GPIO"""
        GPIO.setmode(GPIO.BCM)
        
        # Configuration des boutons (entrées avec pull-up)
        GPIO.setup(self.pin_btn_volume_up, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_btn_volume_down, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_btn_alarm_set, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_btn_mode, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_btn_love, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Configuration des LEDs (sorties)
        GPIO.setup(self.pin_led_music, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.pin_led_problem, GPIO.OUT, initial=GPIO.LOW)
        
        # États initiaux des LEDs
        self.led_music_state = False
        self.led_camera_state = True
        self.led_problem_state = False
        
        # Variables anti-rebond
        self.last_press = {
            self.pin_btn_volume_up: 0,
            self.pin_btn_volume_down: 0,
            self.pin_btn_alarm_set: 0,
            self.pin_btn_mode: 0,
            self.pin_btn_love: 0
        }
        self.debounce_time = 0.3  # 300 ms
    
    def manage_led(self):
        #Pour l'instant une Led pour la musique ON, une autre pour un probleme disk        
        GPIO.output(self.pin_led_music, GPIO.HIGH if self.music_mode else GPIO.LOW)
        GPIO.output(self.pin_led_problem, GPIO.HIGH if self.disk_full else GPIO.LOW)
        if self.led_callback:
            self.led_callback(self.music_mode,self.disk_full)
            #print("envoi callback")
        #else:
            #print("PB")
            
    def set_led_camera(self, state):
        """Allume/éteint la LED caméra"""
        self.led_camera_state = state
    
    def set_led_problem(self, state, auto_clear=True):
        """Allume/éteint la LED problème"""
        self.led_problem_state = state
        GPIO.output(self.pin_led_problem, GPIO.HIGH if state else GPIO.LOW)
        
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
                    pass
                    #self.display_manager.show_message("LOW", 2)
                return False
            return True
        except:
            return True
            
    def write_love(self):
        timestamp = datetime.now().strftime("%Y %m %d %H:%M:%S")
        print(f"ecriture de l'instant {timestamp}")
        love_file = "recordings/lovetime.txt"
        with open(love_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp}\n")
        self.blove = False
    
    def push_button(self,btn,state):
        """Callback appelé quand un bouton est pressé depuis l'IHM"""
        self.pushed_IHM[btn]=state
        #print(f"bouton {btn} a l'etat {self.pushed_IHM[btn]}")
        self.synthese_button()
    
    def _on_button_event(self, pin):
        """Callback appelé quand un bouton physique est pressé ou relaché"""
        current_time = time.time()
        
        # Anti-rebond
        if current_time - self.last_press[pin] < self.debounce_time:
            return
        
        self.last_press[pin] = current_time
        #self.pushed_cpt = max(self.pushed_cpt,3)
        self.pushed_GPIO[pin]= GPIO.input(pin) == GPIO.LOW
        #print(f"bouton {pin} a l'etat {self.pushed_GPIO[pin]}")
        self.synthese_button()
            
    def synthese_button(self):
        """fonction de synthese des boutons IHM et GPIO pour simplifier l'ecriture dans la state machine"""
        self.bplus = self.pushed_GPIO[self.pin_btn_volume_up] or self.pushed_IHM[self.pin_btn_volume_up]
        self.bmoins = self.pushed_GPIO[self.pin_btn_volume_down] or self.pushed_IHM[self.pin_btn_volume_down]
        self.bsnooze = self.pushed_GPIO[self.pin_btn_alarm_set] or self.pushed_IHM[self.pin_btn_alarm_set]
        self.bmode = self.pushed_GPIO[self.pin_btn_mode] or self.pushed_IHM[self.pin_btn_mode]
        if self.pushed_GPIO[self.pin_btn_love] or self.pushed_IHM[self.pin_btn_love]:
            self.blove = True #trigger reinitialise apres l'ecriture
    
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
        self.set_led_camera(True)
        
        # Jouer un son d'alarme
        alarm_sound = os.path.join("music", "alarm.mp3")
        if os.path.exists(alarm_sound):
            self.audio_manager.play_music(alarm_sound)
        # lancer la playlist_manager
        self.music_mode = True
        self.playlist_manager.start()
        #affichage et changement de mode
        self.current_mode = self.MODE_AFF_ALARM_ACTIVE
        self.display_manager.set_text("bEEP")
        self.display_manager.set_mode(3)#??
        self.cpt_mode = 50
        # Afficher sur TM1637
        if self.display_manager:
            self.display_manager.show_message("ALRM", 3)
    
    def state_machine_mode(self):
        #print(f"appel machine etats {self.current_mode} et cpt {self.cpt_mode}")
        match self.current_mode:
            case self.MODE_AFF_INIT: #on ne fait rien, on attend la tempo
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode) #on envoi le mode NORMAL au display apres la tempo
                    print("mode normal sm")
            case self.MODE_AFF_NORMAL: #affichage de l'heure, le cas courant
                if self.bmode:
                    print("passage mode alarme ON/OFF")
                    self.current_mode = self.MODE_AFF_ALARM_ON_OFF
                    txt = f"{self.alarm_hour:02d}{self.alarm_minute:02d}" if self.alarm_enabled else "noAl"
                    self.display_manager.set_text(txt)
                    self.display_manager.set_mode(3)#??
                    self.cpt_mode = 40

                if self.music_mode and (self.bplus or self.bmoins):
                    #print("appui sur le bouton plus")
                    self.cpt_mode = 30
                    self.display_manager.set_text(f"u{self.audio_manager.volume}")
                    self.display_manager.set_mode(3)#??
                    self.current_mode = self.MODE_AFF_VOLUME
                if self.bsnooze:
                    self.music_mode = not self.music_mode
                    if self.music_mode:
                        self.playlist_manager.start()
                    else:
                        self.playlist_manager.stop()
                    txt = f"PLAY" if self.music_mode else "OFF"
                    self.display_manager.set_text(txt)
                    self.display_manager.set_mode(3)
                    self.current_mode = self.MODE_AFF_MUSIC
                    self.cpt_mode = 40
                    #print("appui sur le bouton snooze")
                
            case self.MODE_AFF_ALARM_SET:
                pass
            case self.MODE_AFF_ALARM_ACTIVE:
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode) #on envoi le mode NORMAL au display apres la tempo
                if self.bmode or self.bplus or self.bmoins or self.bsnooze:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode) 
                    self.music_mode = False
                    self.playlist_manager.stop()
            case self.MODE_AFF_ALARM_SET_HOUR:
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode)
                elif self.cpt_mode < 35:
                    if self.bplus or self.bmoins:
                        print("changement heure")
                        if self.bplus:
                            self.alarm_hour=self.alarm_hour+1 if self.alarm_hour <23 else 0
                        if self.bmoins:
                            self.alarm_hour=self.alarm_hour-1 if self.alarm_hour >0 else 23
                        self.display_manager.set_text(f"{self.alarm_hour:02d}  ")
                        self.display_manager.set_mode(3)#??
                        config.set("alarm","hour",self.alarm_hour)
                        self.cpt_mode = 40
                    if self.bmode:#on va vers les minutes
                        self.current_mode = self.MODE_AFF_ALARM_SET_MINUTE
                        print("passage au reglage minutes")
                        txt = f"  {self.alarm_minute:02d}"
                        self.display_manager.set_text(txt)
                        self.display_manager.set_mode(3)#??
                        self.cpt_mode = 40

            case self.MODE_AFF_ALARM_SET_MINUTE:
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode)
                elif self.cpt_mode < 35:
                    if self.bplus or self.bmoins:
                        if self.bplus:
                            self.alarm_minute=self.alarm_minute+1 if self.alarm_minute <59 else 0
                        if self.bmoins:
                            self.alarm_minute=self.alarm_minute-1 if self.alarm_minute >0 else 59
                        self.display_manager.set_text(f"  {self.alarm_minute:02d}")
                        self.display_manager.set_mode(3)#??
                        config.set("alarm","minute",self.alarm_minute)
                        self.cpt_mode = 40
                    if self.bmode:#on va vers heure/minute alarme
                        self.current_mode = self.MODE_AFF_ALARM_ON_OFF
                        txt = f"{self.alarm_hour:02d}{self.alarm_minute:02d}" if self.alarm_enabled else "noAl"
                        self.display_manager.set_text(txt)
                        self.display_manager.set_mode(3)#??
                        self.cpt_mode = 40

            case self.MODE_AFF_MUSIC:
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode)
                if self.cpt_mode <30:
                    if self.bsnooze:
                        self.music_mode = not self.music_mode
                        if self.music_mode:
                            self.playlist_manager.start()
                        else:
                            self.playlist_manager.stop()
                        txt = f"PLAY" if self.music_mode else "OFF"
                        self.display_manager.set_text(txt)
                        self.display_manager.set_mode(3)
                        self.cpt_mode = 40
                if self.music_mode and (self.bplus or self.bmoins):
                    #print("appui sur le bouton plus")
                    self.cpt_mode = 30
                    self.display_manager.set_text(f"u{self.audio_manager.volume}")
                    self.display_manager.set_mode(3)#??
                    self.current_mode = self.MODE_AFF_VOLUME
                        
            case self.MODE_AFF_VOLUME:
                if self.bplus or self.bmoins:
                    self.cpt_mode = 30 # on reinitialise
                    current_volume = self.audio_manager.volume
                    if self.bplus:
                        new_volume = min(1.0, current_volume + 0.05)
                    else:
                        new_volume = min(1.0, current_volume - 0.05)
                    self.audio_manager.set_volume(new_volume)
                    config.set("audio", "volume", new_volume)
                    if self.display_manager:
                        volume_percent = int(new_volume * 100)
                        self.display_manager.set_text(f"u{volume_percent}")
                        self.display_manager.set_mode(3)#??
                        self.display_manager.show_message(f"u{volume_percent}", 1)                    
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode)
                    
            case self.MODE_AFF_ALARM_ON_OFF:
                if self.cpt_mode == 0:
                    self.current_mode = self.MODE_AFF_NORMAL
                    self.display_manager.set_mode(self.current_mode)
                    
                elif self.cpt_mode <30: #on attend 1s pour eviter de basculer trop vite
                    if self.bmode and self.alarm_enabled: #on ne regle pas l'alarme si elle est desactivee
                        print("on passe en modif heure")
                        self.current_mode = self.MODE_AFF_ALARM_SET_HOUR
                        txt = f"{self.alarm_hour:02d}  "
                        self.display_manager.set_text(txt)
                        self.display_manager.set_mode(3)#??
                        self.cpt_mode = 40
                    if self.bplus or self.bmoins: #on bascule ON/OFF
                        self.alarm_enabled = not self.alarm_enabled
                        txt = f"{self.alarm_hour:02d}{self.alarm_minute:02d}" if self.alarm_enabled else "noAl"
                        print(f"mode alarme {self.alarm_enabled}")
                        self.display_manager.set_text(txt)
                        self.display_manager.set_mode(3)#??
                        config.set("alarm","enabled",self.alarm_enabled)
                        self.cpt_mode = 40


        # decrement du timeout
        self.cpt_mode = max(0,self.cpt_mode-1)

    def run(self):
        """Boucle principale pour la surveillance des boutons"""
        self.running = True
        
        # Ajouter les détections de bord
        GPIO.add_event_detect(self.pin_btn_volume_up, GPIO.BOTH, 
                              callback=self._on_button_event, bouncetime=300)
        GPIO.add_event_detect(self.pin_btn_volume_down, GPIO.BOTH, 
                              callback=self._on_button_event, bouncetime=300)
        GPIO.add_event_detect(self.pin_btn_alarm_set, GPIO.BOTH, 
                              callback=self._on_button_event, bouncetime=300)
        GPIO.add_event_detect(self.pin_btn_mode, GPIO.BOTH, 
                              callback=self._on_button_event, bouncetime=300)
        GPIO.add_event_detect(self.pin_btn_love, GPIO.BOTH, 
                              callback=self._on_button_event, bouncetime=300)
        
        # Boucle pour les vérifications périodiques
        last_alarm_check = 0
        last_disk_check = 0
        last_write_love = 0
        
        while self.running:
            #on fait une boucle de 10ms pour quand un des boutons a ete appuye
            if any(self.pushed_GPIO) or any(self.pushed_IHM):#si on a un bouton qui a ete pousse
                pass
            #puis une fois sur 10 on lance la machine d'etat
            if self.cpt_run == 0:
                self.cpt_run = 10
                # appel de la machine d'etat globale
                self.state_machine_mode()
                
                current_time = time.time()
                
                # Vérifier l'alarme toutes les secondes
                if current_time - last_alarm_check >= 1:
                    self.check_alarm()
                    last_alarm_check = current_time
                    
                # Check de l'ecriture de l'instant toutes les x secondes
                if current_time - last_write_love >= 10:
                    if self.blove:
                        self.write_love()
                    last_write_love = current_time
                
                # Vérifier l'espace disque toutes les 30 secondes
                if current_time - last_disk_check >= 30:
                    self.check_disk_space()
                    last_disk_check = current_time
                
                # Gestion des Led
                self.manage_led()
            self.cpt_run = self.cpt_run-1
            time.sleep(0.01)#on change 
    
    def stop(self):
        """Nettoie les GPIO"""
        self.running = False
        GPIO.cleanup([self.pin_btn_mode, self.pin_btn_alarm_set,
                      self.pin_btn_volume_down, self.pin_btn_volume_up,
                      self.pin_btn_love,
                      self.PIN_LED_MUSIC, self.PIN_LED_PROBLEM])
