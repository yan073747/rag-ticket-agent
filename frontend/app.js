const demoVersion = "20260715-static-demo";

const fixtures = {
  documents: [
    {
      id: 1,
      filename: "星辰科技_考勤与年假管理制度.pdf",
      chunks: [
        {
          index: 0,
          content:
            "员工连续工作满 1 年不满 10 年的，年休假 5 天；满 10 年不满 20 年的，年休假 10 天；满 20 年的，年休假 15 天。"
        },
        {
          index: 1,
          content:
            "年休假由员工本人申请，直属主管确认业务安排后审批。跨部门项目成员需同步项目负责人。"
        }
      ]
    },
    {
      id: 2,
      filename: "星辰科技_财务报销管理制度.docx",
      chunks: [
        {
          index: 0,
          content:
            "单笔报销金额不超过 1000 元由直属主管审批；1000 至 5000 元由部门负责人审批；超过 5000 元须提交财务负责人复核并由总经理审批。"
        },
        {
          index: 1,
          content:
            "差旅报销须提供行程单、发票和审批记录。缺少关键凭证时，财务可退回补充材料。"
        }
      ]
    },
    {
      id: 3,
      filename: "星辰科技_信息安全管理制度.txt",
      chunks: [
        {
          index: 0,
          content:
            "员工不得通过个人网盘、私人邮箱或未授权即时通讯工具传输客户资料、合同、源代码和内部经营数据。"
        },
        {
          index: 1,
          content:
            "发现疑似数据泄露时，应在 30 分钟内通知信息安全负责人，并保留相关日志与沟通记录。"
        }
      ]
    }
  ]
};

const state = {
  documents: [],
  qaRecords: [],
  tickets: [],
  activeView: "documents"
};

const elements = {
  statusTitle: document.querySelector("#statusTitle"),
  statusDetail: document.querySelector("#statusDetail"),
  metricDocs: document.querySelector("#metricDocs"),
  metricChunks: document.querySelector("#metricChunks"),
  metricQa: document.querySelector("#metricQa"),
  metricTickets: document.querySelector("#metricTickets"),
  seedButton: document.querySelector("#seedButton"),
  resetButton: document.querySelector("#resetButton"),
  uploadForm: document.querySelector("#uploadForm"),
  documentFile: document.querySelector("#documentFile"),
  fileName: document.querySelector("#fileName"),
  chunkSize: document.querySelector("#chunkSize"),
  chunkOverlap: document.querySelector("#chunkOverlap"),
  pipelineLog: document.querySelector("#pipelineLog"),
  questionForm: document.querySelector("#questionForm"),
  questionInput: document.querySelector("#questionInput"),
  topK: document.querySelector("#topK"),
  answerBox: document.querySelector("#answerBox"),
  recordList: document.querySelector("#recordList")
};

elements.documentFile.addEventListener("change", () => {
  elements.fileName.textContent = elements.documentFile.files[0]?.name || "未选择文件，可直接使用样例文档";
});

elements.seedButton.addEventListener("click", () => {
  seedKnowledgeBase();
  setPipeline("已载入 3 份样例企业制度，生成 6 个文本块并完成向量索引。");
});

elements.resetButton.addEventListener("click", () => {
  state.documents = [];
  state.qaRecords = [];
  state.tickets = [];
  elements.documentFile.value = "";
  elements.fileName.textContent = "未选择文件，可直接使用样例文档";
  elements.questionInput.value = "";
  elements.answerBox.innerHTML = '<p class="muted">提问后会显示回答、置信度、来源片段和工单状态。</p>';
  setPipeline("演示数据已重置。");
  updateDashboard();
});

elements.uploadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const file = elements.documentFile.files[0];
  if (!file) {
    seedKnowledgeBase();
    setPipeline("未选择文件，已自动载入样例企业制度并完成索引。");
    return;
  }

  const doc = {
    id: Date.now(),
    filename: file.name,
    chunks: [
      {
        index: 0,
        content:
          "演示环境不会读取真实文件内容。系统会把上传动作记录为一次文档入库，并使用安全样例知识库继续完成 RAG 流程。"
      }
    ]
  };
  state.documents = [doc, ...fixtures.documents];
  setPipeline(`已接收 ${file.name}，按 ${elements.chunkSize.value}/${elements.chunkOverlap.value} 参数模拟切分并写入向量索引。`);
  updateDashboard();
});

elements.questionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(elements.questionInput.value.trim());
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    elements.questionInput.value = button.dataset.question;
    askQuestion(button.dataset.question);
  });
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    button.classList.add("active");
    state.activeView = button.dataset.view;
    renderRecords();
  });
});

function seedKnowledgeBase() {
  state.documents = structuredClone(fixtures.documents);
  updateDashboard();
}

function askQuestion(question) {
  if (!question) {
    renderAnswerError("请先输入问题。");
    return;
  }
  if (!state.documents.length) {
    seedKnowledgeBase();
    setPipeline("已自动载入样例知识库，继续回答问题。");
  }

  const result = answerQuestion(question);
  state.qaRecords.unshift({
    id: state.qaRecords.length + 1,
    question,
    answer: result.answer,
    confidence: result.confidence,
    escalated: result.escalated
  });

  if (result.escalated) {
    state.tickets.unshift({
      id: state.tickets.length + 1,
      question,
      reason: "知识库未检索到足够可靠的事实依据，转人工客服确认。",
      status: "open"
    });
  }

  renderAnswer(result);
  updateDashboard();
}

function answerQuestion(question) {
  const normalized = question.toLowerCase();
  if (question.includes("年假") || question.includes("10 年") || question.includes("10年")) {
    return {
      confidence: 0.92,
      escalated: false,
      answer: "根据考勤与年假管理制度，员工连续工作满 10 年但不满 20 年的，每年可享受 10 天年休假。",
      sources: [
        source(1, 0, 0.041),
        source(1, 1, 0.122)
      ]
    };
  }
  if (question.includes("报销") || question.includes("5000")) {
    return {
      confidence: 0.89,
      escalated: false,
      answer: "单笔报销超过 5000 元时，需要提交财务负责人复核，并由总经理审批。",
      sources: [
        source(2, 0, 0.052),
        source(2, 1, 0.188)
      ]
    };
  }
  if (question.includes("客户资料") || question.includes("泄露") || normalized.includes("security")) {
    return {
      confidence: 0.86,
      escalated: false,
      answer: "制度要求不得通过个人网盘、私人邮箱或未授权即时通讯工具传输客户资料；发现疑似泄露时，应在 30 分钟内通知信息安全负责人并保留日志。",
      sources: [
        source(3, 0, 0.064),
        source(3, 1, 0.118)
      ]
    };
  }
  return {
    confidence: 0.31,
    escalated: true,
    answer:
      "当前知识库没有足够可靠的资料回答这个问题。系统不会强行编造答案，已创建人工客服工单，并附上候选片段供人工处理。",
    sources: [
      source(1, 0, 0.481),
      source(2, 0, 0.506)
    ]
  };
}

function source(documentId, chunkIndex, distance) {
  const document = state.documents.find((item) => item.id === documentId) || fixtures.documents.find((item) => item.id === documentId);
  const chunk = document?.chunks[chunkIndex];
  return {
    document_id: documentId,
    filename: document?.filename || "样例制度文档",
    chunk_index: chunkIndex,
    distance,
    content: chunk?.content || ""
  };
}

function renderAnswer(payload) {
  const confidenceClass = payload.escalated ? "confidence warn" : "confidence";
  const ticketLine = payload.escalated
    ? `<p class="handoff">低置信度，已创建工单 #${state.tickets[0]?.id || 1} 等待人工处理。</p>`
    : `<p class="muted">未创建工单，回答可直接引用。</p>`;
  const sourceLabel = payload.escalated ? "候选片段" : "来源";
  const sourceNote = payload.escalated
    ? `<p class="source-note">候选片段仅供人工参考，不作为可直接采信的答案来源。</p>`
    : "";

  elements.answerBox.innerHTML = `
    <span class="${confidenceClass}">置信度 ${(payload.confidence * 100).toFixed(1)}%</span>
    <p>${escapeHtml(payload.answer)}</p>
    ${ticketLine}
    ${sourceNote}
    <div class="sources">
      ${payload.sources
        .map(
          (item, index) => `
            <article class="source-item">
              <small>${sourceLabel} ${index + 1} · ${escapeHtml(item.filename)} · 文本块 ${item.chunk_index} · 距离 ${item.distance.toFixed(3)}</small>
              <p>${escapeHtml(item.content)}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderAnswerError(message) {
  elements.answerBox.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
}

function updateDashboard() {
  const chunkCount = state.documents.reduce((sum, item) => sum + item.chunks.length, 0);
  elements.metricDocs.textContent = state.documents.length;
  elements.metricChunks.textContent = chunkCount;
  elements.metricQa.textContent = state.qaRecords.length;
  elements.metricTickets.textContent = state.tickets.length;
  elements.statusTitle.textContent = state.documents.length ? "知识库已就绪" : "等待文档入库";
  elements.statusDetail.textContent = state.documents.length
    ? `已索引 ${state.documents.length} 份文档、${chunkCount} 个文本块。`
    : "建议先载入样例制度，再提问并观察来源引用。";
  renderRecords();
}

function renderRecords() {
  if (state.activeView === "documents") {
    elements.recordList.innerHTML = state.documents.length
      ? state.documents.map(documentTemplate).join("")
      : `<p class="muted">暂无文档。点击“载入样例制度文档”开始演示。</p>`;
    return;
  }
  if (state.activeView === "qa") {
    elements.recordList.innerHTML = state.qaRecords.length
      ? state.qaRecords.map(qaTemplate).join("")
      : `<p class="muted">暂无问答记录。</p>`;
    return;
  }
  elements.recordList.innerHTML = state.tickets.length
    ? state.tickets.map(ticketTemplate).join("")
    : `<p class="muted">暂无工单。提出知识库外问题会自动创建工单。</p>`;
}

function documentTemplate(item) {
  return `
    <article class="record-item">
      <small>文档 #${item.id} · ${item.chunks.length} 个文本块</small>
      <strong>${escapeHtml(item.filename)}</strong>
      <p>已完成切分、Embedding 和向量索引。</p>
    </article>
  `;
}

function qaTemplate(item) {
  return `
    <article class="record-item">
      <small>问答 #${item.id} · 置信度 ${(item.confidence * 100).toFixed(1)}%</small>
      <strong>${escapeHtml(item.question)}</strong>
      <p>${escapeHtml(item.answer)}</p>
    </article>
  `;
}

function ticketTemplate(item) {
  return `
    <article class="record-item">
      <small>工单 #${item.id} · ${escapeHtml(item.status)}</small>
      <strong>${escapeHtml(item.question)}</strong>
      <p>${escapeHtml(item.reason)}</p>
    </article>
  `;
}

function setPipeline(message, isError = false) {
  elements.pipelineLog.className = isError ? "activity error" : "activity";
  elements.pipelineLog.textContent = message;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

updateDashboard();
