# -*- coding: utf-8 -*-
import argparse, time, re, json, sys, os
from datetime import datetime
import pandas as pd

def _safe_import(pkg, pip_name=None):
    try:
        return __import__(pkg)
    except Exception:
        import subprocess, sys as _sys
        subprocess.call([_sys.executable, "-m", "pip", "install", pip_name or pkg, "-q"])
        return __import__(pkg)

def get_feeds(keywords=None, feeds=None, lang="de"):
    feeds = list(feeds or [])
    if keywords:
        q = "+OR+".join([re.sub(r"\s+", "+", k) for k in keywords])
        # Google News RSS for keywords
        feeds.append(f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={lang.upper()}&ceid={lang.upper()}:{lang}")
    # Always include DW + Tagesschau unless caller overrides
    if not any("rss.dw.com" in f for f in feeds):
        feeds.append("https://rss.dw.com/rdf/rss-en-all")
    if not any("tagesschau.de" in f for f in feeds):
        feeds.append("https://www.tagesschau.de/xml/rss2")
    return feeds

def fetch_news(max_items=120, feeds=None, keywords=None, lang="de"):
    feedparser = _safe_import("feedparser")
    items=[]
    for url in get_feeds(keywords, feeds, lang):
        try:
            d = feedparser.parse(url)
            for e in d.entries:
                title = (e.get("title") or "").strip()
                desc  = (e.get("summary") or e.get("description") or "").strip()
                txt   = (title + " - " + desc).strip()
                if txt: items.append(txt)
                if len(items) >= max_items: break
        except Exception as ex:
            print(f"[feed err] {url}: {ex}")
        if len(items) >= max_items: break
    # Basic clean + dedup
    clean = []
    seen = set()
    for t in items:
        t = re.sub(r"<[^>]+>", " ", t)           # strip HTML
        t = re.sub(r"\s+", " ", t).strip()
        k = t.lower()
        if k and k not in seen:
            seen.add(k)
            clean.append(t)
    return clean[:max_items]

def analyze(texts, model_name, outdir):
    if not texts:
        print("No texts to analyze."); return
    print(f"Found {len(texts)} items! Running sentiment...")

    try:
        tr = _safe_import("transformers")
        from transformers import pipeline
        analyzer = pipeline("sentiment-analysis", model=model_name, truncation=True)
    except Exception as e:
        print(f"[model load failed -> fallback] {e}")
        from transformers import pipeline
        analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", truncation=True)

    res = analyzer(texts)

    # Normalize labels to POSITIVE / NEGATIVE / NEUTRAL
    labels, scores = [], []
    for r in res:
        label = str(r.get("label","")).upper()
        if "NEU" in label:     label = "NEUTRAL"
        elif "POS" in label:   label = "POSITIVE"
        elif "NEG" in label:   label = "NEGATIVE"
        elif label not in {"POSITIVE","NEGATIVE","NEUTRAL"}:
            # rare models: map to POSITIVE vs NEGATIVE by sign
            label = "POSITIVE" if float(r.get("score",0.5)) >= 0.5 else "NEGATIVE"
        labels.append(label)
        scores.append(round(float(r.get("score",0.0)),3))

    df = pd.DataFrame({"Text": texts, "Sentiment": labels, "Score": scores})

    # Summary
    counts = df["Sentiment"].value_counts()
    total = len(df)
    print("\n--- Summary ---")
    for lab in ["POSITIVE","NEGATIVE","NEUTRAL"]:
        c = int(counts.get(lab,0))
        print(f"{lab}: {c} ({(c/total*100):.0f}%)")

    # Save outdir
    os.makedirs(outdir, exist_ok=True)
    df.to_csv(os.path.join(outdir,"analysis.csv"), index=False, encoding="utf-8-sig")
    with open(os.path.join(outdir,"analysis.json"),"w",encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    # Top snippets
    for lab in ["POSITIVE","NEGATIVE"]:
        top = df[df.Sentiment==lab].sort_values("Score", ascending=False).head(10)
        if not top.empty:
            top.to_csv(os.path.join(outdir, f"top_{lab.lower()}.csv"), index=False, encoding="utf-8-sig")

    # Excel export (auto-width)
    try:
        with pd.ExcelWriter(os.path.join(outdir,"analysis.xlsx"), engine="xlsxwriter") as w:
            df.to_excel(w, index=False, sheet_name="Sentiment")
            ws = w.sheets["Sentiment"]
            for i, c in enumerate(df.columns):
                width = max(12, min(120, int(df[c].astype(str).map(len).max()*1.1)))
                ws.set_column(i, i, width)
    except Exception as e:
        print(f"[excel skipped] {e}")

    # Chart with percentages
    try:
        import matplotlib.pyplot as plt
        counts = df["Sentiment"].value_counts()
        pct = (counts / counts.sum() * 100).round(1)
        plt.figure()
        counts.reindex(["NEUTRAL","NEGATIVE","POSITIVE"]).plot(kind="bar")
        plt.title("Sentiment distribution")
        plt.xlabel("Sentiment"); plt.ylabel("Count")
        for i, v in enumerate(counts.reindex(["NEUTRAL","NEGATIVE","POSITIVE"]).fillna(0).astype(int).values):
            if v>0: plt.text(i, v, f"{v} ({pct.iloc[i]}%)", ha="center", va="bottom")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir,"sentiment.png"), dpi=120)
        plt.close()
    except Exception as e:
        print(f"[chart skipped] {e}")

    print(f"\nSaved to: {outdir}")

def main():
    ap = argparse.ArgumentParser(description="News sentiment analyzer v2")
    ap.add_argument("--source", choices=["news","sample"], default="news")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--feeds", nargs="*")
    ap.add_argument("--keywords", nargs="*", help="Google News keywords, e.g. --keywords Oktoberfest Wiesn")
    ap.add_argument("--lang", default="de")
    ap.add_argument("--model", default="cardiffnlp/twitter-xlm-roberta-base-sentiment")
    ap.add_argument("--outdir", default=f"out-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    args = ap.parse_args()

    if args.source == "sample":
        texts = [
            "Oktoberfest opening day is buzzing with excitement and sunshine!",
            "Long lines at the Wiesn today, but the beer tents are worth it.",
            "Prices feel higher this year at Oktoberfest, not thrilled.",
            "Fantastic live music and great crowd energy at the festival!",
        ]
    else:
        texts = fetch_news(max_items=args.limit, feeds=args.feeds, keywords=args.keywords, lang=args.lang)
        if not texts:
            print("All live sources blocked. Using a tiny local sample.")
            return analyze([
                "Oktoberfest opening day is buzzing with excitement and sunshine!",
                "Long lines at the Wiesn today, but the beer tents are worth it.",
                "Prices feel higher this year at Oktoberfest, not thrilled.",
                "Fantastic live music and great crowd energy at the festival!",
            ], args.model, args.outdir)

    analyze(texts, args.model, args.outdir)

if __name__ == "__main__":
    main()
