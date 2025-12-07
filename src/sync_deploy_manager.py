import os
import subprocess
import logging
import schedule
from docker_manager import execute_docker_compose, is_docker_compose_project_running
import git_utils
import genai_utils

jobs = []

def cancel_jobs():
    """Cancela todas las tareas programadas."""
    global jobs
    for job in jobs:
        schedule.cancel_job(job)
    jobs.clear()
    logging.info("Todas las tareas programadas han sido canceladas.")
    
def sync_project(config):
    """Sincroniza una carpeta con un repositorio en GitHub o Gitea."""
    global jobs
    folder_path = config['folder_path']
    repo_name = config['repo_name']
    interval = config['interval']
    private = config.get('private', False)
    option = config.get('option', 'push')
    docker_compose_file = config.get('docker_compose_file', None)
    docker_compose_project_name = config.get('docker_compose_project_name', None)
    env_file = config.get('env_file', None)
    
    github_token_api = config.get('github_token_api', None)
    github_email = config.get('github_email', None)
    github_user = config.get('github_user', None)
    gitea_url = config.get('gitea_url', None)
    git_branch = config.get('git_branch', 'main') # Default to 'main'

    logging.debug(f"Config for {repo_name}:")
    logging.debug(f"  github_token_api: {'*' * len(github_token_api) if github_token_api else 'None'}") # Mask token
    logging.debug(f"  github_email: {github_email}")
    logging.debug(f"  github_user: {github_user}")
    logging.debug(f"  gitea_url: {gitea_url}")

    logging.info(f"Sincronizando proyecto: {repo_name} en {folder_path}")
    
    if not os.path.exists(folder_path):
        logging.info(f"Creando carpeta {folder_path} para el repositorio {repo_name}")
        try:
            os.makedirs(folder_path)
        except OSError as e:
            logging.error(f"Error al crear la carpeta {folder_path}: {e}")
            return
    if not os.path.exists(os.path.join(folder_path, ".git")):
        logging.info(f"Inicializando repositorio Git en {folder_path}")
        if not git_utils.execute_command(["git", "init"], cwd=folder_path):
            logging.error(f"Error al inicializar el repositorio Git en {folder_path}")
            return

        if not git_utils.execute_command(["git", "config", "pull.rebase", "true"], cwd=folder_path):
            logging.error(f"Error al configurar pull.rebase en {folder_path}")
            return
        
        # Configure the initial branch if the repository is new
        if not git_utils.execute_command(["git", "branch", f"-M", git_branch], cwd=folder_path):
            logging.error(f"Error al configurar la rama inicial a {git_branch} en {folder_path}")
            return


    remote_url = git_utils.get_remote_url(repo_name, github_token_api, github_user, gitea_url)

    if not remote_url:
        logging.error("No se pudo obtener la URL remota.")
        return

    # This part needs to be adapted for Gitea if a dedicated API is used.
    # For now, it assumes the repo exists or creation is handled by git_utils (which currently only supports GitHub API)
    try:
        subprocess.check_output(['git', 'ls-remote', remote_url], cwd=folder_path)
    except subprocess.CalledProcessError:  # Repository does not exist
        logging.info(f"El repositorio remoto {remote_url} no existe. Creando...")
        # This will need to be made generic for Gitea as well, or detect if it's GitHub
        if not gitea_url and not git_utils.create_github_repo(repo_name, private, github_token_api):
            logging.error(f"Error al crear el repositorio en GitHub para {repo_name}")
            return
        elif gitea_url:
            logging.warning("Creación automática de repositorios en Gitea no implementada. Asegúrate de que el repositorio exista.")
            # Assume it exists for now, or log an error if it doesn't and can't be created.
            pass


    # Agregar el remoto si no existe
    try:
        subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=folder_path)
    except subprocess.CalledProcessError: # Remote 'origin' does not exist
        logging.info(f"Agregando remoto 'origin' a {remote_url}")
        if not git_utils.execute_command(["git", "remote", "add", "origin", remote_url], cwd=folder_path):
            logging.error(f"Error al agregar el remoto 'origin' a {remote_url}")
            return


    def commit_and_push():
        """Realiza el commit y push."""
        try:
            if not git_utils.git_add(cwd=folder_path):
                logging.error(f"Error al ejecutar 'git add .' en {folder_path}")
                return

            diff = git_utils.get_git_diff(cwd=folder_path)
            if diff:
                commit_message = genai_utils.generate_commit_message(diff)

                if not commit_message:
                    logging.warning("No se pudo generar un mensaje de commit.")
                    commit_message = "Auto commit"
                
                if "SYNTAX_ERROR" in commit_message:
                    logging.error("Error de sintaxis detectado en el mensaje de commit.")
                    return
                    
                logging.info(f"Commit message: {commit_message}")

                if not git_utils.git_commit(folder_path, commit_message):
                    logging.error(f"Error al ejecutar 'git commit' en {folder_path}")
                    return

                if not git_utils.git_pull(cwd=folder_path, repo_name=repo_name, github_token_api=github_token_api, project_email=github_email, project_user=github_user, branch_name=git_branch, gitea_url=gitea_url):
                    logging.error(f"Error al ejecutar 'git pull' en {folder_path}")
                    return
                logging.info(f"Cambios bajados del repositorio {repo_name}")

                if not git_utils.git_push(cwd=folder_path, repo_name=repo_name, github_token_api=github_token_api, project_email=github_email, project_user=github_user, branch_name=git_branch, gitea_url=gitea_url):
                    logging.error(f"Error al ejecutar 'git push' en {folder_path}")
                    return
                logging.info(f"Cambios subidos al repositorio {repo_name}")
            else:
                logging.info(f"No hay cambios para subir en {repo_name}")

        except Exception as e:
            logging.error(f"Error durante el commit y push en {repo_name}: {e}")
            
def pull_and_deploy():
    """Realiza el pull y despliega con Docker Compose si está habilitado."""
    try:
        initial_head_hash =  git_utils.get_head_hash(cwd=folder_path)
        if not git_utils.git_pull(cwd=folder_path, repo_name=repo_name, github_token_api=github_token_api, project_email=github_email, project_user=github_user, branch_name=git_branch, gitea_url=gitea_url):
            logging.error(f"Error al ejecutar 'git pull' en {folder_path}")
            return
        logging.info(f"Cambios bajados del repositorio {repo_name}")
        
        final_head_hash = git_utils.get_head_hash(cwd=folder_path)
        is_project_running = is_docker_compose_project_running(docker_compose_project_name)
        
        if (initial_head_hash != final_head_hash and docker_compose_file) \
            or (not is_project_running and docker_compose_file):
            logging.info(f"Desplegando cambios en {repo_name}")
            execute_docker_compose(folder_path=folder_path, docker_compose_file=docker_compose_file, project_name=docker_compose_project_name, env_file=env_file)
        else:
            logging.info(f"No hay cambios para desplegar en {repo_name}")
            return
    except Exception as e:
        logging.exception(f"Error durante el pull y despliegue en {repo_name}: {e}")
        
    if option == 'push':
        job = schedule.every(interval).minutes.do(commit_and_push)
        jobs.append(job)
    elif option == 'pull':
        job = schedule.every(interval).minutes.do(pull_and_deploy)
        jobs.append(job)
    elif option == 'push_and_pull':
        job = schedule.every(interval).minutes.do(commit_and_push)
        job2 = schedule.every(interval).minutes.do(pull_and_deploy)
        jobs.append(job)
        jobs.append(job2)
    else:
        logging.error(f"Opción no válida: {option}. Debe ser 'push', 'pull' o 'push_and_pull'.")

    logging.info(f"Tarea programada para {repo_name} cada {interval} minutos.")