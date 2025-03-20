import json
import os
import subprocess
import time
import logging
import schedule
import threading
import sys
import signal

# Configuración del logging
logging.basicConfig(filename='log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Variable global para indicar si el programa debe detenerse
running = True

def execute_command(command, cwd=None):
    """Ejecuta un comando del sistema."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=cwd)
        logging.info(f"Comando ejecutado: {' '.join(command)}")
        if result.stdout:
            logging.info(f"Salida del comando:\n{result.stdout}")
        if result.stderr:
            logging.error(f"Error del comando:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar el comando: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logging.error(f"Error: Git no encontrado. Asegúrate de que Git esté instalado y en el PATH.")
        return False

def create_github_repo(repo_name, github_user, github_token, private=False):
    """Crea un repositorio en GitHub usando la API."""
    try:
        url = f"https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"name": repo_name, "private": private, "auto_init": True}

        import requests
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
        logging.info(f"Repositorio '{repo_name}' creado en GitHub.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al crear el repositorio en GitHub: {e}")
        return False
    except Exception as e:
        logging.error(f"Error inesperado al crear el repositorio en GitHub: {e}")
        return False



def sync_project(config, github_user, github_token):
    """Sincroniza una carpeta con un repositorio en GitHub."""
    folder_path = config['folder_path']
    repo_name = config['repo_name']
    interval = config['interval']
    private = config.get('private', False)

    logging.info(f"Sincronizando proyecto: {repo_name} en {folder_path}")

    # Inicializar el repositorio Git si no existe
    if not os.path.exists(os.path.join(folder_path, ".git")):
        logging.info(f"Inicializando repositorio Git en {folder_path}")
        if not execute_command(["git", "init"], cwd=folder_path):
            logging.error(f"Error al inicializar el repositorio Git en {folder_path}")
            return

        # Configurar pull.rebase si es un repositorio nuevo
        if not execute_command(["git", "config", "pull.rebase", "true"], cwd=folder_path):
            logging.error(f"Error al configurar pull.rebase en {folder_path}")
            return

    # Crear el repositorio en GitHub si no existe
    #remote_url = f"https://github.com/{github_user}/{repo_name}.git"
    remote_url = f"https://{github_user}:{github_token}@github.com/{github_user}/{repo_name}.git"
    
    # Verificar si el repositorio remoto ya existe.  Esto es un poco complicado sin usar la API
    # Es mejor no intentar crearlo si ya existe porque la API dará error.
    try:
        subprocess.check_output(['git', 'ls-remote', remote_url], cwd=folder_path)
    except subprocess.CalledProcessError:  # Repository does not exist
        logging.info(f"El repositorio remoto {remote_url} no existe. Creando...")
        if not create_github_repo(repo_name, github_user, github_token, private):
            logging.error(f"Error al crear el repositorio en GitHub para {repo_name}")
            return

    # Agregar el remoto si no existe
    try:
        subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=folder_path)
    except subprocess.CalledProcessError: # Remote 'origin' does not exist
        logging.info(f"Agregando remoto 'origin' a {remote_url}")
        if not execute_command(["git", "remote", "add", "origin", remote_url], cwd=folder_path):
            logging.error(f"Error al agregar el remoto 'origin' a {remote_url}")
            return


    def commit_and_push():
        """Realiza el commit y push."""
        try:
            # Añadir todos los cambios
            if not execute_command(["git", "add", "."], cwd=folder_path):
                logging.error(f"Error al ejecutar 'git add .' en {folder_path}")
                return

            # Comprobar si hay cambios antes de hacer el commit
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=folder_path)
            if result.stdout.strip():
                
                # Hacer commit solo si hay cambios
                if not execute_command(["git", "commit", "-m", "Auto commit"], cwd=folder_path):
                    logging.error(f"Error al ejecutar 'git commit' en {folder_path}")
                    return
                
                # Hacer pull
                if not execute_command(["git", "pull", "origin", "main"], cwd=folder_path):
                    logging.error(f"Error al ejecutar 'git pull' en {folder_path}")
                    return
                logging.info(f"Cambios bajados del repositorio {repo_name}")

                # Hacer push
                if not execute_command(["git", "push", "origin", "main"], cwd=folder_path):
                    logging.error(f"Error al ejecutar 'git push' en {folder_path}")
                    return
                logging.info(f"Cambios subidos al repositorio {repo_name}")
            else:
                logging.info(f"No hay cambios para subir en {repo_name}")

        except Exception as e:
            logging.error(f"Error durante el commit y push en {repo_name}: {e}")

    # Programar la tarea
    schedule.every(interval).seconds.do(commit_and_push)


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
    global running #usamos la variable global running

    config = load_config()
    if not config:
        print("Error al cargar la configuración.  Revisa el log para más detalles.")
        return

    github_user = config.get('github_user')
    github_token = config.get('github_token')

    if not github_user or not github_token:
        logging.error("Falta la configuración de github_user o github_token en config.json")
        print("Falta la configuración de github_user o github_token en config.json.  Revisa el log para más detalles.")
        return

    projects = config.get('projects', []) # obtiene la lista de proyectos

    for project_config in projects:
        sync_project(project_config, github_user, github_token)

    # Bucle principal para ejecutar las tareas programadas
    while running:
        schedule.run_pending()
        time.sleep(1) # Reduce el uso de CPU

def signal_handler(sig, frame):
    """Maneja las señales de interrupción (Ctrl+C)."""
    global running
    print("Deteniendo el programa...")
    logging.info("Deteniendo el programa...")
    running = False  # Indicar que el programa debe detenerse
    sys.exit(0) #sale del programa.


if __name__ == "__main__":
    # Configurar el manejador de señales
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # kill (en Linux)

    main()