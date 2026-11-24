"""Fit the local subword language router on original, parallel examples."""
import json
import math
from pathlib import Path
from random import Random
from src.personality.tanglish import DIM, MODEL, features


def main():
    corpus = Path(__file__).resolve().parents[1]/'finetuning/tanglish_pairs.tsv'
    examples = []
    for line in corpus.read_text(encoding='utf-8').splitlines():
        ta,en,answer = line.split('\t')
        examples.extend([(features(ta),1),(features(en),0),(features(answer),1)])
    w = [0.0]*DIM
    rng = Random(13)
    for _ in range(65):
        rng.shuffle(examples)
        for vector,label in examples:
            score = sum(w[i]*v for i,v in vector.items())
            error = label - 1/(1+math.exp(-score))
            for i,v in vector.items():
                w[i] += .35*(error*v-.0002*w[i])
    MODEL.write_text(json.dumps([round(x,5) for x in w])+'\n',encoding='utf-8')
    print(f'Fitted {DIM} weights on {len(examples)} labeled texts.')


if __name__=='__main__':
    main()
