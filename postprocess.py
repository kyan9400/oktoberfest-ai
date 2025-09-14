import pandas as pd, matplotlib.pyplot as plt
df = pd.read_csv("analysis.csv")

# Save nicely formatted Excel
with pd.ExcelWriter("analysis.xlsx", engine="xlsxwriter") as w:
    df.to_excel(w, index=False, sheet_name="Sentiment")
    ws = w.sheets["Sentiment"]
    for i, c in enumerate(df.columns):
        width = max(12, min(120, int(df[c].astype(str).map(len).max()*1.1)))
        ws.set_column(i, i, width)

# Plot counts with percentages
counts = df["Sentiment"].value_counts()
pct = (counts / counts.sum() * 100).round(1)
plt.figure()
counts.plot(kind="bar")
plt.title("Sentiment distribution"); plt.xlabel("Sentiment"); plt.ylabel("Count")
for i, v in enumerate(counts.values):
    plt.text(i, v, f"{v} ({pct.iloc[i]}%)", ha="center", va="bottom")
plt.tight_layout(); plt.savefig("sentiment.png", dpi=120); plt.close()
print("Post-processing done.")
