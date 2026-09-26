(function () {
    "use strict";

    const form = document.getElementById("ask-form");
    const questionEl = document.getElementById("question");
    const askBtn = document.getElementById("ask-btn");
    const askBtnLabel = document.getElementById("ask-btn-label");
    const clearBtn = document.getElementById("clear-btn");

    const errorPanel = document.getElementById("error-panel");
    const errorMessage = document.getElementById("error-message");

    const sqlPanel = document.getElementById("sql-panel");
    const sqlCode = document.querySelector("#sql code");
    const copySqlBtn = document.getElementById("copy-sql");

    const statsRow = document.getElementById("stats-row");
    const rowsEl = document.getElementById("rows");
    const timeEl = document.getElementById("time");

    const resultsPanel = document.getElementById("results-panel");
    const tableContainer = document.getElementById("table-container");
    const exportBtn = document.getElementById("export-csv");

    const emptyState = document.getElementById("empty-state");

    const historyList = document.getElementById("history-list");
    const clearHistoryBtn = document.getElementById("clear-history");
    const exampleChips = document.getElementById("examples");

    let currentRows = [];
    let sortState = { col: null, dir: 1 };

    // ---------- helpers ----------

    function autoGrow() {
        questionEl.style.height = "auto";
        questionEl.style.height = Math.min(questionEl.scrollHeight, 160) + "px";
    }

    function setLoading(isLoading) {
        askBtn.disabled = isLoading;
        askBtnLabel.textContent = isLoading ? "Running…" : "Run";
    }

    function hide(el) { el.hidden = true; }
    function show(el) { el.hidden = false; }

    function resetPanels() {
        hide(errorPanel);
        hide(sqlPanel);
        hide(statsRow);
        hide(resultsPanel);
    }

    function highlightSql(sql) {
        const keywords = /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|NOT|IN|IS|NULL|COUNT|SUM|AVG|MIN|MAX|DISTINCT|HAVING|INSERT|UPDATE|DELETE|CREATE|TABLE|DESC|ASC)\b/gi;
        let escaped = sql
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        escaped = escaped.replace(/'([^']*)'/g, "<span class=\"sql-str\">'$1'</span>");
        escaped = escaped.replace(/\b(\d+(\.\d+)?)\b/g, "<span class=\"sql-num\">$1</span>");
        escaped = escaped.replace(keywords, "<span class=\"sql-kw\">$&</span>");
        return escaped;
    }

    function formatNumber(n) {
        return Number(n).toLocaleString();
    }

    function formatTime(t) {
        const n = Number(t);
        return (Number.isFinite(n) ? n.toFixed(3) : t) + "s";
    }

    // ---------- history (server-backed) ----------

    async function loadHistory() {
        try {
            const response = await fetch("/api/history/");
            if (!response.ok) throw new Error("history request failed");
            const data = await response.json();
            renderHistory(data);
        } catch (e) {
            // Leave whatever is currently shown; history is a convenience,
            // not something worth surfacing an error panel for.
        }
    }

    function renderHistory(items) {
        historyList.innerHTML = "";

        if (!items || items.length === 0) {
            const li = document.createElement("li");
            li.className = "empty-hint";
            li.textContent = "Your recent questions will show up here.";
            historyList.appendChild(li);
            return;
        }

        items.forEach((item) => {
            const li = document.createElement("li");
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "history-item";
            btn.title = item.question;

            const q = document.createElement("span");
            q.className = "history-question";
            q.textContent = item.question;

            const sql = document.createElement("code");
            sql.className = "history-sql";
            sql.textContent = item.generated_sql;

            const time = document.createElement("span");
            time.className = "history-time";
            time.textContent = formatTime(item.execution_time ?? 0);

            btn.append(q, sql, time);
            btn.addEventListener("click", () => {
                questionEl.value = item.question;
                autoGrow();
                runQuery(item.question);
            });

            li.appendChild(btn);
            historyList.appendChild(li);
        });
    }

    clearHistoryBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/history/", { method: "DELETE" });
        } catch (e) {
            /* if there's no DELETE route yet, this just no-ops server-side */
        }
        loadHistory();
    });

    exampleChips.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (!chip) return;
        questionEl.value = chip.textContent;
        autoGrow();
        runQuery(chip.textContent);
    });

    // ---------- table rendering (XSS-safe: text content, not innerHTML) ----------

    function renderTable(rows) {
        tableContainer.innerHTML = "";

        if (!rows || rows.length === 0) {
            const p = document.createElement("p");
            p.className = "no-data";
            p.textContent = "The query ran successfully but returned no rows.";
            tableContainer.appendChild(p);
            return;
        }

        const columns = Object.keys(rows[0]);
        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headRow = document.createElement("tr");

        columns.forEach((col) => {
            const th = document.createElement("th");
            th.textContent = col;
            if (sortState.col === col) {
                const arrow = document.createElement("span");
                arrow.className = "sort-arrow";
                arrow.textContent = sortState.dir === 1 ? "↑" : "↓";
                th.appendChild(arrow);
            }
            th.addEventListener("click", () => {
                sortState.dir = sortState.col === col ? sortState.dir * -1 : 1;
                sortState.col = col;
                const sorted = [...currentRows].sort((a, b) => {
                    const av = a[col], bv = b[col];
                    if (av === bv) return 0;
                    if (av === null || av === undefined) return 1;
                    if (bv === null || bv === undefined) return -1;
                    return (av > bv ? 1 : -1) * sortState.dir;
                });
                renderTable(sorted);
            });
            headRow.appendChild(th);
        });

        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        rows.forEach((row) => {
            const tr = document.createElement("tr");
            columns.forEach((col) => {
                const td = document.createElement("td");
                const val = row[col];
                td.textContent = val === null || val === undefined ? "—" : String(val);
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        tableContainer.appendChild(table);
    }

    function toCsv(rows) {
        if (!rows || rows.length === 0) return "";
        const columns = Object.keys(rows[0]);
        const escapeCell = (v) => {
            const s = v === null || v === undefined ? "" : String(v);
            return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
        };
        const lines = [columns.join(",")];
        rows.forEach((r) => lines.push(columns.map((c) => escapeCell(r[c])).join(",")));
        return lines.join("\n");
    }

    exportBtn.addEventListener("click", () => {
        if (currentRows.length === 0) return;
        const blob = new Blob([toCsv(currentRows)], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "results.csv";
        a.click();
        URL.revokeObjectURL(url);
    });

    copySqlBtn.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(sqlCode.textContent);
            const original = copySqlBtn.textContent;
            copySqlBtn.textContent = "Copied";
            setTimeout(() => (copySqlBtn.textContent = original), 1200);
        } catch (e) {
            /* clipboard unavailable — silently ignore */
        }
    });

    // ---------- query execution ----------

    async function runQuery(question) {
        if (!question || !question.trim()) return;

        hide(emptyState);
        resetPanels();
        setLoading(true);
        sortState = { col: null, dir: 1 };

        try {
            const response = await fetch("/api/query/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: question.trim() }),
            });

            if (!response.ok) {
                throw new Error("Request failed with status " + response.status);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            loadHistory();

            if (data.sql) {
                sqlCode.innerHTML = highlightSql(data.sql);
                show(sqlPanel);
            }

            rowsEl.textContent = formatNumber(data.row_count ?? (data.data || []).length);
            timeEl.textContent = formatTime(data.execution_time ?? 0);
            show(statsRow);

            currentRows = data.data || [];
            renderTable(currentRows);
            show(resultsPanel);
        } catch (err) {
            errorMessage.textContent = err.message || "The request could not be completed. Please try again.";
            show(errorPanel);
        } finally {
            setLoading(false);
        }
    }

    // ---------- events ----------

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        runQuery(questionEl.value);
    });

    questionEl.addEventListener("input", autoGrow);

    questionEl.addEventListener("keydown", (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            e.preventDefault();
            runQuery(questionEl.value);
        }
    });

    clearBtn.addEventListener("click", () => {
        questionEl.value = "";
        autoGrow();
        questionEl.focus();
        resetPanels();
        show(emptyState);
    });

    // ---------- init ----------

    loadHistory();
    autoGrow();
})();