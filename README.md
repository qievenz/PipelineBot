# PipelineBot

Script de Python para automatizar el ciclo de desarrollo: pull, commit con mensaje generado con IA, push y despliegue con Docker Compose.

```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile main.py
```