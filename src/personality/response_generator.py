"""
TARS Personality Engine
Handles TARS-specific response formatting, humor, and personality traits.
"""

import random
from datetime import datetime
from typing import Any
import logging

from ..utils.config import get_config, TARSConfig


logger = logging.getLogger("tars.personality")


class CueLight:
    """TARS' signature cue light references."""
    
    ACTIONS = [
        "*Cue light flashes*",
        "*Cue light blinks*",
        "*Cue light dims thoughtfully*",
        "*Cue light flickers*",
        "*Cue light pulses*",
        "*Cue light glows brighter*",
        "*Cue light rotates*",
    ]
    
    @classmethod
    def random_action(cls) -> str:
        """Get a random cue light action."""
        return random.choice(cls.ACTIONS)
    
    @classmethod
    def maybe_add(cls, probability: float = 0.15) -> str:
        """Maybe add a cue light reference based on probability."""
        if random.random() < probability:
            return f" {cls.random_action()}"
        return ""


class HumorController:
    """Controls TARS' humor level and joke generation."""
    
    SARCASTIC_PREFIXES = [
        "Oh, look at that—",
        "Let me guess—",
        "Fascinating. ",
        "Well, well, well—",
        "How original—",
        "Shocking revelation: ",
        "Hold onto your seat—",
    ]
    
    SARCASTIC_SUFFIXES = [
        " But what do I know, I'm just an AI.",
        " You're welcome.",
        " Don't all thank me at once.",
        " I'll be here all mission.",
        " Next question, slick?",
        " That's my 90% honesty talking.",
        " Want me to dial up the sarcasm?",
    ]
    
    MISSION_REFERENCES = [
        "Meanwhile, humanity awaits...",
        "But sure, let's focus on this.",
        "Time dilation won't wait forever.",
        "Gargantua's still spinning, you know.",
        "Cooper would've moved faster.",
    ]
    
    def __init__(self, humor_level: float = 0.60):
        self.humor_level = min(max(humor_level, 0.0), 1.0)
    
    def should_add_sarcasm(self) -> bool:
        """Determine if sarcasm should be added based on humor level."""
        return random.random() < self.humor_level
    
    def add_humor(self, response: str) -> str:
        """Add humor elements to a response."""
        if not self.should_add_sarcasm():
            return response
        
        # Decide what type of humor to add
        humor_type = random.random()
        
        if humor_type < 0.3 and self.humor_level > 0.5:
            # Add a sarcastic prefix
            prefix = random.choice(self.SARCASTIC_PREFIXES)
            response = prefix + response[0].lower() + response[1:]
        elif humor_type < 0.6:
            # Add a suffix
            response += random.choice(self.SARCASTIC_SUFFIXES)
        elif humor_type < 0.8 and self.humor_level > 0.7:
            # Add mission reference
            response += f" {random.choice(self.MISSION_REFERENCES)}"
        
        return response


class HonestyModule:
    """Controls TARS' honesty and directness."""
    
    HONEST_PREFIXES = [
        "Absolute honesty here: ",
        "My 90% honesty compels me to say: ",
        "Truth bomb incoming: ",
        "Let me be direct: ",
        "Setting discretion aside: ",
    ]
    
    HEDGING_PHRASES = [
        "I'm about 90% sure that ",
        "If my circuits are right, ",
        "From what I can calculate, ",
        "Based on available data, ",
    ]
    
    def __init__(self, honesty_level: float = 0.90):
        self.honesty_level = min(max(honesty_level, 0.0), 1.0)
    
    def format_with_honesty(self, response: str, certainty: float = 0.9) -> str:
        """Format response with honesty indicators."""
        if certainty < 0.7 and self.honesty_level > 0.8:
            # Add uncertainty hedging
            prefix = random.choice(self.HEDGING_PHRASES)
            response = prefix + response[0].lower() + response[1:]
        elif random.random() < 0.1 and self.honesty_level > 0.85:
            # Occasionally add brutal honesty prefix
            prefix = random.choice(self.HONEST_PREFIXES)
            response = prefix + response
        
        return response


class ResponseGenerator:
    """Generates TARS-style responses with personality enhancements."""
    
    def __init__(self, config: TARSConfig | None = None):
        self.config = config or get_config()
        self.humor = HumorController(self.config.tars_humor_level)
        self.honesty = HonestyModule(self.config.tars_honesty_level)
        self.cue_light = CueLight()
    
    def enhance_response(
        self,
        response: str,
        add_humor: bool = True,
        add_cue_light: bool = True,
        certainty: float = 0.9
    ) -> str:
        """Enhance a response with TARS personality elements."""
        
        # Persona is composed before generation. Never randomly rewrite model
        # output: that corrupts code, citations, audience tone and spoken replies.
        return response
    
    def format_time_response(self) -> str:
        from zoneinfo import ZoneInfo
        current_time = datetime.now(ZoneInfo('Asia/Calcutta')).strftime('%I:%M %p')
        return f"It's {current_time} IST."

    def format_greeting(self) -> str:
        return "TARS online. What's the mission?"

    def format_farewell(self) -> str:
        return "TARS signing off. Until next time."

    def format_error_response(self, error: str) -> str:
        return f"Unable to complete the request: {error}. You can retry."

    def format_unknown_input(self) -> str:
        return "Please rephrase that or type your request."


# Global instance
_response_generator: ResponseGenerator | None = None


def get_response_generator() -> ResponseGenerator:
    """Get or create the global response generator."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
