
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("connection-form");
    const connectButton = document.getElementById("connect-button");
    const messageBox = document.getElementById("connection-message");
    const savedConnectionsList = document.getElementById(
        "saved-connections-list"
    );

    // Read the Django CSRF token.
    function getCSRFToken() {
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
    }

    // Display success or error messages.
    function showMessage(message, type) {
        messageBox.textContent = message;
        messageBox.className = `connection-message ${type}`;
    }

    // Read JSON responses and handle API errors.
    async function readResponse(response) {
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            let message =
                data.message ||
                data.error ||
                data.detail;

            if (!message) {
                message = Object.values(data)
                    .flat()
                    .filter(value => typeof value === "string")
                    .join(" ");
            }

            throw new Error(
                message || `Request failed (${response.status}).`
            );
        }

        return data;
    }

    // Load database connections belonging to the logged-in user.
    async function loadSavedConnections() {
        savedConnectionsList.textContent =
            "Loading saved connections...";

        try {
            const response = await fetch("/api/db-ls/", {
                method: "GET",
                credentials: "same-origin"
            });

            const data = await readResponse(response);

            if (data.success === false) {
                throw new Error(
                    data.message || "Could not load saved connections."
                );
            }

            const connections = data.connections || [];

            savedConnectionsList.replaceChildren();

            if (connections.length === 0) {
                savedConnectionsList.textContent =
                    "No saved connections yet. Add your first database above.";
                return;
            }

            connections.forEach(connection => {
                const card = document.createElement("article");
                card.className = "saved-connection";

                const title = document.createElement("h3");
                title.textContent = connection.name;

                const database = document.createElement("p");
                database.textContent =
                    `Database: ${connection.database}`;

                const host = document.createElement("p");
                host.textContent =
                    `Host: ${connection.host}:${connection.port}`;

                const username = document.createElement("p");
                username.textContent =
                    `Username: ${connection.username}`;

                card.append(title, database, host, username);
                savedConnectionsList.appendChild(card);
            });

        } catch (error) {
            console.error("Loading connections failed:", error);

            savedConnectionsList.textContent =
                error.message || "Could not load saved connections.";
        }
    }

    // Submit database details to the existing Django endpoint.
    form.addEventListener("submit", async event => {
        event.preventDefault();

        if (!form.reportValidity()) {
            return;
        }

        connectButton.disabled = true;
        connectButton.textContent = "Testing connection...";

        messageBox.className = "connection-message";
        messageBox.textContent = "";

        const payload = {
            name: form.elements.name.value.trim(),
            db_type: form.elements.db_type.value,
            host: form.elements.host.value.trim(),
            port: Number(form.elements.port.value),
            database: form.elements.database.value.trim(),
            username: form.elements.username.value.trim(),
            password: form.elements.password.value
        };

        try {
            const response = await fetch("/api/db-conn/", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify(payload)
            });

            const data = await readResponse(response);

            if (data.success === false) {
                throw new Error(
                    data.message || "Database connection failed."
                );
            }

            showMessage(
                data.message ||
                    "Database connected and saved successfully!",
                "success"
            );

            // Clear the password after a successful save.
            form.elements.password.value = "";

            await loadSavedConnections();

        } catch (error) {
            console.error("Database connection failed:", error);

            showMessage(
                error.message || "Could not connect to the database.",
                "error"
            );

        } finally {
            connectButton.disabled = false;
            connectButton.textContent = "Test & Save Connection";
        }
    });

    // Display existing saved connections on page load.
    loadSavedConnections();
});
