/* Chart.js rendering functions for Bug Report Accuracy Analyzer */

const COLORS = {
    valid: '#198754',
    invalid: '#dc3545',
    duplicate: '#6c757d',
    enhancement: '#0dcaf0',
    wont_fix: '#ffc107',
};

function waitForChart(callback) {
    if (typeof Chart !== 'undefined') {
        callback();
    } else {
        setTimeout(function() { waitForChart(callback); }, 50);
    }
}

function renderClassificationDonut(canvasId, distData) {
    waitForChart(function() {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const labels = Object.keys(distData);
        const values = Object.values(distData);
        const colors = labels.map(l => COLORS[l] || '#adb5bd');

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'bottom' },
                }
            }
        });
    });
}

function renderTesterChart(canvasId, testerData) {
    waitForChart(function() {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const testers = Object.keys(testerData);
        const valid = testers.map(t => testerData[t].valid);
        const invalid = testers.map(t => testerData[t].invalid);
        const duplicate = testers.map(t => testerData[t].duplicate);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: testers,
                datasets: [
                    { label: 'Valid', data: valid, backgroundColor: COLORS.valid },
                    { label: 'Invalid', data: invalid, backgroundColor: COLORS.invalid },
                    { label: 'Duplicate', data: duplicate, backgroundColor: COLORS.duplicate },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true },
                }
            }
        });
    });
}

function renderTrendLineChart(canvasId, trends) {
    waitForChart(function() {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const labels = trends.map(t => t.cycle_name);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Testing Accuracy',
                        data: trends.map(t => (t.testing_accuracy * 100).toFixed(1)),
                        borderColor: COLORS.valid,
                        backgroundColor: COLORS.valid + '33',
                        fill: true,
                        tension: 0.3,
                    },
                    {
                        label: 'Invalid Rate',
                        data: trends.map(t => (t.invalid_rate * 100).toFixed(1)),
                        borderColor: COLORS.invalid,
                        tension: 0.3,
                    },
                    {
                        label: 'Duplicate Rate',
                        data: trends.map(t => (t.duplicate_rate * 100).toFixed(1)),
                        borderColor: COLORS.duplicate,
                        tension: 0.3,
                    },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + '%' }
                    }
                }
            }
        });
    });
}

function renderStackedBarChart(canvasId, trends) {
    waitForChart(function() {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const labels = trends.map(t => t.cycle_name);
        const cats = ['valid', 'invalid', 'duplicate', 'enhancement', 'wont_fix'];

        const datasets = cats.map(cat => ({
            label: cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' '),
            data: trends.map(t => (t.classification_distribution || {})[cat] || 0),
            backgroundColor: COLORS[cat] || '#adb5bd',
        }));

        new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true },
                }
            }
        });
    });
}

function renderComponentHeatmap(canvasId, componentData) {
    waitForChart(function() {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const components = Object.keys(componentData);
        const totals = components.map(c => componentData[c].total);
        const accuracies = components.map(c => (componentData[c].accuracy * 100).toFixed(1));

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: components,
                datasets: [
                    {
                        label: 'Total Bugs',
                        data: totals,
                        backgroundColor: '#0d6efd55',
                        borderColor: '#0d6efd',
                        borderWidth: 1,
                        yAxisID: 'y',
                    },
                    {
                        label: 'Accuracy %',
                        data: accuracies,
                        type: 'line',
                        borderColor: COLORS.valid,
                        backgroundColor: COLORS.valid,
                        pointRadius: 5,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: {
                    y: { beginAtZero: true, position: 'left', title: { display: true, text: 'Bug Count' } },
                    y1: { beginAtZero: true, max: 100, position: 'right', title: { display: true, text: 'Accuracy %' },
                           grid: { drawOnChartArea: false } },
                }
            }
        });
    });
}
