const TYPES = {
  CONNECTED_SUCCESS: "conversation.connected.success",
  CONNECTED_FAIL: "conversation.connected.fail",
  CONNECTED_CLOSE: "conversation.connected.close",
  CONNECTED_WARNING: "conversation.connected.warning",
  INSUFFICIENT_BALANCE: "conversation.connected.insufficient_balance",

  REALTIME_SESSION_CREATED: "realtime.session.created",
  REALTIME_SESSION_UPDATED: "realtime.session.updated",

  REALTIME_SPEECH_STARTED: "realtime.input_audio_buffer.speech_started",
  REALTIME_SPEECH_STOPPED: "realtime.input_audio_buffer.speech_stopped",

  REALTIME_CONVERSATION_ITEM_COMPLETED:
    "realtime.conversation.item.input_audio_transcription.completed",

  REALTIME_RESPONSE_AUDIO_TRANSCRIPT_DELTA:
    "realtime.response.audio_transcript.delta",

  REALTIME_RESPONSE_AUDIO_TRANSCRIPT_DONE:
    "realtime.response.audio_transcript.done",

  REALTIME_RESPONSE_AUDIO_DONE:
    "realtime.response.audio.done",

  WEBRTC_OFFER: "webrtc.signaling.offer",
  WEBRTC_ANSWER: "webrtc.signaling.answer",
  WEBRTC_ICE: "webrtc.signaling.iceCandidate",

  INPUT_AUDIO_APPEND: "realtime.input_audio_buffer.append",
};

const DEFAULT_HARD_LIMIT_MS = 3 * 60 * 1000;
const DEFAULT_WRAP_UP_MS = 2 * 60 * 1000;
const TRANSCRIPT_POST_URL = "http://127.0.0.1:5000/transcript";

const state = {
  ws: null,
  wsUrl: null,
  sessionConfig: null,
  peer: null,
  mediaStream: null,
  audioContext: null,
  processor: null,
  processorSource: null,
  transcriptStreamingNode: null,
  transcriptBufferById: new Map(),
  transcriptMessages: [],
  transcriptSent: false,
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
  isStarting: false,
  meetingActive: false,
  meetingStartedAt: null,
  meetingTimer: null,
  micEnabled: true,
  wrapUpPromptSent: false,
  hardStopTriggered: false,
  hardLimitMs: DEFAULT_HARD_LIMIT_MS,
  wrapUpMs: DEFAULT_WRAP_UP_MS,
  pendingEndAfterAudio: false,
  endingMessageSent: false,
};

const els = {
  transcriptPanel: document.getElementById("transcriptPanel"),
  transcriptToggle: document.getElementById("transcriptToggle"),
  fullscreenBtn: document.getElementById("fullscreenBtn"),

  companyLabel: document.getElementById("companyLabel"),
  roleLabel: document.getElementById("roleLabel"),

  clockTime: document.getElementById("clockTime"),
  callBadge: document.getElementById("callBadge"),
  liveDot: document.getElementById("liveDot"),

  statusLabel: document.getElementById("statusLabel"),
  statusDot: document.getElementById("statusDot"),

  micBtn: document.getElementById("micBtn"),
  micIcon: document.getElementById("micIcon"),
  micText: document.getElementById("micText"),

  meetingBtn: document.getElementById("meetingBtn"),
  meetingIcon: document.getElementById("meetingIcon"),
  meetingText: document.getElementById("meetingText"),

  transcriptBox: document.getElementById("transcriptBox"),

  avatarImage: document.getElementById("avatarImage"),
  remoteVideo: document.getElementById("remoteVideo"),

  logBox: document.getElementById("logBox"),
};

function log(message) {
  console.log(`[Prometheus] ${message}`);

  if (!els.logBox) return;

  const line = document.createElement("div");
  line.className = "log-line";
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  els.logBox.appendChild(line);
  els.logBox.scrollTop = els.logBox.scrollHeight;
}

function updateClock() {
  if (!els.clockTime) return;

  const now = new Date();
  els.clockTime.textContent = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const mins = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const secs = String(totalSeconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function getCandidateName() {
  return state.sessionConfig?.interviewer?.candidateName || "Cecil";
}

function getOpeningLine() {
  return (
    state.sessionConfig?.interviewer?.openingLine ||
    `Hello ${getCandidateName()}, I'm Lauren from Prometheus. Thanks for joining today. To start, could you briefly introduce yourself and share one project you're most proud of?`
  );
}

function recordTranscript(role, text, time = null) {
  const cleanText = (text || "").trim();
  if (!cleanText) return;

  state.transcriptMessages.push({
    role,
    text: cleanText,
    time:
      time ||
      new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    timestamp: new Date().toISOString(),
  });
}

function buildTranscriptPayload() {
  return {
    company: state.sessionConfig?.interviewer?.company || "Prometheus",
    role: state.sessionConfig?.interviewer?.role || "Software Engineer Intern",
    candidateName: getCandidateName(),
    startedAt: state.meetingStartedAt
      ? new Date(state.meetingStartedAt).toISOString()
      : null,
    endedAt: new Date().toISOString(),
    durationMs: state.meetingStartedAt ? Date.now() - state.meetingStartedAt : 0,
    transcript: state.transcriptMessages,
    transcriptText: state.transcriptMessages
      .map((m) => `[${m.time}] ${m.role === "user" ? "You" : "Prometheus"}: ${m.text}`)
      .join("\n"),
  };
}

async function sendTranscriptToBackend() {
  if (state.transcriptSent) return;
  if (!state.transcriptMessages.length) {
    log("No transcript to send");
    return;
  }

  try {
    const payload = buildTranscriptPayload();

    const res = await fetch(TRANSCRIPT_POST_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Transcript upload failed with status ${res.status}`);
    }

    state.transcriptSent = true;
    log("Transcript sent successfully");
  } catch (err) {
    log(`Transcript send failed: ${err.message}`);
  }
}

function startMeetingTimer() {
  state.meetingStartedAt = Date.now();
  state.wrapUpPromptSent = false;
  state.hardStopTriggered = false;
  state.pendingEndAfterAudio = false;
  state.endingMessageSent = false;
  state.transcriptSent = false;
  state.transcriptMessages = [];

  if (els.callBadge) els.callBadge.textContent = "00:00";
  if (els.liveDot) els.liveDot.classList.add("active");

  if (state.meetingTimer) {
    clearInterval(state.meetingTimer);
  }

  state.meetingTimer = setInterval(() => {
    if (!state.meetingStartedAt) return;

    const diff = Date.now() - state.meetingStartedAt;

    if (els.callBadge) {
      els.callBadge.textContent = formatDuration(diff);
    }

    if (
      diff >= state.wrapUpMs &&
      !state.wrapUpPromptSent &&
      state.ws &&
      state.ws.readyState === WebSocket.OPEN
    ) {
      state.wrapUpPromptSent = true;

      sendJson({
        type: "conversation.item.create",
        item: {
          type: "message",
          role: "user",
          content: [
            {
              type: "input_text",
              text:
                `Begin wrapping up now. Keep it natural and brief. Ask at most one final question. ` +
                `Do not continue the same project topic. Shift to a short closing or a behavioral/final-fit question if needed. ` +
                `Use the candidate name ${getCandidateName()} naturally.`,
            },
          ],
        },
      });

      log("Sent wrap-up instruction");
    }

    if (
      diff >= state.hardLimitMs &&
      !state.hardStopTriggered &&
      !state.endingMessageSent &&
      state.ws &&
      state.ws.readyState === WebSocket.OPEN
    ) {
      state.hardStopTriggered = true;
      state.pendingEndAfterAudio = true;
      state.endingMessageSent = true;

      sendJson({
        type: "conversation.item.create",
        item: {
          type: "message",
          role: "user",
          content: [
            {
              type: "input_text",
              text:
                `End the interview now with one short professional closing sentence only. ` +
                `Thank ${getCandidateName()} by name. Do not ask another question. ` +
                `Finish your current sentence naturally if already speaking, then close.`,
            },
          ],
        },
      });

      log("Hard interview limit reached; waiting for final audio to finish");
    }
  }, 1000);
}

function stopMeetingTimer() {
  if (state.meetingTimer) {
    clearInterval(state.meetingTimer);
    state.meetingTimer = null;
  }

  state.meetingStartedAt = null;
  state.wrapUpPromptSent = false;
  state.hardStopTriggered = false;

  if (els.callBadge) els.callBadge.textContent = "00:00";
  if (els.liveDot) els.liveDot.classList.remove("active");
}

function setMeetingStartedUI(started) {
  if (!els.meetingBtn) return;

  els.meetingBtn.classList.toggle("start", !started);
  els.meetingBtn.classList.toggle("end", started);

  if (els.meetingIcon) {
    els.meetingIcon.className = started
      ? "ph-fill ph-phone-disconnect"
      : "ph-fill ph-phone-call";
  }

  if (els.meetingText) {
    els.meetingText.textContent = started ? "END CALL" : "START";
  }

  if (els.statusLabel) {
    els.statusLabel.textContent = started
      ? "Connecting..."
      : "Ready to start meeting";
  }
}

function updateMicUI() {
  if (!els.micBtn) return;

  if (state.micEnabled) {
    els.micBtn.classList.remove("muted");
    if (els.micIcon) els.micIcon.className = "ph-fill ph-microphone";
    if (els.micText) els.micText.textContent = "MIC ON";
  } else {
    els.micBtn.classList.add("muted");
    if (els.micIcon) els.micIcon.className = "ph-fill ph-microphone-slash";
    if (els.micText) els.micText.textContent = "MUTED";
  }
}

function setRemoteVisible(showRemote) {
  if (!els.remoteVideo || !els.avatarImage) return;

  els.remoteVideo.style.display = showRemote ? "block" : "none";
  els.avatarImage.style.display = showRemote ? "none" : "block";
}

function removeTranscriptEmpty() {
  const empty = els.transcriptBox?.querySelector(".transcript-empty");
  if (empty) empty.remove();
}

function createTranscriptMessage(role, text, time = null) {
  const msg = document.createElement("div");
  msg.className = `transcript-message ${role === "user" ? "user" : "ai"}`;

  const displayRole = role === "user" ? "You" : "Prometheus";
  const displayTime =
    time ||
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  msg.innerHTML = `
    <div class="msg-meta">
      <span class="msg-role">${displayRole}</span>
      <span class="msg-time">${displayTime}</span>
    </div>
    <div class="msg-text"></div>
  `;

  msg.querySelector(".msg-text").textContent = text;
  return msg;
}

function addTranscript(role, text, extraClass = "", time = null) {
  if (!els.transcriptBox) return null;

  removeTranscriptEmpty();

  const node = createTranscriptMessage(role, text, time);
  if (extraClass) node.classList.add(extraClass);

  els.transcriptBox.appendChild(node);
  els.transcriptBox.scrollTop = els.transcriptBox.scrollHeight;
  return node;
}

function sendJson(payload) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify(payload));
  }
}

async function unlockAudio() {
  try {
    if (!state.audioContext) {
      state.audioContext = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: 24000,
      });
    }

    if (state.audioContext.state === "suspended") {
      await state.audioContext.resume();
    }

    log("Audio context unlocked");
  } catch (err) {
    log(`Audio unlock failed: ${err.message}`);
  }
}

async function fetchSessionConfig() {
  const res = await fetch("/api/session");
  const data = await res.json();

  if (!data.success) {
    throw new Error(data.error || "Failed to get session config");
  }

  state.sessionConfig = data;
  state.hardLimitMs = data.interviewer?.durationMs || DEFAULT_HARD_LIMIT_MS;
  state.wrapUpMs = data.interviewer?.wrapUpMs || DEFAULT_WRAP_UP_MS;

  if (els.companyLabel) {
    els.companyLabel.textContent = data.interviewer?.company || "Prometheus";
  }

  if (els.roleLabel) {
    els.roleLabel.textContent =
      data.interviewer?.role || "Software Engineer Intern";
  }

  const params = new URLSearchParams();
  params.set("license", data.apiKey);

  if (data.avatarId) {
    params.set("avatarId", data.avatarId);
  } else if (data.name) {
    params.set("name", data.name);
  } else {
    throw new Error("Missing avatarId/name");
  }

  state.wsUrl = `${data.wsBase}?${params.toString()}`;
}

async function ensureMicrophoneAccess() {
  if (state.mediaStream) return state.mediaStream;

  state.mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      channelCount: 1,
    },
    video: false,
  });

  state.mediaStream.getAudioTracks().forEach((track) => {
    track.enabled = state.micEnabled;
  });

  return state.mediaStream;
}

async function toggleMic() {
  try {
    await ensureMicrophoneAccess();

    state.micEnabled = !state.micEnabled;

    if (state.mediaStream) {
      state.mediaStream.getAudioTracks().forEach((track) => {
        track.enabled = state.micEnabled;
      });
    }

    updateMicUI();
    log(state.micEnabled ? "Microphone enabled" : "Microphone muted");
  } catch (err) {
    log(`Mic toggle failed: ${err.message}`);
    alert("Could not access microphone.");
  }
}

function sendRealtimeInputConfig() {
  const interviewer = state.sessionConfig?.interviewer || {};

  const config = {
    voice: interviewer.voice || "shimmer",
    prompt: interviewer.systemPrompt || "",
    tools: [],
  };

  sendJson({
    type: "realtime.input_config",
    data: {
      content: JSON.stringify(config),
    },
  });

  log("Sent realtime.input_config");
}

async function sendConversationBootstrap() {
  sendJson({
    type: "conversation.item.create",
    item: {
      type: "message",
      role: "user",
      content: [
        {
          type: "input_text",
          text:
            `Start the interview now with this exact first line: "${getOpeningLine()}". ` +
            `Keep the interview conversational, move between topics quickly, include at least one behavioral question, ` +
            `and do not ask more than one follow-up on the same topic.`,
        },
      ],
    },
  });

  log("Sent interview kickoff message");
}

async function startMicrophoneStreaming() {
  if (!state.mediaStream) {
    await ensureMicrophoneAccess();
  }

  if (!state.audioContext) {
    state.audioContext = new (window.AudioContext || window.webkitAudioContext)(
      { sampleRate: 24000 }
    );
  }

  if (state.audioContext.state === "suspended") {
    await state.audioContext.resume();
  }

  if (state.processor) return;

  state.processorSource =
    state.audioContext.createMediaStreamSource(state.mediaStream);
  state.processor = state.audioContext.createScriptProcessor(8192, 1, 1);

  state.processor.onaudioprocess = (event) => {
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) return;

    const audioTracks = state.mediaStream?.getAudioTracks() || [];
    const enabled = audioTracks.some((track) => track.enabled);
    if (!enabled) return;

    const input = event.inputBuffer.getChannelData(0);
    const pcmBuffer = floatTo16BitPCM(input);
    const base64Audio = base64EncodeUint8(new Uint8Array(pcmBuffer));

    const chunkSize = 4096;
    for (let i = 0; i < base64Audio.length; i += chunkSize) {
      const chunk = base64Audio.slice(i, i + chunkSize);
      sendJson({
        type: TYPES.INPUT_AUDIO_APPEND,
        data: { audio: chunk },
      });
    }
  };

  state.processorSource.connect(state.processor);
  state.processor.connect(state.audioContext.destination);
  log("Microphone streaming started");
}

function floatTo16BitPCM(float32Array) {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);

  let offset = 0;
  for (let i = 0; i < float32Array.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return buffer;
}

function base64EncodeUint8(uint8Array) {
  let binary = "";
  const chunkSize = 0x8000;

  for (let i = 0; i < uint8Array.length; i += chunkSize) {
    const chunk = uint8Array.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return btoa(binary);
}

async function handleOffer(data) {
  if (!data?.sdp) {
    log("Offer missing SDP");
    return;
  }

  if (state.peer) {
    try {
      state.peer.close();
    } catch (_) {}
    state.peer = null;
  }

  state.peer = new RTCPeerConnection({
    iceServers: state.iceServers,
  });

  state.peer.ontrack = async (event) => {
    const stream = event.streams[0];
    if (!stream) return;

    els.remoteVideo.srcObject = stream;
    setRemoteVisible(true);
    els.remoteVideo.muted = false;
    els.remoteVideo.volume = 1.0;

    try {
      await els.remoteVideo.play();
      log("Remote video/audio started");
    } catch (err) {
      log(`Playback failed: ${err.message}`);
    }

    if (els.statusLabel) els.statusLabel.textContent = "Live";
  };

  state.peer.onicecandidate = (event) => {
    if (event.candidate) {
      sendJson({
        type: TYPES.WEBRTC_ICE,
        data: { candidate: event.candidate },
      });
    }
  };

  state.peer.oniceconnectionstatechange = () => {
    log(`ICE state: ${state.peer.iceConnectionState}`);
  };

  state.peer.onconnectionstatechange = () => {
    log(`Peer state: ${state.peer.connectionState}`);
  };

  await state.peer.setRemoteDescription(new RTCSessionDescription(data.sdp));
  const answer = await state.peer.createAnswer();
  await state.peer.setLocalDescription(answer);

  sendJson({
    type: TYPES.WEBRTC_ANSWER,
    data: { sdp: state.peer.localDescription },
  });

  log("Sent WebRTC answer");
}

async function handleAnswer(data) {
  if (!state.peer || !data?.sdp) return;
  await state.peer.setRemoteDescription(new RTCSessionDescription(data.sdp));
  log("Applied WebRTC answer");
}

async function handleIceCandidate(data) {
  if (!state.peer || !data?.candidate) return;

  try {
    await state.peer.addIceCandidate(new RTCIceCandidate(data.candidate));
  } catch (err) {
    log(`ICE add failed: ${err.message}`);
  }
}

function getEventText(data, navData) {
  if (typeof navData?.content === "string") return navData.content;
  if (typeof data?.transcript === "string") return data.transcript;
  if (typeof data?.delta === "string") return data.delta;

  if (Array.isArray(navData?.content)) {
    return navData.content
      .map((item) => item?.text || item?.content || "")
      .join(" ")
      .trim();
  }

  return "";
}

async function startInterview() {
  if (state.isStarting || state.ws) return;
  state.isStarting = true;

  try {
    await unlockAudio();
    await ensureMicrophoneAccess();
    await fetchSessionConfig();

    state.meetingActive = true;
    setMeetingStartedUI(true);
    startMeetingTimer();

    log("Opening NavTalk WebSocket");
    state.ws = new WebSocket(state.wsUrl);
    state.ws.binaryType = "arraybuffer";

    state.ws.onopen = () => {
      log("WebSocket connected");
      if (els.statusLabel) {
        els.statusLabel.textContent = "Configuring session";
      }
      sendRealtimeInputConfig();
    };

    state.ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      log("WebSocket error");
    };

    state.ws.onclose = (event) => {
      log(`WebSocket closed (${event.code})`);
      cleanup(false);
    };

    state.ws.onmessage = async (event) => {
      if (typeof event.data !== "string") return;

      let data;
      try {
        data = JSON.parse(event.data);
      } catch (err) {
        log("Failed to parse incoming JSON");
        return;
      }

      const type = data.type;
      const navData = data.data || {};

      switch (type) {
        case TYPES.CONNECTED_SUCCESS:
          log("conversation.connected.success received");
          if (navData.iceServers) {
            state.iceServers = navData.iceServers;
          }
          if (els.statusLabel) els.statusLabel.textContent = "Connected";
          break;

        case TYPES.CONNECTED_WARNING:
          log(`Connection warning: ${data.message || "warning"}`);
          break;

        case TYPES.CONNECTED_FAIL:
          log(`Connection failed: ${data.message || "unknown error"}`);
          cleanup();
          break;

        case TYPES.CONNECTED_CLOSE:
          log(`Server closed connection: ${data.message || "closed"}`);
          cleanup();
          break;

        case TYPES.INSUFFICIENT_BALANCE:
          log("Insufficient balance");
          cleanup();
          break;

        case TYPES.REALTIME_SESSION_CREATED:
          log("Realtime session created");
          if (els.statusLabel) els.statusLabel.textContent = "Starting interview";
          await sendConversationBootstrap();
          break;

        case TYPES.REALTIME_SESSION_UPDATED:
          log("Realtime session updated");
          if (els.statusLabel) els.statusLabel.textContent = "Live";
          await startMicrophoneStreaming();
          break;

        case TYPES.REALTIME_SPEECH_STARTED:
          log("User speech started");
          try {
            if (els.remoteVideo && !els.remoteVideo.paused) {
              els.remoteVideo.muted = true;
            }
          } catch (_) {}
          break;

        case TYPES.REALTIME_SPEECH_STOPPED:
          log("User speech stopped");
          try {
            if (els.remoteVideo) {
              els.remoteVideo.muted = false;
            }
          } catch (_) {}
          break;

        case TYPES.REALTIME_CONVERSATION_ITEM_COMPLETED: {
          const text = getEventText(data, navData);
          if (text.trim()) {
            addTranscript("user", text);
            recordTranscript("user", text);
          }
          break;
        }

        case TYPES.REALTIME_RESPONSE_AUDIO_TRANSCRIPT_DELTA: {
          const responseId =
            navData.response_id || navData.id || data.response_id || "default";
          const delta = getEventText(data, navData);

          if (!delta) break;

          if (!state.transcriptBufferById.has(responseId)) {
            state.transcriptBufferById.set(responseId, "");
            state.transcriptStreamingNode = addTranscript("ai", "", "streaming");
          }

          const nextText = state.transcriptBufferById.get(responseId) + delta;
          state.transcriptBufferById.set(responseId, nextText);

          if (state.transcriptStreamingNode) {
            const textNode =
              state.transcriptStreamingNode.querySelector(".msg-text");
            if (textNode) textNode.textContent = nextText;
          }

          if (els.transcriptBox) {
            els.transcriptBox.scrollTop = els.transcriptBox.scrollHeight;
          }
          break;
        }

        case TYPES.REALTIME_RESPONSE_AUDIO_TRANSCRIPT_DONE: {
          const responseId =
            navData.response_id || navData.id || data.response_id || "default";

          const finalText =
            getEventText(data, navData) ||
            state.transcriptBufferById.get(responseId) ||
            "";

          if (state.transcriptStreamingNode) {
            const textNode =
              state.transcriptStreamingNode.querySelector(".msg-text");
            if (textNode) textNode.textContent = finalText;
            state.transcriptStreamingNode.classList.remove("streaming");
            state.transcriptStreamingNode = null;
          } else if (finalText.trim()) {
            addTranscript("ai", finalText);
          }

          if (finalText.trim()) {
            recordTranscript("ai", finalText);
          }

          state.transcriptBufferById.delete(responseId);
          log("Assistant response complete");
          break;
        }

        case TYPES.REALTIME_RESPONSE_AUDIO_DONE:
          log("Assistant audio complete");

          if (state.pendingEndAfterAudio) {
            state.pendingEndAfterAudio = false;
            log("Final sentence finished, ending interview now");
            await cleanup();
          }
          break;

        case TYPES.WEBRTC_OFFER:
          log("Received WebRTC offer");
          await handleOffer(navData);
          break;

        case TYPES.WEBRTC_ANSWER:
          log("Received WebRTC answer");
          await handleAnswer(navData);
          break;

        case TYPES.WEBRTC_ICE:
          await handleIceCandidate(navData);
          break;

        default:
          log(`Unhandled event: ${type}`);
          break;
      }
    };
  } catch (err) {
    console.error(err);
    log(`Start failed: ${err.message}`);
    await cleanup();
    alert(err.message || "Failed to start interview.");
  } finally {
    state.isStarting = false;
  }
}

async function cleanup(closeSocket = true) {
  await sendTranscriptToBackend();

  if (state.processor) {
    try {
      state.processor.disconnect();
    } catch (_) {}
    state.processor.onaudioprocess = null;
    state.processor = null;
  }

  if (state.processorSource) {
    try {
      state.processorSource.disconnect();
    } catch (_) {}
    state.processorSource = null;
  }

  if (state.peer) {
    try {
      state.peer.close();
    } catch (_) {}
    state.peer = null;
  }

  if (closeSocket && state.ws) {
    try {
      state.ws.close();
    } catch (_) {}
  }

  state.ws = null;
  state.transcriptStreamingNode = null;
  state.transcriptBufferById.clear();

  if (els.remoteVideo) {
    try {
      els.remoteVideo.pause();
    } catch (_) {}
    els.remoteVideo.srcObject = null;
    els.remoteVideo.muted = false;
  }

  setRemoteVisible(false);

  state.meetingActive = false;
  state.pendingEndAfterAudio = false;
  state.endingMessageSent = false;
  setMeetingStartedUI(false);
  stopMeetingTimer();

  if (els.statusLabel) {
    els.statusLabel.textContent = "Ready to start meeting";
  }
}

async function toggleMeeting() {
  if (state.meetingActive) {
    await cleanup();
    log("Interview ended");
  } else {
    await startInterview();
  }
}

function bindUi() {
  if (els.transcriptToggle && els.transcriptPanel) {
    els.transcriptToggle.addEventListener("click", () => {
      els.transcriptPanel.classList.toggle("minimized");
      const minimized = els.transcriptPanel.classList.contains("minimized");
      els.transcriptToggle.title = minimized
        ? "Expand transcript"
        : "Minimize transcript";
    });
  }

  if (els.fullscreenBtn) {
    els.fullscreenBtn.addEventListener("click", async () => {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    });
  }

  if (els.micBtn) {
    els.micBtn.addEventListener("click", toggleMic);
  }

  if (els.meetingBtn) {
    els.meetingBtn.addEventListener("click", toggleMeeting);
  }
}

function init() {
  updateClock();
  setInterval(updateClock, 1000);

  updateMicUI();
  setMeetingStartedUI(false);
  setRemoteVisible(false);
  bindUi();

  if (els.companyLabel && !els.companyLabel.textContent.trim()) {
    els.companyLabel.textContent = "Prometheus";
  }

  if (els.roleLabel && !els.roleLabel.textContent.trim()) {
    els.roleLabel.textContent = "Software Engineer Intern";
  }

  log("UI initialized");
}

init();