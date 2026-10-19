(function () {
    "use strict";

    const PAGE_SIZE = 5;

    // ---------- DOM ----------
    const $ = id => document.getElementById(id);

    const form = $("ask-form");
    const question = $("question");

    const askBtn = $("ask-btn");
    const askLabel = $("ask-btn-label");
    const clearBtn = $("clear-btn");

    const sqlPanel = $("sql-panel");
    const sqlCode = document.querySelector("#sql code");
    const copyBtn = $("copy-sql");

    const statsRow = $("stats-row");
    const rows = $("rows");
    const time = $("time");

    const insightPanel = $("insight-panel");
    const insightText = $("insightText");

    const resultPanel = $("results-panel");
    const tableContainer = $("table-container");

    const errorPanel = $("error-panel");
    const errorMessage = $("error-message");

    const loading = $("loading");
    const emptyState = $("empty-state");

    const pagination = $("pagination");
    const prev = $("prevBtn");
    const next = $("nextBtn");
    const pageNo = $("pageNo");

    const historyList = $("history-list");
    const historySection = $("history-section");
    const chips = $("examples");
    const exportCsv = $("export-csv");

    let currentQuestion = "";
    let currentPage = 1;
    let totalPages = 1;
    let currentRows = [];
    let requestId = 0; // guards against out-of-order responses

    // ---------- CSRF ----------
    function getCSRFToken() {
        const token = document.querySelector("[name=csrfmiddlewaretoken]");
        return token ? token.value : "";
    }

    // ---------- HELPERS ----------
    function hide(el) { if (el) el.hidden = true; }
    function show(el) { if (el) el.hidden = false; }

    function setLoading(value) {
        if (askBtn) askBtn.disabled = value;
        if (askLabel) askLabel.textContent = value ? "Running…" : "Run";
        if (value) show(loading); else hide(loading);
    }

    function autoGrow() {
        if (!question) return;
        question.style.height = "auto";
        question.style.height = Math.min(question.scrollHeight, 150) + "px";
    }

    function resetUI() {
        hide(errorPanel);
        hide(sqlPanel);
        hide(statsRow);
        hide(resultPanel);
        hide(insightPanel);
        hide(pagination);

        if (window.hideVisuals) window.hideVisuals();
    }

    function showError(message) {
        if (errorMessage) errorMessage.textContent = message;
        hide(emptyState);
        show(errorPanel);
    }

    function highlight(sql) {
        // Escape HTML before inserting syntax highlighting.
        const escaped = String(sql ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[char]);

        return escaped.replace(
            /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|OFFSET|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|NOT|IN|LIKE|BETWEEN|IS|NULL|COUNT|SUM|AVG|MIN|MAX|DISTINCT|HAVING|DESC|ASC)\b/gi,
            '<span class="sql-kw">$1</span>'
        );
    }

    function formatTime(value) {
        const n = Number(value);
        if (!Number.isFinite(n)) return "0 s";
        return `${n < 1 ? n.toFixed(3) : n.toFixed(2)} s`;
    }

    function isNumeric(value) {
        return typeof value === "number" ||
            (typeof value === "string" && value.trim() !== "" && !isNaN(Number(value)));
    }

    // ---------- TABLE ----------
    function renderTable(data) {
        if (!tableContainer) return;

        tableContainer.innerHTML = "";

        if (!Array.isArray(data) || !data.length) {
            tableContainer.textContent = "No rows found.";
            return;
        }

        const columns = Object.keys(data[0]);
        // A column is right-aligned when every non-empty value is numeric.
        const numeric = new Set(
            columns.filter(column =>
                data.every(row => row[column] == null || isNumeric(row[column]))
            )
        );

        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        columns.forEach(column => {
            const th = document.createElement("th");
            th.textContent = column;
            if (numeric.has(column)) th.className = "num";
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        data.forEach(row => {
            const tr = document.createElement("tr");

            columns.forEach(column => {
                const td = document.createElement("td");
                const value = row[column];

                td.textContent = value === null || value === undefined ? "—" : String(value);
                if (numeric.has(column)) td.className = "num";

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        tableContainer.appendChild(table);
    }

    // ---------- HISTORY ----------
    function markActiveHistory() {
        if (!historyList) return;
        historyList.querySelectorAll(".history-item").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.question === currentQuestion);
        });
    }

    async function loadHistory() {
        if (!historyList) return;

        try {
            const response = await fetch("/api/history/", { credentials: "same-origin" });

            if (!response.ok) throw new Error("Could not load query history.");

            const data = await response.json();
            const items = Array.isArray(data) ? data : data.results;

            historyList.innerHTML = "";

            if (!Array.isArray(items) || !items.length) {
                const li = document.createElement("li");
                li.className = "empty-hint";
                li.textContent = "Recent queries will appear here.";
                historyList.appendChild(li);
                return;
            }

            items.forEach(item => {
                const text = item.question || "Untitled query";
                const li = document.createElement("li");
                const button = document.createElement("button");

                button.type = "button";
                button.className = "history-item";
                button.title = text;
                button.dataset.question = text;

                const span = document.createElement("span");
                span.className = "history-question";
                span.textContent = text;

                button.appendChild(span);
                li.appendChild(button);

                button.addEventListener("click", () => {
                    if (!question) return;
                    question.value = item.question || "";
                    autoGrow();
                    runQuery(question.value, 1);
                });

                historyList.appendChild(li);
            });

            markActiveHistory();
        } catch (error) {
            console.error("History error:", error);
        }
    }

    // ---------- PAGINATION ----------
    function updatePagination() {
        if (!pagination) return;

        if (totalPages <= 1) {
            hide(pagination);
            return;
        }

        show(pagination);

        if (pageNo) pageNo.textContent = `Page ${currentPage} of ${totalPages}`;
        if (prev) prev.disabled = currentPage === 1;
        if (next) next.disabled = currentPage === totalPages;
    }

    // ---------- MAIN API ----------
    async function runQuery(queryText, page = 1) {
        if (!queryText || !queryText.trim()) return;

        const thisRequest = ++requestId;

        currentQuestion = queryText;
        resetUI();
        hide(emptyState);
        setLoading(true);

        try {
            const response = await fetch(
                `/api/query/?page=${page}&page_size=${PAGE_SIZE}`,
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken()
                    },
                    body: JSON.stringify({ question: queryText })
                }
            );

            const json = await response.json();

            // A newer request has started; ignore this one.
            if (thisRequest !== requestId) return;

            if (!response.ok) {
                throw new Error(
                    json.message || json.error || json.detail || "Query request failed."
                );
            }

            // Supports a paginated { count, results: {...} } or a direct response.
            const data = json.results ?? json;

            if (Array.isArray(data)) {
                throw new Error("Unexpected API response: expected query-result object.");
            }

            currentPage = page;

            const count = Number(json.count ?? data.row_count ?? 0);
            totalPages = json.count !== undefined
                ? Math.max(1, Math.ceil(count / PAGE_SIZE))
                : 1;

            // SQL
            if (sqlCode) sqlCode.innerHTML = highlight(data.sql || "");
            if (data.sql) show(sqlPanel);

            // Stats
            if (rows) rows.textContent = data.row_count ?? data.data?.length ?? 0;
            if (time) time.textContent = formatTime(data.execution_time);
            show(statsRow);

            // Insight
            const insight = data.insights ?? data.insides;
            if (insight && insightText) {
                insightText.textContent = insight;
                show(insightPanel);
            }

            // Chart
            if (window.renderChart && data.chart) window.renderChart(data.chart);

            // Results
            currentRows = Array.isArray(data.data) ? data.data : [];
            renderTable(currentRows);
            show(resultPanel);

            updatePagination();
            loadHistory();
        } catch (error) {
            if (thisRequest !== requestId) return;
            console.error("QUERY ERROR:", error);
            showError(error.message || "Something went wrong.");
        } finally {
            if (thisRequest === requestId) setLoading(false);
        }
    }

    // ---------- CSV ----------
    if (exportCsv) {
        exportCsv.addEventListener("click", () => {
            if (!currentRows.length) return;

            const columns = Object.keys(currentRows[0]);

            function csvCell(value) {
                const text = String(value ?? "");
                return `"${text.replace(/"/g, '""')}"`;
            }

            const csv = [
                columns.map(csvCell).join(","),
                ...currentRows.map(row => columns.map(column => csvCell(row[column])).join(","))
            ].join("\r\n");

            const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = url;
            link.download = "result.csv";
            link.click();

            URL.revokeObjectURL(url);
        });
    }

    // ---------- COPY SQL ----------
    if (copyBtn) {
        copyBtn.addEventListener("click", async () => {
            if (!sqlCode) return;

            try {
                await navigator.clipboard.writeText(sqlCode.textContent);
                copyBtn.textContent = "Copied";
                setTimeout(() => { copyBtn.textContent = "Copy"; }, 1200);
            } catch (error) {
                showError("Could not copy SQL. Please copy it manually.");
            }
        });
    }

    // ---------- FORM ----------
    if (form) {
        form.addEventListener("submit", event => {
            event.preventDefault();
            runQuery(question ? question.value : "", 1);
        });
    }

    // Ctrl/Cmd + Enter submits, as the hint promises.
    if (question) {
        question.addEventListener("keydown", event => {
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                runQuery(question.value, 1);
            }
        });
        question.addEventListener("input", autoGrow);
    }

    // ---------- PREVIOUS / NEXT ----------
    if (prev) {
        prev.addEventListener("click", () => {
            if (currentPage > 1) runQuery(currentQuestion, currentPage - 1);
        });
    }

    if (next) {
        next.addEventListener("click", () => {
            if (currentPage < totalPages) runQuery(currentQuestion, currentPage + 1);
        });
    }

    // ---------- CLEAR ----------
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            requestId++; // cancel any in-flight response
            if (question) { question.value = ""; question.focus(); }
            autoGrow();
            currentRows = [];
            currentQuestion = "";
            resetUI();
            setLoading(false);
            hide(loading);
            if (tableContainer) tableContainer.innerHTML = "";
            show(emptyState);
            markActiveHistory();
        });
    }

    // ---------- EXAMPLE CHIPS ----------
    if (chips) {
        chips.addEventListener("click", event => {
            const chip = event.target.closest(".chip");
            if (!chip) return;

            const text = chip.textContent.trim();

            if (question) {
                question.value = text;
                autoGrow();
            }

            runQuery(text, 1);
        });
    }

    // ---------- "Query history" in the account menu ----------
    document.addEventListener("open-query-history", () => {
        if (!historySection) return;
        historySection.scrollIntoView({ behavior: "smooth", block: "center" });
        historySection.classList.remove("flash");
        void historySection.offsetWidth; // restart animation
        historySection.classList.add("flash");
    });

    // ---------- INITIALIZE ----------
    autoGrow();
    loadHistory();
})();