# -*- coding: utf-8 -*-
import time, json, argparse
import pandas as pd

def try_twitter(limit=30, attempts=2, backoff=5, query=None):
    print("Trying Twitter via snscrape (Python API)...")
    try:
        import snscrape.modules.twitter as sntwitter
    except Exception as e:
        print(f"snscrape.twitter import failed: {e}")
        return []
    q = query or "Oktoberfest OR Wiesn lang:en -filter:replies"
    items=[]
    for attempt in range(1, attempts+1):
        try:
            for i, tw in enumerate(sntwitter.TwitterSearchScraper(q).get_items()):
                if i>=limit: break
                t = getattr(tw, "rawContent", None) or getattr(tw, "content", "")
                if t: items.append(t)
            if items: break
        except Exception as e:
            print(f"[Attempt {attempt}/{attempts}] Twitter error: {e}")
            if attempt < attempts:
                time.sleep(backoff*attempt)
    return items

def try_news(max_items=60, feeds=None):
    print("Using Google/Custom News RSS...")
    try:
        import feedparser
    except ImportError:
        import subprocess, sys as _sys
        subprocess.check_call([_sys.executable, "-m", "pip", "install", "feedparser"])
        import feedparser
    feeds = feeds or [
        "https://news.google.com/rss/search?q=Oktoberfest&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Wiesn&hl=en-US&gl=US&ceid=US:en",
    ]
    items=[]
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries:
                title = (e.get("title") or "").strip()
                desc  = (e.get("summary") or "").strip()
                txt   = (title + " - " + desc).strip()
                if txt: items.append(txt)
                if len(items) >= max_items:
                    return items
        except Exception as ex:
            print(f"Feed error ({url}): {ex}")
    return items

def _batch_sentiment(texts, model_name):
    from transformers import pipeline
    analyzer = pipeline(
        "sentiment-analysis",
        model=model_name,
        truncation=True
    )
    return analyzer(texts)

def analyze(texts, model_name):
    if not texts:
        print("No texts to analyze.")
        return
    print(f"Found {len(texts)} items! Running sentiment...")
    res = _batch_sentiment(texts, model_name)

    # Normalize labels for common multilingual models
    labels = []
    scores = []
    for r in res:
        label = str(r["label"]).upper()
        if "NEG" in label and "POS" not in label:
            label = "NEGATIVE"
        elif "POS" in label and "NEG" not in label:
            label = "POSITIVE"
        labels.append(label)
        scores.append(round(float(r["score"]),3))

    df = pd.DataFrame({"Text": texts, "Sentiment": labels, "Score": scores})

    counts = df["Sentiment"].value_counts().to_dict()
    total = len(df)
    pos = counts.get("POSITIVE", 0)
    neg = counts.get("NEGATIVE", 0)
    print("\n--- Summary ---")
    print(f"POSITIVE: {pos} ({pos/total:.0%}) | NEGATIVE: {neg} ({neg/total:.0%})")

    top_pos = df[df.Sentiment=="POSITIVE"].sort_values("Score", ascending=False).head(3)
    top_neg = df[df.Sentiment=="NEGATIVE"].sort_values("Score", ascending=False).head(3)
    pd.set_option("display.max_colwidth", 140)
    if not top_pos.empty:
        print("\nTop 3 positive:")
        print(top_pos[["Score","Text"]])
    if not top_neg.empty:
        print("\nTop 3 negative:")
        print(top_neg[["Score","Text"]])

    df.to_csv("analysis.csv", index=False, encoding="utf-8-sig")
    with open("analysis.json","w",encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    print("\nSaved: analysis.csv, analysis.json")

    try:
        import matplotlib.pyplot as plt
        counts_sorted = df["Sentiment"].value_counts()
        plt.figure()
        counts_sorted.plot(kind="bar")
        plt.title("Sentiment distribution")
        plt.xlabel("Sentiment")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig("sentiment.png", dpi=120)
        plt.close()
        print("Saved: sentiment.png")
    except Exception as e:
        print(f"Chart error (skipped): {e}")

def main():
    ap = argparse.ArgumentParser(description="Oktoberfest sentiment analyzer")
    ap.add_argument("--source", choices=["twitter","news","sample"], default="news")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--query", type=str, default=None, help="Custom Twitter query")
    ap.add_argument("--feeds", nargs="*", help="Custom RSS feed URLs")
    ap.add_argument("--model", type=str,
        default="distilbert-base-uncased-finetuned-sst-2-english",
        help="HF model id for sentiment (e.g., cardiffnlp/twitter-xlm-roberta-base-sentiment)")
    args = ap.parse_args()

    texts=[]
    if args.source == "twitter":
        texts = try_twitter(limit=args.limit, query=args.query)
        if not texts:
            print("Twitter failed; falling back to news...")
            texts = try_news(max_items=max(args.limit, 40), feeds=args.feeds)
    elif args.source == "news":
        texts = try_news(max_items=max(args.limit, 40), feeds=args.feeds)

    if not texts:
        print("All live sources blocked. Using a tiny local sample.")
        texts = [
            "Oktoberfest opening day is buzzing with excitement and sunshine!",
            "Long lines at the Wiesn today, but the beer tents are worth it.",
            "Prices feel higher this year at Oktoberfest, not thrilled.",
            "Fantastic live music and great crowd energy at the festival!",
        ]
    analyze(texts, args.model)

if __name__ == "__main__":
    main()
