document.addEventListener("DOMContentLoaded", async () => {

    try {

        const res = await fetch("/api/dash-data/");

        if (!res.ok) {
            throw new Error(`API Failed: ${res.status}`);
        }

        const data = await res.json();

        console.log("Dashboard Data:", data);

        // =========================
        // KPI
        // =========================

        document.getElementById("db-total").textContent =
            Number(data.total).toLocaleString();


        // =========================
        // TOP CATEGORY
        // =========================

        let topCategory = "-";

        if (
            data.pie &&
            data.pie.labels &&
            data.pie.labels.length > 0
        ) {
            topCategory = data.pie.labels[0];
        }

        document.getElementById("db-city").textContent =
            topCategory;


        // =========================
        // TOTAL CATEGORIES
        // =========================

        document.getElementById("db-cities").textContent =
            data.pie?.labels?.length || 0;


        // =========================
        // YEARS
        // =========================

        document.getElementById("db-years").textContent =
            data.line?.labels?.length || 0;


        // =========================
        // PIE CHART
        // =========================

        if (data.pie) {

            new Chart(
                document.getElementById("dashboard-pie"),
                {
                    type: "pie",

                    data: {
                        labels: data.pie.labels,

                        datasets: [{
                            data: data.pie.values
                        }]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                }
            );
        }


        // =========================
        // LINE CHART
        // =========================

        if (data.line) {

            new Chart(
                document.getElementById("dashboard-line"),
                {
                    type: "line",

                    data: {
                        labels: data.line.labels,

                        datasets: [{
                            label: "Records",

                            data: data.line.values,

                            borderWidth: 2,

                            tension: 0.3,

                            fill: false
                        }]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                }
            );
        }


        // =========================
        // TABLE
        // =========================

        const table = document.getElementById("city-table");

        if (data.pie && data.pie.labels.length > 0) {

            table.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Records</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${data.pie.labels.map((label, i) => `
                            <tr>
                                <td>${label}</td>
                                <td>${data.pie.values[i]}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;

        } else {

            table.innerHTML = "<p>No category data available.</p>";

        }

    } catch (err) {

        console.error("Dashboard Error:", err);

        alert(err.message);
    }

});