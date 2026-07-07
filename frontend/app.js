const state = {
  activeView: "documents",
};

const apiStatus = document.querySelector("#apiStatus");
const uploadForm = document.querySelector("#uploadForm");
const documentFile = document.querySelector("#documentFile");
const fileName = document.querySelector("#fileName");
const chunkSize = document.querySelector("#chunkSize");
const chunkOverlap = document.querySelector("#chunkOverlap");
const pipelineLog = document.querySelector("#pipelineLog");
const questionForm = document.querySelector("#questionForm");
const questionInput = document.querySelector("#questionInput");
const topK = document.querySelector("#topK");
const answerBox = document.querySelector("#answerBox");
const metricsGrid = document.querySelector("#metricsGrid");
const recordList = document.querySelector("#recordList");
const refreshButton = document.querySelector("#refreshButton");
const resetButton = document.querySelector("#resetButton");
const defaultAnswerHint = "提问后会显示回答、置信度、来源引用和工单状态。";

documentFile.addEventListener("change", () => {
  fileName.textContent = documentFile.files[0]?.name || "尚未选择文件";
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = documentFile.files[0];
  if (!file) {
    setPipeline("请先选择 .txt 或 .md 文档。", true);
    return;
  }

  setBusy(uploadForm, true);
  try {
    setPipeline("正在上传文档...");
    const formData = new FormData();
    formData.append("file", file);
    const uploaded = await request("/documents/upload", {
      method: "POST",
      body: formData,
    });

    setPipeline(`文档 #${uploaded.id} 上传成功，正在切分文本...`);
    const split = await request(
      `/documents/${uploaded.id}/chunks?chunk_size=${chunkSize.value}&chunk_overlap=${chunkOverlap.value}`,
      { method: "POST" },
    );

    setPipeline(`已生成 ${split.chunk_count} 个文本块，正在写入向量库...`);
    const indexed = await request(`/documents/${uploaded.id}/embeddings`, {
      method: "POST",
    });

    setPipeline(`完成。${uploaded.filename} 已写入 ${indexed.indexed_count} 个向量。`);
    await refreshDashboard();
  } catch (error) {
    setPipeline(error.message, true);
  } finally {
    setBusy(uploadForm, false);
  }
});

questionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) {
    renderAnswerError("请先输入问题。");
    return;
  }

  setBusy(questionForm, true);
  answerBox.innerHTML = `<p class="muted">正在检索来源并生成回答...</p>`;
  try {
    const payload = await request("/rag/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: Number(topK.value) }),
    });
    renderAnswer(payload);
    await refreshDashboard();
  } catch (error) {
    renderAnswerError(error.message);
  } finally {
    setBusy(questionForm, false);
  }
});

refreshButton.addEventListener("click", refreshDashboard);

resetButton.addEventListener("click", async () => {
  const confirmed = window.confirm("确定清空当前演示数据吗？文档记录、问答记录、工单和向量索引都会被清空。");
  if (!confirmed) {
    return;
  }

  resetButton.disabled = true;
  try {
    await request("/admin/reset-demo", { method: "POST" });
    setPipeline("演示数据已清空，可以重新上传文档测试。");
    documentFile.value = "";
    fileName.textContent = "尚未选择文件";
    resetQuestionWorkspace();
    await refreshDashboard();
  } catch (error) {
    setPipeline(error.message, true);
  } finally {
    resetButton.disabled = false;
  }
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    button.classList.add("active");
    state.activeView = button.dataset.view;
    await renderRecords();
  });
});

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return data;
}

function setPipeline(message, isError = false) {
  pipelineLog.className = isError ? "activity error" : "activity";
  pipelineLog.textContent = message;
}

function renderAnswer(payload) {
  const confidenceClass = payload.escalated_to_ticket ? "confidence warn" : "confidence";
  const ticketLine = payload.escalated_to_ticket
    ? `<p class="error">低置信度，已创建工单 #${payload.ticket_id} 等待人工处理。</p>`
    : `<p class="muted">未创建工单。</p>`;

  const sourceLabel = payload.escalated_to_ticket ? "候选片段" : "来源";
  const sourceHelp = payload.escalated_to_ticket
    ? `<p class="source-note">候选片段仅供人工处理参考，不是可直接采信的答案来源。</p>`
    : "";
  const sourceClass = payload.escalated_to_ticket ? "sources candidate-sources" : "sources";

  const sources = payload.sources.length
    ? payload.sources.map((source, index) => `
        <div class="source-item">
          <small>${sourceLabel} ${index + 1} · 文档 ${source.document_id} · 文本块 ${source.chunk_index} · 距离 ${source.distance.toFixed(4)}</small>
          <p>${escapeHtml(source.content)}</p>
        </div>
      `).join("")
    : `<p class="muted">没有返回来源。</p>`;

  answerBox.innerHTML = `
    <span class="${confidenceClass}">置信度 ${(payload.confidence * 100).toFixed(1)}%</span>
    <p>${escapeHtml(payload.answer).replace(/\n/g, "<br />")}</p>
    ${ticketLine}
    ${sourceHelp}
    <div class="${sourceClass}">${sources}</div>
  `;
}

function renderAnswerError(message) {
  answerBox.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
}

function resetQuestionWorkspace() {
  questionInput.value = "";
  topK.value = "2";
  answerBox.innerHTML = `<p class="muted">${defaultAnswerHint}</p>`;
}

async function refreshDashboard() {
  await Promise.all([renderMetrics(), renderRecords(), checkApi()]);
}

async function renderMetrics() {
  try {
    const metrics = await request("/admin/metrics");
    const cards = [
      ["文档数", metrics.total_documents],
      ["问答记录", metrics.total_qa_records],
      ["工单数", metrics.total_tickets],
      ["低置信度", metrics.low_confidence_count],
      ["平均置信度", `${(metrics.average_confidence * 100).toFixed(1)}%`],
      ["转人工比例", `${(metrics.escalation_rate * 100).toFixed(1)}%`],
    ];
    metricsGrid.innerHTML = cards.map(([label, value]) => `
      <div class="metric">
        <span>${label}</span>
        <strong>${value}</strong>
      </div>
    `).join("");
  } catch (error) {
    metricsGrid.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

async function renderRecords() {
  try {
    if (state.activeView === "documents") {
      const data = await request("/admin/documents");
      renderRecordItems(data.documents, documentTemplate, "暂无上传文档。");
    } else if (state.activeView === "qa") {
      const data = await request("/admin/qa-records");
      renderRecordItems(data.qa_records, qaTemplate, "暂无问答记录。");
    } else {
      const data = await request("/tickets");
      renderRecordItems(data.tickets, ticketTemplate, "暂无工单。");
    }
  } catch (error) {
    recordList.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

function renderRecordItems(items, template, emptyText) {
  recordList.innerHTML = items.length
    ? items.map(template).join("")
    : `<p class="muted">${emptyText}</p>`;
}

function documentTemplate(item) {
  return `
    <div class="record-item">
      <small>文档 #${item.id}</small>
      <p><strong>${escapeHtml(item.filename)}</strong></p>
      <small>${escapeHtml(item.file_path)}</small>
    </div>
  `;
}

function qaTemplate(item) {
  return `
    <div class="record-item">
      <small>问答 #${item.id} · 置信度 ${(item.confidence * 100).toFixed(1)}%</small>
      <p><strong>${escapeHtml(item.question)}</strong></p>
      <p>${escapeHtml(item.answer).slice(0, 220)}</p>
    </div>
  `;
}

function ticketTemplate(item) {
  return `
    <div class="record-item">
      <small>工单 #${item.id} · ${escapeHtml(item.status)}</small>
      <p><strong>${escapeHtml(item.question)}</strong></p>
      <small>${escapeHtml(item.reason)}</small>
    </div>
  `;
}

async function checkApi() {
  try {
    await request("/health");
    apiStatus.textContent = "接口在线";
    apiStatus.className = "status-pill ok";
  } catch {
    apiStatus.textContent = "接口离线";
    apiStatus.className = "status-pill bad";
  }
}

function setBusy(form, isBusy) {
  form.querySelectorAll("button, input, textarea").forEach((element) => {
    element.disabled = isBusy;
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

refreshDashboard();
