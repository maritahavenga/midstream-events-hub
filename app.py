now = ...
res = []
for _, r in df.iterrows():
    ...
    res.append({
        "r": r,
        "dt": dt,
        "ds": rd
    })

res.sort(key=lambda x: x["dt"])
