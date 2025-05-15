import logging
import subprocess

def execute_docker_compose(folder_path=None, docker_compose_file=None, project_name=None):
    """Ejecuta los comandos de Docker Compose en la carpeta especificada o con el archivo especificado."""
    
    try:
        if docker_compose_file and project_name:
            execute_docker_compose_with_file(docker_compose_file, project_name)
        elif folder_path:
            execute_docker_compose_with_folder(folder_path)
        else:
            logging.error("Error: Debe proporcionar una carpeta o un archivo Docker Compose y un nombre de proyecto.")
            return
        logging.info("Docker Compose ejecutado correctamente.")
    except Exception as e:
        logging.exception(f"Error al ejecutar Docker Compose: {e}")

def execute_docker_compose_with_file(docker_compose_file, project_name):
    """Ejecuta los comandos de Docker Compose en la carpeta especificada."""
    logging.info(f"Ejecutando Docker Compose con archivo: {docker_compose_file}")
    try:
        logging.info(f"Usando archivo Docker Compose: {docker_compose_file}")
        subprocess.run(['docker-compose', '-f', docker_compose_file, '-p', project_name, 'down'], check=True, capture_output=True)
        logging.info(f"Comando 'docker-compose down' ejecutado.")
        result = subprocess.run(['docker-compose', '-f', docker_compose_file, '-p', project_name, 'up', '-d', '--build'], check=True, capture_output=True, text=True)
        logging.info(f"Docker Compose output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar Docker Compose: {e}")
        logging.error(f"Stderr: {e.stderr.decode()}")
    except FileNotFoundError:
        logging.error("Error: 'docker-compose' no se encontró en el sistema.")

def execute_docker_compose_with_folder(folder_path):
    """Ejecuta los comandos de Docker Compose en la carpeta especificada."""
    logging.info(f"Ejecutando Docker Compose en: {folder_path}")
    try:
        subprocess.run(['docker-compose', 'down'], cwd=folder_path, check=True, capture_output=True)
        logging.info(f"Comando 'docker-compose down' ejecutado.")
        result = subprocess.run(['docker-compose', 'up', '-d', '--build'], cwd=folder_path, check=True, capture_output=True, text=True)
        logging.info(f"Comando 'docker-compose up -d --build' ejecutado.")
        logging.info(f"Docker Compose output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar Docker Compose en {folder_path}: {e}")
        logging.error(f"Stderr: {e.stderr.decode()}")
    except FileNotFoundError:
        logging.error("Error: 'docker-compose' no se encontró en el sistema.")