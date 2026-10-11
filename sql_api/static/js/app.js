
(function () {
    "use strict";

    const PAGE_SIZE = 5;

    // ---------- DOM ----------
    const form = document.getElementById("ask-form");
    const question = document.getElementById("question");

    const askBtn = document.getElementById("ask-btn");
    const askLabel = document.getElementById("ask-btn-label");
    const clearBtn = document.getElementById("clear-btn");

    const sqlPanel = document.getElementById("sql-panel");
    const sqlCode = document.querySelector("#sql code");
    const copyBtn = document.getElementById("copy-sql");

    const statsRow = document.getElementById("stats-row");
    const rows = document.getElementById("rows");
    const time = document.getElementById("time");

    const insightPanel = document.getElementById("insight-panel");
    const insightText = document.getElementById("insightText");

    const resultPanel = document.getElementById("results-panel");
    const tableContainer = document.getElementById("table-container");

    const errorPanel = document.getElementById("error-panel");
    const errorMessage = document.getElementById("error-message");

    const pagination = document.getElementById("pagination");
    const prev = document.getElementById("prevBtn");
    const next = document.getElementById("nextBtn");
    const pageNo = document.getElementById("pageNo");

    const historyList = document.getElementById("history-list");
    const chips = document.getElementById("examples");
    const exportCsv = document.getElementById("export-csv");

    let currentQuestion = "";
    let currentPage = 1;
    let totalPages = 1;
    let currentRows = [];

    // ---------- CSRF ----------
    function getCSRFToken() {
        const token = document.querySelector("[name=csrfmiddlewaretoken]");
        return token ? token.value : "";
    }

    // ---------- HELPERS ----------
    function hide(el) {
        if (el) el.hidden = true;
    }

    function show(el) {
        if (el) el.hidden = false;
    }

    function setLoading(value) {
        if (askBtn) askBtn.disabled = value;
        if (askLabel) askLabel.textContent = value ? "Running..." : "Run";
    }

    function autoGrow() {
        if (!question) return;
        question.style.height = "auto";
        question.style.height =
            Math.min(question.scrollHeight, 150) + "px";
    }

    function resetUI() {
        hide(errorPanel);
        hide(sqlPanel);
        hide(statsRow);
        hide(resultPanel);
        hide(insightPanel);
        hide(pagination);

        if (window.hideVisuals) {
            window.hideVisuals();
        }
    }

    function showError(message) {
        if (errorMessage) {
            errorMessage.textContent = message;
        }
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
            /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|COUNT|SUM|AVG|MIN|MAX|DISTINCT|HAVING|DESC|ASC)\b/gi,
            '<span class="sql-kw">$1</span>'
        );
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
        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        columns.forEach(column => {
            const th = document.createElement("th");
            th.textContent = column;
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

                td.textContent =
                    value === null || value === undefined
                        ? "—"
                        : String(value);

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        tableContainer.appendChild(table);
    }

    // ---------- HISTORY ----------
    async function loadHistory() {
        if (!historyList) return;

        try {
            const response = await fetch("/api/history/");

            if (!response.ok) {
                throw new Error("Could not load query history.");
            }

            const data = await response.json();
            const items = Array.isArray(data) ? data : data.results;

            historyList.innerHTML = "";

            if (!Array.isArray(items) || !items.length) {
                historyList.textContent = "No history";
                return;
            }

            items.forEach(item => {
                const li = document.createElement("li");
                const button = document.createElement("button");

                button.type = "button";
                button.className = "history-item";

                const span = document.createElement("span");
                span.className = "history-question";
                span.textContent = item.question || "Untitled query";

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

        if (pageNo) {
            pageNo.textContent = `Page ${currentPage} of ${totalPages}`;
        }

        if (prev) prev.disabled = currentPage === 1;
        if (next) next.disabled = currentPage === totalPages;
    }

    // ---------- MAIN API ----------
    async function runQuery(queryText, page = 1) {
        if (!queryText || !queryText.trim()) return;

        currentQuestion = queryText;
        resetUI();
        setLoading(true);

        try {
            const response = await fetch(
                `/api/query/?page=${page}&page_size=${PAGE_SIZE}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken()
                    },
                    body: JSON.stringify({
                        question: queryText
                    })
                }
            );

            const json = await response.json();

            console.log("API STATUS:", response.status);
            console.log("API RESPONSE:", json);

            if (!response.ok) {
                throw new Error(
                    json.message ||
                    json.error ||
                    json.detail ||
                    "Query request failed."
                );
            }

            /*
             * Supports either:
             * 1. A paginated response: { count, results: {...} }
             * 2. A direct API response: { sql, data, row_count, ... }
             *
             * We will confirm the exact response structure against views.py.
             */
            const data = json.results ?? json;

            if (Array.isArray(data)) {
                throw new Error(
                    "Unexpected API response: expected query-result object."
                );
            }

            currentPage = page;

            const count = Number(json.count ?? data.row_count ?? 0);
            totalPages = json.count !== undefined
                ? Math.max(1, Math.ceil(count / PAGE_SIZE))
                : 1;

            // SQL
            if (sqlCode) {
                sqlCode.innerHTML = highlight(data.sql || "");
            }
            if (data.sql) show(sqlPanel);

            // Stats
            if (rows) rows.textContent = data.row_count ?? data.data?.length ?? 0;
            if (time) time.textContent = `${data.execution_time ?? 0} s`;
            show(statsRow);

            // Insight
            const insight = data.insights ?? data.insides;
            if (insight && insightText) {
                insightText.textContent = insight;
                show(insightPanel);
            }

            // Results
            currentRows = Array.isArray(data.data) ? data.data : [];
            renderTable(currentRows);
            show(resultPanel);

            // Chart
            if (window.renderChart && data.chart) {
                window.renderChart(data.chart);
            }

            updatePagination();

            // Refresh history without failing the current query.
            loadHistory();

        } catch (error) {
            console.error("QUERY ERROR:", error);
            showError(error.message || "Something went wrong.");
        } finally {
            setLoading(false);
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
                ...currentRows.map(row =>
                    columns.map(column => csvCell(row[column])).join(",")
                )
            ].join("\r\n");

            const blob = new Blob(["\uFEFF" + csv], {
                type: "text/csv;charset=utf-8;"
            });

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

                setTimeout(() => {
                    copyBtn.textContent = "Copy";
                }, 1200);
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

    // ---------- PREVIOUS ----------
    if (prev) {
        prev.addEventListener("click", () => {
            if (currentPage > 1) {
                runQuery(currentQuestion, currentPage - 1);
            }
        });
    }

    // ---------- NEXT ----------
    if (next) {
        next.addEventListener("click", () => {
            if (currentPage < totalPages) {
                runQuery(currentQuestion, currentPage + 1);
            }
        });
    }

    // ---------- CLEAR ----------
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (question) question.value = "";
            autoGrow();
            currentRows = [];
            resetUI();

            if (tableContainer) tableContainer.innerHTML = "";
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

    // ---------- TEXTAREA ----------
    if (question) {
        question.addEventListener("input", autoGrow);
    }

    // ---------- INITIALIZE ----------
    autoGrow();
    loadHistory();

})();
