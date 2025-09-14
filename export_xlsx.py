import pandas as pd
df = pd.read_csv("analysis.csv")
with pd.ExcelWriter("analysis.xlsx", engine="xlsxwriter") as w:
    df.to_excel(w, index=False, sheet_name="Sentiment")
    ws = w.sheets["Sentiment"]
    for i, c in enumerate(df.columns):
        width = max(12, min(120, int(df[c].astype(str).map(len).max() * 1.1)))
        ws.set_column(i, i, width)
