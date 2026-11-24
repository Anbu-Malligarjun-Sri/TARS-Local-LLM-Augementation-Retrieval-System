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


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
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
