# RevCam
Projet de radio reveil video surveillance en python pour Raspberry

installer Raspberry OS 13
activer SSH
activer VNC via SSH (sudo raspi-config)
activer GPIO via SSH ou VNC (sudo raspi-config)
installer samba (pour partage de fichier):
sudo apt install samba samba-common-bin -y
rajouter au fichier /etc/samba/smb.conf
[RevCam]  # C'est le nom que vous verrez sur Windows
   comment = Dossier partage pour RevCam
   path = /srv/samba/partage  # OU /home/pi/RevCam si vous préférez
   browseable = yes
   writeable = yes
   read only = no
   create mask = 0777
   directory mask = 0777
   valid users = pi
   force user = pi

ajouter un utilisateur samba :
sudo smbpasswd -a pi
relancer le serveur :
sudo systemctl restart smbd

sudo apt update && sudo apt upgrade -y
sudo apt full-upgrade -y

# Installation complète de Picamera2
sudo apt install -y python3-picamera2
# Installation de gpiod (recommandé pour Trixie)
sudo apt install -y gpiod python3-libgpiod
# Installation depuis les dépôts système (plus fiable que pip) de pyqt5
sudo apt install -y python3-pyqt5 python3-pyqt5.qtmultimedia python3-pyqt5.qtsvg
# Version système opencv (compatible avec Picamera2)
sudo apt install -y python3-opencv
# Installation pygame pour la musique
sudo apt install -y python3-pygame

# Installation de la bibliothèque TM1637 compatible gpiod
pip install tm1637-gpiod
# verification
python3 -c "from picamera2 import Picamera2; print('Picamera2 OK')"
python3 -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
python3 -c "import cv2; print(f'OpenCV OK - version {cv2.__version__}')"
python3 -c "import pygame; print('Pygame OK')"

pip install gpiod-tm1637
# Activation de l'environnement virtuel (si vous en utilisez un)
cd ~/RevCam
python3 -m venv --system-site-packages venv
source venv/bin/activate

# pour lancer le programme
pyhton main.py