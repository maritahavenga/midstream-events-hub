# --------------------------------------------------
# Execution
# --------------------------------------------------
st.image("https://midstream-primary.co.za/wp-content/uploads/2025/12/LMCP-Logo-JPEG.jpg", use_container_width=True)
raw_df = load_data()

SA_TIME = pytz.timezone('Africa/Johannesburg')
today = datetime.now(SA_TIME).date()

if st.button("🔄 REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

# SEARCH BAR BO-AAN
search_q = st.text_input("🔍 Search Activity or Age Group:", placeholder="e.g. u13 hockey").lower()

if not raw_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        view = st.radio("View:", ["Upcoming", "Results"], horizontal=True)
    with col2:
        cat = st.selectbox("Category:", ["All", "Sport", "Culture", "Academics"])

    # Filtering Logic
    if view == "Upcoming":
        df = raw_df[raw_df['dt_fixed'].dt.date >= today].sort_values(by='dt_fixed')
    else:
        df = raw_df[raw_df['dt_fixed'].dt.date < today].sort_values(by='dt_fixed', ascending=False)
    
    if cat != "All":
        df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]
    
    if search_q:
        df = df[df.apply(lambda r: search_q in str(r.values).lower(), axis=1)]

    # DISPLAY CARDS
    for _, r in df.iterrows():
        # Kolomme: 1=Activity, 2=Age Group
        sport = str(r.iloc[1])
        age_raw = str(r.iloc[2]).strip()
        age = age_raw if (age_raw.lower() != 'nan' and age_raw != "") else ""
        
        date_str = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else "TBA"
        venue = str(r.iloc[4])
        
        other_btns = ""
        prog_html = ""
        team_html = ""
        note_html = ""

        # Process columns 5 to 8 (Programme, Team, Confirm, Information)
        for idx, lbl in [(5, "PROGRAMME"), (6, "TEAM"), (7, "CONFIRM"), (8, "INFORMATION")]:
            val = str(r.iloc[idx]).strip()
            if val.lower() == 'nan' or not val: continue
            
            link = re.search(r'(https?://[^\s<>"]+)', val)
            if link:
                url = link.group(0)
                btn_tag = f'<a href="{url}" target="_blank" class="btn">{lbl}</a>'
                if lbl == "PROGRAMME": 
                    prog_html = f'<div class="prog-container">{btn_tag}</div>'
                else: 
                    other_btns += btn_tag
            else:
                if lbl == "TEAM":
                    team_html = f'<div class="team-box"><b>TEAMS:</b><br>{val}</div>'
                elif lbl == "INFORMATION":
                    note_html = f'<div class="box"><b>Note:</b><br>{val}</div>'

        # Render Final Card
        st.markdown(f"""
        <div class="card">
            <div style="font-size:0.85rem;color:#666">🗓️ {date_str}</div>
            <div class="t">{sport} {age}</div>
            <div style="font-size:0.85rem;color:#333">📍 {venue}</div>
            {team_html}
            <div class="btn-row">{other_btns}</div>
            {note_html}
            {prog_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No data available. Please check the sheet or filters.")
