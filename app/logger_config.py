import logging
import sys

def setup_logger():
    # Cria o logger principal
    logger = logging.getLogger("DocQueryAI")
    logger.setLevel(logging.DEBUG) # Captura tudo de Debug para cima

    # Formato da mensagem: Data - Nome - Nível - Mensagem
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler 1: Salvar em arquivo
    file_handler = logging.FileHandler("app_debug.log", encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Handler 2: Exibir no terminal (para você ver enquanto desenvolve)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)

    # Adiciona os handlers ao logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

# Instância global para ser usada no projeto
log = setup_logger()