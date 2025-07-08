import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QComboBox, QLabel
)
from PyQt5.QtCore import pyqtSignal
from yt_dlp import YoutubeDL, DownloadError
import time

class Downloader(QWidget):
    """Aplicación PyQt5 para descargar videos de YouTube con selección de calidad usando yt-dlp."""
    status_update = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.status_update.connect(self.handle_status)
        self._last_print = 0

    def initUI(self):
        self.setWindowTitle('YouTube Video Downloader')
        self.setGeometry(100, 100, 400, 380)

        layout = QVBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Introduce el enlace de YouTube')
        layout.addWidget(self.url_input)

        self.choose_btn = QPushButton('Seleccionar carpeta de salida')
        self.choose_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.choose_btn)

        layout.addWidget(QLabel('Seleccionar calidad:'))
        self.quality_combo = QComboBox()
        qualities = ['Mejor disponible', '1080p', '720p', '480p', '360p', '240p', '144p']
        self.quality_combo.addItems(qualities)
        layout.addWidget(self.quality_combo)

        self.download_btn = QPushButton('Descargar')
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        self.status = QTextEdit()
        self.status.setReadOnly(True)
        layout.addWidget(self.status)

        self.setLayout(layout)
        self.output_path = None

    def handle_status(self, message):
        if message == 'ENABLE_BUTTON':
            self.download_btn.setEnabled(True)
        else:
            self.status.append(message)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Seleccionar carpeta')
        if path:
            self.output_path = path
            self.status_update.emit(f'Carpeta de salida: {path}')

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_update.emit('Por favor ingresa una URL.')
            return
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        if not self.output_path:
            self.output_path = r"D:\Images"
            print(self.output_path)

        self.download_btn.setEnabled(False)
        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        choice = self.quality_combo.currentText()
        # Construir formato para yt-dlp
        if choice == 'Mejor disponible':
            fmt = 'bestvideo+bestaudio/best'
        else:
            height = ''.join(filter(str.isdigit, choice))
            fmt = f"bestvideo[height={height}]+bestaudio/best"

        def progress_hook(d):
            if d.get('status') == 'downloading':
                now = time.time()
                if now - self._last_print < 3:
                    return
                self._last_print = now

                total = d.get('total_bytes') or 1
                percent = int(d['downloaded_bytes'] / total)
                self.status_update.emit(f'Progreso: {percent}%')
            elif d.get('status') == 'finished':
                self.status_update.emit('Descarga completada, finalizando...')

        opts = {
            'outtmpl': f'{self.output_path}/%(title)s.%(ext)s',
            'format': fmt,
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'quiet': True,
        }
        try:
            self.status_update.emit(f'Descargando {choice} de: {url}')
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.status_update.emit('Video descargado correctamente.')
        except DownloadError as e:
            self.status_update.emit(f'Error de descarga o formato no disponible: {e}')
        except Exception as e:
            self.status_update.emit(f'Error inesperado: {e}')
        finally:
            self.status_update.emit('ENABLE_BUTTON')

if __name__ == '__main__':
    # Instalar: pip install PyQt5 yt-dlp
    app = QApplication(sys.argv)
    window = Downloader()
    window.show()
    sys.exit(app.exec_())

