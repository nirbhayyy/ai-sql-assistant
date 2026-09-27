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

    let currentQuestion = "";
    let currentPage = 1;
    let totalPages = 1;
    let currentRows = [];

    // ---------- helpers ----------

    const hide = el => el && (el.hidden = true);
    const show = el => el && (el.hidden = false);

    function setLoading(v) {
        askBtn.disabled = v;
        askLabel.textContent = v ? "Running..." : "Run";
    }

    function autoGrow() {
        question.style.height = "auto";
        question.style.height = Math.min(question.scrollHeight, 150) + "px";
    }

    function resetUI() {
        hide(errorPanel);
        hide(sqlPanel);
        hide(statsRow);
        hide(resultPanel);
        hide(insightPanel);

        if (window.hideVisuals) window.hideVisuals();
    }

    function highlight(sql) {
        const kw = /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|COUNT|SUM|AVG|MIN|MAX|DISTINCT|HAVING)\b/gi;

        return sql.replace(
            kw,
            '<span class="sql-kw">$&</span>'
        );
    }

    // ---------- table ----------

    function renderTable(data) {

        tableContainer.innerHTML = "";

        if (!data.length) {
            tableContainer.innerHTML = "<p>No rows found.</p>";
            return;
        }

        const cols = Object.keys(data[0]);

        const table = document.createElement("table");

        const thead = document.createElement("thead");
        const tr = document.createElement("tr");

        cols.forEach(c => {
            const th = document.createElement("th");
            th.textContent = c;
            tr.appendChild(th);
        });

        thead.appendChild(tr);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        data.forEach(row => {

            const tr = document.createElement("tr");

            cols.forEach(c => {
                const td = document.createElement("td");
                td.textContent = row[c] ?? "—";
                tr.appendChild(td);
            });

            tbody.appendChild(tr);

        });

        table.appendChild(tbody);

        tableContainer.appendChild(table);

    }

    // ---------- history ----------

    async function loadHistory() {

        try {

            const r = await fetch("/api/history/");

            if (!r.ok) return;

            const data = await r.json();

            historyList.innerHTML = "";

            if (!data.length) {

                historyList.innerHTML =
                    "<li class='empty-hint'>No history</li>";

                return;
            }

            data.forEach(item => {

                const li = document.createElement("li");

                li.innerHTML = `
                    <button class="history-item">
                        <span class="history-question">${item.question}</span>
                    </button>
                `;

                li.onclick = () => {

                    question.value = item.question;
                    autoGrow();

                    runQuery(item.question, 1);

                };

                historyList.appendChild(li);

            });

        } catch (e) { }

    }

    // ---------- pagination ----------

    function updatePagination() {

        if (totalPages <= 1) {

            hide(pagination);
            return;

        }

        show(pagination);

        pageNo.textContent =
            `Page ${currentPage} of ${totalPages}`;

        prev.disabled = currentPage === 1;
        next.disabled = currentPage === totalPages;

    }

    // ---------- main api ----------

    async function runQuery(q, page = 1) {

        if (!q.trim()) return;

        resetUI();
        setLoading(true);

        try {

            const res = await fetch(
                `/api/query/?page=${page}&page_size=${PAGE_SIZE}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: q
                    })
                }
            );

            const json = await res.json();

            if (!res.ok)
                throw new Error(json.detail || "API Error");

            // IMPORTANT
            const data = json.results;

            currentQuestion = q;
            currentPage = page;
            totalPages = Math.ceil(json.count / PAGE_SIZE);

            // SQL
            sqlCode.innerHTML = highlight(data.sql);
            show(sqlPanel);

            // Stats
            rows.textContent = data.row_count;
            time.textContent = data.execution_time + " s";
            show(statsRow);

            // Insight
            if (data.insight) {
                insightText.textContent = data.insight;
                show(insightPanel);
            }

            // Chart
            if (window.renderChart)
                window.renderChart(data.chart);

            // Table
            currentRows = data.data;
            renderTable(currentRows);
            show(resultPanel);

            updatePagination();
            loadHistory();

        }

        catch (err) {

            errorMessage.textContent = err.message;
            show(errorPanel);

        }

        finally {

            setLoading(false);

        }

    }

    // ---------- csv ----------

    document
        .getElementById("export-csv")
        .addEventListener("click", () => {

            if (!currentRows.length) return;

            const cols = Object.keys(currentRows[0]);

            const csv = [
                cols.join(","),
                ...currentRows.map(r =>
                    cols.map(c => r[c]).join(",")
                )
            ].join("\n");

            const blob = new Blob([csv], { type: "text/csv" });

            const a = document.createElement("a");

            a.href = URL.createObjectURL(blob);
            a.download = "result.csv";
            a.click();

        });

    // ---------- copy sql ----------

    copyBtn.addEventListener("click", async () => {

        await navigator.clipboard.writeText(sqlCode.textContent);

        copyBtn.textContent = "Copied";

        setTimeout(() => {

            copyBtn.textContent = "Copy";

        }, 1200);

    });

    // ---------- events ----------

    form.addEventListener("submit", e => {

        e.preventDefault();

        runQuery(question.value, 1);

    });

    prev.onclick = () => {

        if (currentPage > 1)
            runQuery(currentQuestion, currentPage - 1);

    };

    next.onclick = () => {

        if (currentPage < totalPages)
            runQuery(currentQuestion, currentPage + 1);

    };

    clearBtn.onclick = () => {

        question.value = "";
        autoGrow();

        resetUI();

        tableContainer.innerHTML = "";

    };

    chips.onclick = e => {

        const chip = e.target.closest(".chip");

        if (!chip) return;

        question.value = chip.textContent;

        autoGrow();

        runQuery(chip.textContent, 1);

    };

    question.addEventListener("input", autoGrow);

    autoGrow();
    loadHistory();

})();