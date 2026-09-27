/**
 * chartt.js
 * Handles Bar, Line, Pie & KPI
 */

(function () {
    "use strict";

    const chartPanel = document.getElementById("chart-panel");
    const chartCanvas = document.getElementById("chart");
    const chartTitle = document.getElementById("chart-title");

    const kpiPanel = document.getElementById("kpi-panel");
    const kpiValue = document.getElementById("kpi-value");
    const kpiLabel = document.getElementById("kpi-label");

    let chartInstance = null;

    const COLORS = [
        "#2563EB",
        "#7C3AED",
        "#10B981",
        "#F59E0B",
        "#EF4444",
        "#06B6D4",
        "#EC4899",
        "#84CC16"
    ];

    const hide = (el) => el && (el.hidden = true);
    const show = (el) => el && (el.hidden = false);

    function destroyChart() {
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }
    }

    function hideVisuals() {
        destroyChart();
        hide(chartPanel);
        hide(kpiPanel);
    }

    function renderChart(chart) {

        hideVisuals();

        if (!chart) return;

        /* ---------- KPI ---------- */

        if (chart.type === "kpi") {

            destroyChart();

            hide(chartPanel);
            show(kpiPanel);

            kpiValue.textContent = Number(chart.value).toLocaleString();

            kpiLabel.textContent = chart.label || "Result";

            return;
        }

        /* ---------- BAR / LINE / PIE ---------- */

        if (typeof Chart === "undefined") {
            console.error("Chart.js not loaded");
            return;
        }

        show(chartPanel);

        chartTitle.textContent = chart.title || "Analytics";

        const ctx = chartCanvas.getContext("2d");

        const isPie = chart.type === "pie";

        chartInstance = new Chart(ctx, {

            type: chart.type,

            data: {
                labels: chart.labels || [],
                datasets: [{
                    label: chart.y_label || "",
                    data: chart.values || [],
                    backgroundColor: isPie ? COLORS : "#2563EB",
                    borderColor: isPie ? "#FFFFFF" : "#1D4ED8",
                    borderWidth: 2,
                    tension: 0.35,
                    fill: chart.type === "line" ? false : true,
                    pointRadius: chart.type === "line" ? 4 : 0
                }]
            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: isPie,
                        position: "bottom"
                    },

                    // We already show the title in HTML
                    title: {
                        display: false
                    }
                },

                scales: isPie ? {} : {

                    x: {
                        title: {
                            display: !!chart.x_label,
                            text: chart.x_label
                        },
                        grid: {
                            display: false
                        }
                    },

                    y: {
                        beginAtZero: true,
                        title: {
                            display: !!chart.y_label,
                            text: chart.y_label
                        }
                    }
                }
            }
        });
    }

    window.renderChart = renderChart;
    window.hideVisuals = hideVisuals;

})();