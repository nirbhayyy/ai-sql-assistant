"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const historyList = document.getElementById("history-list");
    const historyStatus = document.getElementById("history-status");
    const searchInput = document.getElementById("history-search");
    const refreshButton = document.getElementById("refresh-history");
    const clearButton = document.getElementById("clear-history");

    let historyRecords = [];
    let requestId = 0;            // ignores out-of-order responses
    let clearTimer = null;        // resets the "Confirm clear?" state

    const SQL_KEYWORDS =
        /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|OFFSET|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|AND|OR|NOT|IN|LIKE|BETWEEN|IS|NULL|COUNT|SUM|AVG|MIN|MAX|DISTINCT|HAVING|DESC|ASC|EXTRACT)\b/gi;

    // ---------- HELPERS ----------

    // Session-expiry redirect comes from APIClient (api.js) when it is loaded.
    function apiGet(url) {
        if (typeof APIClient !== "undefined") {
            return APIClient.fetch(url, { method: "GET" });
        }
        return fetch(url, { method: "GET", credentials: "same-origin" });
    }

    function getCSRFToken() {
        const field = document.querySelector("[name=csrfmiddlewaretoken]");
        if (field && field.value) return field.value;

        const match = document.cookie
            .split(";")
            .map(item => item.trim())
            .find(item => item.startsWith("csrftoken="));

        return match ? decodeURIComponent(match.slice("csrftoken=".length)) : "";
    }

    function setStatus(message, type = "") {
        historyStatus.textContent = message;
        historyStatus.className = type;
    }

    function getRecords(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.history)) return data.history;
        if (data && Array.isArray(data.results)) return data.results;
        if (data && Array.isArray(data.data)) return data.data;
        return [];
    }

    function recordSql(record) {
        return record.sql || record.generated_sql || "";
    }

    function recordQuestion(record) {
        return record.question || record.query || "";
    }

    // Python's str(datetime) is "2026-10-27 11:01:22.123456+00:00",
    // which some browsers will not parse as-is.
    function parseDate(value) {
        if (!value) return null;

        const normalized = String(value)
            .replace(" ", "T")
            .replace(/(\.\d{3})\d+/, "$1");

        const date = new Date(normalized);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    function startOfDay(date) {
        return new Date(date.getFullYear(), date.getMonth(), date.getDate());
    }

    function dayLabel(date) {
        if (!date) return "Earlier";

        const days = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86400000);

        if (days === 0) return "Today";
        if (days === 1) return "Yesterday";

        return date.toLocaleDateString(undefined, {
            weekday: "short",
            day: "numeric",
            month: "short",
            year: "numeric"
        });
    }

    function formatSeconds(value) {
        const n = Number(value);
        if (!Number.isFinite(n)) return "Time unavailable";
        return `${n < 1 ? n.toFixed(3) : n.toFixed(2)} s`;
    }

    // Builds the SQL block with highlighted keywords, without using innerHTML.
    function buildSql(sql) {
        const pre = document.createElement("pre");
        const code = document.createElement("code");

        if (!sql) {
            code.textContent = "SQL query unavailable.";
        } else {
            let last = 0;
            SQL_KEYWORDS.lastIndex = 0;

            for (const match of sql.matchAll(SQL_KEYWORDS)) {
                if (match.index > last) {
                    code.append(sql.slice(last, match.index));
                }

                const keyword = document.createElement("span");
                keyword.className = "sql-kw";
                keyword.textContent = match[0];
                code.append(keyword);

                last = match.index + match[0].length;
            }

            if (last < sql.length) code.append(sql.slice(last));
        }

        pre.append(code);
        return pre;
    }

    // ---------- LOAD ----------

    async function loadHistory() {
        const thisRequest = ++requestId;

        setStatus("Loading your history...");
        historyList.replaceChildren();
        refreshButton.disabled = true;

        try {
            const response = await apiGet("/api/history/");
            const data = await response.json().catch(() => ({}));

            if (thisRequest !== requestId) return;

            if (!response.ok) {
                throw new Error(
                    data.message || data.detail || "Could not load query history."
                );
            }

            historyRecords = getRecords(data);
            renderHistory();
        } catch (error) {
            if (thisRequest !== requestId) return;
            setStatus(error.message || "Failed to load history.", "error");
        } finally {
            if (thisRequest === requestId) refreshButton.disabled = false;
        }
    }

    // ---------- RENDER ----------

    function renderHistory() {
        const searchTerm = searchInput.value.trim().toLowerCase();

        const filteredRecords = historyRecords.filter(record =>
            recordQuestion(record).toLowerCase().includes(searchTerm) ||
            recordSql(record).toLowerCase().includes(searchTerm)
        );

        historyList.replaceChildren();
        clearButton.disabled = historyRecords.length === 0;

        if (filteredRecords.length === 0) {
            setStatus("");

            const emptyMessage = document.createElement("div");
            emptyMessage.className = "history-empty";
            emptyMessage.textContent = searchTerm
                ? "No history matches your search."
                : "You haven't executed any queries yet.";

            historyList.appendChild(emptyMessage);
            return;
        }

        const count = filteredRecords.length;
        const total = historyRecords.length;

        setStatus(
            searchTerm
                ? `${count} of ${total} ${total === 1 ? "query" : "queries"}`
                : `${count} ${count === 1 ? "query" : "queries"}`
        );

        let currentDay = null;

        filteredRecords.forEach(record => {
            const date = parseDate(record.created_at || record.create_at || record.timestamp);
            const label = dayLabel(date);

            // Day headings: Today, Yesterday, then dates
            if (label !== currentDay) {
                currentDay = label;

                const heading = document.createElement("h2");
                heading.className = "history-day";
                heading.textContent = label;
                historyList.appendChild(heading);
            }

            const card = document.createElement("article");
            card.className = "history-card";

            // ----- head: question + copy button -----
            const head = document.createElement("div");
            head.className = "history-card-head";

            const title = document.createElement("h3");
            title.textContent = recordQuestion(record) || "Untitled query";

            const copy = document.createElement("button");
            copy.type = "button";
            copy.className = "history-copy";
            copy.textContent = "Copy SQL";
            copy.disabled = !recordSql(record);

            copy.addEventListener("click", async () => {
                try {
                    await navigator.clipboard.writeText(recordSql(record));
                    copy.textContent = "Copied";
                } catch {
                    copy.textContent = "Copy failed";
                }
                setTimeout(() => { copy.textContent = "Copy SQL"; }, 1200);
            });

            head.append(title, copy);

            // ----- meta pills -----
            const metadata = document.createElement("div");
            metadata.className = "history-meta";

            const when = document.createElement("span");
            if (date) {
                when.textContent = date.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit"
                });
                when.title = date.toLocaleString();
            } else {
                when.textContent = "Date unavailable";
            }

            const executionTime = document.createElement("span");
            executionTime.textContent =
                formatSeconds(record.execution_time ?? record.executionTime);
            executionTime.title = "Execution time";

            metadata.append(when, executionTime);

            // ----- SQL -----
            const sqlDetails = document.createElement("details");
            const summary = document.createElement("summary");
            summary.textContent = "View generated SQL";
            sqlDetails.append(summary, buildSql(recordSql(record)));

            card.append(head, metadata, sqlDetails);
            historyList.appendChild(card);
        });
    }

    // ---------- CLEAR (two-step confirm, no browser popup) ----------

    function resetClearButton() {
        clearTimeout(clearTimer);
        clearButton.classList.remove("confirm");
        clearButton.textContent = "Clear history";
    }

    clearButton.addEventListener("click", async () => {
        if (!clearButton.classList.contains("confirm")) {
            clearButton.classList.add("confirm");
            clearButton.textContent = "Confirm clear?";
            clearTimer = setTimeout(resetClearButton, 4000);
            return;
        }

        resetClearButton();
        clearButton.disabled = true;

        try {
            // Plain fetch: a 403 here means a CSRF problem, not an expired session.
            const response = await fetch("/api/history/", {
                method: "DELETE",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "X-CSRFToken": getCSRFToken()
                }
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(
                    data.message || data.detail || "Could not clear your history."
                );
            }

            requestId++;
            historyRecords = [];
            searchInput.value = "";
            renderHistory();
            setStatus(data.message || "History cleared");
        } catch (error) {
            clearButton.disabled = historyRecords.length === 0;
            setStatus(error.message || "Could not clear your history.", "error");
        }
    });

    // ---------- EVENTS ----------

    searchInput.addEventListener("input", renderHistory);
    refreshButton.addEventListener("click", loadHistory);

    loadHistory();
});