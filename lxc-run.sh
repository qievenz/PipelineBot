#!/bin/bash
cd /PipelineBot
if [ ! -f "env/bin/activate" ]; then
    python3 -m venv env
fi
source env/bin/activate
pip install -r requirements.txt
python3 pipeline_bot.py --config '/pipeline/PipelineBot.config.json' --log '/pipeline/pipeline.log' > /dev/null 2>&1
# /PipelineBot/./lxc-run.sh &
# @reboot /PipelineBot/lxc-run.sh >> '/pipeline/pipeline.log' 2>&1
