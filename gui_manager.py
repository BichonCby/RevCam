# gui_manager.py - Version complète corrigée
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import config

class TM1637DisplayWidget(QWidget):
    """Widget qui simule l'affichage du TM1637"""
    
    # Segments pour les chiffres (7 segments)
    SEGMENT_MAP = {
        '0': [1,1,1,1,1,1,0],
        '1': [0,1,1,0,0,0,0],
        '2': [1,1,0,1,1,0,1],
        '3': [1,1,1,1,0,0,1],
        '4': [0,1,1,0,0,1,1],
        '5': [1,0,1,1,0,1,1],
        '6': [1,0,1,1,1,1,1],
        '7': [1,1,1,0,0,0,0],
        '8': [1,1,1,1,1,1,1],
        '9': [1,1,1,1,0,1,1],
        'A': [1,1,1,0,1,1,1],
        'b': [0,0,1,1,1,1,1],
        'C': [1,0,0,1,1,1,0],
        'c': [0,0,0,1,1,0,1],
        'd': [0,1,1,1,1,0,1],
        'E': [1,0,0,1,1,1,1],
        'F': [1,0,0,0,1,1,1],
        'H': [0,1,1,0,1,1,1],
        'L': [0,0,0,1,1,1,0],
        'P': [1,1,0,0,1,1,1],
        'r': [0,0,0,0,1,0,1],
        'U': [0,1,1,1,1,1,0],
        '-': [0,0,0,0,0,0,1],
        '_': [0,0,0,0,0,1,0],
        ' ': [0,0,0,0,0,0,0],
        'o': [0,0,1,1,1,0,1],
        'l': [0,0,0,0,1,1,0],
        'L': [0,0,0,1,1,1,0],
        'n': [0,0,1,0,1,0,1]
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(240, 70)
        self.setMaximumSize(400, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Valeurs d'affichage
        self.digits = ['8', '8', '8', '8']
        self.colon = True
        self.brightness = 5
        
        # Fond noir pour simuler l'afficheur
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(10, 10, 10))
        self.setPalette(palette)
        
        # Police pour le label texte (optionnel)
        self.text_label = QLabel(self)
        self.text_label.setStyleSheet("color: #00ff00; font-family: monospace; font-size: 12px; background-color: transparent;")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setGeometry(0, 55, 200, 20)
    
    def resizeEvent(self, event):
        """Ajuste la position du label quand le widget est redimensionné"""
        #super().resizeEvent(event)
        #self.text_label.setGeometry(0, self.height() - 18, self.width(), 15)
        
    def set_display(self, text, colon=True):
        """Affiche un texte de 4 caractères"""
        #text = str(text).upper()
        # Remplir avec des espaces
        self.digits = list(text.ljust(4)[:4])
        self.colon = colon
        self.update()
    
    def set_numbers(self, num1, num2, colon=True):
        """Affiche deux nombres (format HH:MM)"""
        text = f"{num1:02d}{num2:02d}"
        self.set_display(text, colon)
    
    def clear(self):
        """Efface l'affichage"""
        self.digits = [' ', ' ', ' ', ' ']
        self.update()
    
    def set_brightness(self, value):
        """Simule la luminosité (0-7)"""
        self.brightness = max(0, min(7, value))
        self.update()
    
    def paintEvent(self, event):
        """Dessine l'afficheur 7 segments"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculer la taille de chaque digit
        w = self.width()
        h = self.height()
                
        # CORRECTION : Calculer une marge proportionnelle
        margin = max(10, w // 20)
        available_width = w - (2 * margin)
        
        # CORRECTION : Espace pour les deux-points
        colon_width = 8
        digit_total_width = available_width - colon_width
        digit_width = digit_total_width // 4
        digit_height = h - 25  # Réserver de la place pour le label
        
        # Ne pas dépasser une taille raisonnable
        digit_width = min(digit_width, 45)
        digit_height = min(digit_height, 65)
        
        # Recalculer la position de départ pour centrer
        total_digits_width = (digit_width * 4) + colon_width
        start_x = (w - total_digits_width) // 2
        
        # Couleurs
        intensity = 30 + (self.brightness * 20)  # 30 à 170
        color_on = QColor(0, intensity, 0)
        color_off = QColor(0, 15, 0)
        
        # Dessiner les 4 digits
        for i, digit in enumerate(self.digits):
            x = 20 + i * digit_width + (i * 5)  # 5px d'espace entre digits
            if i >= 2:# and self.colon:
                x += 8  # Décalage pour les deux-points
            
            self.draw_digit(painter, x, 10, digit_width, digit_height, digit, color_on, color_off)
        
        # Dessiner les deux-points
        if self.colon:
            colon_x = 20 + 2 * digit_width + 10
            colon_y1 = h // 2 - 8
            colon_y2 = h // 2 + 8
            
            painter.setBrush(color_on)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(colon_x, colon_y1, 4, 4)
            painter.drawEllipse(colon_x, colon_y2, 4, 4)
        else:
            colon_x = 20 + 2 * digit_width + 10
            colon_y1 = h // 2 - 8
            colon_y2 = h // 2 + 8
            
            painter.setBrush(color_off)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(colon_x, colon_y1, 4, 4)
            painter.drawEllipse(colon_x, colon_y2, 4, 4)
        # Afficher l'état en bas
        if self.brightness < 7:
            self.text_label.setText(f"Brightness: {self.brightness}/7")
        else:
            self.text_label.setText("")
    
    def draw_digit(self, painter, x, y, w, h, digit, color_on, color_off):
        """Dessine un chiffre 7 segments"""
        segments = self.SEGMENT_MAP.get(digit, [0,0,0,0,0,0,0])
        
        # Épaisseur des segments
        thick = max(3, w // 8)
        margin = thick // 2
        
         # Segment A (haut)
        painter.setBrush(color_on if segments[0] else color_off)
        painter.setPen(Qt.NoPen)
        painter.drawRect(x + margin, y, w - 2*margin, thick)
        
        # Segment B (haut droit)
        painter.setBrush(color_on if segments[1] else color_off)
        painter.drawRect(x + w - thick, y + margin, thick, (h//2) - margin)
        
        # Segment C (bas droit)
        painter.setBrush(color_on if segments[2] else color_off)
        painter.drawRect(x + w - thick, y + h//2 + margin, thick, (h//2) - margin)
        
        # Segment D (bas)
        painter.setBrush(color_on if segments[3] else color_off)
        painter.drawRect(x + margin, y + h - thick, w - 2*margin, thick)
        
        # Segment E (bas gauche)
        painter.setBrush(color_on if segments[4] else color_off)
        painter.drawRect(x, y + h//2 + margin, thick, (h//2) - margin)
        
        # Segment F (haut gauche)
        painter.setBrush(color_on if segments[5] else color_off)
        painter.drawRect(x, y + margin, thick, (h//2) - margin)
        
        # Segment G (milieu)
        painter.setBrush(color_on if segments[6] else color_off)
        painter.drawRect(x + margin, y + h//2 - thick//2, w - 2*margin, thick)


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray, str)
    
    def __init__(self, camera_manager):
        super().__init__()
        self.camera_manager = camera_manager
        self.mode = "raw"
        self.running = True
    
    def set_mode(self, mode):
        self.mode = mode
    
    def run(self):
        while self.running:
            frame = None
            try:
                if self.mode == "raw":
                    frame = self.camera_manager.current_frame_raw
                elif self.mode == "bw":
                    if self.camera_manager.current_frame_bw is not None:
                        frame = cv2.cvtColor(
                            self.camera_manager.current_frame_bw, 
                            cv2.COLOR_GRAY2RGB
                        )
                elif self.mode == "motion":
                    frame = self.camera_manager.current_frame_motion
                
                if frame is not None:
                    self.change_pixmap_signal.emit(frame, self.mode)
            except Exception as e:
                print(f"Erreur dans VideoThread: {e}")
            
            self.msleep(33)
    
    def stop(self):
        self.running = False
        self.wait()

class GUIManager(QMainWindow):
    BOUTON_PLUS = 1
    BOUTON_MOINS = 0
    BOUTON_SNOOZE = 2
    BOUTON_MODE =3
    
    def __init__(self, camera_manager, display_manager, audio_manager, gpio_controller):
        super().__init__()
        self.camera_manager = camera_manager
        self.display_manager = display_manager
        self.audio_manager = audio_manager
        self.gpio_controller = gpio_controller
        
        self.setWindowTitle("Système de Surveillance - Raspberry Pi")
        self.setGeometry(100, 100, 1200, 800)
        
        self.slider_multipliers = {}
        
        self.init_ui()
        
        self.video_thread = VideoThread(camera_manager)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()

        # Timer pour synchroniser l'affichage TM1637 simulé
        self.tm1637_timer = QTimer()
        self.tm1637_timer.timeout.connect(self.update_tm1637_display)
        self.tm1637_timer.start(500)  # Mise à jour 2x par seconde    
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Panneau gauche - Vidéo
        left_panel = QWidget()
        left_panel.setMaximumWidth(550)
        left_layout = QVBoxLayout(left_panel)
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(480, 360)
        self.video_label.setMaximumSize(480, 360)
        self.video_label.setStyleSheet("border: 2px solid black; background-color: #333;")
        self.video_label.setScaledContents(True)
        left_layout.addWidget(self.video_label)
        
        # Boutons de mode vidéo
        mode_layout = QHBoxLayout()
        self.btn_raw = QPushButton("RAW")
        self.btn_bw = QPushButton("Noir & Blanc")
        self.btn_motion = QPushButton("Détection Mouvement")
        
        self.btn_raw.clicked.connect(lambda: self.set_video_mode("raw"))
        self.btn_bw.clicked.connect(lambda: self.set_video_mode("bw"))
        self.btn_motion.clicked.connect(lambda: self.set_video_mode("motion"))
        
        mode_layout.addWidget(self.btn_raw)
        mode_layout.addWidget(self.btn_bw)
        mode_layout.addWidget(self.btn_motion)
        left_layout.addLayout(mode_layout)
        
        # NOUVEAU : Widget d'affichage TM1637 simulé
        tm1637_container = QGroupBox("État de l'afficheur TM1637")
        tm1637_container.setStyleSheet("QGroupBox { font-weight: bold; }")
        tm1637_container.setMinimumHeight(120)  # Hauteur minimale
        tm1637_container.setMaximumHeight(150)  # Hauteur maximale  
        
        container_layout = QVBoxLayout(tm1637_container)
        container_layout.setContentsMargins(5, 10, 5, 5)  # Marges réduites
        container_layout.setSpacing(2)
        
        self.tm1637_sim = TM1637DisplayWidget()
        container_layout.addWidget(self.tm1637_sim, 0, Qt.AlignCenter)
        
        # Label pour l'info texte
        #self.tm1637_info = QLabel("Affichage synchronisé avec l'afficheur physique")
        #self.tm1637_info.setStyleSheet("color: gray; font-size: 10px;")
        #self.tm1637_info.setAlignment(Qt.AlignCenter)
        #container_layout.addWidget(self.tm1637_info)
        
        left_layout.addWidget(tm1637_container)
        
        # Panneau droit - Contrôles
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Section Caméra
        camera_group = QGroupBox("Paramètres Caméra")
        camera_layout = QFormLayout()
        
        self.brightness_slider = self.create_slider(0.0, 1.0, config.get("camera", "brightness"))
        self.brightness_slider.valueChanged.connect(self.update_brightness)
        camera_layout.addRow("Luminosité:", self.brightness_slider)
        
        self.contrast_slider = self.create_slider(0.0, 2.0, config.get("camera", "contrast"))
        self.contrast_slider.valueChanged.connect(self.update_contrast)
        camera_layout.addRow("Contraste:", self.contrast_slider)
        
        self.iso_slider = self.create_slider(100, 800, config.get("camera", "iso"))
        self.iso_slider.valueChanged.connect(self.update_iso)
        camera_layout.addRow("ISO:", self.iso_slider)
        
        camera_group.setLayout(camera_layout)
        right_layout.addWidget(camera_group)
        
        # Section Mouvement
        motion_group = QGroupBox("Détection Mouvement")
        motion_layout = QFormLayout()
        
        self.threshold_slider = self.create_slider(10, 100, config.get("motion", "threshold"))
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        motion_layout.addRow("Sensibilité:", self.threshold_slider)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(config.get("motion", "record_duration"))
        self.duration_spin.valueChanged.connect(self.update_duration)
        motion_layout.addRow("Durée enregistrement (s):", self.duration_spin)
        
        motion_group.setLayout(motion_layout)
        right_layout.addWidget(motion_group)
        
        # Section Audio
        audio_group = QGroupBox("Audio")
        audio_layout = QFormLayout()
        
        self.volume_slider = self.create_slider(0, 100, self.audio_manager.volume * 100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        audio_layout.addRow("Volume:", self.volume_slider)
        
        self.motion_sound_cb = QCheckBox()
        self.motion_sound_cb.setChecked(config.get("audio", "play_on_motion"))
        self.motion_sound_cb.stateChanged.connect(self.update_motion_sound)
        audio_layout.addRow("Son sur mouvement:", self.motion_sound_cb)
        
        audio_group.setLayout(audio_layout)
        right_layout.addWidget(audio_group)
        
        # Section Affichage TM1637
        display_group = QGroupBox("Affichage TM1637")
        display_layout = QFormLayout()
        
        self.display_brightness = self.create_slider(0, 7, config.get("display", "brightness_tm1637"))
        self.display_brightness.valueChanged.connect(self.update_display_brightness)
        display_layout.addRow("Luminosité:", self.display_brightness)
        
        display_group.setLayout(display_layout)
        right_layout.addWidget(display_group)
        
        # Boutons musique
        music_group = QGroupBox("Musique")
        music_layout = QVBoxLayout()
        
        self.btn_play = QPushButton("▶ Jouer")
        self.btn_stop = QPushButton("⏹ Arrêter")
        
        self.btn_play.clicked.connect(self.play_music)
        self.btn_stop.clicked.connect(self.stop_music)
        
        music_layout.addWidget(self.btn_play)
        music_layout.addWidget(self.btn_stop)
        music_group.setLayout(music_layout)
        right_layout.addWidget(music_group)
        
        # Statut
        status_group = QGroupBox("Statut")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("✅ Système actif")
        self.motion_status = QLabel("🟢 Aucun mouvement")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.motion_status)
        status_group.setLayout(status_layout)
        right_layout.addWidget(status_group)
        
        # Boutons et LED
        btnled_group = QGroupBox("LED et boutons")
        btnled_layout = QVBoxLayout()
        self.btn_plus = QPushButton("PLUS")
        self.btn_moins = QPushButton("MOINS")
        self.btn_snooze = QPushButton("snooze")
        self.btn_mode = QPushButton("mode")
        self.greenled_label = QLabel()
        self.redled_label = QLabel()
        self.greenled_label.setFixedSize(20, 20)
        self.redled_label.setFixedSize(20, 20)
        btnled_layout.addWidget(self.btn_plus)
        btnled_layout.addWidget(self.btn_moins)
        btnled_layout.addWidget(self.btn_snooze)
        btnled_layout.addWidget(self.btn_mode)
        btnled_layout.addWidget(self.greenled_label)
        btnled_layout.addWidget(self.redled_label)
        btnled_group.setLayout(btnled_layout)
        self.btn_plus.clicked.connect(self.button_plus)
        self.btn_moins.clicked.connect(self.button_moins)
        self.btn_snooze.clicked.connect(self.button_snooze)
        self.btn_mode.clicked.connect(self.button_mode)
        right_layout.addWidget(btnled_group)
        
        right_layout.addStretch()
        
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 1)
    
    def update_tm1637_display(self):
        """Met à jour l'affichage simulé depuis le vrai TM1637"""
        try:
            # Récupérer l'état réel depuis le display_manager
            # Pour cela, vous devez stocker les dernières valeurs dans display_manager
            # Ou simplement lire l'heure actuelle (comportement identique)
            #from datetime import datetime
            #now = datetime.now()
            texte,colon = self.display_manager.get_display()
            #self.tm1637_sim.set_numbers(now.hour, now.minute, colon=(now.second % 2 == 0))
            self.tm1637_sim.set_display(texte,colon)
            #################
            # Synchroniser la luminosité
            if hasattr(self.display_manager, 'brightness_val'):
                self.tm1637_sim.set_brightness(self.display_manager.brightness_val)
        except Exception as e:
            print(f"Erreur synchro TM1637: {e}")
        
    def create_slider(self, min_val, max_val, initial):
        """Crée un slider avec gestion des floats"""
        slider = QSlider(Qt.Horizontal)
        
        if isinstance(min_val, float) or isinstance(max_val, float) or isinstance(initial, float):
            multiplier = 100
            slider.setMinimum(int(min_val * multiplier))
            slider.setMaximum(int(max_val * multiplier))
            slider.setValue(int(initial * multiplier))
            self.slider_multipliers[slider] = multiplier
        else:
            slider.setMinimum(int(min_val))
            slider.setMaximum(int(max_val))
            slider.setValue(int(initial))
            self.slider_multipliers[slider] = 1
        
        slider.setTickPosition(QSlider.TicksBelow)
        return slider
    
    def get_slider_value(self, slider):
        """Récupère la valeur réelle d'un slider"""
        multiplier = self.slider_multipliers.get(slider, 1)
        return slider.value() / multiplier
    
    def set_video_mode(self, mode):
        self.video_thread.set_mode(mode)
    
    def update_image(self, frame, mode):
        """Met à jour l'affichage vidéo"""
        try:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.video_label.size()/2, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
            QApplication.processEvents()
        except Exception as e:
            print(f"Erreur affichage: {e}")
    
    def update_brightness(self):
        value = self.get_slider_value(self.brightness_slider)
        config.set("camera", "brightness", value)
        self.camera_manager.update_camera_params()
    
    def update_contrast(self):
        value = self.get_slider_value(self.contrast_slider)
        config.set("camera", "contrast", value)
        self.camera_manager.update_camera_params()
    
    def update_iso(self):
        value = int(self.get_slider_value(self.iso_slider))
        config.set("camera", "iso", value)
        self.camera_manager.update_camera_params()
    
    def update_threshold(self):
        value = int(self.get_slider_value(self.threshold_slider))
        config.set("motion", "threshold", value)
        self.camera_manager.motion_threshold = value
    
    def update_duration(self, value):
        config.set("motion", "record_duration", value)
        self.camera_manager.record_duration = value
    
    def update_volume(self):
        value = self.get_slider_value(self.volume_slider)
        self.audio_manager.set_volume(value / 100)
        config.set("audio", "volume", value / 100)
    
    def update_motion_sound(self, state):
        config.set("audio", "play_on_motion", state == Qt.Checked)
    
    def update_display_brightness(self):
        value = int(self.get_slider_value(self.display_brightness))
        config.set("display", "brightness_tm1637", value)
        self.display_manager.set_brightness(value)
    
    def play_music(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Choisir un fichier audio", "music/", 
            "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if filepath:
            self.audio_manager.play_music(filepath)
    
    def stop_music(self):
        self.audio_manager.stop_music()
    
    def button_plus(self):
        #self.greenled_label.setText("BOUTON_PLUS")
        self.gpio_controller.push_button(self.BOUTON_PLUS)
        print("bouton plus")
 
    def button_moins(self):
        #self.greenled_label.setText("BOUTON_MOINS")
        self.gpio_controller.push_button(self.BOUTON_MOINS)
        print("bouton moins")

    def button_snooze(self):
        #self.greenled_label.setText("BOUTON_SNOOZE")
        self.gpio_controller.push_button(self.BOUTON_SNOOZE)
        print("bouton snooze")

    def button_mode(self):
        #self.greenled_label.setText("MODE")
        self.gpio_controller.push_button(self.BOUTON_MODE)
        print("bouton mode")
    
    def set_led(self,led1,led2):
        #print(f"led callback appele {led1} {led2}")
        if led1:
            #self.greenled_label.setText("🟢green")
            self.greenled_label.setStyleSheet("""
                background-color: #00FF00;
                border-radius: 10px;
                border: 2px solid #00AA00;
            """)
        else:
            self.greenled_label.setStyleSheet("""
                background-color: #000000;
                border-radius: 10px;
                border: 2px solid #00AA00;
            """)
        if led2:
             self.redled_label.setStyleSheet("""
                background-color: #FF0000;
                border-radius: 10px;
                border: 2px solid #00AA00;
            """)
        else:
             self.redled_label.setStyleSheet("""
                background-color: #000000;
                border-radius: 10px;
                border: 2px solid #00AA00;
            """)
           

            
    def closeEvent(self, event):
        self.video_thread.stop()
        event.accept()