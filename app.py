def format_group_final(age_val, team_val):
    """Formateer na '11A Boys' styl sonder die 'U' tensy dit 'n reeks is."""
    try:
        # Verwyder .0, NAN en enige bestaande 'U' om van voor af te begin
        age_str = str(age_val).upper().replace(".0", "").replace("NAN", "").replace("U", "").strip()
        team_str = str(team_val).upper().replace("NAN", "").strip()
        combined = f"{age_str} {team_str}"
        
        all_nums = re.findall(r'\d+', age_str)
        valid_nums = [n for n in all_nums if len(n) < 4]
        
        if not valid_nums:
            return combined.replace("  ", " ").strip()
        
        # Check vir reeks (bv. 10 - 13)
        if "-" in age_str and len(valid_nums) >= 2:
            age_part = f"{valid_nums[0]} - {valid_nums[1]}"
        else:
            # Net die nommer (bv. 11)
            age_part = f"{valid_nums[0]}"
        
        # Kry die Span (A, B, C)
        team = ""
        for letter in ["A", "B", "C"]:
            if re.search(rf"\b{letter}\b", combined):
                team = letter
                break
                
        # Kry die Geslag
        gender = ""
        if any(x in combined for x in ["GIRL", "DOGTER", "GIRLS"]): gender = "Girls"
        elif any(x in combined for x in ["BOY", "SEUN", "BOYS"]): gender = "Boys"
        
        # Bou die finale string: "11A Boys"
        return f"{age_part}{team} {gender}".strip()
    except:
        return str(age_val)
