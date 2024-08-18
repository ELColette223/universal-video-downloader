import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tkinter import messagebox, Toplevel, Label
import webbrowser
import cloudscraper

class GenericDownloader:
    def __init__(self, url, download_folder):
        self.url = url
        self.download_folder = download_folder
        self.scraper = cloudscraper.create_scraper()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.headers = {"User-Agent": self.user_agent}

    def download_content(self):
        if not self.url or not self.download_folder:
            messagebox.showwarning("Input Error", "Por favor, insira a URL do site e selecione a pasta de download.")
            return

        # Janela temporária informando o download em andamento
        self.show_downloading_message()

        try:
            response = self.try_download(self.url)
            if response.status_code != 200:
                messagebox.showerror("Erro", f"Erro ao acessar o site: Status Code {response.status_code}")
                return

            soup = BeautifulSoup(response.content, "html.parser")
            domain_name = self.extract_domain_name(self.url)

            # Definir diretórios para salvar os arquivos
            image_folder = os.path.join(self.download_folder, domain_name, "imagens")
            vector_folder = os.path.join(self.download_folder, domain_name, "vetores")
            font_folder = os.path.join(self.download_folder, domain_name, "fontes")
            os.makedirs(image_folder, exist_ok=True)
            os.makedirs(vector_folder, exist_ok=True)
            os.makedirs(font_folder, exist_ok=True)

            # Procurar por todas as imagens, SVGs, ícones, arquivos Lottie e fontes
            media_files = []
            for img in soup.find_all("img"):
                src = img.get("src")
                if src and src.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")):
                    media_files.append((src, image_folder))

            for svg in soup.find_all("img", {"src": lambda x: x and x.endswith(".svg")}):
                src = svg.get("src")
                if src:
                    media_files.append((src, vector_folder))

            for icon in soup.find_all("link", {"rel": lambda x: x and "icon" in x}):
                href = icon.get("href")
                if href:
                    media_files.append((href, vector_folder))

            for lottie in soup.find_all("script", {"src": lambda x: x and x.endswith(".json")}):
                src = lottie.get("src")
                if src and "lottie" in src:
                    media_files.append((src, vector_folder))

            for font in soup.find_all("link", {"href": lambda x: x and x.endswith((".woff", ".woff2", ".ttf", ".otf"))}):
                href = font.get("href")
                if href:
                    media_files.append((href, font_folder))

            if not media_files:
                messagebox.showinfo("Nada encontrado", "Nenhuma imagem, SVG, ícone, arquivo Lottie ou fonte foi encontrado no site.")
                return

            # Baixar arquivos de mídia encontrados
            for media, folder in media_files:
                file_name = os.path.join(folder, media.split("/")[-1])
                self.download_file(media, file_name)

            messagebox.showinfo("Sucesso", f"Download dos arquivos de mídia concluído com sucesso!\nSalvo em: {os.path.join(self.download_folder, domain_name)}")
            self.open_download_folder(os.path.join(self.download_folder, domain_name))

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao tentar baixar o conteúdo: {str(e)}")
        finally:
            self.downloading_message.destroy()

    def try_download(self, url):
        """Tenta baixar o conteúdo primeiro com requests, depois com cloudscraper."""
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            else:
                raise Exception("Tentativa com requests falhou, tentando com cloudscraper.")
        except Exception:
            return self.scraper.get(url)

    def download_file(self, url, file_name):
        try:
            response = self.try_download(url)
            if response.status_code == 200:
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar {url}: {str(e)}")

    def extract_domain_name(self, url):
        """Extrai o nome do domínio a partir da URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain.split('.')[-2]

    def show_downloading_message(self):
        """Mostra uma janela temporária enquanto o download está em andamento"""
        self.downloading_message = Toplevel()
        self.downloading_message.title("Download em andamento")
        Label(self.downloading_message, text="Download em andamento, favor aguarde...").pack(padx=20, pady=20)
        self.downloading_message.geometry("300x100")
        self.downloading_message.transient()  # Não aparece na barra de tarefas
        self.downloading_message.grab_set()  # Bloqueia interações com a janela principal
        self.downloading_message.update_idletasks()

    def open_download_folder(self, folder):
        if os.path.isdir(folder):
            webbrowser.open(folder.replace("\\", "/"))  # Corrige barras invertidas
