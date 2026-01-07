import argparse
from logging.handlers import TimedRotatingFileHandler
import os
import time
import logging
import schedule
import sys
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_path)

from config_manager import check_config_changes, load_config
from sync_deploy_manager import cancel_jobs, sync_project
import genai_utils
import git_utils

parser = argparse.ArgumentParser(description="Automatiza el push y pull de repositorios Git y despliega con Docker.")
parser.add_argument('--config', type=str, default='config.json',
                    help='Ruta al archivo de configuración (ej. config/my_config.json). Por defecto es config.json en el directorio del script.')
parser.add_argument('--logdir', type=str, default='logs',
                    help='Ruta al archivo de log (ej. /app/logs). Por defecto es logs en el directorio del script.')
args = parser.parse_args()

log_format = "%(asctime)s [%(levelname)s] %(message)s"
formatter = logging.Formatter(log_format)
os.makedirs(args.logdir, exist_ok=True)
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(args.logdir, "pipeline.log"),
    when="midnight",         # Rota cada medianoche
    interval=1,              # Cada día
    backupCount=7,           # Mantiene 7 días
    encoding="utf-8",        # Evita problemas con caracteres
    utc=False                # Usa hora local
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

running = True
config_file = args.config
config_file_path = os.path.join(os.path.dirname(__file__), config_file)

def check_config_and_schedule_jobs():
    config_changed = check_config_changes(config_file_path)
    
    if config_changed:
        logging.info("Se detectaron cambios en la configuración. Recargando...")
        
        config = load_config(config_file_path)
        if not config:
            logging.error("Error al recargar la configuración. Usando la configuración anterior.")
            return 

        git_utils.configure(config.get('github_user'), config.get('github_email'), config.get('github_token'))
        genai_utils.configure(config.get('google_api_key'))

        cancel_jobs()
        projects = config.get('projects', [])
        for project_config in projects:
            sync_project(project_config)
        logging.info("Configuración recargada y tareas reprogramadas.")

def signal_handler(sig, frame):
    global running
    print("Deteniendo el programa...")
    logging.info("Deteniendo el programa...")
    running = False
    sys.exit(0)

class ConfigChangeHandler(FileSystemEventHandler):
    def __init__(self, config_filepath):
        super().__init__()
        self.config_filepath = config_filepath
        logging.info(f"Monitoreando cambios en: {self.config_filepath}")

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.config_filepath:
            logging.debug(f"Evento de modificación detectado para: {event.src_path}")
            time.sleep(0.5) 
            check_config_and_schedule_jobs()

def main():

    check_config_and_schedule_jobs()

    observer = Observer()
    event_handler = ConfigChangeHandler(config_file_path)
    observer.schedule(event_handler, path=os.path.dirname(config_file_path), recursive=False)
    observer.start()
    logging.info(f"Watchdog iniciado para monitorear {config_file_path}.")

    try:
        heartbeat_counter = 0
        logging.info(f"Iniciando bucle principal. Tareas programadas: {len(schedule.get_jobs())}")
        while running:
            schedule.run_pending()
            time.sleep(1)
            
            # Log de latido cada 60 segundos para confirmar que el loop está activo
            heartbeat_counter += 1
            if heartbeat_counter >= 60:
                logging.debug(f"Bucle activo. Tareas programadas: {len(schedule.get_jobs())}")
                heartbeat_counter = 0
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()