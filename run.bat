@echo off
cd C:\git\PipelineBot
if not exist env\Scripts\activate.bat (
    python -m venv env
    call env\Scripts\activate.bat
) else (
    call env\Scripts\activate.bat
)

pip install -r requirements.txt
python pipeline_bot.py