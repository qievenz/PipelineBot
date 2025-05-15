import json
import os
import logging
from sync_manager import sync_project

config_last_modified = None 

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

def check_config_changes(config_file='config.json'):
    """Verifica si el archivo de configuración ha cambiado."""
    global config_last_modified
    try:
        current_last_modified = os.path.getmtime(config_file)
        
        if config_last_modified is None or current_last_modified > config_last_modified:
            config_last_modified = current_last_modified            
            return True
        else:
            return False 
    except FileNotFoundError:
        logging.error(f"Archivo de configuración no encontrado: {config_file}")
    except Exception as e:
        logging.exception(f"Error al verificar los cambios en la configuración: {e}")
