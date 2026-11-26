# Using the local companion

From the project directory on Windows, run `scripts/start-local.ps1` and use the paired browser tab. The sidebar and chat history scroll independently. On narrow screens the sidebar starts collapsed.

## Conversation memory

Try “My name is Maya”, then start a fresh owner conversation and ask “En peru enna?” Open **Memory graph** in the sidebar. Select a node to center its neighborhood, zoom in and drag the background to pan. Selecting a relationship opens its source. Search can bring a node outside the first 61 displayed nodes into view. The facts list supports correction and forgetting.

New owner statements about name, home city, preferences and projects are matched with bounded English, Tamil and Tanglish patterns. When a match is found, one SQL transaction writes the user message, claim, provenance and indexing event. A repeated fact is deduplicated and a new conversational name or city supersedes the previous conversational value. Each claim defaults to owner-only, local-only access. Embedding failure leaves canonical and keyword lookup available. The graph derives from authorized active claims. An existing cloud disclosure grant is still needed to retrieve a fact through cloud routing.

Capture starts with new messages. Previews, prior chat logs and assistant-generated claims are excluded. Complex statements can require a manual entry. To disable capture, set `CAPTURE_CHAT_FACTS=false` in the private backend environment and restart. Use **Personal memory** to edit or forget existing claims. The transcript and older backups have their own retention.

## Tanglish

“Enna panra?” selects Romanized Tamil. Asking “Answer in English” switches that turn. The portable router learns a linear classifier from hashed word and character-trigram features. It was fitted on 108 texts from 36 original parallel dialogue triples. Directives and Tamil script checks take precedence. For closely matching casual owner questions, the prompt includes a bilingual dialogue example. Memory retrieval can add shared relationship terms for spellings such as *peru*, *ooru* and *pidikkum* before embedding lookup.

Retrain the router with `..\.venv\Scripts\python.exe -m scripts.train_tanglish`. It writes the versioned router weights and leaves the base chat model unchanged. Dialects, new slang and Romanized proper names still need broader evaluation. See the [Qwen adapter recipe](../finetuning/QWEN_TANGLISH.md).

## Local voice and face models

The paired desktop provides English and Tamil microphone recognition using Whisper Tiny for English and Whisper Small for Tamil, English synthesis with the Lessac Piper model and Tamil-script synthesis with tinisoft's Rasa Piper model. Open **Voice settings**, select the input language and choose **Record locally with Whisper**. Finish the recording and review the transcript before sending. Local dictation uses Piper for the reply. **Read latest reply with local Piper** reads up to 600 characters. The synthesizer selects Tamil for Tamil-script text and English for Latin-only text, so Tanglish pronunciation varies. The separate browser recognition button requires consent to the browser speech provider.

A generated English voice sample survived the speech round trip. On generated Tamil, Whisper Small recognized the name குமார் but joined it to the preceding word. In another sample it transcribed இன்று as என்று. These checks used generated WAV files. Repeating the name sample through the running HTTP API also lost the end of the name. Human speech, room noise and mixed-language dictation still need testing.

**Face profiles** supports up to 32 consenting named people. Obtain agreement for the specific capture, open the preview and take one centered, front-facing capture. The camera closes after capture. YuNet locates a single face and SFace computes the template. The service retains the name and feature vector in `.runtime/biometrics/profiles.sqlite3`. Treat this file as sensitive and restrict access to the desktop account. Removing a profile deletes its stored template. A photo can resemble its subject, and the similarity thresholds have not been calibrated for a household. The match supplies a possible label only. Device pairing controls access to the assistant.

For a new installation with the existing desktop prerequisites:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements-media.txt
..\.venv\Scripts\python.exe scripts/install_speech_models.py
..\.venv\Scripts\python.exe scripts/install_face_models.py
.\scripts\start-local.ps1
```

Downloads are stored under the ignored runtime directory. The APIs process microphone samples and camera frames in memory. Model installation and live capture are separate actions. Public distribution needs its own license review. Tamil voice attribution: tinisoft, trained on AI4Bharat Rasa by Praveen Srinivasa Varadhan, Ashwin Sankar, Giri Raju and Mitesh M. Khapra, Interspeech 2024. [Tamil model and CC BY 4.0 terms](https://huggingface.co/tinisoft/piper-ta_IN-rasa_female-medium) · [English Piper model](https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/vits.html) · [Sherpa Whisper](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/whisper/index.html) · [OpenCV Zoo recognition pipeline](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)

## Try the visitor preview

From the repository root, run one visitor worker. The paired desktop, LM Studio and GPU are optional for this preview.

```powershell
..\.venv\Scripts\python.exe -m uvicorn demo.api:app --host 127.0.0.1 --port 8091 --no-access-log
```

Open [the visitor preview](http://visitor.localhost:8091/) in a current Edge or Chrome browser on the same computer. Choose **Start visit** and select the Firefly teaching message. After the reply finishes, switch the reply language to Tamil or Tanglish and select the recall message. Try **Stop** halfway through teaching in a fresh visit. The companion remembers the example only if the server finishes its reply. Free text outside the supported examples gets a scripted explanation. The closed set of examples uses zero model inference.

A visit includes five turns in 15 minutes. Stop counts as one turn. Refresh clears the visible transcript and restores the remaining turns and visit memory. Tabs in one browser profile share the visit cookie. End visit clears the example memory and the open transcript in connected tabs. An incognito window or separate browser profile starts an independent visit. A browser timer clears the page when time runs out. The server enforces expiry independently.

The FastAPI app serves only the page and its two explicitly named assets from `demo/web/`. It uses same-origin requests and disables microphone, camera and geolocation in this text preview. The client needs no npm build. A hosting release will require an isolated service identity and deployment configuration. Stop the foreground visitor worker with Ctrl+C.

**Reproduce the checks.** Run `..\.venv\Scripts\python.exe -m pytest tests -q`. For the browser checks, start the visitor worker above. With the existing local Playwright installation and Microsoft Edge, run:

```powershell
$env:NODE_PATH = (Resolve-Path .runtime/browser-qa/node_modules).Path
$env:VISITOR_BROWSER = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
node tests/browser/visitor.cjs
```

On a fresh QA machine, install `playwright-core` into a test-only prefix or provide it on Node's module path. Adjust the browser executable for the machine. The desktop view and phone viewport checks use temporary browser profiles. For rollback, stop this visitor worker. It uses in-memory state and requires no desktop data migration.

## R1 visitor API

Start the isolated visitor process on loopback using the [R0 visitor runbook](COMPANION_R0_RELEASE.md). Keep its existing session cookie, Host and X-Demo-Client headers. Create a turn with `POST /demo/turns` and JSON fields `message` and `language` (`en`, `ta` or `tanglish`). The server returns the turn ID, remaining quota and provider label `scripted-preview`. Use `POST /demo/turns/{id}/stream` for SSE and `POST /demo/turns/{id}/stop` to cancel even before first output. Expiry or ending a visit invalidates access. Each visit admits five turns and one active stream, with four concurrent streams per worker. A stopped turn consumes a slot in the five-turn quota.

This unit exercises isolation, cancellation and admission with fixed sample text and zero paid inference. The next unit is a budget ledger before paid routing, followed by a visitor-safe model benchmark. The private desktop, models, face templates and memory database stay outside the visitor process.
