import google.generativeai as genai

MODEL_NAME = 'gemini-1.5-flash'  # O 'gemini-1.5-pro'

def configure(google_api_key, model_name='gemini-1.5-flash'):
    if not google_api_key:
        raise EnvironmentError("La variable GOOGLE_API_KEY no está configurada.  Debes obtener una clave de API de Google AI Studio y configurarla.")

    genai.configure(api_key=google_api_key)
    MODEL_NAME = model_name
    
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

