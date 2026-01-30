now = datetime.now(pytz.timezone('Africa/Johannesburg')).date()
res = []

for _, r in df.iterrows():

    cat = str(r.iloc[2]).lower().strip()
    act = str(r.iloc[3]).strip()
    age = cl(r.iloc[11])
    rd  = cl(r.iloc[5])

    # --- DATUM (ROBUST) ---
    dt = pd.to_datetime(rd, dayfirst=True, errors='coerce')
    if pd.isnull(dt):
        dt = datetime(2099, 1, 1)
    elif dt.date() < now:
        continue

    # --- CATEGORY FILTER ---
    if sc:
        if not any(x.lower() in cat for x in sc):
            # allow academics hidden in activity name
            if not (
                "academics" in [x.lower() for x in sc]
                and any(k in act.lower() for k in ["afrikaans", "wiskunde", "hooftaal", "eerste"])
            ):
                continue

    # --- ACTIVITY FILTER (FIXED) ---
    if sa and not any(x.lower() in act.lower() for x in sa):
        continue

    # --- AGE FILTER (SAFE) ---
    if sg and age:
        if not any(v.replace("Gr ", "").replace("U", "") in age for v in sg):
            continue

    res.append({
        "r": r,
        "dt": dt,
        "ds": rd
    })

res.sort(key=lambda x: x["dt"])
