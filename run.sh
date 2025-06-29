cd "~/PipelineBot"
if [ ! -f "env/bin/activate" ]; then
    python3 -m venv env
fi
source env/bin/activate
pip install -r requirements.txt
python3 pipeline_bot.py #> /dev/null 2>&1
# ./run.sh &
