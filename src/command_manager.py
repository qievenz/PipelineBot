import logging
import subprocess
import threading

def log_stream(stream, log_level):
    """Lee un stream línea por línea y lo loguea."""
    for line in iter(stream.readline, ''):
        if line:
            logging.log(log_level, f"  {line.strip()}")
    stream.close()

def execute_command(command, shell=False, cwd=None):
    """Ejecuta un comando del sistema y muestra la salida en tiempo real."""
    try:
        if isinstance(command, str):
            command = command.split()
        cmd_str = ' '.join(command)
        logging.info(f"Ejecutando comando: {cmd_str}")
        logging.info("-" * 40)  # Línea separadora
        
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
        
        # Crear hilos para leer stdout y stderr simultáneamente
        stdout_thread = threading.Thread(target=log_stream, args=(process.stdout, logging.INFO))
        stderr_thread = threading.Thread(target=log_stream, args=(process.stderr, logging.ERROR)) # O logging.INFO si prefieres no marcar todo stderr como error

        stdout_thread.start()
        stderr_thread.start()

        # Esperar a que el proceso termine
        return_code = process.wait()

        # Esperar a que los hilos terminen de leer la salida
        stdout_thread.join()
        stderr_thread.join()
                
        logging.info("-" * 40)  # Línea separadora
        logging.info(f"Comando {cmd_str} finalizado con código: {return_code}")
                
        return return_code == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar el comando {' '.join(command)}: {e}")
        logging.error(f"Salida del error {' '.join(command)}: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Error: {' '.join(command)} no se encontró en el sistema.")
        return False