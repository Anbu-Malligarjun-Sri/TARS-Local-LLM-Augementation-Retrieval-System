"""Small supervised script/style router, independent of the chat tokenizer."""
from collections import Counter
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import re

MODEL = Path(__file__).with_name('tanglish_weights.json')
DIM = 2048


def features(text):
    words = re.findall(r'[a-z]+',text.casefold())
    counts = Counter()
    for word in words:
        word = re.sub(r'(.)\1{2,}',r'\1\1',word)
        wrapped = '^'+word+'$'
        for token in [wrapped]+[wrapped[i:i+3] for i in range(len(wrapped)-2)]:
            index = int.from_bytes(hashlib.blake2s(token.encode(),digest_size=2).digest(),'big') % DIM
            counts[index] += 1
    norm = math.sqrt(sum(n*n for n in counts.values())) or 1
    return {i:n/norm for i,n in counts.items()}


@lru_cache
def weights():
    return json.loads(MODEL.read_text(encoding='utf-8'))


def is_tanglish(text):
    vec = features(text)
    return sum(weights()[i]*v for i,v in vec.items()) > .72
