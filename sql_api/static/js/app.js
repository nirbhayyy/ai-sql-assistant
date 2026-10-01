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
    const tableContainer =
        document.getElementById("table-container");

    const errorPanel =
        document.getElementById("error-panel");

    const errorMessage =
        document.getElementById("error-message");

    const pagination =
        document.getElementById("pagination");

    const prev =
        document.getElementById("prevBtn");

    const next =
        document.getElementById("nextBtn");

    const pageNo =
        document.getElementById("pageNo");

    const historyList =
        document.getElementById("history-list");

    const chips =
        document.getElementById("examples");


    let currentQuestion = "";
    let currentPage = 1;
    let totalPages = 1;
    let currentRows = [];


    // ---------- CSRF ----------

    function getCSRFToken() {

        const token = document.querySelector(
            "[name=csrfmiddlewaretoken]"
        );

        return token ? token.value : "";
    }


    // ---------- HELPERS ----------

    const hide = el => {
        if (el) {
            el.hidden = true;
        }
    };


    const show = el => {
        if (el) {
            el.hidden = false;
        }
    };


    function setLoading(value) {

        askBtn.disabled = value;

        askLabel.textContent =
            value ? "Running..." : "Run";
    }


    function autoGrow() {

        question.style.height = "auto";

        question.style.height =
            Math.min(
                question.scrollHeight,
                150
            ) + "px";
    }


    function resetUI() {

        hide(errorPanel);
        hide(sqlPanel);
        hide(statsRow);
        hide(resultPanel);
        hide(insightPanel);

        if (window.hideVisuals) {
            window.hideVisuals();
        }
    }


    function highlight(sql) {

        const keywords =
            /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|COUNT|SUM|AVG|MIN|MAX|DISTINCT|HAVING)\b/gi;

        return sql.replace(
            keywords,
            '<span class="sql-kw">$&</span>'
        );
    }


    // ---------- TABLE ----------

    function renderTable(data) {

        tableContainer.innerHTML = "";

        if (!data || !data.length) {

            tableContainer.innerHTML =
                "<p>No rows found.</p>";

            return;
        }


        const columns =
            Object.keys(data[0]);


        const table =
            document.createElement("table");


        const thead =
            document.createElement("thead");


        const headerRow =
            document.createElement("tr");


        columns.forEach(column => {

            const th =
                document.createElement("th");

            th.textContent = column;

            headerRow.appendChild(th);
        });


        thead.appendChild(headerRow);

        table.appendChild(thead);


        const tbody =
            document.createElement("tbody");


        data.forEach(row => {

            const tr =
                document.createElement("tr");


            columns.forEach(column => {

                const td =
                    document.createElement("td");

                td.textContent =
                    row[column] ?? "—";

                tr.appendChild(td);
            });


            tbody.appendChild(tr);
        });


        table.appendChild(tbody);

        tableContainer.appendChild(table);
    }


    // ---------- HISTORY ----------

    async function loadHistory() {

        try {

            const response =
                await fetch("/api/history/");


            if (!response.ok) {
                return;
            }


            const data =
                await response.json();


            historyList.innerHTML = "";


            if (!data.length) {

                historyList.innerHTML =
                    "<li class='empty-hint'>No history</li>";

                return;
            }


            data.forEach(item => {

                const li =
                    document.createElement("li");


                li.innerHTML = `
                    <button
                        class="history-item"
                        type="button"
                    >
                        <span class="history-question">
                            ${item.question}
                        </span>
                    </button>
                `;


                li.onclick = () => {

                    question.value =
                        item.question;

                    autoGrow();

                    runQuery(
                        item.question,
                        1
                    );
                };


                historyList.appendChild(li);
            });


        } catch (error) {

            console.error(
                "History error:",
                error
            );
        }
    }


    // ---------- PAGINATION ----------

    function updatePagination() {

        if (totalPages <= 1) {

            hide(pagination);

            return;
        }


        show(pagination);


        pageNo.textContent =
            `Page ${currentPage} of ${totalPages}`;


        prev.disabled =
            currentPage === 1;


        next.disabled =
            currentPage === totalPages;
    }


    // ---------- MAIN API ----------

    async function runQuery(
        queryText,
        page = 1
    ) {

        if (!queryText.trim()) {
            return;
        }


        resetUI();

        setLoading(true);


        try {

            const response =
                await fetch(
                    `/api/query/?page=${page}&page_size=${PAGE_SIZE}`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type": "application/json",

                            // Django CSRF token
                            "X-CSRFToken":
                                getCSRFToken()
                        },

                        body: JSON.stringify({
                            question: queryText
                        })
                    }
                );


            const json =
                await response.json();


            console.log(
                "API STATUS:",
                response.status
            );


            console.log(
                "API RESPONSE:",
                json
            );


            if (!response.ok) {

                throw new Error(
                    json.message ||
                    json.error ||
                    json.detail ||
                    "API Error"
                );
            }


            // DRF pagination response
            const data =
                json.results;


            currentQuestion =
                queryText;


            currentPage =
                page;


            totalPages =
                Math.ceil(
                    json.count / PAGE_SIZE
                );


            // ---------- SQL ----------

            sqlCode.innerHTML =
                highlight(data.sql);

            show(sqlPanel);


            // ---------- STATS ----------

            rows.textContent =
                data.row_count;


            time.textContent =
                data.execution_time + " s";


            show(statsRow);


            // ---------- INSIGHT ----------

            if (data.insides) {

                insightText.textContent =
                    data.insides;

                show(insightPanel);
            }


            // ---------- CHART ----------

            if (window.renderChart) {

                window.renderChart(
                    data.chart
                );
            }


            // ---------- TABLE ----------

            currentRows =
                data.data || [];


            renderTable(
                currentRows
            );


            show(resultPanel);


            // ---------- PAGINATION ----------

            updatePagination();


            // ---------- HISTORY ----------

            loadHistory();


        } catch (error) {

            console.error(
                "QUERY ERROR:",
                error
            );


            errorMessage.textContent =
                error.message;


            show(errorPanel);


        } finally {

            setLoading(false);
        }
    }


    // ---------- CSV ----------

    const exportCsv =
        document.getElementById(
            "export-csv"
        );


    if (exportCsv) {

        exportCsv.addEventListener(
            "click",
            () => {

                if (!currentRows.length) {
                    return;
                }


                const columns =
                    Object.keys(
                        currentRows[0]
                    );


                const csv = [

                    columns.join(","),

                    ...currentRows.map(row =>
                        columns
                            .map(column =>
                                row[column] ?? ""
                            )
                            .join(",")
                    )

                ].join("\n");


                const blob =
                    new Blob(
                        [csv],
                        {
                            type: "text/csv"
                        }
                    );


                const link =
                    document.createElement("a");


                link.href =
                    URL.createObjectURL(blob);


                link.download =
                    "result.csv";


                link.click();


                URL.revokeObjectURL(
                    link.href
                );
            }
        );
    }


    // ---------- COPY SQL ----------

    if (copyBtn) {

        copyBtn.addEventListener(
            "click",
            async () => {

                await navigator.clipboard.writeText(
                    sqlCode.textContent
                );


                copyBtn.textContent =
                    "Copied";


                setTimeout(() => {

                    copyBtn.textContent =
                        "Copy";

                }, 1200);
            }
        );
    }


    // ---------- FORM ----------

    form.addEventListener(
        "submit",
        event => {

            event.preventDefault();

            runQuery(
                question.value,
                1
            );
        }
    );


    // ---------- PREVIOUS ----------

    prev.onclick = () => {

        if (currentPage > 1) {

            runQuery(
                currentQuestion,
                currentPage - 1
            );
        }
    };


    // ---------- NEXT ----------

    next.onclick = () => {

        if (currentPage < totalPages) {

            runQuery(
                currentQuestion,
                currentPage + 1
            );
        }
    };


    // ---------- CLEAR ----------

    clearBtn.onclick = () => {

        question.value = "";

        autoGrow();

        resetUI();

        tableContainer.innerHTML = "";
    };


    // ---------- EXAMPLE CHIPS ----------

    chips.onclick = event => {

        const chip =
            event.target.closest(".chip");


        if (!chip) {
            return;
        }


        question.value =
            chip.textContent;


        autoGrow();


        runQuery(
            chip.textContent,
            1
        );
    };


    // ---------- TEXTAREA ----------

    question.addEventListener(
        "input",
        autoGrow
    );


    // ---------- INITIALIZE ----------

    autoGrow();

    loadHistory();

})();