"""Original guided dialogue for the isolated, unmetered visitor preview."""
import unicodedata

PROMPTS = {
    "en": ["Help me pick a task.", "Remember my project is Firefly.", "What's my project called?"],
    "ta": ["முதலில் எந்த வேலையைச் செய்யலாம்?", "என் திட்டத்தின் பெயர் Firefly. நினைவில் வை.", "என் திட்டத்தின் பெயர் என்ன?"],
    "tanglish": ["Endha velaiya mudhalla seyyalaam?", "En project peru Firefly. Nyabagam vechuko.", "En project peru enna?"],
}

REPLIES = {
    "en": (
        "Pick one task you can finish today. The list can survive the suspense.",
        "I'll remember Firefly for this visit. A small project with excellent lighting.",
        "Your project is called Firefly. Still glowing.",
        "You haven't given me a project name this visit. Try the Firefly example.",
        "I have three scripted scenes. Choose one below to plan a task or try my visit memory.",
    ),
    "ta": (
        "இன்றே முடிக்கக்கூடிய ஒரு வேலையைத் தேர்ந்தெடு. மீதிப் பட்டியலுக்கும் கொஞ்சம் ஓய்வு கிடைக்கட்டும்.",
        "இந்த உரையாடலில் Firefly என்ற பெயரை நினைவில் வைத்துக்கொள்கிறேன். பெயரிலேயே வெளிச்சம் இருக்கிறது.",
        "உன் திட்டத்தின் பெயர் Firefly. இன்னும் மின்னிக்கொண்டுதான் இருக்கிறது.",
        "இந்த உரையாடலில் இன்னும் திட்டத்துக்குப் பெயர் சொல்லவில்லை. Firefly உதாரணத்தை முயன்று பார்.",
        "இங்கே மூன்று மாதிரி உரையாடல்கள் உள்ளன. கீழே ஒன்றைத் தேர்ந்தெடு.",
    ),
    "tanglish": (
        "Innaikku mudikka mudiyura oru velaiya therndhedu. Meedhi list konjam kaathirukkattum.",
        "Indha visit mudiyara varaikkum Firefly-nu nyabagam vechukaren. Perukke nalla velicham.",
        "Un project peru Firefly. Innum minnum.",
        "Indha visit-la innum project peru sollala. Firefly example-a try pannu.",
        "Inga moonu sample conversations irukku. Keezha irundhu onna therndhedu.",
    ),
}


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().replace("’", "'").split()).rstrip(".!?")


def response(message: str, language: str, remembers_firefly: bool) -> tuple[str, bool]:
    """Match the input independently of the selected reply language."""
    message = normalize(message)
    for prompts in PROMPTS.values():
        if message in {normalize(prompts[0]), "plan today"}:
            return REPLIES[language][0], False
        if message == normalize(prompts[1]):
            return REPLIES[language][1], True
        if message == normalize(prompts[2]):
            return REPLIES[language][2 if remembers_firefly else 3], False
    return REPLIES[language][4], False
