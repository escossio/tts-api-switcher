const textEl = document.getElementById("text");
const providerEl = document.getElementById("provider");
const languageEl = document.getElementById("language");
const voiceEl = document.getElementById("voice");
const speedEl = document.getElementById("speed");
const generateBtn = document.getElementById("generate");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const playerEl = document.getElementById("player");
const downloadEl = document.getElementById("download");

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`.trim();
}

generateBtn.addEventListener("click", async () => {
  const payload = {
    text: textEl.value.trim(),
    provider: providerEl.value,
    language: languageEl.value.trim() || "pt-BR",
    voice: voiceEl.value.trim(),
    speed: Number(speedEl.value || 1.0),
  };

  if (!payload.text) {
    setStatus("Cole um texto antes de gerar.", "error");
    return;
  }

  generateBtn.disabled = true;
  setStatus("Gerando áudio...");
  resultEl.classList.add("hidden");

  try {
    const response = await fetch("/api/generate-audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data?.detail?.error || data?.error || "Falha ao gerar áudio.");
    }

    const audioUrl = data.audio_url;
    playerEl.src = audioUrl;
    downloadEl.href = audioUrl;
    downloadEl.download = data.filename;
    resultEl.classList.remove("hidden");
    setStatus(`Áudio gerado com sucesso usando ${data.provider}.`, "ok");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    generateBtn.disabled = false;
  }
});

