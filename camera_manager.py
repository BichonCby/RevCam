# camera_manager.py - Version avec réinitialisation complète

import threading
import time
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import controls
from picamera2.outputs import FfmpegOutput

import cv2
from datetime import datetime
import os
from config import config

class CameraManager:
    def __init__(self, recording_callback=None):
        self.camera = None
        self.running = False
        self.recording = False
        self.encoder = None
        self.recording_filepath = None
        self.camera_lock = threading.Lock()  # Verrou pour les accès caméra
        
        # Paramètres de détection
        self.motion_threshold = config.get("motion", "threshold")
        self.min_motion_area = config.get("motion", "min_area")
        self.blur_size = config.get("motion", "blur_size")
        
        # Paramètres du compteur
        self.motion_counter = 0
        self.start_threshold = 5
        self.stop_threshold = 2
        self.max_counter = 30
        
        self.previous_frame = None
        self.recording_callback = recording_callback
        
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
                controls={
                    "AeEnable": True,
                    "AwbEnable": True,
                    "AeExposureMode": controls.AeExposureModeEnum.Normal,  # Changera selon lumière
                    "AeMeteringMode": controls.AeMeteringModeEnum.Matrix   # Mesure globale
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
            
            self.encoder = H264Encoder(bitrate=10000000, repeat=True)
    
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
                controls={
                    "AeEnable": True,
                    "AwbEnable": True,
                    "AeExposureMode": controls.AeExposureModeEnum.Normal,  # Changera selon lumière
                    "AeMeteringMode": controls.AeMeteringModeEnum.Matrix   # Mesure globale
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
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        
        if self.previous_frame is None:
            self.previous_frame = gray
            return False, None
        
        # on fait la difference entre deux images grises successives
        diff = cv2.absdiff(self.previous_frame, gray)
        
        #tout ce qui a bouge sera blanc, le reste noir
        _, thresh = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
        # on dilate les points blancs pour avoir une meilleure homogeneite. None c'est comme un 3x3
        thresh = cv2.dilate(thresh, None, iterations=2)
        self.current_frame_detection = thresh.copy()
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_mask = np.zeros_like(gray)
        
        for contour in contours:
            if cv2.contourArea(contour) > self.min_motion_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(motion_mask, (x, y), (x+w, y+h), 255, -1)
        
        self.previous_frame = gray
        return motion_detected, motion_mask
    
    def update_motion_counter(self, motion_detected):
        """Met à jour le compteur de mouvement"""
        start_needed = False
        stop_needed = False
        
        if motion_detected:
            self.motion_counter = min(self.motion_counter + 1, self.max_counter)
            #print(f"🟢 Mouvement +1 → Compteur: {self.motion_counter}")
            
            if not self.recording and self.motion_counter >= self.start_threshold:
                start_needed = True
        else:
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
            filename = f"recordings/motion_{timestamp}.mp4"
            #self.recording_filepath = f"recordings/motion_{timestamp}.h264"
            os.makedirs("recordings", exist_ok=True)
            
            print(f"🎬 DÉMARRAGE ENREGISTREMENT: {self.recording_filepath}")
            
            with self.camera_lock:
                output = FfmpegOutput(filename, audio=False)
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
        
        print(f"⏹ ARRÊT ENREGISTREMENT: {self.recording_filepath}")
        
        try:
            with self.camera_lock:
                self.camera.stop_recording()
                if self.current_recording:
                    self.current_recording.flush()
                    self.current_recording.close()
                    self.current_recording = None
            
            # Vérifier la taille du fichier
            if self.recording_filepath and os.path.exists(self.recording_filepath):
                file_size = os.path.getsize(self.recording_filepath)
                if file_size > 0:
                    print(f"✅ Enregistrement sauvegardé: {self.recording_filepath} ({file_size} bytes)")
                else:
                    print(f"⚠ Fichier vide supprimé: {self.recording_filepath}")
                    os.remove(self.recording_filepath)
            
            self.recording_filepath = None
            
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
            if self.current_frame_motion is not None:
                cv2.putText(
                    self.current_frame_motion, 
                    f"Count: {self.motion_counter}", 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 0) if not self.recording else (0, 0, 255),
                    2
                )
                if self.recording:
                    cv2.putText(
                        self.current_frame_motion, 
                        "RECORDING", 
                        (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 0, 255),
                        2
                    )
            
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