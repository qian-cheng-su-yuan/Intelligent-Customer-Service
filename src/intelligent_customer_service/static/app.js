const state = {
  customerId: "CUST-001",
};

const customerInput = document.querySelector("#customerId");
const healthText = document.querySelector("#healthText");
const llmText = document.querySelector("#llmText");
const runtimeDot = document.querySelector("#runtimeDot");
const llmDot = document.querySelector("#llmDot");
const ticketCount = document.querySelector("#ticketCount");
const approvalCount = document.querySelector("#approvalCount");
const refundCount = document.querySelector("#refundCount");
const ticketBadge = document.querySelector("#ticketBadge");
const refundBadge = document.querySelector("#refundBadge");
const thresholdValue = document.querySelector("#thresholdValue");
const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const toolOutput = document.querySelector("#toolOutput");
const approvalList = document.querySelector("#approvalList");
const ticketList = document.querySelector("#ticketList");
const refundList = document.querySelector("#refundList");
const modelPill = document.querySelector("#modelPill");
const handoffBanner = document.querySelector("#handoffBanner");

function customerId() {
  return customerInput.value.trim() || state.customerId;
}

function renderJson(target, data) {
  target.textContent = JSON.stringify(data, null, 2);
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString("zh-CN", {
    style: "currency",
    currency: "CNY",
    maximumFractionDigits: 2,
  });
}

function appendMessage(kind, text) {
  const article = document.createElement("article");
  article.className = `message ${kind}`;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);
  chatLog.appendChild(article);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw data;
  }
  return data;
}

function emptyItem(title, detail) {
  const node = document.createElement("div");
  node.className = "record-item empty";
  node.innerHTML = `<strong>${title}</strong><span>${detail}</span>`;
  return node;
}

function renderTickets(items) {
  ticketList.innerHTML = "";
  ticketBadge.textContent = items.length;
  if (!items.length) {
    ticketList.appendChild(emptyItem("No tickets", "售后队列暂无记录"));
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "record-item";
    row.innerHTML = `
      <div>
        <strong>#${item.id} ${item.issue_type}</strong>
        <span>${item.order_id} · ${item.status} · ${item.created_at}</span>
      </div>
      <small>${item.contact}</small>
    `;
    ticketList.appendChild(row);
  });
}

function renderApprovals(items) {
  approvalList.innerHTML = "";
  if (!items.length) {
    approvalList.appendChild(emptyItem("No pending approvals", "高风险操作队列已清空"));
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "record-item approval-item";
    row.innerHTML = `
      <div>
        <strong>#${item.id} ${item.action}</strong>
        <span>${item.risk_reason}</span>
      </div>
      <button type="button" data-approval="${item.id}">Approve</button>
    `;
    approvalList.appendChild(row);
  });
}

function renderRefunds(items) {
  refundList.innerHTML = "";
  refundBadge.textContent = items.length;
  if (!items.length) {
    refundList.appendChild(emptyItem("No refunds", "审批通过后会出现在这里"));
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "record-item";
    row.innerHTML = `
      <div>
        <strong>#${item.id} ${item.order_id}</strong>
        <span>${item.reason} · ${item.status} · ${item.created_at}</span>
      </div>
      <small>${formatMoney(item.amount)}</small>
    `;
    refundList.appendChild(row);
  });
}

async function refreshStatus() {
  try {
    await requestJson("/health");
    healthText.textContent = "Online";
    runtimeDot.classList.add("ok");
  } catch {
    healthText.textContent = "Offline";
    runtimeDot.classList.remove("ok");
  }

  try {
    const [tickets, approvals, refunds, config] = await Promise.all([
      requestJson("/tickets"),
      requestJson("/approvals"),
      requestJson("/refunds"),
      requestJson("/config/status"),
    ]);
    ticketCount.textContent = tickets.length;
    approvalCount.textContent = approvals.length;
    refundCount.textContent = refunds.length;
    thresholdValue.textContent = formatMoney(config.refund_review_threshold);
    llmText.textContent = config.llm_ready ? `LLM ready: ${config.model}` : "LLM key missing";
    modelPill.textContent = config.model || "OpenAI-compatible";
    handoffBanner.querySelector("span").textContent = config.next_step;
    llmDot.classList.toggle("ready", config.llm_ready);
    renderTickets(tickets);
    renderApprovals(approvals);
    renderRefunds(refunds);
  } catch {
    ticketCount.textContent = "0";
    approvalCount.textContent = "0";
    refundCount.textContent = "0";
    llmText.textContent = "Config unavailable";
    llmDot.classList.remove("ready");
  }
}

function toolPayload(name) {
  const base = {
    order_id: "ORD-1001",
    customer_id: customerId(),
  };
  if (name === "create_repair_ticket") {
    return {
      ...base,
      issue_type: "hardware",
      description: "Noise cancelling function is unstable and needs inspection.",
      contact: "19838622783",
    };
  }
  if (name === "request_refund") {
    return {
      ...base,
      amount: 899,
      reason: "quality issue",
    };
  }
  return base;
}

async function executeTool(name) {
  renderJson(toolOutput, { status: "running", tool: name });
  try {
    const data = await requestJson(`/tools/${name}`, {
      method: "POST",
      body: JSON.stringify(toolPayload(name)),
    });
    renderJson(toolOutput, data);
    await refreshStatus();
  } catch (error) {
    renderJson(toolOutput, error);
  }
}

async function approve(id) {
  try {
    const data = await requestJson(`/approvals/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer: "admin" }),
    });
    renderJson(toolOutput, data);
    await refreshStatus();
  } catch (error) {
    renderJson(toolOutput, error);
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  appendMessage("user", message);
  messageInput.value = "";
  renderJson(toolOutput, { status: "waiting_for_llm", message });
  try {
    const data = await requestJson("/chat", {
      method: "POST",
      body: JSON.stringify({ message, customer_id: customerId() }),
    });
    appendMessage("agent", data.answer);
    renderJson(toolOutput, data.tool_calls.length ? data.tool_calls : { status: "no_tool_call" });
    await refreshStatus();
  } catch (error) {
    appendMessage("agent", error.detail || "Chat service is not available.");
    renderJson(toolOutput, error);
  }
});

document.querySelectorAll("[data-tool]").forEach((button) => {
  button.addEventListener("click", () => executeTool(button.dataset.tool));
});

approvalList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-approval]");
  if (button) approve(button.dataset.approval);
});

document.querySelector("#refreshBtn").addEventListener("click", refreshStatus);
document.querySelector("#loadApprovalsBtn").addEventListener("click", refreshStatus);
document.querySelector("#clearResultBtn").addEventListener("click", () => {
  renderJson(toolOutput, { status: "ready" });
});

refreshStatus();
