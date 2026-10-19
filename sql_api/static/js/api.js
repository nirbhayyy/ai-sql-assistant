const APIClient = {
    async fetch(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            credentials: "same-origin"
        });

        if (
            response.status === 401 ||
            response.status === 403
        ) {
            window.location.replace("/api/login-page/");
            throw new Error("Your session has expired. Please log in again.");
        }

        return response;
    }
};