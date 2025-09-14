# -*- coding: utf-8 -*-
import json, pandas as pd
from transformers import pipeline

texts = []
with open("posts.jsonl","r",encoding="utf-8") as f:
    for line in f:
        try:
            o = json.loads(line)
            title = o.get("title") or ""
            body  = o.get("selftext") or ""
            t = (title + " - " + body).strip()
            if t:
                texts.append(t)
        except json.JSONDecodeError:
            pass

if not texts:
    print("No items parsed from posts.jsonl")
    raise SystemExit(0)

sent = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
res  = sent(texts)

df = pd.DataFrame({
    "Text": texts,
    "Sentiment": [r["label"] for r in res],
    "Score": [round(float(r["score"]),3) for r in res],
})
pd.set_option("display.max_colwidth", None)
print(df)
