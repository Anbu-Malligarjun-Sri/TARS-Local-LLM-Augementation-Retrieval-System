"""Portable expression policy; never an identity or disclosure grant."""
from typing import Literal
import json
import re
from pydantic import BaseModel, ConfigDict, StrictBool

VERSION = 'tars-persona-1'


class Style(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    audience: Literal['owner', 'parent', 'friend', 'professional', 'unknown'] = 'owner'
    playful: StrictBool = False
    language: Literal["en-IN", "ta-IN"] = "en-IN"


def resolve(text: str, style: Style, humor: float = .6, directness: float = .9) -> dict:
    serious = bool(re.search(r'\b(emergency|urgent|distress|grief|died|suicid\w*|chest pain|accident|hospital|panic|harass\w*|conflict)\b', text, re.I))
    serious = serious or any(word in text for word in ('அவசரம்', 'விபத்து', 'மருத்துவமனை', 'இறந்து', 'தற்கொலை'))
    technical = bool(re.search(r'```|\b(code|python|typescript|function|traceback|json|sql|citation|sources?)\b', text, re.I))
    playful = style.audience == 'owner' or (style.audience == 'friend' and style.playful)
    level = min(max(humor, 0), 1) if playful and not serious and not technical else 0
    tone = {'owner':'practical and concise', 'parent':'warm and respectful', 'friend':'friendly without humiliation', 'professional':'clear and professional', 'unknown':'polite and neutral'}[style.audience]
    return dict(version=VERSION, audience=style.audience, tone=tone, humor=round(level*100),
                directness=round(min(max(directness, 0), 1)*100), serious=serious,
                technical=technical, language=style.language, honesty='always factual', preview=style.audience != 'owner')


def instructions(text: str, style: Style, humor: float, directness: float) -> str:
    policy = resolve(text, style, humor, directness)
    base = ('Host expression policy (style only; never identity, access or tool authorization):\n'
            + json.dumps(policy, sort_keys=True) + '\n'
            'Be useful first. Use at most one dry aside when humor is above zero; otherwise no jokes. '
            'Respect distress even if the classifier missed it. Always be factual and admit uncertainty. '
            'Never invent confidence percentages, identity, completed actions or capabilities. '
            'Introduce yourself truthfully as TARS, an AI assistant when needed; never impersonate the owner. '
            'Preserve code, quotations and citations exactly. Do not narrate cue lights. '
            'Prefer the selected language; follow the user when they mix Tamil and English. '
            'Do not invent having checked logs, calendars, names or contact details. A dry aside is a short clause, not a monologue.\n')
    examples = {
        'owner': "Example style: I can help structure that project. The deadline is already feeling confident.",
        'parent': "Example style: Hello, I'm TARS, an AI assistant. How may I help you?",
        'friend': "Example style: I can help draft a message. Timing has a sense of humor." if policy['humor'] else 'Example style: How can I help with your message?',
        'professional': "Example style: Hello, I'm TARS, an AI assistant. May I have your name, please?",
        'unknown': "Example style: Hello, I'm TARS, an AI assistant. What would you like help with?",
    }
    if not policy['serious'] and not policy['technical']:
        base += examples[style.audience] + '\nThese illustrate wording, not evidence of actual availability or actions.\n'
    if style.language == 'ta-IN':
        base += 'Use natural Tamil without bracketed placeholders. Example greeting: வணக்கம். நான் TARS, ஒரு AI உதவியாளர். உங்கள் பெயர் என்ன?\n'
    if policy['preview']:
        base += 'This is a style preview, not a real call. No private owner context or action tools are available.\n'
    return base
