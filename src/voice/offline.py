"""On-demand local speech models. PCM and waveforms stay in memory."""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import wave
import re

ROOT = Path(__file__).resolve().parents[2]/'.runtime/speech-models'


@lru_cache(maxsize=2)
def recognizer(language):
    import sherpa_onnx as sherpa
    folder = ROOT/'sherpa-onnx-whisper-tiny'
    if not (folder/'tiny-decoder.int8.onnx').is_file():
        raise FileNotFoundError('Install the Whisper model.')
    return sherpa.OfflineRecognizer.from_whisper(
        encoder=str(folder/'tiny-encoder.int8.onnx'), decoder=str(folder/'tiny-decoder.int8.onnx'),
        tokens=str(folder/'tiny-tokens.txt'),language=language,task='transcribe',num_threads=2)


def transcribe(pcm,language):
    import numpy as np
    if not 3200 <= len(pcm) <= 640000 or len(pcm)%2:
        raise ValueError('Record between 0.1 and 20 seconds at 16 kHz.')
    model = recognizer(language)
    stream = model.create_stream()
    if language == 'ta':
        # Tamil glyphs often require several Whisper vocabulary tokens.
        stream.set_option('max_tokens_per_second','24')
    samples = np.frombuffer(pcm,dtype='<i2').astype('float32') / 32768
    if abs(samples).max()<.002:
        raise ValueError('No audible signal.')
    stream.accept_waveform(16000,samples)
    model.decode_stream(stream)
    return stream.result.text.strip()[:4000]


@lru_cache(maxsize=1)
def synthesizer():
    import sherpa_onnx as sherpa
    folder = ROOT/'vits-piper-en_US-lessac-medium'
    if not (folder/'en_US-lessac-medium.onnx').is_file() or not (ROOT/'lexicon-en-us.txt').is_file():
        raise FileNotFoundError('Install the Piper voice.')
    voice = sherpa.OfflineTtsVitsModelConfig(model=str(folder/'en_US-lessac-medium.onnx'),
            tokens=str(folder/'tokens.txt'),lexicon=str(ROOT/'lexicon-en-us.txt'))
    return sherpa.OfflineTts(sherpa.OfflineTtsConfig(model=sherpa.OfflineTtsModelConfig(vits=voice,num_threads=2)))


@lru_cache(maxsize=1)
def tamil_synthesizer():
    from piper import PiperVoice
    model = ROOT/'tamil-piper/ta_IN-rasa_female-medium.onnx'
    if not model.is_file():
        raise FileNotFoundError('Install the Tamil Piper voice.')
    return PiperVoice.load(model)


def synthesize(text):
    import numpy as np
    if re.search(r'[\u0b80-\u0bff]',text):
        buf = BytesIO()
        with wave.open(buf,'wb') as wav:
            tamil_synthesizer().synthesize_wav(text,wav)
        return buf.getvalue()
    audio = synthesizer().generate(text,sid=0,speed=1)
    if not audio.sample_rate or not len(audio.samples):
        raise ValueError('The local voice could not pronounce this text.')
    buf = BytesIO()
    with wave.open(buf,'wb') as wav:
        wav.setparams((1,2,audio.sample_rate,0,'NONE','not compressed'))
        wav.writeframes((np.clip(audio.samples,-1,1)*32767).astype('<i2').tobytes())
    return buf.getvalue()
