import logging
import subprocess

def execute_command(command, cwd=None):
    """Ejecuta un comando del sistema."""
    try:
        logging.info(f"Ejecutando comando: {command}")
        result = subprocess.run(command, capture_output=True, check=True, cwd=cwd)
        if result.stdout:
            logging.info(f"Salida del comando {' '.join(command)}: {result.stdout}")
        if result.stderr:
            logging.error(f"Error del comando {' '.join(command)}: {result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar el comando {' '.join(command)}: {e}")
        logging.error(f"Salida del error {' '.join(command)}: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Error: {' '.join(command)} no se encontró en el sistema.")
        return False