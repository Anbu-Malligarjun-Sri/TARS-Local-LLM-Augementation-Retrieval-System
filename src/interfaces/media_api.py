"""Paired local media operations. Face labels never grant permissions."""
import asyncio
import base64
from contextlib import closing, contextmanager
from functools import lru_cache
from pathlib import Path
import sqlite3
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, StrictBool
from src.voice.offline import transcribe, synthesize

router = APIRouter(prefix='/api/media')
RUNTIME = Path(__file__).resolve().parents[2]/'.runtime'
face_lock, speech_lock = Lock(), Lock()


@contextmanager
def inference(lock):
    if not lock.acquire(blocking=False):
        raise HTTPException(429,'Local model is busy.')
    try:
        yield
    except (ImportError,FileNotFoundError) as exc:
        raise HTTPException(503,'Install the local media requirements and models.') from exc
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    finally:
        lock.release()


@router.post('/transcribe')
async def recognize_speech(request:Request,language:Literal['en','ta']='en'):
    data = bytearray()
    async for chunk in request.stream():
        if len(data)+len(chunk)>640000:
            raise HTTPException(413,'Recording too long.')
        data.extend(chunk)
    def run():
        with inference(speech_lock):
            return {'text':transcribe(data,language)}
    return await asyncio.to_thread(run)


class Speech(BaseModel):
    text:str = Field(min_length=1,max_length=600)


@router.post('/speak')
def speak(body:Speech):
    with inference(speech_lock):
        return Response(synthesize(body.text),media_type='audio/wav',headers={'Cache-Control':'no-store'})


class Snapshot(BaseModel):
    rgb:str = Field(min_length=147456,max_length=147456)
    consent:StrictBool


class Enrollment(Snapshot):
    name:str = Field(min_length=1,max_length=60)


@lru_cache(maxsize=1)
def models():
    import cv2
    folder = RUNTIME/'face-models'
    detector = folder/'face_detection_yunet_2023mar.onnx'
    recognizer = folder/'face_recognition_sface_2021dec.onnx'
    if not detector.exists() or not recognizer.exists():
        raise FileNotFoundError()
    return cv2.FaceDetectorYN.create(str(detector),'',(192,192)), cv2.FaceRecognizerSF.create(str(recognizer),'')


def feature(body):
    if not body.consent:
        raise HTTPException(403,'Consent is required for this capture.')
    import cv2
    import numpy as np
    raw = base64.b64decode(body.rgb,validate=True)
    if len(raw)!=192*192*3:
        raise ValueError('Invalid RGB frame.')
    image = cv2.cvtColor(np.frombuffer(raw,np.uint8).reshape(192,192,3),cv2.COLOR_RGB2BGR)
    detector,recognizer = models()
    _,faces = detector.detect(image)
    if faces is None or len(faces)!=1:
        raise ValueError('Include exactly one front-facing face in the frame.')
    vector = recognizer.feature(recognizer.alignCrop(image,faces[0])).flatten()
    return vector / max(1e-8,np.linalg.norm(vector))


@contextmanager
def profiles():
    folder = RUNTIME/'biometrics'
    folder.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(folder/'profiles.sqlite3')) as db, db:
        db.execute('PRAGMA secure_delete=ON')
        db.execute('CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,name TEXT UNIQUE COLLATE NOCASE,vector BLOB NOT NULL)')
        yield db


@router.get('/faces')
def list_faces():
    with profiles() as db:
        return [{'id':i,'name':n} for i,n in db.execute('SELECT id,name FROM profiles ORDER BY name')]


@router.post('/faces/enroll',status_code=201)
def enroll(body:Enrollment):
    name=body.name.strip()
    if not name:
        raise HTTPException(422,'Enter a profile name.')
    with inference(face_lock):
        vector = feature(body)
        with profiles() as db:
            if db.execute('SELECT count(*) FROM profiles').fetchone()[0]>=32:
                raise HTTPException(409,'Profile limit reached.')
            try:
                identifier = str(uuid4())
                db.execute('INSERT INTO profiles VALUES(?,?,?)',(identifier,name,vector.astype('<f4').tobytes()))
            except sqlite3.IntegrityError:
                raise HTTPException(409,'That name is enrolled. Remove its profile before replacing it.')
            return {'id':identifier,'name':name}


@router.post('/faces/match')
def match(body:Snapshot):
    import numpy as np
    with inference(face_lock):
        vector = feature(body)
        with profiles() as db:
            ranked = sorted(((float(vector @ np.frombuffer(blob,dtype='<f4')),name) for name,blob in db.execute('SELECT name,vector FROM profiles')),reverse=True)
        if not ranked or ranked[0][0]<.50 or (len(ranked)>1 and ranked[0][0]-ranked[1][0]<.08):
            return {'name':None}
        return {'name':ranked[0][1]}


@router.delete('/faces/{identifier}',status_code=204)
def remove_profile(identifier:UUID):
    with profiles() as db:
        db.execute('DELETE FROM profiles WHERE id=?',(str(identifier),))
    return Response(status_code=204)
