import logging
import subprocess

def is_docker_compose_project_running(project_name):
    """
    Verifica si algún servicio del proyecto Docker Compose está corriendo.
    Retorna True si al menos un contenedor está activo, False si no.
    """
    try:
        if not project_name:
            logging.error("Error: El nombre del proyecto Docker Compose no esta configurado.")
            return False
        
        logging.info(f"Verificando si el proyecto '{project_name}' está corriendo...")
        result = subprocess.run(
            ['docker', 'compose', '-p', project_name, 'ps', '--status=running'],
            check=True,
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        
        if project_name in output:
            logging.info(f"Servicios en ejecución para el proyecto '{project_name}'.")
            return True
        else:
            logging.info(f"No hay servicios corriendo para el proyecto '{project_name}'.")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error verificando el estado de los servicios Docker Compose: {e}")
        logging.error(f"Salida estándar:\n{e.stdout}")
        logging.error(f"Salida de error:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error("Error: 'docker compose' no se encontró en el sistema.")
        return False

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
    try:# 
        logging.info(f"Deteniendo servicios del proyecto '{project_name}' antes de reiniciar.")
        subprocess.run("docker stop $(docker ps -q) && docker rm $(docker ps -a -q)", shell=True, check=True, capture_output=True)

        subprocess.run(['docker', 'compose', '-f', docker_compose_file, '-p', project_name, 'down'], check=True, capture_output=True)
        logging.info(f"Comando 'docker compose down' ejecutado. Ejecutando build sin caché.")

        # ⛔ Build sin caché
        subprocess.run(['docker', 'compose', '-f', docker_compose_file, '-p', project_name, 'build', '--no-cache'], check=True, capture_output=True)
        logging.info(f"Build sin caché completado. Ejecutando docker compose up.")

        # 🚀 Levantar servicios
        result = subprocess.run(['docker', 'compose', '-f', docker_compose_file, '-p', project_name, 'up', '-d'], check=True, capture_output=True, text=True)
        logging.info(f"Docker Compose output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar Docker Compose: {e}")
        logging.error(f"Salida estándar:\n{e.stdout}")
        logging.error(f"Salida de error:\n{e.stderr}")
    except FileNotFoundError:
        logging.error("Error: 'docker compose' no se encontró en el sistema.")

def execute_docker_compose_with_folder(folder_path):
    """Ejecuta los comandos de Docker Compose en la carpeta especificada."""
    logging.info(f"Ejecutando Docker Compose en: {folder_path}")
    try:
        subprocess.run(['docker', 'compose', 'down'], cwd=folder_path, check=True, capture_output=True)
        logging.info(f"Comando 'docker compose down' ejecutado.")
        result = subprocess.run(['docker', 'compose', 'up', '-d', '--build'], cwd=folder_path, check=True, capture_output=True, text=True)
        logging.info(f"Comando 'docker compose up -d --build' ejecutado.")
        logging.info(f"Docker Compose output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar Docker Compose en {folder_path}: {e}")
        logging.error(f"Salida estándar:\n{e.stdout}")
        logging.error(f"Salida de error:\n{e.stderr}")
    except FileNotFoundError:
        logging.error("Error: 'docker compose' no se encontró en el sistema.")
        
