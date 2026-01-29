def format_group_final(age_val, team_val):
    """Verhoed U11-U0 deur .0 weg te gooi en slegs reekse met '-' te erken."""
    # 1. Maak skoon: Verwyder .0 en NAN
    age_str = str(age_val).upper().replace(".0", "").replace("NAN", "").strip()
    team_str = str(team_val).upper().replace("NAN", "").strip()
    combined = f"{age_str} {team_str}"
    
    # 2. Soek alle nommers (ignoreer lang Excel-datums)
    all_nums = re.findall(r'\d+', age_str)
    valid_nums = [n for n in all_nums if len(n) < 4]
    
    if not valid_nums:
        return combined.replace("  ", " ").strip()
    
    # 3. Bepaal Ouderdom (Slegs reeks as daar '-' in die teks is)
    if "-" in age_str and len(valid_nums) >= 2:
        age_part = f"U{valid_nums[0]}-U{valid_nums[1]}"
    else:
        # Vat net die eerste nommer (verhoed U11-U0)
        age_part = f"U{valid_nums[0]}"
    
    # 4. Soek Span (A, B, C)
    team = ""
    for letter in ["A", "B", "C"]:
        if re.search(rf"\b{letter}\b", combined):
            team = letter
            break
            
    # 5. Soek Geslag
    gender = ""
    if any(x in combined for x in ["GIRL", "DOGTER"]): gender = "Girls"
    elif any(x in combined for x in ["BOY", "SEUN"]): gender = "Boys"
    
    return f"{age_part}{team} {gender}".strip()
