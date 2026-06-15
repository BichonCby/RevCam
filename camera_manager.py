# camera_manager.py - Version avec réinitialisation complète

import threading
import time
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FileOutput
from libcamera import controls
from picamera2.outputs import FfmpegOutput

import cv2
from datetime import datetime
import os
from config import config

class CameraManager:
    def __init__(self, recording_callback=None, motion_callback=None):
        self.camera = None
        self.running = False
        self.recording = False
        self.encoder = None
        self.recording_filepath = None
        self.camera_lock = threading.Lock()  # Verrou pour les accès caméra
        self.luminosity = 50.0
#        self.cpt_lum = 0
        
        # Paramètres de détection
        self.motion_threshold = config.get("motion", "threshold")
        self.min_motion_area = config.get("motion", "min_area")
        self.blur_size = config.get("motion", "blur_size")
        
        
        # Paramètres du compteur
        self.motion_counter = 0
        self.start_threshold = config.get("record", "start_threshold")#10
        self.stop_threshold = config.get("record", "stop_threshold")#2
        self.max_counter = config.get("record", "max_counter")#500
        
        self.previous_frame = None
        self.recording_callback = recording_callback
        self.motion_callback = motion_callback
        
        self.current_frame_raw = None
        self.current_frame_bw = None
        self.current_frame_motion = None
        self.current_frame_detection = None
        
        self.init_camera()
    
    def init_camera(self):
        """Initialise la caméra"""
        with self.camera_lock:
            if self.camera is not None:
                try:
                    self.camera.stop()
                    self.camera.close()
                except:
                    pass
            
            self.camera = Picamera2()
            
            camera_config = self.camera.create_video_configuration(
                main={"format": "RGB888", "size": (800,600)},
                raw={"size": (3280, 2464)},  # Force le mode plein capteur (2x2 binning)
                controls={
                    "AeEnable": True,
                    "AwbEnable": True,
                    "AeExposureMode": controls.AeExposureModeEnum.Normal,  # Changera selon lumière
                    "AeMeteringMode": controls.AeMeteringModeEnum.Matrix,   # Mesure globale
                    "FrameDurationLimits": (100000, 100000)  # 10 fps
                    # "Brightness": config.get("camera", "brightness"),
                    # "Contrast": config.get("camera", "contrast"),
                    # "Saturation": config.get("camera", "saturation"),
                    # "Sharpness": config.get("camera", "sharpness"),
                    # "ExposureTime": config.get("camera", "exposure_speed"),
                    # "AnalogueGain": config.get("camera", "iso") / 100
                }
            )
            self.camera.configure(camera_config)
            self.camera.start()
            time.sleep(2)
            
            self.encoder = H264Encoder(repeat=True, iperiod=60)
            self.quality = Quality.LOW
    
    def full_camera_reset(self):
        """Réinitialisation complète de la caméra - solution au blocage"""
        print("🔄 Réinitialisation complète de la caméra...")
        with self.camera_lock:
            try:
                if self.recording:
                    try:
                        self.camera.stop_recording()
                    except:
                        pass
                    self.recording = False
                
                self.camera.stop()
                self.camera.close()
            except Exception as e:
                print(f"Erreur lors de l'arrêt: {e}")
            
            time.sleep(0.5)
            
            # Recréer la caméra
            self.camera = Picamera2()
            camera_config = self.camera.create_video_configuration(
                main={"format": "RGB888", "size": (800,600)},
                raw={"size": (3280, 2464)},  # Force le mode plein capteur (2x2 binning)
                controls={
                    "AeEnable": True,
                    "AwbEnable": True,
                    "AeExposureMode": controls.AeExposureModeEnum.Normal,  # Changera selon lumière
                    "AeMeteringMode": controls.AeMeteringModeEnum.Matrix,   # Mesure globale
                    "FrameDurationLimits": (100000, 100000)  # 10 fps
                    # "Brightness": config.get("camera", "brightness"),
                    # "Contrast": config.get("camera", "contrast"),
                    # "Saturation": config.get("camera", "saturation"),
                    # "Sharpness": config.get("camera", "sharpness"),
                    # "ExposureTime": config.get("camera", "exposure_speed"),
                    # "AnalogueGain": config.get("camera", "iso") / 100
                }
            )
            self.camera.configure(camera_config)
            self.camera.start()
            time.sleep(1)
            
            self.encoder = H264Encoder(bitrate=10000000, repeat=True)
            print("✅ Caméra réinitialisée")
            
    # def determine_luminosite(self):
        # if self.cpt_lum >=9:
            # try :
                # with self.camera.capture_request() as request:
                    #on utilise les meta donnes de la camera pour bypasser le mode auto
                    # metadata = request.get_metadata()
                    # exposure_time = metadata.get("ExposureTime", 0) #microsecond
                    # analogue_gain = metadata.get("AnalogueGain", 0)
                    #La valeur de luminosité brute
                    # self.luminosity = int(float(exposure_time) * analogue_gain)
                    # print(f"exposure time :{exposure_time}, analogue gain : {analogue_gain}, luminosite : {self.luminosity}")
            # except Exception as e:
                # print(f"Erreur récupération métadonnées: {e}")
            
            # self.cpt_lum = 0
        # self.cpt_lum = self.cpt_lum+1
    
    def update_camera_params(self):
        """Met à jour les paramètres de la caméra"""
        return # on supprime cette fonctionnalite pour passer en automatique
        if self.camera:
            try:
                self.camera.set_controls({
                    "Brightness": config.get("camera", "brightness"),
                    "Contrast": config.get("camera", "contrast"),
                    "Saturation": config.get("camera", "saturation"),
                    "Sharpness": config.get("camera", "sharpness"),
                    "ExposureTime": config.get("camera", "exposure_speed"),
                    "AnalogueGain": config.get("camera", "iso") / 100
                })
            except:
                pass
    
    def detect_motion(self, frame):
        """Détecte le mouvement"""
        # passage en niveau de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # calcul de la luminosite moyenne
        self.luminosity = int(np.mean(gray))
        
        # application du flou
        blur = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        # pas de detection sur la premiere image
        if self.previous_frame is None:
            self.previous_frame = blur
            return False, None
        
        # on fait la difference entre deux images grises successives
        diff = cv2.absdiff(self.previous_frame, blur)
        
        #tout ce qui a bouge sera blanc, le reste noir
        _, thresh = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
        
        is_detected = (cv2.countNonZero(thresh)>self.min_motion_area)
        self.current_frame_detection = thresh.copy()
        # on dilate les points blancs pour avoir une meilleure homogeneite. None c'est comme un 3x3
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_mask = np.zeros_like(blur)
        
        for contour in contours:
            if cv2.contourArea(contour) > self.min_motion_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(motion_mask, (x, y), (x+w, y+h), 255, -1)
        #self.current_frame_detection = motion_mask.copy()
        
        self.previous_frame = blur
        motion_detected = is_detected # pour le test de la strategie a l'ancienne
        return motion_detected, motion_mask
    
    def update_motion_counter(self, motion_detected):
        """Met à jour le compteur de mouvement"""
        start_needed = False
        stop_needed = False
        
        if motion_detected:
            if self.motion_callback:
                self.motion_callback(True)
            self.motion_counter = min(self.motion_counter + 1, self.max_counter)
            #print(f"🟢 Mouvement +1 → Compteur: {self.motion_counter}")
            
            if not self.recording and self.motion_counter >= self.start_threshold:
                start_needed = True
        else:
            if self.motion_callback:
                self.motion_callback(False)
            self.motion_counter = max(self.motion_counter - 1, 0)
            #print(f"⚪ Pas mouvement -1 → Compteur: {self.motion_counter}")
            
            if self.recording and self.motion_counter <= self.stop_threshold:
                stop_needed = True
        
        return start_needed, stop_needed
    
    def start_recording(self):
        """Démarre l'enregistrement vidéo"""
        if self.recording:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            year = datetime.now().year
            month = datetime.now().month
            day = datetime.now().day
            self.recording_filename = f"recordings/{year}/{month:02d}/{day:02d}/motion_{timestamp}.mp4"
            #self.recording_filepath = f"recordings/motion_{timestamp}.h264"
            os.makedirs(f"recordings/{year}/{month:02d}/{day:02d}", exist_ok=True)
            
            print(f"🎬 DÉMARRAGE ENREGISTREMENT: {self.recording_filename}")
            
            with self.camera_lock:
                output = FfmpegOutput(self.recording_filename, audio=False)
                #self.current_recording = open(self.recording_filepath, 'wb')
                #output = FileOutput(self.current_recording)
                self.camera.start_recording(self.encoder, output)
                self.recording = True
            
            if self.recording_callback:
                self.recording_callback(True)
                
        except Exception as e:
            print(f"Erreur start_recording: {e}")
            self.recording = False
    
    def stop_recording(self):
        """Arrête l'enregistrement et réinitialise la caméra"""
        if not self.recording:
            return
        
        print(f"⏹ ARRÊT ENREGISTREMENT: {self.recording_filename}")
        
        try:
            with self.camera_lock:
                self.camera.stop_recording()
                # if self.current_recording:
                    # self.current_recording.flush()
                    # self.current_recording.close()
                    # self.current_recording = None
            
            # Vérifier la taille du fichier
            if self.self.recording_filename and os.path.exists(self.recording_filename):
                file_size = os.path.getsize(self.recording_filename)
                if file_size > 0:
                    print(f"✅ Enregistrement sauvegardé: {self.recording_filename} ({file_size} bytes)")
                else:
                    print(f"⚠ Fichier vide supprimé: {self.recording_filename}")
                    os.remove(self.recording_filename)
            
            self.recording_filename = None
            
        except Exception as e:
            print(f"Erreur stop_recording: {e}")
        
        self.recording = False
        
        if self.recording_callback:
            self.recording_callback(False)
        
        # CRUCIAL: Réinitialiser complètement la caméra après l'enregistrement
        # Cela évite le blocage de capture_array()
        self.full_camera_reset()
        
        # Réinitialiser aussi la frame précédente pour la détection
        self.previous_frame = None
        self.motion_counter = 0
    
    def capture_frame(self):
        """Capture une frame - avec gestion d'erreur et tentative de reprise"""
        try:
            frame = None
            
            # Tentative de capture avec timeout implicite
            with self.camera_lock:
                try:
                    frame = self.camera.capture_array()
                except Exception as e:
                    print(f"Erreur capture_array: {e}")
                    # Si la capture échoue, tenter de réinitialiser
                    self.full_camera_reset()
                    return False
            
            if frame is None:
                return False
            
            self.current_frame_raw = frame.copy()
            self.current_frame_bw = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            motion_detected, mask = self.detect_motion(frame)
            
            start_needed, stop_needed = self.update_motion_counter(motion_detected)
            
            if start_needed:
                self.start_recording()
            elif stop_needed:
                self.stop_recording()
            
            #self.current_frame_detection = mask.copy()
            # Création du flux motion
            self.current_frame_motion = frame.copy()
            
            if mask is not None and mask.shape == frame.shape[:2]:
                mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
                mask_colored[:, :, 0] = 0
                mask_colored[:, :, 1] = 0
                
                if mask_colored.shape == frame.shape:
                    self.current_frame_motion = cv2.addWeighted(
                        self.current_frame_motion, 0.7, mask_colored, 0.3, 0
                    )
            
            # Ajouter le compteur à l'image
            # if self.current_frame_motion is not None:
                # cv2.putText(
                    # self.current_frame_motion, 
                    # f"Count: {self.motion_counter}", 
                    # (10, 30), 
                    # cv2.FONT_HERSHEY_SIMPLEX, 
                    # 0.7, 
                    # (0, 255, 0) if not self.recording else (0, 0, 255),
                    # 2
                # )
                # if self.recording:
                    # cv2.putText(
                        # self.current_frame_motion, 
                        # "RECORDING", 
                        # (10, 60), 
                        # cv2.FONT_HERSHEY_SIMPLEX, 
                        # 0.7, 
                        # (0, 0, 255),
                        # 2
                    # )
            
            return motion_detected
            
        except Exception as e:
            print(f"Erreur capture_frame: {e}")
            return False
    
    def run(self):
        """Boucle principale de capture"""
        self.running = True
        while self.running:
            try:
                self.capture_frame()
                #self.determine_luminosite()
                time.sleep(0.1)#0.033 pour 30 frames/s
            except Exception as e:
                print(f"Erreur dans run: {e}")
                time.sleep(0.5)
                # Tentative de récupération
                self.full_camera_reset()
    
    def stop(self):
        """Arrête la caméra"""
        self.running = False
        if self.recording:
            self.stop_recording()
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass