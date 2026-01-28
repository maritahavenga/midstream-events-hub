else:
        # Bou die kaartjies met HTML
        h = """<style>body { background:#008080; font-family:sans-serif; padding:15px; } .card { background:white; padding:20px; border-radius:15px; border-left:10px solid #800000; margin-bottom:15px; box-shadow:0 4px 8px rgba(0,0,0,0.1); } .card-title { color:#800000; font-size:1.2rem; font-weight:bold; margin-top:5px; } .btn { background:#800000 !important; color:white !important; padding:8px 12px; border-radius:8px; text-decoration:none; font-size:0.7rem; display:inline-block; margin-right:5px; margin-top:10px; font-weight:bold; }</style>"""
        
        for _, r in df.iterrows():
            # Kry rou data
            cat_raw = str(r.iloc[0]).strip()
            sport_raw = str(r.iloc[1]).strip()
            age_raw = str(r.iloc[2]).strip()
            raw_dt = str(r.iloc[3]).strip()
            ven_raw = str(r.iloc[4]).strip()
            
            # Formateer Datum
            display_date = r['dt_fixed'].strftime('%d %B %Y') if pd.notnull(r['dt_fixed']) else raw_dt
            
            # Bou Knoppies
            btns = ""
            for i in [5, 6, 7]:
                if i < len(r):
                    val = str(r.iloc[i])
                    if "https://" in val:
                        lbl = "PROGRAMME" if i == 5 else ("TEAM LIST" if i == 6 else "DOCUMENT")
                        btns += f"<a href='{fix_drive_link(val)}' target='_blank' class='btn'>{lbl}</a> "
            
            # Note (Kolom I)
            extra = ""
            if len(r) > 8:
                info_val = str(r.iloc[8])
                if info_val.lower() != 'nan' and info_val.strip() != "":
                    extra = f"<div style='font-size:0.8rem; margin-top:10px; color:#333; border-top:1px solid #eee; padding-top:5px;'><b>Note:</b> {info_val}</div>"

            # Die HTML Kaartjie - Skoon en geskei
            h += f"""
            <div class='card'>
                <div style='font-size:0.75rem; color:#666; text-transform: uppercase; letter-spacing: 1px;'>{cat_raw}</div>
                <div class='card-title'>{sport_raw} {age_raw}</div>
                <div style='font-size:0.9rem; color:#008080; font-weight: 500;'>📅 {display_date}</div>
                <div style='font-size:0.9rem; color:#444;'>📍 {ven_raw}</div>
                {btns}
                {extra}
            </div>
            """
        
        components.html(h, height=2500, scrolling=True)
