document.addEventListener("DOMContentLoaded", async () => {
    const total = document.getElementById("db-total");
    const city = document.getElementById("db-city");
    const cities = document.getElementById("db-cities");
    const years = document.getElementById("db-years");
    const table = document.getElementById("city-table");

    const res = await fetch("/api/dash-data/");
    const data = await res.json();

    // KPI
    total.textContent = data.total_customers.toLocaleString();
    city.textContent = data.top_city;
    cities.textContent = data.city_distribution.labels.length;
    years.textContent = data.yearly_growth.labels.length;

    // Pie
    new Chart(document.getElementById("dashboard-pie"), {
        type: "pie",
        data: {
            labels: data.city_distribution.labels,
            datasets: [{
                data: data.city_distribution.values
            }]
        }
    });

    // Line
    new Chart(document.getElementById("dashboard-line"), {
        type: "line",
        data: {
            labels: data.yearly_growth.labels,
            datasets: [{
                label: "Customers",
                data: data.yearly_growth.values,
                tension: 0.3,
                fill: false
            }]
        }
    });

    // Table
    table.innerHTML = `
        <table>
            <thead>
                <tr><th>City</th><th>Customers</th></tr>
            </thead>
            <tbody>
                ${data.city_distribution.labels.map((c, i) => `
                    <tr>
                        <td>${c}</td>
                        <td>${data.city_distribution.values[i]}</td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;
});