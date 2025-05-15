import argparse
import os
import time
import logging
import schedule
import sys
import signal
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_path)
from config_manager import check_config_changes, load_config
from sync_deploy_manager import cancel_jobs, sync_project
import genai_utils
import git_utils

# Configuración del logging
log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename='log.txt', level=logging.INFO, format=log_format)
logger = logging.getLogger()
console_handler = logging.StreamHandler()
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

running = True
config_file = 'config.json'

def check_config_and_schedule_jobs():
    """Verifica cambios en la configuración y programa las tareas."""
    config_changed = check_config_changes(config_file)
    
    if config_changed:
        logging.info("Se detectaron cambios en la configuración. Recargando...")
        
        config = load_config()
        if not config:
            logging.error("Error al recargar la configuración.  Usando la configuración anterior.")
            return 

        #Reconfigurar las credenciales
        git_utils.configure(config.get('github_user'), config.get('github_email'), config.get('github_token'))
        genai_utils.configure(config.get('google_api_key'))

        # Volver a programar las tareas
        cancel_jobs()
        projects = config.get('projects', [])
        for project_config in projects:
            sync_project(project_config)
        logging.info("Configuración recargada y tareas reprogramadas.")

def main():
    """Función principal del programa."""
    parser = argparse.ArgumentParser(description="Automatiza el push y pull de repositorios Git y despliega con Docker.")
    parser.add_argument('-c', '--config-check-interval-minutes', type=int, default=1, help='Intervalo en minutos para verificar cambios en la configuración.')
    args = parser.parse_args()

    check_config_and_schedule_jobs()

    schedule.every(args.config_check_interval_minutes).minute.do(check_config_and_schedule_jobs)

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