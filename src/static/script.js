const state = {
  mode: "baseline",
};

const els = {
  tabs: document.querySelectorAll(".tab-btn"),
  form: document.getElementById("queryForm"),
  input: document.getElementById("questionInput"),
  sendBtn: document.getElementById("sendBtn"),
  resultArea: document.getElementById("resultArea"),
  testCaseList: document.getElementById("testCaseList"),
  providerBadge: document.getElementById("providerBadge"),
};

// ---------- Tabs ----------
els.tabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    els.tabs.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.mode = btn.dataset.mode;
  });
});

// ---------- Load test cases ----------
async function loadTestCases() {
  try {
    const res = await fetch("/api/test-cases");
    const data = await res.json();
    els.testCaseList.innerHTML = "";
    data.forEach((tc) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "test-case-btn";
      btn.innerHTML = `<span class="cat">#${tc.id} — ${tc.category}</span>${tc.question}`;
      btn.addEventListener("click", () => {
        els.input.value = tc.question;
        els.form.requestSubmit();
      });
      els.testCaseList.appendChild(btn);
    });
  } catch (e) {
    els.testCaseList.innerHTML = `<p class="loading">Không tải được test cases (${e.message})</p>`;
  }
}
loadTestCases();

// ---------- API calls ----------
async function callBaseline(question) {
  const res = await fetch("/api/baseline", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return res.json();
}

async function callAgent(question) {
  const res = await fetch("/api/agent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return res.json();
}

// ---------- Renderers ----------
function renderBaselinePanel(question, data) {
  const tpl = document.getElementById("tpl-baseline").content.cloneNode(true);
  tpl.querySelector(".question").textContent = "🙋 " + question;

  const answerEl = tpl.querySelector(".answer");
  if (data.error) {
    answerEl.textContent = "❌ " + data.error;
    answerEl.classList.add("provider-error");
  } else if (data.provider_error) {
    answerEl.textContent = data.provider_error;
    answerEl.classList.add("provider-error");
  } else {
    answerEl.textContent = data.response;
  }

  if (data.provider) {
    els.providerBadge.textContent = "🔌 " + data.provider;
  }
  return tpl;
}

function renderAgentPanel(question, data) {
  const tpl = document.getElementById("tpl-agent").content.cloneNode(true);
  tpl.querySelector(".question").textContent = "🙋 " + question;

  if (data.error) {
    const err = document.createElement("div");
    err.className = "final-box guardrail";
    err.textContent = data.error;
    tpl.querySelector(".final-box").replaceWith(err);
    return tpl;
  }

  if (data.provider_error) {
    const err = document.createElement("div");
    err.className = "final-box provider-error";
    err.textContent = data.provider_error;
    tpl.querySelector(".final-box").replaceWith(err);
    if (data.provider) els.providerBadge.textContent = "🔌 " + data.provider;
    return tpl;
  }

  const timeline = tpl.querySelector(".trace-timeline");
  data.steps.forEach((step) => {
    const stepTpl = document.getElementById("tpl-step").content.cloneNode(true);
    const stepEl = stepTpl.querySelector(".trace-step");
    if (step.error) stepEl.classList.add("error");
    stepTpl.querySelector(".step-badge").textContent = step.step;
    stepTpl.querySelector(".step-thought").textContent = step.thought || "(không có Thought)";

    const actionEl = stepTpl.querySelector(".step-action");
    if (step.action) {
      actionEl.textContent = step.action;
    } else {
      actionEl.remove();
    }

    const obsEl = stepTpl.querySelector(".step-observation");
    if (step.observation) {
      obsEl.textContent = step.observation;
    } else {
      obsEl.remove();
    }

    timeline.appendChild(stepTpl);
  });

  const finalBox = tpl.querySelector(".final-box");
  if (data.guardrail_triggered) {
    finalBox.classList.add("guardrail");
    finalBox.textContent = `Agent chưa đưa ra được Final Answer sau ${data.max_iterations} vòng lặp. Phanh an toàn MAX_ITERATIONS đã ngắt vòng lặp để tránh chạy vô hạn.`;
  } else {
    finalBox.textContent = data.final_answer;
  }

  if (data.provider) {
    els.providerBadge.textContent = "🔌 " + data.provider;
  }

  return tpl;
}

// ---------- Submit ----------
els.form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = els.input.value.trim();
  if (!question) return;

  els.sendBtn.disabled = true;
  els.sendBtn.textContent = "Đang chạy...";
  els.resultArea.innerHTML = `<p class="spinner">⏳ Đang gọi LLM, vui lòng chờ...</p>`;

  try {
    if (state.mode === "baseline") {
      const data = await callBaseline(question);
      els.resultArea.innerHTML = "";
      els.resultArea.appendChild(renderBaselinePanel(question, data));
    } else if (state.mode === "agent") {
      const data = await callAgent(question);
      els.resultArea.innerHTML = "";
      els.resultArea.appendChild(renderAgentPanel(question, data));
    } else {
      // compare: chạy song song cả 2
      const [baseline, agent] = await Promise.all([
        callBaseline(question),
        callAgent(question),
      ]);
      els.resultArea.innerHTML = "";
      const grid = document.createElement("div");
      grid.className = "compare-grid";
      grid.appendChild(renderBaselinePanel(question, baseline));
      grid.appendChild(renderAgentPanel(question, agent));
      els.resultArea.appendChild(grid);
    }
  } catch (err) {
    els.resultArea.innerHTML = `<p class="final-box guardrail">Lỗi kết nối tới server: ${err.message}</p>`;
  } finally {
    els.sendBtn.disabled = false;
    els.sendBtn.textContent = "Gửi ▶";
  }
});
