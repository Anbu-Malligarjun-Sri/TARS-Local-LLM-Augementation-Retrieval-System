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


@lru_cache
def parallel_examples():
    corpus = Path(__file__).resolve().parents[2]/'finetuning/tanglish_pairs.tsv'
    return [(features(question),question,meaning,answer)
            for line in corpus.read_text(encoding='utf-8').splitlines()
            for question,meaning,answer in [line.split('\t')]]


def nearby_dialogue(text):
    """Retrieve a parallel demonstration only for closely matching wording."""
    query = features(text)
    scored = [(sum(query.get(i,0)*v for i,v in example.items()),question,meaning,answer)
              for example,question,meaning,answer in parallel_examples()]
    score,question,meaning,answer = max(scored)
    if score < .64:
        return ''
    return (f'Illustrative Tanglish dialogue: {question} (meaning: {meaning}) → {answer}. '
            'Example names and details are fictional. Answer the actual user. ')
