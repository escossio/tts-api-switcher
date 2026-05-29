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
const providerStatusEl = document.getElementById("provider-status");

const providerState = {};

function renderProviderStatus(providers) {
  providerStatusEl.innerHTML = providers
    .map((provider) => {
      providerState[provider.id] = provider;
      const className = provider.enabled ? "pill enabled" : "pill disabled";
      const label = provider.enabled ? "habilitado" : "desabilitado";
      return `<span class="${className}">${provider.name}: ${label}</span>`;
    })
    .join(" ");

  [...providerEl.options].forEach((option) => {
    const provider = providerState[option.value];
    if (provider) {
      option.disabled = !provider.enabled;
    }
  });

  if (providerState[providerEl.value] && !providerState[providerEl.value].enabled) {
    const firstEnabled = providers.find((provider) => provider.enabled);
    if (firstEnabled) {
      providerEl.value = firstEnabled.id;
    }
  }
}

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`.trim();
}

async function loadProviders() {
  try {
    const response = await fetch("/api/providers");
    const data = await response.json();
    renderProviderStatus(data.providers || []);
  } catch (error) {
    setStatus("Falha ao carregar provedores.", "error");
  }
}

generateBtn.addEventListener("click", async () => {
  const selectedProvider = providerState[providerEl.value];
  if (selectedProvider && !selectedProvider.enabled) {
    setStatus("Provider selecionado está desabilitado.", "error");
    return;
  }

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
      throw new Error(data?.detail || data?.error || "Falha ao gerar áudio.");
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

loadProviders();
