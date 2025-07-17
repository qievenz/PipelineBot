import logging
import subprocess

def execute_command(command, shell=False, cwd=None):
    """Ejecuta un comando del sistema."""
    try:
        if isinstance(command, str):
            command = command.split()
        logging.info(f"Ejecutando comando: {' '.join(command)}")
        result = subprocess.run(command,
                                capture_output=True, 
                                check=True, 
                                cwd=cwd, 
                                shell=shell, 
                                text=True)
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