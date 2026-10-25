
const APIClient = {
    async fetch(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            credentials: "same-origin"
        });

        if (response.status === 401 || response.status === 403) {
            window.location.replace("/api/login-page/");
            throw new Error(
                "Your session has expired. Please log in again."
            );
        }

        return response;
    },

    getCSRFToken() {
        const match = document.cookie.match(
            /(?:^|;\s*)csrftoken=([^;]+)/
        );

        if (match) {
            return decodeURIComponent(match[1]);
        }

        const input = document.querySelector(
            'input[name="csrfmiddlewaretoken"]'
        );

        return input ? input.value : "";
    },

    async getConnections() {
        const response = await this.fetch("/api/db-ls/");
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.message || "Failed to load database connections."
            );
        }

        return result.connections || [];
    },

    async runQuery(connectionId, question) {
        const response = await this.fetch(
            `/api/query/?page=1&page_size=5`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.getCSRFToken()
                },
                body: JSON.stringify({
                    connection_id: Number(connectionId),
                    question: question
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.message ||
                result.error ||
                result.detail ||
                "Query request failed."
            );
        }

        return result;
    }
};
