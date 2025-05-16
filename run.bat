@echo off
cd C:\git\PipelineBot
if not exist env\Scripts\activate.bat (
    python -m venv env
    call env\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call env\Scripts\activate.bat
)

python pipeline_bot.py -c 10