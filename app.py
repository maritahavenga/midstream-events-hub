# ---------------- CLEAN CARD RENDERING ----------------
for i in res:
    r, ds = i['r'], i['ds']
    cv, act, age, ven = str(r.iloc[2]).lower(), str(r.iloc[3]), cl(r.iloc[11]), cl(r.iloc[6])
    t_l, i_r = cl(r.iloc[8]), cl(r.iloc[10])

    # --- Age Label Logic ---
    is_sport_card = "sport" in cv or any(x in c_a(act) for x in ["Tennis","Rugby","Hockey","Netball","Athletics"])
    age_lbl = ""
    if age:
        if is_sport_card:
            age_lbl = f"U{age}"
            if "Academics" in sc:
                # Show Grade equivalent only if Academics is present
                age_lbl += f" (Gr {int(age)-6 if int(age)>7 else int(age)+6})"
        else:
            age_lbl = f"Gr {age}"

    title_text = f"{c_a(act)} {age_lbl} {tr(cl(r.iloc[4]), act)}"

    # Search filter
    if sq and sq.lower() not in title_text.lower():
        continue

    # --- CARD ---
    with st.container():
        # Card header
        st.markdown(f"**{title_text}**")

        # Date
        st.markdown(f"📅 **{tr(ds, act)}**")

        # Venue with map link
        if ven:
            map_url = f"https://www.google.com/maps/search/?api=1&query={ven.replace(' ','+')}+Midstream"
            st.markdown(f"📍 [**{tr(ven, act).upper()}**]({map_url})")

        # Notes / Teams
        notes = []
        if t_l and "http" not in t_l.lower():
            notes.append(f"**Teams:** {t_l}")
        if i_r and "http" not in i_r.lower():
            notes.append(f"**Note:** {i_r}")
        for n in notes:
            st.info(n)  # Nice teal info box for each note

        # Buttons (Documents, Assessment, Info)
        b1, b2, b_info = ("Documents", "Assessment", "Information")
        if "afrikaans" in act.lower() or "eerste" in act.lower() or "hooftaal" in act.lower():
            b1, b2, b_info = "Dokumente", "Assessering", "Inligting"
        cols = st.columns(3)
        if "http" in cl(r.iloc[7]).lower():
            cols[0].markdown(f"[{b1}]({cl(r.iloc[7])})")
        if "http" in t_l.lower():
            cols[1].markdown(f"[{b2}]({t_l})")
        if "http" in i_r.lower():
            cols[2].markdown(f"[{b_info}]({i_r})")

        # Divider
        st.markdown("---")
