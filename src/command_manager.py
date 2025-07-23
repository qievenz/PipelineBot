import logging
import subprocess

def execute_command(command, shell=False, cwd=None):
    """Ejecuta un comando del sistema y muestra la salida en tiempo real."""
    try:
        if isinstance(command, str):
            command = command.split()
        logging.info(f"Ejecutando comando: {' '.join(command)}")
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            shell=shell,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Leer stdout y stderr en tiempo real
        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            
            if stdout_line:
                logging.info(f"[{' '.join(command)}] {stdout_line.strip()}")
            if stderr_line:
                logging.info(f"[{' '.join(command)}] {stderr_line.strip()}")
                
            # Verificar si el proceso ha terminado
            if process.poll() is not None:
                # Leer las últimas líneas si quedan
                for line in process.stdout:
                    logging.info(f"[{' '.join(command)}] {line.strip()}")
                for line in process.stderr:
                    logging.info(f"[{' '.join(command)}] {line.strip()}")
                break
                
        return process.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar el comando {' '.join(command)}: {e}")
        logging.error(f"Salida del error {' '.join(command)}: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Error: {' '.join(command)} no se encontró en el sistema.")
        return False