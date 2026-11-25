"""Capture a small set of directly stated facts from new owner turns."""
import re
import unicodedata

# Predicates are stable across scripts and model providers.
RULES = [
    ('name', r'(?:my name is|call me|en(?:noda)? pe(?:y)?[ar]+u?|என் பெயர்)\s+(.+)'),
    ('lives_in', r'(?:i live in|my home city is|naan vasikkira ooru|என் ஊர்)\s+(.+)'),
    ('lives_in', r'(?:naan|நான்)\s+(.+?)(?:la irukken|ல் வசிக்கிறேன்)'),
    ('works_on', r"(?:i(?: am|'m) working on|my project is|en project|என் திட்டம்)\s+(.+)"),
    ('likes', r'(?:i like|i love|i prefer|my favourite is|my favorite is)\s+(.+)'),
    ('likes', r'(?:enakku|எனக்கு)\s+(.+?)\s+(?:pidikkum|pudikkum|பிடிக்கும்)'),
]
ALIASES = {
    'name': ('name','peru','peyar','paeru','பெயர்'),
    'lives_in': ('live','city','ooru','oor','வசிக்கிறேன்','ஊர்'),
    'works_on': ('project','projects','வேலை','திட்டம்'),
    'likes': ('like','likes','prefer','favorite','favourite','pidikkum','pudikkum','பிடிக்கும்'),
}


def terms(text):
    words = set(re.findall(r'[a-z0-9_]+|[\u0b80-\u0bff]+', unicodedata.normalize('NFC',text).casefold()))
    return words | {key for key,aliases in ALIASES.items() if words.intersection(aliases)}


def assertions(text):
    text = text.strip()
    if any(mark in text for mark in ('?', '"', '“', '”', chr(96))) or re.search(
        r"(?i)\b(?:hypothetical|pretend|example|password|token|secret|pin|do(?:n't| not) (?:save|store|remember)|off the record|keep this private|if|unless)\b",text
    ):
        return []
    result = []
    for part in re.split(r'[.!;\n]+|,\s+|\s+and\s+(?=I |my )',text,flags=re.I):
        for predicate, pattern in RULES:
            match = re.fullmatch(pattern,part.strip(),re.I)
            if match:
                value = match[1].strip()
                if (len(value)<=100 and len(value.split())<=10 and
                    not re.search(r'\b(?:not|never|maybe|either|or|but|isn.t)\b|https?://|@',value,re.I)):
                    result.append((predicate,value))
                break
    return result[:5]
