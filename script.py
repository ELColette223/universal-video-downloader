import tkinter as tk
from tkinter import Menu, filedialog, messagebox, ttk
import yt_dlp
import threading
import os
import configparser
import webbrowser
import shutil
import signal
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from image_downloader import ImageDownloader  # Importa o módulo de download de imagens
from generic import GenericDownloader  # Importa o módulo para baixar conteúdo genérico

class YTDLApp:
    def __init__(self, root):
        self.root = root
        self.root.resizable(False, False)
        self.root.title("Content Downloader - By: @elgustta - v1.1.2")

        # Carregar configurações
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_config()

        # Criar Notebook para as abas
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10)

        # Frame para aba de vídeos
        self.video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.video_frame, text="Vídeos")

        # Frame para aba de Instagram
        self.image_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.image_frame, text="Instagram")

        # Frame para aba de Genérico
        self.generic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.generic_frame, text="Genérico")

        # Construir a aba de vídeos
        self.build_video_tab(self.video_frame)

        # Construir a aba de Instagram
        self.build_image_tab(self.image_frame)

        # Construir a aba de Genérico
        self.build_generic_tab(self.generic_frame)

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

    def build_video_tab(self, frame):
        # URL
        ttk.Label(frame, text="URL do Vídeo:", foreground="gray88").grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = ttk.Entry(frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)

        # Pasta de Download
        ttk.Label(frame, text="Pasta de Download:", foreground="gray88").grid(row=1, column=0, padx=10, pady=10)
        self.folder_path = ttk.StringVar(value=self.default_download_folder + '/ContentDownloader')
        ttk.Entry(frame, textvariable=self.folder_path, width=50).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(frame, text="Procurar", command=self.browse_folder).grid(row=2, column=1, padx=10, pady=10, sticky='e')

        # Checkbox para salvar pasta
        self.save_folder_var = ttk.BooleanVar(value=self.save_download_folder)
        ttk.Checkbutton(frame, text="Salvar pasta de Downloads", variable=self.save_folder_var).grid(row=2, column=1, padx=10, pady=5, sticky='w')

        # Espaçamento
        ttk.Label(frame, text="").grid(row=3, column=0, padx=5, pady=5)

        # Qualidade do Vídeo
        ttk.Label(frame, text="Qualidade do Vídeo:", foreground="gray88").grid(row=4, column=0, padx=5, pady=5)
        self.quality_var = ttk.StringVar(value="Original")
        qualities = ["Original", "Melhor", "Bom", "Ruim"]
        ttk.OptionMenu(frame, self.quality_var, *qualities).grid(row=4, column=1, padx=5, pady=5, sticky='ew')

        # Formato de Saída
        ttk.Label(frame, text="Formato de Saída:", foreground="gray88").grid(row=5, column=0, padx=5, pady=5)
        self.format_var = ttk.StringVar(value="mp4")
        formats = ["Mp4", "Original"] #, "mkv", "mov" 
        ttk.OptionMenu(frame, self.format_var, *formats).grid(row=5, column=1, padx=5, pady=5, sticky='ew')

        # Botão de Download
        ttk.Button(frame, text="Baixar", command=self.start_download_thread).grid(row=6, column=1, columnspan=3, padx=10, pady=20, sticky='ew')

    def build_image_tab(self, frame):
        # URL do perfil
        ttk.Label(frame, text="URL do Perfil do Instagram:", foreground="gray88").grid(row=0, column=0, padx=10, pady=10)
        self.image_url_entry = ttk.Entry(frame, width=50)
        self.image_url_entry.grid(row=0, column=1, padx=10, pady=10)

        # Pasta de Download
        ttk.Label(frame, text="Pasta de Download:", foreground="gray88").grid(row=1, column=0, padx=10, pady=10)
        self.image_folder_path = ttk.StringVar(value=self.default_download_folder + '/ContentDownloader/Instagram')
        ttk.Entry(frame, textvariable=self.image_folder_path, width=50).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(frame, text="Procurar", command=self.browse_generic_folder).grid(row=1, column=2, padx=10, pady=10, sticky='w')

        # Botão de Download
        ttk.Button(frame, text="Baixar Imagens", command=self.start_image_download_thread).grid(row=2, column=0, columnspan=3, padx=10, pady=20, sticky='ew')

    def build_generic_tab(self, frame):
        # URL do site
        ttk.Label(frame, text="URL do Site:", foreground="gray88").grid(row=0, column=0, padx=10, pady=10)
        self.generic_url_entry = ttk.Entry(frame, width=50)
        self.generic_url_entry.grid(row=0, column=1, padx=10, pady=10)

        # Pasta de Download
        ttk.Label(frame, text="Pasta de Download:", foreground="gray88").grid(row=1, column=0, padx=10, pady=10)
        self.generic_folder_path = ttk.StringVar(value=self.default_download_folder + '/ContentDownloader/Generic')
        ttk.Entry(frame, textvariable=self.generic_folder_path, width=50).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(frame, text="Procurar", command=self.browse_generic_folder).grid(row=1, column=2, padx=10, pady=10, sticky='w')

        # Botão de Download
        ttk.Button(frame, text="Baixar Conteúdo", command=self.start_generic_download_thread).grid(row=2, column=0, columnspan=3, padx=10, pady=20, sticky='ew')

        # Espaçamento
        ttk.Label(frame, text="").grid(row=3, column=0, padx=10, pady=10)

        # Disclaimer
        disclaimer_text = "Este modo é experimental e pode não funcionar em todos os sites.\nBaixa apenas imagem, fontes e vetores se disponíveis, não faz conversão de nada!"
        disclaimer_label = ttk.Label(frame, text=disclaimer_text, foreground="red", wraplength=400, justify="center")
        disclaimer_label.grid(row=4, column=0, columnspan=3, padx=10, pady=20)

        # Centralizar conteúdo
        frame.grid_rowconfigure(4, weight=1)  # Configura a linha para expandir
        frame.grid_columnconfigure(0, weight=1)  # Centraliza na horizontal

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def browse_image_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.image_folder_path.set(folder_selected)

    def browse_generic_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.generic_folder_path.set(folder_selected)

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

    def start_image_download_thread(self):
        self.download_thread = threading.Thread(target=self.download_images)
        self.download_thread.start()

    def start_generic_download_thread(self):
        self.download_thread = threading.Thread(target=self.download_generic_content)
        self.download_thread.start()

    def check_disk_space(self, folder, required_space):
        free = shutil.disk_usage(folder)
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
        download_folder = self.folder_path.get() + '/Videos'
        quality = self.quality_var.get()

        if not url or not download_folder:
            messagebox.showwarning("Input Error", "Por favor, insira a URL e selecione a pasta de download.")
            return

        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            self.video_title = info_dict.get('title', 'Desconhecido')
            self.total_size = sum([f.get('filesize', 0) for f in info_dict.get('requested_formats', []) if f.get('filesize')]) or info_dict.get('filesize_approx', None) or info_dict.get('filesize', None)

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

    def download_images(self):
        url = self.image_url_entry.get()
        download_folder = self.image_folder_path.get()

        image_downloader = ImageDownloader(url, download_folder)
        image_downloader.download_images()

    def download_generic_content(self):
        url = self.generic_url_entry.get()
        download_folder = self.generic_folder_path.get()

        generic_downloader = GenericDownloader(url, download_folder)
        generic_downloader.download_content()

    def run_download(self, ydl_opts, url):
        self.ydl_process = yt_dlp.YoutubeDL(ydl_opts)
        try:
            self.ydl_process.download([url])
        except yt_dlp.utils.DownloadError:
            if self.cancel_requested.is_set():
                messagebox.showinfo("Cancelado", "O download foi cancelado pelo usuário.")
            else:
                raise

    def ytdl_hook(self, d):
        if self.cancel_requested.is_set():
            self.ydl_process.cache.remove()  # Remove o cache do processo
            os.kill(os.getpid(), signal.SIGINT)  # Envia um sinal de interrupção para parar o processo
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

            # Limpa o cache do processo
            self.ydl_process.cache.remove()

            # Limpa arquivos parciais se houver
            partial_files = [f for f in os.listdir(self.folder_path.get() + '/Videos') if f.startswith(self.video_title) and f.endswith('.part')]
            for f in partial_files:
                os.remove(os.path.join(self.folder_path.get() + '/Videos', f))

    def cancel_download(self):
        self.cancel_requested.set()  # Sinaliza que o cancelamento foi solicitado
        self.is_downloading = False

        if self.ydl_process:
            self.ydl_process.cache.remove()
            os.kill(os.getpid(), signal.SIGINT)  # Interrompe o processo de download forçadamente

        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.join()  # Aguarda a thread terminar
        self.progress_popup.destroy()

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
