SIMPLE_P = r"\[(\w)\s*-\s*(\w)\]"
COMPOUND_P = r"\[(\w)\s*-\s*(\w)\s*(\w)\s*-\s*(\w)\]"
REGEX_P = r"^let\s+\w+\s+=\s+(.*?)$"
SPACES_P = r"\[(\\s|\\t|\\n|,|\s)+\]"
CLEAN_UP_REGEX= r'(?<!["\'])[\t\n](?!["\'])'
CLEAN_UP_REGEX_TWO = r'''(?:[^ "']|"[^"]*"|'[^']*')+'''