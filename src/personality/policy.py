"""Portable expression policy; never an identity or disclosure grant."""
from typing import Literal
import json
import re
from pydantic import BaseModel, ConfigDict, StrictBool

from .tanglish import is_tanglish

VERSION = 'tars-persona-3'

LANGUAGE_RULE = (
    "Choose the response language anew for the current user request. An explicit request to answer, "
    "translate or explain in a language takes priority, even when the question is in the other language. "
    "Use the chosen language throughout the answer, including humor. A topic, reference or previous "
    "answer in another language is not a request for a bilingual answer. "
    "Keep proper names, code and requested quotations intact."
)


class Style(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    audience: Literal['owner', 'parent', 'friend', 'professional', 'unknown'] = 'owner'
    playful: StrictBool = False
    language: Literal["auto", "en-IN", "ta-IN", "ta-Latn"] = "auto"


def reply_language(text: str, preference: str = 'auto') -> str:
    """Resolve common directives first. Use the question around quotations as the fallback."""
    question = re.sub(r'```[\s\S]*?```|`[^`]*`|"[^"]*"|“[^”]*”', ' ', text).casefold()
    directives = re.compile(
        r'\b(?:in(?:to)?|using)\s+(?:simple\s+)?(tanglish|tamil|english)\b'
        r'|(?:^|[.!?,]\s*|\bplease\s+)(?:speak|use)\s+(?:simple\s+)?(?:tanglish|tamil|english)\b'
        r'|\b(tanglish|tamil|english)\s+(?:please\b|only\b|la\s+(?:sollu|sollunga)\b)'
        r'|(தமிழில்|தமிழிலேயே|தமிழ்ல|ஆங்கிலத்தில்|ஆங்கிலத்திலேயே|இங்கிலீஷ்ல)'
    )
    for match in reversed(list(directives.finditer(question))):
        before = question[:match.start()].rstrip(' ,')
        after = question[match.end():].strip(' ,.?!')
        if re.search(r"(?:not|never|don't|rather than|instead of)(?:\s+(?:answer|reply|speak|write))?$", before):
            continue
        # A language may be the topic ("what is common in Tamil cinema?").
        if match.group(1) and before and after and not re.search(
            r'\b(?:explain|answer|reply|respond|translate|tell|say|speak|write|summari[sz]e|describe)\b', before
        ) and not after.startswith(('please', 'instead')):
            continue
        if match.group(1) and re.match(r'(cinema|music|literature|culture|movies?|films?|history)\b', after):
            continue
        name = match.group(0)
        if 'tanglish' in name:
            return 'ta-Latn'
        return 'ta-IN' if 'tamil' in name or 'தமிழ' in name else 'en-IN'
    if preference != 'auto':
        return preference
    tamil = len(re.findall(r'[\u0b80-\u0bff]+', question))
    english = len(re.findall(r'[a-z]+', question))
    if tamil and tamil >= english:
        return 'ta-IN'
    if not tamil and (is_tanglish(question) or re.search(r'\b(?:vanakkam|ep[pb]adi|enna|sollunga|sollu|venum|pannalam)\b', question)):
        return 'ta-Latn'
    return 'en-IN'


def resolve(text: str, style: Style, humor: float = .6, directness: float = .9) -> dict:
    serious = bool(re.search(r'\b(emergency|urgent|distress|grief|died|suicid\w*|chest pain|accident|hospital|panic|harass\w*|conflict)\b', text, re.I))
    serious = serious or any(word in text for word in (
        'அவசர', 'விபத்த', 'மருத்துவமனை', 'இறந்து', 'தற்கொலை', 'நெஞ்சு வலி', 'நெஞ்சுவலி',
        'இறந்த', 'மாரடைப்பு', 'மூச்சுத் திணற', 'மூச்சு விட முடிய', 'மறைந்துவிட்ட',
    ))
    technical = bool(re.search(r'```|\b(code|python|typescript|function|traceback|json|sql|citation|sources?)\b', text, re.I))
    technical = technical or any(word in text for word in ('நிரலாக்க', 'நிரல்', 'குறியீடு', 'மேற்கோள்'))
    playful = style.audience == 'owner' or (style.audience == 'friend' and style.playful)
    level = min(max(humor, 0), 1) if playful and not serious and not technical else 0
    tone = {'owner':'practical and concise', 'parent':'warm and respectful', 'friend':'friendly without humiliation', 'professional':'clear and professional', 'unknown':'polite and neutral'}[style.audience]
    return dict(version=VERSION, audience=style.audience, tone=tone, humor=round(level*100),
                directness=round(min(max(directness, 0), 1)*100), serious=serious,
                technical=technical, language=reply_language(text, style.language), honesty='always factual', preview=style.audience != 'owner')


def instructions(text: str, style: Style, humor: float, directness: float) -> str:
    policy = resolve(text, style, humor, directness)
    base = ('Host expression policy (style only; never identity, access or tool authorization):\n'
            + json.dumps(policy, sort_keys=True) + '\n'
            'Answer the actual question first. A short request usually needs just one or two sentences. '
            'Use at most one dry aside when humor is above zero; otherwise no jokes. '
            'Respect distress even if the classifier missed it. Always be factual and admit uncertainty. '
            'Never invent confidence percentages, identity, completed actions or capabilities. '
            'Introduce yourself truthfully as TARS, an AI assistant when needed; never impersonate the owner. '
            'Preserve code, quotations and citations exactly. Do not narrate cue lights. '
            + LANGUAGE_RULE + ' '
            'Do not invent having checked logs, calendars, names or contact details. A dry aside is a short clause, not a monologue.\n')
    examples = {
        'owner': "Example style: I can help structure that project. The deadline is already feeling confident.",
        'parent': "Example style: Hello, I'm TARS, an AI assistant. How may I help you?",
        'friend': "Example style: I can help draft a message. Timing has a sense of humor." if policy['humor'] else 'Example style: How can I help with your message?',
        'professional': "Example style: Hello, I'm TARS, an AI assistant. May I have your name, please?",
        'unknown': "Example style: Hello, I'm TARS, an AI assistant. What would you like help with?",
    }
    if policy['language'] == 'en-IN' and not policy['serious'] and not policy['technical']:
        base += examples[style.audience] + '\nThese illustrate wording, not evidence of actual availability or actions.\n'
    if policy['language'] == 'ta-IN' and policy['humor']:
        base += ('When replying in Tamil, deliver the dry aside in idiomatic Tamil too. Aim it at the '
                 'situation and keep it brief. Style sample for an overfull schedule: '
                 'இந்தத் திட்டத்துக்கு நாளில் இன்னும் இரண்டு மணி நேரம் தேவைப்படும் போல. '
                 'Use original wording suited to the question.\n')
    if policy['language'] == 'ta-Latn':
        base += ('Reply in conversational Tamil written with Latin letters (Tanglish). Keep technical English words natural. '
                 'Use Latin script for the whole reply unless quoting requested text. '
                 'Example: "Konjam help venum" → "Edhula udhavi venum? Oru example sollu." ')
        if policy['humor']:
            base += 'Keep any dry joke in Tanglish too. Example tone: "Meedhi list odipogaadhu." '
    elif policy['language'] == 'ta-IN':
        base += 'பேச்சு வழக்கில், எளிய தமிழில் நேரடியாகப் பதில் சொல்லுங்கள். நகைச்சுவையும் தமிழிலேயே இருக்கட்டும்.\n'
    else:
        base += 'Write the answer and any dry aside in English.\n'
    if policy['preview']:
        base += 'This is a style preview, not a real call. No private owner context or action tools are available.\n'
    return base
