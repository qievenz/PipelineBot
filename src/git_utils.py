import subprocess
import logging
from command_manager import execute_command

_git_config_user = None
_git_config_email = None
_git_config_token = None

def configure(user, email, token=None):
    global _git_config_user, _git_config_email, _git_config_token
    if not user or not email:
        logging.error("Falta la configuración de git_user o git_email en config.json")
        print("Falta la configuración de git_user o git_email en config.json. Revisa el log para más detalles.")
        return False
    
    _git_config_user = user
    _git_config_email = email
    _git_config_token = token # Assign global token

    execute_command(["git", "config", "user.email", _git_config_email], cwd=None)
    execute_command(["git", "config", "user.name", _git_config_user], cwd=None)

    logging.info("Usuario y email de Git configurados globalmente para commits.")
    if _git_config_token:
        logging.info("Token de Git configurado globalmente para autenticación.")
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

def git_pull(cwd, repo_name, github_token_api=None, project_email=None, project_user=None, branch_name='main', gitea_url=None):
    """Realiza git pull."""
    try:
        current_user = project_user if project_user else _git_config_user
        current_email = project_email if project_email else _git_config_email
        
        # Temporarily configure user.email and user.name for this specific operation
        if current_user and current_email:
            execute_command(["git", "config", "user.email", current_email], cwd=cwd)
            execute_command(["git", "config", "user.name", current_user], cwd=cwd)

        remote_url = get_remote_url(repo_name, github_token_api, current_user, gitea_url)
        if remote_url:
            # Temporarily change remote origin for this pull operation
            execute_command(['git', 'remote', 'set-url', 'origin', remote_url], cwd=cwd)
            result = execute_command(['git', 'pull', 'origin', branch_name], cwd=cwd)
            return result
        else:
            logging.error("No se pudo obtener la URL remota para git pull.")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar git pull: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        logging.error(f"Error: Git no encontrado. Asegúrate de que Git esté instalado y en el PATH.")
        return False


def git_push(cwd, repo_name, github_token_api=None, project_email=None, project_user=None, branch_name='main', gitea_url=None):
    """Realiza git push."""
    try:
        current_user = project_user if project_user else _git_config_user
        current_email = project_email if project_email else _git_config_email

        # Temporarily configure user.email and user.name for this specific operation
        if current_user and current_email:
            execute_command(["git", "config", "user.email", current_email], cwd=cwd)
            execute_command(["git", "config", "user.name", current_user], cwd=cwd)

        remote_url = get_remote_url(repo_name, github_token_api, current_user, gitea_url)
        if remote_url:
            # Temporarily change remote origin for this push operation
            execute_command(['git', 'remote', 'set-url', 'origin', remote_url], cwd=cwd)
            result = subprocess.run(['git', 'push', 'origin', branch_name], capture_output=True, text=True, check=True, cwd=cwd)
            logging.info(f"Comando ejecutado: git push origin {branch_name}")
            if result.stdout:
                logging.info(f"Salida del comando:\n{result.stdout}")
            if result.stderr:
                logging.error(f"Error del comando:\n{result.stderr}")
            return result.returncode == 0
        else:
            logging.error("No se pudo obtener la URL remota para git push.")
            return False
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
    

def create_github_repo(repo_name, private=False, github_token_api=None):
    """Crea un repositorio en GitHub usando la API."""
    global _git_config_user, _git_config_token

    # Use project-specific token if provided, otherwise fallback to global token
    token_to_use = github_token_api if github_token_api else _git_config_token

    if not _git_config_user or not token_to_use:
        logging.error("Usuario de GitHub o token de API no configurados. Llama a configure() o proporciona github_token_api.")
        return False
    
    try:
        url = f"https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {token_to_use}",
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

def get_remote_url(repo_name, github_token_api=None, owner=None, gitea_url=None):
    """Devuelve la URL remota para un repositorio dado, con credenciales y soporte para Gitea."""
    global _git_config_user, _git_config_token

    # Determine the owner (user) to use in the URL
    actual_owner = owner if owner else _git_config_user
    if not actual_owner:
        logging.error("No se pudo determinar el propietario del repositorio. Faltan el usuario global y el del proyecto.")
        return None

    # Determine the token to use for authentication
    token_to_use = github_token_api if github_token_api else _git_config_token

    if gitea_url:
        if token_to_use:
            return f"https://{actual_owner}:{token_to_use}@{gitea_url}/{actual_owner}/{repo_name}.git"
        else:
            # Fallback for Gitea if token is not provided (e.g., public repo or SSH)
            return f"https://{gitea_url}/{actual_owner}/{repo_name}.git"
    else: # Default to GitHub
        if token_to_use:
            return f"https://x-access-token:{token_to_use}@github.com/{actual_owner}/{repo_name}.git"
        elif _git_config_user: # Fallback to global user if no specific token is provided (rely on credential helper or SSH)
            return f"https://github.com/{actual_owner}/{repo_name}.git"
        else:
            logging.error("No se pudo construir la URL remota para GitHub. Faltan credenciales o usuario propietario.")
            return None

def get_head_hash(cwd):
    """Obtiene el hash del commit HEAD."""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al obtener el hash del HEAD: {e}")
        logging.error(f"Salida del error: {e.stderr}")
        return None