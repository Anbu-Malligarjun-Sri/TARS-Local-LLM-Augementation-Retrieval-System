"""Install verified OpenCV Zoo ONNX models in private runtime storage."""
from pathlib import Path
import hashlib
import json
from urllib.request import urlopen


def main():
    folder = Path(__file__).resolve().parents[1] / '.runtime' / 'face-models'
    folder.mkdir(parents=True,exist_ok=True)
    with urlopen('https://api.github.com/repos/opencv/opencv_zoo/commits/main',timeout=30) as r:
        revision = json.load(r)['sha']
    for name,kind in [('face_detection_yunet_2023mar','face_detection_yunet'),('face_recognition_sface_2021dec','face_recognition_sface')]:
        suffix = f'opencv/opencv_zoo/{revision}/models/{kind}/{name}.onnx'
        with urlopen('https://raw.githubusercontent.com/'+suffix,timeout=30) as response:
            pointer = response.read(1024).decode()
        digest = next(line.split(':')[1] for line in pointer.splitlines() if line.startswith('oid sha256:'))
        path = folder / (name+'.onnx')
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==digest:
            continue
        with urlopen('https://media.githubusercontent.com/media/'+suffix,timeout=90) as response:
            data = response.read(50_000_000)
        if hashlib.sha256(data).hexdigest()!=digest:
            raise RuntimeError('Unexpected OpenCV model hash')
        partial = path.with_suffix('.part')
        partial.write_bytes(data)
        partial.replace(path)
        print(name,revision,digest)


if __name__=='__main__':
    main()
