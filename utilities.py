# Script for universal utilities

# Strips symbols before sending to TTS Agent
def stripSymbols(s):
    s = s.replace("&",' and ').strip()
    s = s.replace("%",' percent ').strip()
    s = s.replace("-",' ').strip()
    s = s.replace("*",' star ').strip()
    s = s.replace("#",' pound ').strip()
    s = s.replace("@",' at ').strip()
    s = s.replace("'",'').strip()
    return s
    