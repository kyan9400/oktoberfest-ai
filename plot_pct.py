import pandas as pd, matplotlib.pyplot as plt
df = pd.read_csv("analysis.csv")
counts = df["Sentiment"].value_counts()
pct = (counts / counts.sum() * 100).round(1)
plt.figure()
counts.plot(kind="bar")
plt.title("Sentiment distribution")
plt.xlabel("Sentiment"); plt.ylabel("Count")
for i, v in enumerate(counts.values):
    plt.text(i, v, f"{v} ({pct.iloc[i]}%)", ha="center", va="bottom")
plt.tight_layout(); plt.savefig("sentiment.png", dpi=120); plt.close()
