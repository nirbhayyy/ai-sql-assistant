
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

    const hide = (el) => {
        if (el) el.hidden = true;
    };

    const show = (el) => {
        if (el) el.hidden = false;
    };

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

        // KPI card
        if (chart.type === "kpi") {
            if (!kpiValue || !kpiLabel || !kpiPanel) return;

            const value = Number(chart.value);

            kpiValue.textContent = Number.isFinite(value)
                ? value.toLocaleString()
                : String(chart.value ?? "—");

            kpiLabel.textContent = chart.label || "Result";

            show(kpiPanel);
            return;
        }

        // Check required chart elements
        if (!chartCanvas || !chartPanel || !chartTitle) {
            console.error("Chart elements are missing from the HTML.");
            return;
        }

        // Check Chart.js
        if (typeof Chart === "undefined") {
            console.error("Chart.js is not loaded.");
            return;
        }

        const supportedTypes = ["bar", "line", "pie"];

        if (!supportedTypes.includes(chart.type)) {
            console.error("Unsupported chart type:", chart.type);
            return;
        }

        const labels = Array.isArray(chart.labels)
            ? chart.labels
            : [];

        const values = Array.isArray(chart.values)
            ? chart.values
            : [];

        if (labels.length === 0 || values.length === 0) {
            console.warn("No chart data available.");
            return;
        }

        const isPie = chart.type === "pie";
        const isLine = chart.type === "line";

        chartTitle.textContent = chart.title || "Analytics";

        chartInstance = new Chart(chartCanvas.getContext("2d"), {
            type: chart.type,

            data: {
                labels: labels,

                datasets: [{
                    label: chart.y_label || "Value",
                    data: values,

                    backgroundColor: isPie
                        ? COLORS
                        : isLine
                            ? "#2563EB33"
                            : "#2563EB",

                    borderColor: isPie
                        ? "#FFFFFF"
                        : "#2563EB",

                    borderWidth: 2,
                    tension: 0.35,
                    fill: isLine,
                    pointRadius: isLine ? 4 : 0
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

                    title: {
                        display: false
                    }
                },

                scales: isPie
                    ? {}
                    : {
                        x: {
                            title: {
                                display: Boolean(chart.x_label),
                                text: chart.x_label || ""
                            },
                            grid: {
                                display: false
                            }
                        },

                        y: {
                            beginAtZero: true,
                            title: {
                                display: Boolean(chart.y_label),
                                text: chart.y_label || ""
                            }
                        }
                    }
            }
        });

        show(chartPanel);
    }

    // Make functions available to app.js
    window.renderChart = renderChart;
    window.hideVisuals = hideVisuals;

})();
