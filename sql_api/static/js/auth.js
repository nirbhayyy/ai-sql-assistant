
"use strict";

const API = {
    csrf: "/api/csrf/",
    register: "/api/reg-api/",
    login: "/api/login/",
    logout: "/api/logout/",
    home: "/api/"
};


function getCookie(name) {
    const prefix = `${name}=`;
    const cookie = document.cookie
        .split(";")
        .map(item => item.trim())
        .find(item => item.startsWith(prefix));

    return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
}

// Ensure the CSRF cookie exists before making a POST request.
async function ensureCsrfToken() {
    let token = getCookie("csrftoken");

    if (token) {
        return token;
    }

    const response = await fetch(API.csrf, {
        method: "GET",
        credentials: "same-origin",
        headers: { "Accept": "application/json" }
    });

    if (!response.ok) {
        throw new Error("Could not initialize CSRF protection. Refresh the page and try again.");
    }

    token = getCookie("csrftoken");

    if (!token) {
        throw new Error("CSRF cookie was not set. Check your Django CSRF configuration.");
    }

    return token;
}

function showMessage(element, message, type = "error") {
    if (!element) return;

    element.textContent = message;
    element.className = `message ${type}`;
}

function getApiError(data, fallback) {
    if (data && typeof data.message === "string") {
        return data.message;
    }

    if (data && typeof data.detail === "string") {
        return data.detail;
    }

    if (data && typeof data === "object") {
        const messages = Object.entries(data)
            .map(([field, errors]) => {
                const values = Array.isArray(errors) ? errors : [errors];
                return `${field}: ${values.join(" ")}`;
            })
            .filter(Boolean);

        if (messages.length) return messages.join(" ");
    }

    return fallback;
}

async function postJson(url, payload) {
    const csrfToken = await ensureCsrfToken();

    const response = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(payload)
    });

    let data;

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            getApiError(data, `Request failed with status ${response.status}.`)
        );
    }

    return data;
}

// Registration form
const registerForm = document.getElementById("register-form");

if (registerForm) {
    registerForm.addEventListener("submit", async event => {
        event.preventDefault();

        const button = document.getElementById("register-button");
        const message = document.getElementById("register-message");

        const username = document.getElementById("register-username").value.trim();
        const email = document.getElementById("register-email").value.trim();
        const password = document.getElementById("register-password").value;

        showMessage(message, "");
        message.className = "message";

        if (!username || !email || !password) {
            showMessage(message, "Please fill in all fields.");
            return;
        }

        if (password.length < 8) {
            showMessage(message, "Password must contain at least 8 characters.");
            return;
        }

        button.disabled = true;
        button.textContent = "Creating account...";

        try {
            const data = await postJson(API.register, {
                username,
                email,
                password
            });

            showMessage(
                message,
                data.message || "Registration successful! Redirecting to login...",
                "success"
            );

            registerForm.reset();

            setTimeout(() => {
                window.location.href = "/api/login-page/";
            }, 1000);
        } catch (error) {
            showMessage(message, error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Create account";
        }
    });
}

// Login form
const loginForm = document.getElementById("login-form");

if (loginForm) {
    loginForm.addEventListener("submit", async event => {
        event.preventDefault();

        const button = document.getElementById("login-button");
        const message = document.getElementById("login-message");

        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;

        showMessage(message, "");
        message.className = "message";

        if (!username || !password) {
            showMessage(message, "Enter your username and password.");
            return;
        }

        button.disabled = true;
        button.textContent = "Logging in...";

        try {
            await postJson(API.login, { username, password });

            showMessage(message, "Login successful! Redirecting...", "success");

            // The session cookie is handled by the browser.
            // Redirect to the existing Django home page.
            window.location.replace(API.home);
        } catch (error) {
            showMessage(message, error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Log in";
        }
    });
}

// Optional logout helper for the existing SQL Assistant UI.
// Call window.logoutUser() from your logout button.
window.logoutUser = async function () {
    try {
        await postJson(API.logout, {});
        window.location.replace("/api/login-page/");
    } catch (error) {
        console.error("Logout failed:", error);
        alert(error.message);
    }
};

document.addEventListener("DOMContentLoaded", () => {
    const logoutButton = document.getElementById("logout-button");

    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            logoutButton.disabled = true;
            logoutButton.textContent = "Logging out...";

            try {
                await window.logoutUser();
            } finally {
                logoutButton.disabled = false;
                logoutButton.textContent = "Logout";
            }
        });
    }
});
