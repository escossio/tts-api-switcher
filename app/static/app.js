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
const providerNoteEl = document.getElementById("provider-note");
const historyListEl = document.getElementById("history-list");
const historyStatusEl = document.getElementById("history-status");
const refreshHistoryBtn = document.getElementById("refresh-history");

const providerState = {};

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`.trim();
}

function setHistoryStatus(message, type = "") {
  historyStatusEl.textContent = message;
  historyStatusEl.className = `status ${type}`.trim();
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

function clearProviderState() {
  Object.keys(providerState).forEach((key) => {
    delete providerState[key];
  });
}

function renderProviderNote(provider) {
  providerNoteEl.className = "provider-note";
  if (!provider) {
    providerNoteEl.textContent = "";
    return;
  }

  if (provider.id === "mock") {
    providerNoteEl.textContent = "Mock é apenas teste: gera um tom/zumbido em WAV, não fala o texto.";
    providerNoteEl.classList.add("info");
    return;
  }

  if (!provider.enabled) {
    providerNoteEl.textContent =
      provider.disabled_reason || "Configure as credenciais deste provider no .env para gerar voz real.";
    providerNoteEl.classList.add("warn");
    return;
  }

  providerNoteEl.textContent = "";
}

function renderProviderStatus(providers) {
  clearProviderState();
  providerStatusEl.replaceChildren();
  providerEl.replaceChildren();

  const fragment = document.createDocumentFragment();
  providers.forEach((provider) => {
    providerState[provider.id] = provider;

    const pill = document.createElement("span");
    pill.className = `pill ${provider.enabled ? "enabled" : "disabled"}`;
    pill.textContent = `${provider.name}: ${provider.enabled ? "habilitado" : "desabilitado"}`;
    fragment.appendChild(pill);

    const option = document.createElement("option");
    option.value = provider.id;
    option.textContent = provider.name;
    option.disabled = !provider.enabled;
    option.title = provider.disabled_reason || "";
    providerEl.appendChild(option);
  });
  providerStatusEl.appendChild(fragment);

  const enabledProvider = providers.find((provider) => provider.enabled);
  if (enabledProvider) {
    const currentProvider = providerState[providerEl.value];
    if (!currentProvider || !currentProvider.enabled) {
      providerEl.value = enabledProvider.id;
    }
  }

  renderProviderNote(providerState[providerEl.value]);
}

function renderHistory(items) {
  historyListEl.replaceChildren();

  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "history-empty";
    empty.textContent = "Nenhuma geração registrada ainda.";
    historyListEl.appendChild(empty);
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "history-item";

    const top = document.createElement("div");
    top.className = "history-top";

    const titleBlock = document.createElement("div");
    const dateEl = document.createElement("div");
    dateEl.className = "history-date";
    dateEl.textContent = formatDateTime(item.created_at);

    const previewTitle = document.createElement("strong");
    previewTitle.textContent = `${item.provider} • ${item.audio_format || "n/a"}`;
    titleBlock.append(dateEl, previewTitle);

    const statusTag = document.createElement("span");
    statusTag.className = `tag ${item.status === "ok" ? "ok" : "error"}`;
    statusTag.textContent = item.status;

    top.append(titleBlock, statusTag);

    const meta = document.createElement("div");
    meta.className = "history-meta";
    [
      ["Idioma", item.language || "-"],
      ["Voz", item.voice || "-"],
      ["Velocidade", item.speed ?? "-"],
      ["Tamanho", item.text_length],
    ].forEach(([label, value]) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = `${label}: ${value}`;
      meta.appendChild(tag);
    });

    const preview = document.createElement("div");
    preview.className = "history-preview";
    preview.textContent = item.text_preview;

    card.append(top, meta, preview);

    if (item.status === "error" && item.error_message) {
      const error = document.createElement("div");
      error.className = "history-error";
      error.textContent = item.error_message;
      card.appendChild(error);
    }

    if (item.audio_url) {
      const audio = document.createElement("audio");
      audio.controls = true;
      audio.src = item.audio_url;

      const download = document.createElement("a");
      download.className = "history-link";
      download.href = item.audio_url;
      download.download = item.filename || "";
      download.textContent = "Baixar áudio";

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "secondary";
      removeBtn.textContent = "Remover do histórico";
      removeBtn.addEventListener("click", () => deleteHistoryItem(item.id));

      const footer = document.createElement("div");
      footer.className = "history-footer";
      footer.append(audio, download, removeBtn);
      card.appendChild(footer);
    } else {
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "secondary";
      removeBtn.textContent = "Remover do histórico";
      removeBtn.addEventListener("click", () => deleteHistoryItem(item.id));

      const footer = document.createElement("div");
      footer.className = "history-footer";
      footer.append(removeBtn);
      card.appendChild(footer);
    }

    historyListEl.appendChild(card);
  });
}

async function loadProviders() {
  try {
    const response = await fetch("/api/providers");
    const data = await response.json();
    renderProviderStatus(data.providers || []);
    setStatus("Pronto para gerar.", "");
  } catch (error) {
    setStatus("Falha ao carregar provedores.", "error");
  }
}

async function loadHistory() {
  try {
    setHistoryStatus("Carregando histórico...");
    const response = await fetch("/api/history?limit=20");
    const data = await response.json();
    renderHistory(data.items || []);
    setHistoryStatus("Histórico atualizado.", "ok");
  } catch (error) {
    setHistoryStatus("Falha ao carregar histórico.", "error");
  }
}

async function deleteHistoryItem(itemId) {
  try {
    const response = await fetch(`/api/history/${itemId}`, {
      method: "DELETE",
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data?.detail || "Falha ao remover item.");
    }
    setHistoryStatus("Item removido do histórico.", "ok");
    await loadHistory();
  } catch (error) {
    setHistoryStatus(error.message, "error");
  }
}

generateBtn.addEventListener("click", async () => {
  const selectedProvider = providerState[providerEl.value];
  if (selectedProvider && !selectedProvider.enabled) {
    renderProviderNote(selectedProvider);
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
    await loadHistory();
  }
});

refreshHistoryBtn.addEventListener("click", loadHistory);
providerEl.addEventListener("change", () => {
  renderProviderNote(providerState[providerEl.value]);
});

loadProviders();
loadHistory();
