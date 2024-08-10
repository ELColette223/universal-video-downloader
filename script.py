import tkinter as tk
from tkinter import Menu
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import os
import configparser
import webbrowser
import shutil
import signal
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class YTDLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader - By: @elgustta - v1.0.0b")

        # Carregar configurações
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_config()

        # URL
        ttk.Label(root, text="URL do Vídeo:", foreground="gray88").grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = ttk.Entry(root, width=50)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)

        # Pasta de Download
        ttk.Label(root, text="Pasta de Download:", foreground="gray88").grid(row=1, column=0, padx=10, pady=10)
        self.folder_path = ttk.StringVar(value=self.default_download_folder)
        ttk.Entry(root, textvariable=self.folder_path, width=50).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(root, text="Procurar", command=self.browse_folder).grid(row=2, column=1, padx=10, pady=10, sticky='e')

        # Checkbox para salvar pasta
        self.save_folder_var = ttk.BooleanVar(value=self.save_download_folder)
        ttk.Checkbutton(root, text="Salvar pasta de Downloads", variable=self.save_folder_var).grid(row=2, column=1, padx=10, pady=5, sticky='w')

        # Espaçamento
        ttk.Label(root, text="").grid(row=3, column=0, padx=5, pady=5)

        # Qualidade do Vídeo
        ttk.Label(root, text="Qualidade do Vídeo:", foreground="gray88").grid(row=4, column=0, padx=5, pady=5)
        self.quality_var = ttk.StringVar(value="Original")
        qualities = ["Original", "Melhor", "Bom", "Ruim"]
        ttk.OptionMenu(root, self.quality_var, *qualities).grid(row=4, column=1, padx=5, pady=5, sticky='ew')

        # Formato de Saída
        ttk.Label(root, text="Formato de Saída:", foreground="gray88").grid(row=5, column=0, padx=5, pady=5)
        self.format_var = ttk.StringVar(value="mp4")
        formats = ["Mp4", "Original"] #, "mkv", "mov" 
        ttk.OptionMenu(root, self.format_var, *formats).grid(row=5, column=1, padx=5, pady=5, sticky='ew')

        # Botão de Download
        ttk.Button(root, text="Baixar", command=self.start_download_thread).grid(row=6, column=1, padx=10, pady=20, sticky='ew')

        # Separador
        ttk.Separator(root, orient='horizontal').grid(row=7, column=0, columnspan=2, sticky='ew', padx=10)

        # Texto de Rodapé
        footer_frame = ttk.Frame(root)
        footer_frame.grid(row=8, column=0, columnspan=2, pady=10)

        # Texto de rodapé
        footer_text2 = "O uso deste software é de responsabilidade do usuário."
        ttk.Label(footer_frame, text=footer_text2, foreground="gray").grid(row=1, column=0, columnspan=2)

        footer_text3 = "O desenvolvedor não se responsabiliza pelo uso indevido do software."
        ttk.Label(footer_frame, text=footer_text3, foreground="gray").grid(row=2, column=0, columnspan=2)

        # Centralizando o rodapé
        footer_frame.grid_columnconfigure(0, weight=1)

        self.is_downloading = False
        self.cancel_requested = threading.Event()  # Usando Event para controle de cancelamento
        self.ydl = None  # Armazena a instância do YoutubeDL
        self.download_thread = None  # Thread do download

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            self.default_download_folder = self.config.get('Settings', 'download_folder', fallback=os.path.expanduser("~"))
            self.save_download_folder = self.config.getboolean('Settings', 'save_download_folder', fallback=False)
        else:
            self.default_download_folder = os.path.expanduser("~")
            self.save_download_folder = False

    def save_config(self):
        self.config['Settings'] = {
            'download_folder': self.folder_path.get(),
            'save_download_folder': str(self.save_folder_var.get()),
        }

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def start_download_thread(self):
        self.cancel_requested.clear()  # Reseta o evento de cancelamento
        self.download_thread = threading.Thread(target=self.download_video)
        self.download_thread.start()

    def check_disk_space(self, folder, required_space):
        total, used, free = shutil.disk_usage(folder)
        return free >= required_space

    def select_best_format(self, formats, quality):
        format_expression = 'bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[ext=mp4][height<=2160]'

        if quality == "Original":
            format_expression = 'bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[ext=mp4][height<=2160]'
        elif quality == "Melhor":
            format_expression = 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]'
        elif quality == "Bom":
            format_expression = 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]'
        elif quality == "Ruim":
            format_expression = 'bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4][height<=360]'

        return format_expression

    def download_video(self):
        url = self.url_entry.get()
        download_folder = self.folder_path.get()
        quality = self.quality_var.get()

        if not url or not download_folder:
            messagebox.showwarning("Input Error", "Por favor, insira a URL e selecione a pasta de download.")
            return

        try:
            with yt_dlp.YoutubeDL() as ydl:
                info_dict = ydl.extract_info(url, download=False)
                self.video_title = info_dict.get('title', 'Desconhecido')
                self.total_size = info_dict.get('filesize_approx', None) or info_dict.get('filesize', None)

                if self.total_size and not self.check_disk_space(download_folder, self.total_size):
                    messagebox.showerror("Erro de Espaço em Disco", "Espaço insuficiente no disco para o download.")
                    return

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar o espaço em disco: {str(e)}")
            return

        ydl_opts = {
            'format': self.select_best_format(formats=info_dict.get('formats', []), quality=quality),
            'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
            'quiet': False,
            'noprogress': False,
            'progress_hooks': [self.ytdl_hook],
        }

        self.progress_popup = tk.Toplevel(self.root)
        self.progress_popup.title("Progresso do Download")
        self.progress_label = tk.Label(self.progress_popup, text="Iniciando...")
        self.progress_label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.progress_popup, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=10, padx=10)
        self.cancel_button = tk.Button(self.progress_popup, text="Cancelar", command=self.cancel_download)
        self.cancel_button.pack(pady=10)

        self.is_downloading = True

        try:
            self.run_download(ydl_opts, url)
            if self.is_downloading:
                self.save_config()
                messagebox.showinfo("Sucesso", "Download concluído com sucesso!")
                self.progress_popup.destroy()
                self.open_download_folder(download_folder)
        except yt_dlp.utils.DownloadError as e:
            if not self.cancel_requested.is_set():
                messagebox.showerror("Erro", f"Ocorreu um erro ao tentar baixar o vídeo: {str(e)}\nPor favor, verifique os formatos disponíveis e tente novamente.")
        except Exception as e:
            if self.is_downloading:
                messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            self.progress_popup.destroy()
        finally:
            if self.cancel_requested.is_set():
                self.cleanup_partial_download(download_folder, self.video_title)

    def run_download(self, ydl_opts, url):
        self.ydl = yt_dlp.YoutubeDL(ydl_opts)
        try:
            self.ydl.download([url])
        except yt_dlp.utils.DownloadError:
            if self.cancel_requested.is_set():
                messagebox.showinfo("Cancelado", "O download foi cancelado pelo usuário.")
            else:
                raise

    def ytdl_hook(self, d):
        if self.cancel_requested.is_set():
            self.ydl.downloader.interrupt_requested = True
            raise yt_dlp.utils.DownloadError("Download cancelado pelo usuário.")
            
        if d['status'] == 'downloading':
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = self.total_size or 1

            self.progress_bar['value'] = (downloaded_bytes / total_bytes) * 100 if total_bytes else 0

            eta = d.get('eta', 0)
            eta = int(eta) if eta else "Desconhecido"
            speed = d.get('speed', 0)
            
            self.progress_label.config(
                text=f"Baixando: {self.video_title}\n"
                    f"Tamanho: {total_bytes / (1024**2):.2f} MB\n"
                    f"Baixado: {downloaded_bytes / (1024**2):.2f} MB\n"
                    f"Velocidade: {(speed or 0) / (1024**2): .2f} MiB/s\n"
                    f"Tempo restante: {eta} segundos"
            )
            self.progress_popup.update()

        if d['status'] == 'finished':
            self.progress_label.config(text=f"Download Concluído!")
            self.progress_bar['value'] = 100
            self.progress_popup.update()

    def cancel_download(self):
        self.cancel_requested.set()  # Sinaliza que o cancelamento foi solicitado
        self.is_downloading = False

        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.join()  # Aguarda a thread terminar
        self.progress_popup.destroy()
        self.cleanup_partial_download(self.folder_path.get(), self.video_title)
        
        os.kill(os.getpid(), signal.SIGINT)

    def cleanup_partial_download(self, folder, title):
        # Remove o arquivo parcial
        partial_files = [f for f in os.listdir(folder) if f.startswith(title) and f.endswith('.part')]
        for f in partial_files:
            os.remove(os.path.join(folder, f))

    def open_download_folder(self, folder):
        if os.path.isdir(folder):
            webbrowser.open(folder)

# Iniciar o aplicativo
root = ttk.Window(themename="darkly")
app = YTDLApp(root)
root.mainloop()
