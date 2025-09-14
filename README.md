# Oktoberfest AI

News/RSS sentiment analyzer using HuggingFace Transformers.
- Fetches RSS (DW, Tagesschau, Google News)
- Runs sentiment with XLM-R or German BERT
- Saves CSV/JSON and auto-fit Excel
- Generates a bar chart with % labels

## Quickstart

```bash
# create/activate venv (Windows PowerShell)
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# run (German news with Oktoberfest focus)
python oktoberfest_analyzer.py --source news --limit 120 --keywords Oktoberfest Wiesn --lang de
