import subprocess
import logging
from command_manager import execute_command

_github_user = None
_github_email = None
_github_token = None

def configure(user, email, token):
    global _github_user, _github_email, _github_token
    if not user or not email or not token:
        logging.error("Falta la configuración de github_user o github_token en config.json")
        print("Falta la configuración de github_user o github_token en config.json.  Revisa el log para más detalles.")
        return False
    
    _github_user = user
    _github_email = email
    _github_token = token
    
    execute_command(["git", "config", "user.email", _github_email], cwd=None)
    execute_command(["git", "config", "user.name", _github_user], cwd=None)

    logging.info("Usuario y token de GitHub configurados.")
    return True

def get_git_diff(cwd=None):
    """Obtiene la salida de 'git diff --staged'."""
    try:
        result = subprocess.run(['git', 'diff', '--staged'], capture_output=True, text=True, check=True, cwd=cwd, encoding='utf-8', errors='ignore')
        
        if result.stdout:
            logging.debug(f"Salida del comando:\n{result.stdout}")
        if result.stderr:
            logging.debug(f"Error del comando:\n{result.stderr}")
            
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar 'git diff --staged': {e}")
        return None
    except FileNotFoundError:
        print("Error: 'git' no se encuentra en la ruta del sistema. Asegúrate de que Git esté instalado.")
        return None

def git_pull(cwd):
    """Realiza git pull."""
    try:
        result = subprocess.run(['git', 'pull', 'origin', 'main'], capture_output=True, text=True, check=True, cwd=cwd)
        logging.info(f"Comando ejecutado: git pull origin main")
        if result.stdout:
            logging.info(f"Salida del comando:\n{result.stdout}")
        if result.stderr:
            logging.error(f"Error del comando:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar git pull: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logging.error(f"Error: Git no encontrado. Asegúrate de que Git esté instalado y en el PATH.")
        return False


def git_push(cwd):
    """Realiza git push."""
    try:
        result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True, check=True, cwd=cwd)
        logging.info(f"Comando ejecutado: git push origin main")
        if result.stdout:
            logging.info(f"Salida del comando:\n{result.stdout}")
        if result.stderr:
            logging.error(f"Error del comando:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar git push: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logging.error(f"Error: Git no encontrado. Asegúrate de que Git esté instalado y en el PATH.")
        return False

def git_add(cwd):
    """Realiza git add ."""
    try:
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True, check=True, cwd=cwd)
        logging.info(f"Comando ejecutado: git add .")
        if result.stdout:
            logging.info(f"Salida del comando:\n{result.stdout}")
        if result.stderr:
            logging.error(f"Error del comando:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar git add .: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logging.error(f"Error: Git no encontrado. Asegúrate de que Git esté instalado y en el PATH.")
        return False

def git_commit(cwd, commit_message):
    """Realiza git commit -m."""
    try:
        result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True, check=True, cwd=cwd)
        logging.info(f"Comando ejecutado: git commit -m {commit_message}")
        if result.stdout:
            logging.info(f"Salida del comando:\n{result.stdout}")
        if result.stderr:
            logging.error(f"Error del comando:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar git commit -m {commit_message}: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logging.error(f"Error: Git no encontrado. Asegúrate de que Git esté instalado y en el PATH.")
        return False

def git_status(cwd):
    """Realiza git status --porcelain."""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar 'git status --porcelain': {e}")
        return None
    except FileNotFoundError:
        print("Error: 'git' no se encuentra en la ruta del sistema. Asegúrate de que Git esté instalado.")
        return None
    

def create_github_repo(repo_name, private=False):
    """Crea un repositorio en GitHub usando la API."""
    global _github_user, _github_token

    if not _github_user or not _github_token:
        logging.error("Usuario o token de GitHub no configurados. Llama a configure() primero.")
        return False
    
    try:
        url = f"https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {_github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"name": repo_name, "private": private, "auto_init": True}

        import requests
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
        logging.info(f"Repositorio '{repo_name}' creado en GitHub.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al crear el repositorio en GitHub: {e}")
        return False
    except Exception as e:
        logging.error(f"Error inesperado al crear el repositorio en GitHub: {e}")
        return False

def get_remote_url(repo_name):
    """Devuelve la URL remota para un repositorio dado."""
    global _github_user, _github_token

    if not _github_user or not _github_token:
        logging.error("Usuario o token de GitHub no configurados. Llama a configure() primero.")
        return None

    return f"https://{_github_user}:{_github_token}@github.com/{_github_user}/{repo_name}.git"

def get_head_hash(cwd):
    """Obtiene el hash del commit HEAD."""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al obtener el hash del HEAD: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return None