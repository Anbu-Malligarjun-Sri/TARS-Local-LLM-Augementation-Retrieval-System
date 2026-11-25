"""Install official Sherpa model assets under ignored local storage."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1] / '.runtime' / 'speech-models'
PACKS = [('asr-models', 'sherpa-onnx-whisper-tiny'), ('tts-models', 'vits-piper-en_US-lessac-medium')]


def install_tamil_recognizer():
    """Download only the quantized model and vocabulary from the pinned upstream release."""
    folder = ROOT/'sherpa-onnx-whisper-small'
    folder.mkdir(parents=True,exist_ok=True)
    origin = 'https://huggingface.co/csukuangfj/sherpa-onnx-whisper-small/resolve/8f3c18b358db4d1f2fc1eae49d75cd20989e4309/'
    files = {
        'small-decoder.int8.onnx':(262226114,'acad50b5c782696e91b55914cc5ab4f756f1532f76e22aa6fc615f39fb69a8ee'),
        'small-encoder.int8.onnx':(112442483,'4cbe7b22fa9026b843b60a68640c747de05bafb1a11b57edc0e66c232d9f33a9'),
        'small-tokens.txt':(816730,''),
    }
    for name,(length,digest) in files.items():
        path=folder/name
        if path.is_file() and path.stat().st_size==length:
            with path.open('rb') as saved:
                if not digest or hashlib.file_digest(saved,'sha256').hexdigest()==digest:
                    continue
        with TemporaryDirectory(dir=folder) as staging:
            pending=Path(staging)/name
            with urlopen(origin+name,timeout=120) as response, pending.open('wb') as out:
                shutil.copyfileobj(response,out)
            with pending.open('rb') as downloaded:
                checksum=hashlib.file_digest(downloaded,'sha256').hexdigest()
            if pending.stat().st_size!=length or (digest and checksum!=digest):
                raise RuntimeError('Tamil ASR checksum mismatch')
            pending.replace(path)
            print(name,checksum,flush=True)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    voice = ROOT/'tamil-piper'
    voice.mkdir(exist_ok=True)
    revision = '89e15edafc8b31e66ddf25f2adbe3bd3f20a9496'
    files = {
        'ta_IN-rasa_female-medium.onnx':'1befd7c4034429cecf3143d5eab4810b29833420aedb951bef4092779d074d59',
        'ta_IN-rasa_female-medium.onnx.json':'e49a5f947bfe64bc232d9f900a163b3b771b812780fd8efe0d411a3d8f4b4ee2',
        'README.md':'9018341aeb86a02577ca0d5b30ec428b3fd77fc67dde1b1e056bb0362d057285',
    }
    for filename,digest in files.items():
        path=voice/filename
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==digest:
            continue
        url=f'https://huggingface.co/tinisoft/piper-ta_IN-rasa_female-medium/resolve/{revision}/{filename}'
        with urlopen(url,timeout=90) as response:
            data=response.read(100_000_000)
        if hashlib.sha256(data).hexdigest()!=digest:
            raise RuntimeError('Tamil voice checksum mismatch')
        partial=path.with_suffix('.download')
        partial.write_bytes(data)
        partial.replace(path)
    install_tamil_recognizer()
    lexicon = ROOT/'lexicon-en-us.txt'
    if not lexicon.exists():
        with urlopen('https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/lexicon-en-us.txt',timeout=90) as response:
            data = response.read(40_000_000)
        if not data.strip() or len(data)>=40_000_000:
            raise RuntimeError('Invalid pronunciation lexicon')
        lexicon.write_bytes(data)
    for tag, name in PACKS:
        if (ROOT / name).is_dir():
            continue
        with urlopen('https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/tags/' + tag, timeout=60) as response:
            assets = json.load(response)['assets']
        asset = next(item for item in assets if item['name'] == name + '.tar.bz2')
        with TemporaryDirectory(dir=ROOT) as temp:
            archive = Path(temp) / 'model.tar.bz2'
            with urlopen(asset['browser_download_url'], timeout=90) as response, archive.open('wb') as out:
                shutil.copyfileobj(response, out)
            with archive.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if archive.stat().st_size != asset['size'] or (asset.get('digest') and asset['digest'] != 'sha256:' + digest):
                raise RuntimeError('Model archive verification failed')
            with tarfile.open(archive) as pack:
                for member in pack:
                    if member.name.startswith(name + '/') and member.isfile():
                        pack.extract(member, temp, filter='data')
            (Path(temp) / name).rename(ROOT / name)
            print(name, digest, flush=True)


if __name__ == '__main__':
    main()
