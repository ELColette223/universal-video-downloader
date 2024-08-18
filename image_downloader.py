import instaloader
import os
from tkinter import messagebox, Toplevel, Label
import webbrowser

class ImageDownloader:
    def __init__(self, url, download_folder):
        self.url = url
        self.download_folder = download_folder
        self.loader = instaloader.Instaloader()

    def download_images(self):

        def open_download_folder(folder):
            if os.path.isdir(folder):
                webbrowser.open(folder.replace("\\", "/"))  # Corrige barras invertidas

        if not self.url or not self.download_folder:
            messagebox.showwarning("Input Error", "Por favor, insira a URL do post e selecione a pasta de download.")
            return

        # Verificar se a URL é do Instagram
        if not self.url.startswith("https://www.instagram.com/"):
            messagebox.showinfo("Atenção", "Parece que você inseriu uma URL que não é do Instagram. Por favor, insira uma URL válida do Instagram.")
            return

        # Verificar se a URL é de um perfil de usuário
        if "/p/" not in self.url and "/reel/" not in self.url and "/stories/" not in self.url:
            messagebox.showinfo("Atenção", "Meu rei, no momento esse script é incapaz de fazer isso. Por favor, insira a URL de um post, reel ou story.")
            return

        # Janela temporária informando o download em andamento
        self.show_downloading_message()

        try:
            if "/stories/" in self.url:
                messagebox.showinfo("Atenção", "No momento, o download de stories não está disponível. Por favor, insira a URL de um post ou reel.")
                return

                # Extrair nome do usuário a partir da URL
                username = self.extract_username(self.url)

                # Criando diretório para armazenar stories
                target_folder = os.path.join(self.download_folder, username, "stories")
                os.makedirs(target_folder, exist_ok=True)

                # Configurar o caminho do diretório
                self.loader.dirname_pattern = target_folder

                # Baixar todas as stories disponíveis do usuário
                self.loader.download_stories(userids=[self.loader.check_profile_id(username)], filename_target="{shortcode}")

                # Corrigir barras invertidas no caminho
                target_folder = target_folder.replace("\\", "/")

                messagebox.showinfo("Sucesso", f"Download das stories concluído com sucesso!\nSalvo em: {target_folder}")
                open_download_folder(target_folder)

            else:
                # Extrair o shortcode da URL
                shortcode = self.extract_shortcode(self.url)

                # Carregar o post
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                author = post.owner_username  # Obtém o nome do autor

                # Criar diretório baseado no nome do autor e shortcode
                target_folder = os.path.join(self.download_folder, author, shortcode)
                os.makedirs(target_folder, exist_ok=True)

                # Configurar o caminho do diretório
                self.loader.dirname_pattern = target_folder

                # Baixar o post
                self.loader.download_post(post, target=target_folder)

                # Apagar o arquivo json.xz gerado
                self.cleanup_metadata_files(target_folder)

                # Corrigir barras invertidas no caminho
                target_folder = target_folder.replace("\\", "/")

                messagebox.showinfo("Sucesso", f"Download do conteúdo do post concluído com sucesso!\nSalvo em: {target_folder}")
                open_download_folder(target_folder)

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao tentar baixar o conteúdo do post: {str(e)}")
        finally:
            self.downloading_message.destroy()

    def extract_shortcode(self, url):
        """Extrai o shortcode da URL do post"""
        if '?' in url:
            url = url.split('?')[0]  # Remove parâmetros adicionais
        return url.rstrip('/').split('/')[-1]

    def extract_username(self, url):
        """Extrai o nome de usuário da URL da story"""
        if '/stories/' in url:
            return url.split('/')[4]
        return None

    def cleanup_metadata_files(self, target_folder):
        """Apaga arquivos json.xz gerados pelo Instaloader"""
        for file in os.listdir(target_folder):
            if file.endswith('.json.xz'):
                try:
                    os.remove(os.path.join(target_folder, file))
                except Exception:
                    pass

    def show_downloading_message(self):
        """Mostra uma janela temporária enquanto o download está em andamento"""
        self.downloading_message = Toplevel()
        self.downloading_message.title("Download em andamento")
        Label(self.downloading_message, text="Download em andamento, favor aguarde...").pack(padx=20, pady=20)
        self.downloading_message.geometry("300x100")
        self.downloading_message.transient()  # Não aparece na barra de tarefas
        self.downloading_message.grab_set()  # Bloqueia interações com a janela principal
        self.downloading_message.update_idletasks()
