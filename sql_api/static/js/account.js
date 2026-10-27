"use strict";

// Account dropdown for the SQL Assistant page.
// Logout is NOT wired here: auth.js already attaches a click handler to
// #logout-button that calls window.logoutUser().

document.addEventListener("DOMContentLoaded", async () => {
    const usernameElement = document.getElementById("navbar-username");
    const avatarElement = document.getElementById("user-avatar");
    const toggle = document.getElementById("account-toggle");
    const dropdown = document.getElementById("account-dropdown");

    if (!usernameElement || !dropdown || !toggle) return;

    function setOpen(open) {
        dropdown.hidden = !open;
        toggle.setAttribute("aria-expanded", String(open));
    }

    // Load the logged-in user's details
    try {
        // APIClient redirects to the login page on 401/403.
        const response = await APIClient.fetch("/api/me/");

        if (!response.ok) {
            throw new Error("Unable to load account details");
        }

        const user = await response.json();
        const name = user.username || "User";

        usernameElement.textContent = name;
        if (avatarElement) {
            avatarElement.textContent = name.charAt(0).toUpperCase();
        }
    } catch (error) {
        console.error("Account loading failed:", error);
        usernameElement.textContent = "Account";
    }

    // Open and close the dropdown
    toggle.addEventListener("click", () => setOpen(dropdown.hidden));

    // Close when clicking outside
    document.addEventListener("click", event => {
        if (!event.target.closest(".account-menu")) setOpen(false);
    });

    // Close with Escape and return focus to the toggle
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !dropdown.hidden) {
            setOpen(false);
            toggle.focus();
        }
    });

    // Query history: app.js scrolls to and highlights the sidebar history
    const historyLink = document.getElementById("history-link");
    if (historyLink) {
    historyLink.addEventListener("click", () => {
        setOpen(false);
    });
}
});