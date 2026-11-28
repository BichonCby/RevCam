# config.py
import json
import os

class Config:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.save_needed = False
        self.default_config = {
            "camera": {
                #"brightness": 0.5,
                #"contrast": 1.0,
                #"saturation": 1.0,
                #"sharpness": 1.0,
                #"exposure_speed": 30000,
                #"iso": 200,
                "active":True,
                "resolution":2,#(480,640)(800,600)
                "width":800,
                "height":600
                
            },
            "motion": {
                "threshold": 20,
                "min_area": 50,
                "blur_size": 5
               # "record_duration": 5
            },
            "record": {
                "start_threshold": 10,
                "max_counter": 100,
                "stop_threshold": 6
            },
                
            "display": {
                "brightness_tm1637": 5,
                "auto_off_hours": [23, 6]
            },
            "audio": {
                "volume": 0.7,
                "play_on_motion": False,
                "motion_sound": "alert.mp3"
            },
            "alarm": {
                "hour": 7,
                "minute": 0,
                "enabled": False
            },
            "GPIO": {
                "PIN_BTN_VOLUME_UP":7,
                "PIN_BTN_VOLUME_DOWN": 1,
                "PIN_BTN_ALARM_SET": 8,
                "PIN_BTN_MODE": 25,
                "PIN_BTN_LOVE": 12,
                "PIN_LED_GREEN" :16,
                "PIN_LED_RED": 20
            }

        }
        self.load()
        
    def _merge_config(self, default, saved):
        for key, value in saved.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(default[key], value)
            else:
                default[key] = value
                
    def load(self):
        self.config = self.default_config
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
#                self.default_config.update(saved_config)
            self._merge_config(self.config, saved_config)
#        self.config = self.default_config
    
    def save(self): #le compteur dans GPIO va appeler toutes les 30s cette methode
        if self.save_needed:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.save_needed = False
            print("ecriture de la config")
    
    def get(self, category, key=None):
        if key:
            return self.config.get(category, {}).get(key)
        return self.config.get(category, {})
    
    def set(self, category, key, value):
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = value
        self.save_needed = True
        #self.save() 

config = Config()
