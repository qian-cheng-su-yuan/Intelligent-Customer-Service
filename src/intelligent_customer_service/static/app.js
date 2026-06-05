const state = {
  customerId: "CUST-001",
};

const customerInput = document.querySelector("#customerId");
const healthText = document.querySelector("#healthText");
const llmText = document.querySelector("#llmText");
const statusDot = document.querySelector(".status-dot");
const llmDot = document.querySelector(".status-dot.llm");
const ticketCount = document.querySelector("#ticketCount");
const approvalCount = document.querySelector("#approvalCount");
const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const toolOutput = document.querySelector("#toolOutput");
const approvalList = document.querySelector("#approvalList");
const modelPill = document.querySelector("#modelPill");
const handoffBanner = document.querySelector("#handoffBanner");

function customerId() {
  return customerInput.value.trim() || state.customerId;
}

function renderJson(target, data) {
  target.textContent = JSON.stringify(data, null, 2);
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

async function refreshStatus() {
  try {
    await requestJson("/health");
    healthText.textContent = "Online";
    statusDot.classList.add("ok");
  } catch {
    healthText.textContent = "Offline";
    statusDot.classList.remove("ok");
  }

  try {
    const [tickets, approvals, config] = await Promise.all([
      requestJson("/tickets"),
      requestJson("/approvals"),
      requestJson("/config/status"),
    ]);
    ticketCount.textContent = tickets.length;
    approvalCount.textContent = approvals.length;
    llmText.textContent = config.llm_ready ? `LLM ready: ${config.model}` : "LLM key missing";
    modelPill.textContent = config.model || "OpenAI-compatible";
    handoffBanner.querySelector("span").textContent = config.next_step;
    llmDot.classList.toggle("ready", config.llm_ready);
    renderApprovals(approvals);
  } catch {
    ticketCount.textContent = "0";
    approvalCount.textContent = "0";
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

function renderApprovals(items) {
  approvalList.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "approval-item";
    empty.innerHTML = "<div><strong>No pending approvals</strong><span>Queue is clear</span></div>";
    approvalList.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "approval-item";
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
  try {
    const data = await requestJson("/chat", {
      method: "POST",
      body: JSON.stringify({ message, customer_id: customerId() }),
    });
    appendMessage("agent", data.answer);
    renderJson(toolOutput, data.tool_calls);
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
