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
        
        if result.returncode == 0:
            if result.stdout:
                logging.info(f"Salida stdout RC:{result.returncode} {' '.join(command)}: {result.stdout}")
            if result.stderr:
                logging.info(f"Salida stderr RC:{result.returncode} {' '.join(command)}: {result.stderr}")
            return True
        else:
            if result.stdout:
                logging.error(f"Salida stdout RC:{result.returncode} {' '.join(command)}: {result.stdout}")
            if result.stderr:
                logging.error(f"Salida stderr RC:{result.returncode} {' '.join(command)}: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar el comando {' '.join(command)}: {e}")
        logging.error(f"Salida del error {' '.join(command)}: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Error: {' '.join(command)} no se encontró en el sistema.")
        return False