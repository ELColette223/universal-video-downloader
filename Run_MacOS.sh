#!/bin/bash

# Função para mostrar a etapa no terminal
function show_step() {
    if [ "$QUIET_MODE" = false ]; then
        echo -e "\n==== $1 ====\n"
    fi
}

# Caminho para o arquivo que indica a primeira execução
FIRST_RUN_FILE="$HOME/.my_script_first_run"

# Flag de modo silencioso
QUIET_MODE=true

# Verifica se é a primeira execução
if [ ! -f "$FIRST_RUN_FILE" ]; then
    QUIET_MODE=false
    echo -e "\n==== Esta é a primeira vez que executa este script, a primeira inicialização pode demorar até 5 minutos. ====\n"
    touch "$FIRST_RUN_FILE"
fi

# Verifica e instala Homebrew, se necessário
if ! command -v brew &> /dev/null
then
    QUIET_MODE=false
    show_step "Instalando Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Verifica e instala ffmpeg usando Homebrew, se necessário
if ! command -v ffmpeg &> /dev/null
then
    QUIET_MODE=false
    show_step "Instalando ffmpeg"
    brew install ffmpeg
fi

# Verifica e instala Python3, se necessário
if ! command -v python3 &> /dev/null
then
    QUIET_MODE=false
    show_step "Instalando Python3"
    brew install python3
fi

# Instala as bibliotecas Python necessárias
PYTHON_LIBRARIES=(yt-dlp ttkbootstrap configparser instaloader cloudscraper beautifulsoup4 ffmpeg)
DEPENDENCIES_OK=true

for LIBRARY in "${PYTHON_LIBRARIES[@]}"
do
    if ! pip3 show $LIBRARY &> /dev/null
    then
        QUIET_MODE=false
        show_step "Instalando biblioteca Python: $LIBRARY"
        pip3 install $LIBRARY
        if [ $? -ne 0 ]; then
            show_step "Erro ao instalar $LIBRARY"
            DEPENDENCIES_OK=false
        fi
    fi
done

# Verifica se todas as dependências foram instaladas corretamente e executa o script Python
if $DEPENDENCIES_OK; then
    show_step "Todas as dependências estão instaladas. Executando script.py..."
    show_step "NÃO FECHE ESTA JANELA ENQUANTO O SCRIPT ESTIVER SENDO EXECUTADO."
    python3 script.py
else
    show_step "Alguma dependência falhou. Verifique e tente novamente."
fi
