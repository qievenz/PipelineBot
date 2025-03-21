import json
import os
import subprocess
import time
import logging
import schedule
import threading
import sys
import signal
import git_utils
import genai_utils

# Configuración del logging
logging.basicConfig(filename='log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Variable global para indicar si el programa debe detenerse
running = True

def sync_project(config):
    """Sincroniza una carpeta con un repositorio en GitHub."""
    folder_path = config['folder_path']
    repo_name = config['repo_name']
    interval = config['interval']
    private = config.get('private', False)

    logging.info(f"Sincronizando proyecto: {repo_name} en {folder_path}")

    if not os.path.exists(os.path.join(folder_path, ".git")):
        logging.info(f"Inicializando repositorio Git en {folder_path}")
        if not git_utils.execute_command(["git", "init"], cwd=folder_path):
            logging.error(f"Error al inicializar el repositorio Git en {folder_path}")
            return

        if not git_utils.execute_command(["git", "config", "pull.rebase", "true"], cwd=folder_path):
            logging.error(f"Error al configurar pull.rebase en {folder_path}")
            return

    remote_url = git_utils.get_remote_url(repo_name)
    
    if not remote_url:
        logging.error("No se pudo obtener la URL remota.")
        return
    
    try:
        subprocess.check_output(['git', 'ls-remote', remote_url], cwd=folder_path)
    except subprocess.CalledProcessError:  # Repository does not exist
        logging.info(f"El repositorio remoto {remote_url} no existe. Creando...")
        if not git_utils.create_github_repo(repo_name, github_user, github_token, private):
            logging.error(f"Error al crear el repositorio en GitHub para {repo_name}")
            return

    # Agregar el remoto si no existe
    try:
        subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=folder_path)
    except subprocess.CalledProcessError: # Remote 'origin' does not exist
        logging.info(f"Agregando remoto 'origin' a {remote_url}")
        if not git_utils.execute_command(["git", "remote", "add", "origin", remote_url], cwd=folder_path):
            logging.error(f"Error al agregar el remoto 'origin' a {remote_url}")
            return


    def commit_and_push():
        """Realiza el commit y push."""
        try:
            if not git_utils.git_add(cwd=folder_path):
                logging.error(f"Error al ejecutar 'git add .' en {folder_path}")
                return

            diff = git_utils.get_git_diff(cwd=folder_path)
            if diff:
                commit_message = genai_utils.generate_commit_message(diff)
                
                if commit_message:
                    print(f"Mensaje de commit sugerido: {commit_message}")
                else:
                    print("No se pudo generar un mensaje de commit.")
                    commit_message = "Auto commit"
                
                if not git_utils.git_commit(folder_path, commit_message):
                    logging.error(f"Error al ejecutar 'git commit' en {folder_path}")
                    return
                
                if not git_utils.git_pull(cwd=folder_path):
                    logging.error(f"Error al ejecutar 'git pull' en {folder_path}")
                    return
                logging.info(f"Cambios bajados del repositorio {repo_name}")

                if not git_utils.git_push(cwd=folder_path):
                    logging.error(f"Error al ejecutar 'git push' en {folder_path}")
                    return
                logging.info(f"Cambios subidos al repositorio {repo_name}")
            else:
                logging.info(f"No hay cambios para subir en {repo_name}")

        except Exception as e:
            logging.error(f"Error durante el commit y push en {repo_name}: {e}")

    schedule.every(interval).minutes.do(commit_and_push)


def load_config(config_file='config.json'):
    """Carga la configuración desde el archivo JSON."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        logging.error(f"Archivo de configuración no encontrado: {config_file}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error al decodificar el archivo JSON: {config_file}")
        return None

def main():
    """Función principal del programa."""
    global running

    config = load_config()
    if not config:
        print("Error al cargar la configuración.  Revisa el log para más detalles.")
        return

    git_utils.configure(config.get('github_user'), config.get('github_token'))
    genai_utils.configure(config.get('google_api_key'))

    projects = config.get('projects', [])

    for project_config in projects:
        sync_project(project_config)

    while running:
        schedule.run_pending()
        time.sleep(1) 

def signal_handler(sig, frame):
    """Maneja las señales de interrupción (Ctrl+C)."""
    global running
    print("Deteniendo el programa...")
    logging.info("Deteniendo el programa...")
    running = False 
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # kill (en Linux)

    main()