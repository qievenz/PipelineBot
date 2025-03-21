import os
import subprocess
import google.generativeai as genai

# Configura tu clave de API de Google Generative AI (Gemini)
#  Asegúrate de que esta clave esté almacenada de forma segura,
#  por ejemplo, como una variable de entorno.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise EnvironmentError("La variable de entorno GOOGLE_API_KEY no está configurada.  Debes obtener una clave de API de Google AI Studio y configurarla.")

genai.configure(api_key=GOOGLE_API_KEY)

# El modelo que se usará.  'gemini-1.5-flash' es rápido y económico.
#  'gemini-1.5-pro' es más preciso pero más lento y costoso.
MODEL_NAME = 'gemini-1.5-flash'  # O 'gemini-1.5-pro'

def get_git_diff():
    """
    Obtiene la salida de 'git diff --staged' para ver los cambios preparados.

    Returns:
        str: La salida de 'git diff --staged'.  Retorna None si hay un error
             al ejecutar el comando.
    """
    try:
        result = subprocess.run(['git', 'diff', '--staged'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar 'git diff --staged': {e}")
        return None
    except FileNotFoundError:
        print("Error: 'git' no se encuentra en la ruta del sistema. Asegúrate de que Git esté instalado.")
        return None


def generate_commit_message(diff, model_name=MODEL_NAME):
    """
    Genera un mensaje de commit usando Google AI Studio, dado el diff.

    Args:
        diff (str): La salida de 'git diff --staged'.
        model_name (str): El nombre del modelo de Gemini a utilizar (ej. 'gemini-1.5-flash', 'gemini-1.5-pro').

    Returns:
        str: El mensaje de commit generado.  Retorna None si hay un error.
    """

    if not diff:
        print("No hay cambios preparados (staged). No se puede generar un mensaje de commit.")
        return None

    model = genai.GenerativeModel(model_name)

    prompt = f"""
    Eres un asistente experto en generar mensajes de commit concisos y descriptivos
    para proyectos de Git.  Analiza el siguiente diff y genera un mensaje de
    commit de no más de 50 caracteres que resuma los cambios realizados. Usa la
    convención de mensajes de commit de Angular (tipo(scope): descripcion).
    Si el scope no es obvio, omítelo. Ejemplos de tipos: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.

    Diff:
    ```
    {diff}
    ```

    Mensaje de commit:
    """

    try:
        response = model.generate_content(prompt)
        commit_message = response.text.strip()

        # Clean up commit message (remove quotes, etc.)
        commit_message = commit_message.replace('"', '')
        commit_message = commit_message.replace("'", '')

        # Limit to 50 characters after cleanup.
        commit_message = commit_message[:50]

        return commit_message
    except Exception as e:
        print(f"Error al generar el mensaje de commit: {e}")
        return None


def create_commit(commit_message):
    """
    Crea un commit con el mensaje dado.

    Args:
        commit_message (str): El mensaje de commit.
    """
    try:
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print(f"Commit creado con el mensaje: {commit_message}")
    except subprocess.CalledProcessError as e:
        print(f"Error al crear el commit: {e}")


def main():
    """
    Función principal para generar y crear un commit.
    """
    diff = get_git_diff()

    if diff:
        commit_message = generate_commit_message(diff)

        if commit_message:
             print(f"Mensaje de commit sugerido: {commit_message}")
             #Preguntar al usuario si quiere usar este mensaje de commit
             answer = input("¿Quieres usar este mensaje de commit? (y/n): ")
             if answer.lower() == "y":
                 create_commit(commit_message)
             else:
                 print("Commit cancelado.")
        else:
            print("No se pudo generar un mensaje de commit.")
    else:
        print("No hay cambios para commitear.")



if __name__ == "__main__":
    main()