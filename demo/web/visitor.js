const el = id => document.getElementById(id);
const tabs = typeof BroadcastChannel === "function" ? new BroadcastChannel("companion-visits") : null;
let scenes, visit, turn, deadline = 0, remaining = 0, changing = false, offline = false;

class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

async function api(path, method = "GET", data, signal, scope = visit) {
  const headers = { "X-Demo-Client": "1" };
  if (scope) headers["X-Demo-Visit"] = scope;
  if (data) headers["Content-Type"] = "application/json";
  const result = await fetch("/demo/" + path, {
    method, headers, credentials: "same-origin", cache: "no-store",
    body: data ? JSON.stringify(data) : undefined, signal: signal || AbortSignal.timeout(12000),
  });
  if (!result.ok) {
    const info = await result.json().catch(() => ({}));
    throw new ApiError(result.status, typeof info.detail === "string" ? info.detail : "The request could not be completed.");
  }
  return result;
}

function status(text) { el("status").textContent = text; }
function updateClock() {
  if (!visit) return;
  const seconds = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
  el("timer").textContent = Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0");
  if (!seconds) reset("Visit expired. Start a new visit to try again.");
}

function render() {
  el("welcome").hidden = !!visit;
  el("session").hidden = !visit;
  el("end").hidden = !visit;
  el("end").disabled = changing;
  el("start").disabled = changing || !scenes || offline;
  el("recheck").hidden = !offline;
  el("recheck").disabled = changing;
  el("language").disabled = changing || !!turn;
  const ready = visit && !changing && !turn && remaining > 0 && !offline;
  el("message").disabled = !ready;
  el("send").hidden = !!turn;
  el("send").disabled = !ready || !el("message").value.trim();
  el("stop").hidden = !turn;
  el("stop").disabled = changing || !!turn?.stopped;
  el("quota").textContent = remaining + (remaining === 1 ? " turn left" : " turns left");
  for (const button of el("scenes").children) button.disabled = !ready;
  const state = !turn || turn.stopped ? "idle" : turn.output ? "replying" : "waiting";
  el("robot").dataset.state = state;
  el("state").textContent = { idle: "Idle", waiting: "Waiting", replying: "Replying" }[state];
  updateClock();
}

function reset(message) {
  turn?.stream?.abort();
  turn = null;
  visit = null;
  remaining = 0;
  el("history").replaceChildren();
  el("message").value = "";
  offline = false;
  status(message);
  render();
}

function buttons() {
  const lang = el("language").value;
  el("scenes").replaceChildren(...scenes[lang].map(prompt => {
    const button = document.createElement("button");
    button.type = "button";
    button.lang = { en: "en", ta: "ta", tanglish: "ta-Latn" }[lang];
    button.textContent = prompt;
    button.onclick = () => send(prompt);
    return button;
  }));
  render();
}

function line(author, content, lang) {
  const item = document.createElement("p");
  item.className = author === "You" ? "line user" : "line";
  const label = document.createElement("b");
  label.textContent = author;
  const body = document.createElement("span");
  body.lang = lang || "";
  body.textContent = content;
  item.append(label, body);
  el("history").append(item);
  el("history").scrollTop = el("history").scrollHeight;
  return body;
}

function problem(error) {
  if (error.status === 401 || error.status === 409) {
    reset("Your previous visit has ended or changed. Start again to continue.");
  } else {
    offline = true;
    status(error instanceof ApiError ? error.message : "Connection interrupted. Check the connection to continue.");
  }
}

async function sync(start = false) {
  if (changing) return;
  changing = true;
  render();
  try {
    if (!scenes) { scenes = await (await api("scenes")).json(); buttons(); }
    if (start) await api("visit", "POST");
    const info = await (await api("visit")).json();
    if (visit && visit !== info.visit_id) reset("");
    visit = info.visit_id;
    deadline = Date.now() + info.expires_in_seconds * 1000;
    remaining = info.turns_remaining;
    // Refresh can leave a prepared turn that has no stream consumer.
    turn = info.active_turn ? { id: info.active_turn, recovered: true } : null;
    offline = false;
    status(turn ? "A turn is already open. Stop it to continue." :
      remaining ? "Choose a scene or send a message." : "All five turns are used. You can end this visit.");
  } catch (error) {
    if (!start && !visit && error.status === 401) reset("");
    else problem(error);
  } finally { changing = false; render(); }
}

async function cancelServer(active) {
  if (!active.id) return;
  try { await api("turns/" + active.id + "/stop", "POST", undefined, undefined, active.visit || visit); }
  catch (error) { if (error.status !== 404) throw error; }
}

async function stop() {
  const active = turn;
  if (!active || active.stopped) return;
  active.stopped = true;
  active.stream?.abort();
  status("Stopping…");
  render();
  if (!active.id) return; // send() cancels as soon as the prepare response arrives.
  try {
    await cancelServer(active);
    if (turn === active) status("Stopped. This turn counts toward your visit.");
  } catch (error) { if (turn === active) problem(error); }
  finally { if (turn === active) turn = null; render(); }
}

async function readStream(response, active) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (turn !== active || active.stopped) return;
      buffer += decoder.decode(value, { stream: !done });
      let end;
      while ((end = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        if (!block.startsWith("data: ")) continue;
        const event = JSON.parse(block.slice(6));
        if (event.turn_id !== active.id) throw new Error("Unexpected turn.");
        if (event.type === "end" || event.type === "cancelled") return event.type;
        if (event.type === "chunk" && typeof event.content === "string") {
          if (!active.output) {
            active.output = line("Companion", "", active.lang);
            render();
          }
          active.output.append(document.createTextNode(event.content));
          el("history").scrollTop = el("history").scrollHeight;
        }
      }
      if (done) throw new Error("The stream closed early.");
    }
  } finally { reader.releaseLock(); }
}

async function send(message) {
  if (!visit || changing || turn || !remaining || offline || !message.trim()) return;
  const language = el("language").value;
  const active = { visit, lang: { en: "en", ta: "ta", tanglish: "ta-Latn" }[language] };
  turn = active;
  line("You", message);
  el("message").value = "";
  status("Waiting for companion…");
  render();
  try {
    const info = await (await api("turns", "POST", { message, language })).json();
    active.id = info.id;
    if (turn !== active) return;
    remaining = info.turns_remaining;
    if (active.stopped) {
      await cancelServer(active);
      if (turn === active) { turn = null; status("Stopped. This turn counts toward your visit."); }
      return;
    }
    active.stream = new AbortController();
    const response = await api("turns/" + active.id + "/stream", "POST", undefined,
      AbortSignal.any([active.stream.signal, AbortSignal.timeout(20000)]));
    const terminal = await readStream(response, active);
    if (turn === active && !active.stopped) {
      status(terminal === "cancelled" ? "Reply stopped." : remaining ? "Reply complete." : "All five turns are used.");
    }
  } catch (error) {
    if (turn === active && (!active.stopped || !active.stream)) {
      turn = null;
      problem(error);
    }
  } finally { if (turn === active && !active.stopped) turn = null; render(); }
}

async function endVisit() {
  if (!visit || changing) return;
  changing = true;
  const ended = visit;
  render();
  try {
    await api("visit", "DELETE");
    tabs?.postMessage({ ended });
    reset("Visit ended. Your conversation has been cleared.");
  } catch (error) { problem(error); }
  finally { changing = false; render(); }
}

el("start").onclick = () => sync(true);
el("end").onclick = endVisit;
el("stop").onclick = stop;
el("recheck").onclick = () => sync();
el("language").onchange = () => { if (scenes) buttons(); };
el("message").oninput = render;
el("composer").onsubmit = event => { event.preventDefault(); send(el("message").value.trim()); };
if (tabs) tabs.onmessage = event => { if (event.data?.ended === visit) reset("Visit ended in another tab."); };
window.addEventListener("pageshow", event => { if (event.persisted) { reset(""); sync(); } });
setInterval(updateClock, 1000);
sync();
