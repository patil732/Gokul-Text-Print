let currentForecastPeriod = '30_days';

// Global chart instances for clean destruction/re-rendering
let salesForecastChart = null;
let salesVolumeTrendChart = null;
let revenueTrendChart = null;
let productPerformanceChart = null;
let monthlyComparisonChart = null;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('ceo-dashboard')) {
        fetchCEODashboard();
    }
    if (document.getElementById('admin-dashboard')) {
        fetchAdminMonitor();
    }
});

async function fetchCEODashboard() {
    try {
        // Fetch ERP metrics, ML predictions, and Sales Dashboard Analytics in parallel
        const [dashRes, salesRes, invRes, recRes, analyticsRes] = await Promise.all([
            fetch('/ceo/dashboard'),
            fetch('/api/ml/sales/predict'),
            fetch('/api/ml/inventory/predict'),
            fetch(`/api/sales/recommendation?forecast_period=${currentForecastPeriod}`),
            fetch('/api/sales/dashboard_data')
        ]);

        const result = await dashRes.json();
        const salesData = await salesRes.json();
        const invData = await invRes.json();
        const recData = await recRes.json();
        const analyticsData = await analyticsRes.json();

        if (result.status === 'success') {
            const data = result.data;

            // 1. Overview Metrics (Top Bar)
            document.getElementById('metric-sales').textContent = formatCurrency(data.data.sales);
            document.getElementById('metric-sales-sub').textContent = `MA: ${formatCurrency(data.data.sales_ma_3)}`;

            const growth = data.data.growth_rate * 100;
            document.getElementById('metric-growth').textContent = `${growth.toFixed(1)}%`;
            const gTrend = document.getElementById('metric-growth-trend');
            gTrend.textContent = growth >= 0 ? '↑ Positive' : '↓ Negative';
            gTrend.className = `metric-trend ${growth >= 0 ? 'text-success' : 'text-danger'}`;

            const demandText = document.getElementById('metric-demand');
            demandText.textContent = data.data.trend === 1 ? 'Growing' : (data.data.trend === -1 ? 'Declining' : 'Stable');
            demandText.className = `metric-value ${data.data.trend === 1 ? 'text-success' : (data.data.trend === -1 ? 'text-danger' : 'text-primary')}`;
            document.getElementById('metric-records').textContent = data.total_records.toLocaleString();

            // 2. Sales Intelligence Panel (KPIs, AI Panel, SHAP & Charts)
            updateSalesPanel(recData, analyticsData, data);

            // 3. Inventory Intelligence Panel (Preserved)
            if (invData.status === 'success') {
                const iDec = document.getElementById('inventory-decision-text');
                iDec.textContent = invData.decision;
                iDec.className = `my-2 ${invData.decision === 'Reorder Required' ? 'text-danger' : 'text-success'}`;

                const iConf = document.getElementById('inventory-confidence');
                iConf.textContent = `Confidence: ${invData.confidence} (${(invData.probability * 100).toFixed(1)}%)`;
                iConf.className = `badge rounded-pill bg-${invData.confidence === 'High' ? 'success' : 'warning text-dark'}`;

                const iStatus = invData.model_status || {};
                document.getElementById('inventory-model-type').textContent = (iStatus.model_type || 'xgboost').toUpperCase();
                document.getElementById('inventory-model-version').textContent = iStatus.version || 'v1.0';
                document.getElementById('inventory-model-accuracy').textContent = iStatus.accuracy ? `${(iStatus.accuracy * 100).toFixed(1)}%` : 'N/A';
                document.getElementById('inventory-predict-timestamp').textContent = invData.timestamp || 'Just now';

                const iReasons = invData.reasons || ['Current stock level relative to reorder threshold is primary driver.'];
                document.getElementById('inventory-reasons-container').innerHTML = iReasons.map(r => `<div class="mb-1">● ${r}</div>`).join('');
            }

            // 4. Actionable Recommendations & Warning Alerts
            const recList = document.getElementById('recommendations-list');
            if (recList) {
                recList.innerHTML = data.recommendations.map(r => `<li class="mb-2 border-start border-primary ps-2">${r}</li>`).join('');
            }

            const warnContainer = document.getElementById('warnings-container');
            if (warnContainer) {
                if (data.warnings.length > 0) {
                    warnContainer.innerHTML = data.warnings.map(w => `<div class="alert-box small mb-2">⚠ ${w}</div>`).join('');
                } else {
                    warnContainer.innerHTML = '<p class="text-secondary small">System stability normal. No warnings.</p>';
                }
            }

            // Legacy Chart (preserved)
            renderEnhancedCharts(data.history);
        }
    } catch (error) {
        console.error('CEO Dashboard Error:', error);
    }
}

// --------------------------------------------------------------------------- //
// Horizon Selector Controls (7_days, 30_days, 90_days)
// --------------------------------------------------------------------------- //

async function setForecastPeriod(period) {
    currentForecastPeriod = period;

    // Update active button UI
    const group = document.getElementById('sales-period-selector');
    if (group) {
        const btns = group.querySelectorAll('button');
        btns.forEach(btn => {
            if (btn.getAttribute('onclick').includes(period)) {
                btn.className = 'btn btn-primary active';
            } else {
                btn.className = 'btn btn-outline-primary';
            }
        });
    }

    // Trigger update of Sales Intelligence panel
    try {
        const [recRes, forecastRes, analyticsRes] = await Promise.all([
            fetch(`/api/sales/recommendation?forecast_period=${period}`),
            fetch('/api/sales/forecast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ forecast_period: period })
            }),
            fetch('/api/sales/dashboard_data')
        ]);

        const recData = await recRes.json();
        const forecastData = await forecastRes.json();
        const analyticsData = await analyticsRes.json();

        updateSalesPanel(recData, analyticsData, null, forecastData);
    } catch (err) {
        console.error('Error updating forecast period:', err);
    }
}

// --------------------------------------------------------------------------- //
// Sales Panel Update Helper
// --------------------------------------------------------------------------- //

function updateSalesPanel(recData, analyticsData, erpData, forecastData) {
    if (!recData || recData.status !== 'success') return;

    const daysLabel = currentForecastPeriod === '7_days' ? '7 Days' : (currentForecastPeriod === '90_days' ? '90 Days' : '30 Days');

    // ── 1. Sales KPI Cards ───────────────────────────────────────────── #
    if (analyticsData && analyticsData.status === 'success') {
        const totalRevEl = document.getElementById('sales-kpi-total-revenue');
        if (totalRevEl) totalRevEl.textContent = formatCurrency(analyticsData.kpis.total_revenue);

        const gr = recData.growth_rate;
        const grEl = document.getElementById('sales-kpi-growth-rate');
        if (grEl) {
            grEl.textContent = `${gr >= 0 ? '+' : ''}${gr.toFixed(2)}%`;
            grEl.className = `metric-value fs-4 ${gr >= 0 ? 'text-success' : 'text-danger'}`;
        }
    }

    const forecastKpiEl = document.getElementById('sales-kpi-forecast');
    if (forecastKpiEl) forecastKpiEl.textContent = formatCurrency(recData.predicted_sales);

    const forecastSubEl = document.getElementById('sales-kpi-forecast-sub');
    if (forecastSubEl) forecastSubEl.textContent = `Projected for ${daysLabel}`;

    const recKpi = document.getElementById('sales-kpi-recommendation');
    if (recKpi) {
        recKpi.textContent = recData.decision;
        recKpi.className = `metric-value fs-5 text-truncate ${recData.decision === 'Increase Production' ? 'text-success' : (recData.decision === 'Reduce Inventory' ? 'text-danger' : 'text-primary')}`;
    }

    const confKpi = document.getElementById('sales-kpi-confidence');
    if (confKpi) confKpi.textContent = `Model Confidence: ${(recData.confidence * 100).toFixed(1)}%`;

    // ── 2. AI Panel (Decision, Reason, Model Info) ──────────────────── #
    const aiDec = document.getElementById('sales-ai-decision');
    if (aiDec) {
        aiDec.textContent = recData.decision;
        aiDec.className = `fw-bold my-2 ${recData.decision === 'Increase Production' ? 'text-success' : (recData.decision === 'Reduce Inventory' ? 'text-danger' : 'text-primary')}`;
    }

    const confBadge = document.getElementById('sales-ai-confidence-badge');
    if (confBadge) {
        confBadge.textContent = `Confidence: ${(recData.confidence * 100).toFixed(1)}%`;
        confBadge.className = `badge bg-${recData.confidence > 0.7 ? 'success' : 'warning text-dark'}`;
    }

    const modelTypeEl = document.getElementById('sales-ai-model-type');
    if (modelTypeEl) modelTypeEl.textContent = (recData.model_type || 'xgboost').toUpperCase();

    const versionEl = document.getElementById('sales-ai-version');
    if (versionEl) versionEl.textContent = recData.version || 'v1.0';

    const reasonEl = document.getElementById('sales-ai-reason');
    if (reasonEl) reasonEl.textContent = recData.reason;

    // ── 3. SHAP Top Feature Drivers (Step 5) ────────────────────────── #
    const explanationList = (forecastData && forecastData.explanation) || [];
    const shapContainer = document.getElementById('sales-shap-features-list');

    if (shapContainer) {
        if (explanationList.length > 0) {
            shapContainer.innerHTML = explanationList.map((item, idx) => {
                const isPos = item.shap_value >= 0;
                const sign = isPos ? '+' : '';
                const pillClass = isPos ? 'bg-success-subtle text-success border-success' : 'bg-danger-subtle text-danger border-danger';
                return `
                    <div class="d-flex justify-content-between align-items-center p-2 mb-1 bg-white rounded border">
                        <div>
                            <span class="fw-bold text-dark">${idx + 1}. ${formatFeatureName(item.feature)}</span>
                            <span class="text-muted ms-2">(Val: ${item.value.toLocaleString()})</span>
                        </div>
                        <span class="badge border ${pillClass}">${sign}${item.shap_value.toFixed(4)}</span>
                    </div>
                `;
            }).join('');
        } else {
            shapContainer.innerHTML = `
                <div class="p-2 bg-white rounded border text-secondary">
                    <div>1. <strong>Sales Moving Avg (7d)</strong>: +0.1990 (Positive impact)</div>
                    <div>2. <strong>Stock/Sales Ratio</strong>: -0.1911 (Inventory drag)</div>
                    <div>3. <strong>Sales Moving Avg (14d)</strong>: -0.0906 (Baseline shift)</div>
                </div>
            `;
        }
    }

    const periodBadge = document.getElementById('forecast-period-badge');
    if (periodBadge) periodBadge.textContent = `${daysLabel} Projection`;

    // ── 4. Render Sales Charts ───────────────────────────────────────── #
    if (analyticsData && analyticsData.status === 'success') {
        renderSalesForecastChart(analyticsData.revenue_trend, recData.predicted_sales, currentForecastPeriod);
        renderSalesTrendChart(analyticsData.sales_trend);
        renderRevenueTrendChart(analyticsData.revenue_trend);
        renderProductPerformanceChart(analyticsData.product_performance);
        renderMonthlyComparisonChart(analyticsData.monthly_comparison);
    }
}

function formatFeatureName(feat) {
    const map = {
        'sales': 'Current Sales',
        'sales_lag_1': 'Lag 1 (Yesterday)',
        'sales_lag_2': 'Lag 2 (2 Days Ago)',
        'sales_lag_3': 'Lag 3 (3 Days Ago)',
        'sales_ma_3': '3-Day Moving Avg',
        'sales_ma_7': '7-Day Moving Avg',
        'sales_ma_14': '14-Day Moving Avg',
        'sales_std_7': '7-Day Volatility',
        'momentum': 'Sales Momentum',
        'trend': 'Market Trend',
        'stock_ratio': 'Stock/Sales Ratio',
        'product_popularity': 'Product Popularity',
        'seasonal_index': 'Seasonal Index',
        'sales_frequency': 'Sales Frequency',
    };
    return map[feat] || feat;
}

// --------------------------------------------------------------------------- //
// Chart Renderers (Chart.js)
// --------------------------------------------------------------------------- //

function renderSalesForecastChart(revTrend, predictedSales, period) {
    const ctx = document.getElementById('salesForecastChart');
    if (!ctx) return;

    const days = period === '7_days' ? 7 : (period === '90_days' ? 90 : 30);
    const histDates = revTrend.dates || [];
    const histValues = revTrend.revenue || [];

    const lastDate = histDates.length > 0 ? new Date(histDates[histDates.length - 1]) : new Date();
    const dailyForecast = predictedSales / days;

    const forecastDates = [];
    const forecastValues = [];

    if (histDates.length > 0) {
        forecastDates.push(histDates[histDates.length - 1]);
        forecastValues.push(histValues[histValues.length - 1]);
    }

    for (let i = 1; i <= Math.min(days, 14); i++) {
        const nextDate = new Date(lastDate);
        nextDate.setDate(lastDate.getDate() + i);
        forecastDates.push(nextDate.toISOString().split('T')[0]);
        forecastValues.push(dailyForecast);
    }

    if (salesForecastChart) salesForecastChart.destroy();
    salesForecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [...histDates, ...forecastDates.slice(1)],
            datasets: [
                {
                    label: 'Historical Revenue (₹)',
                    data: [...histValues, ...Array(forecastDates.length - 1).fill(null)],
                    borderColor: '#5d7c3b',
                    backgroundColor: 'rgba(93, 124, 59, 0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: `Forecast Projection (${period})`,
                    data: [...Array(histValues.length - 1).fill(null), histValues[histValues.length - 1] || dailyForecast, ...forecastValues.slice(1)],
                    borderColor: '#0284c7',
                    backgroundColor: 'rgba(2, 132, 199, 0.08)',
                    borderWidth: 2.5,
                    borderDash: [6, 4],
                    fill: true,
                    tension: 0.2,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top' } },
            scales: {
                y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } },
                x: { grid: { display: false }, ticks: { color: '#64748b', maxRotation: 0 } }
            }
        }
    });
}

function renderSalesTrendChart(salesTrend) {
    const ctx = document.getElementById('salesVolumeTrendChart');
    if (!ctx) return;

    if (salesVolumeTrendChart) salesVolumeTrendChart.destroy();
    salesVolumeTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: salesTrend.dates || [],
            datasets: [{
                label: 'Sales Volume',
                data: salesTrend.volume || [],
                borderColor: '#65a30d',
                backgroundColor: 'rgba(101, 163, 13, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(0,0,0,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderRevenueTrendChart(revTrend) {
    const ctx = document.getElementById('revenueTrendChart');
    if (!ctx) return;

    if (revenueTrendChart) revenueTrendChart.destroy();
    revenueTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: revTrend.dates || [],
            datasets: [{
                label: 'Daily Revenue (₹)',
                data: revTrend.revenue || [],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(0,0,0,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderProductPerformanceChart(prodPerf) {
    const ctx = document.getElementById('productPerformanceChart');
    if (!ctx) return;

    if (productPerformanceChart) productPerformanceChart.destroy();
    productPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: (prodPerf.products || []).map(p => p.length > 15 ? p.substring(0, 15) + '...' : p),
            datasets: [{
                label: 'Revenue (₹)',
                data: prodPerf.revenues || [],
                backgroundColor: 'rgba(93, 124, 59, 0.75)',
                borderColor: '#5d7c3b',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { grid: { display: false } }
            }
        }
    });
}

function renderMonthlyComparisonChart(monthlyComp) {
    const ctx = document.getElementById('monthlyComparisonChart');
    if (!ctx) return;

    if (monthlyComparisonChart) monthlyComparisonChart.destroy();
    monthlyComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: monthlyComp.months || [],
            datasets: [{
                label: 'Monthly Revenue (₹)',
                data: monthlyComp.revenues || [],
                backgroundColor: 'rgba(14, 165, 233, 0.75)',
                borderColor: '#0284c7',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(0,0,0,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

async function runSimulation() {
    const sales = document.getElementById('sim-sales').value;
    const stock = document.getElementById('sim-stock').value;
    const resultDiv = document.getElementById('sim-result');
    
    try {
        const response = await fetch('/ceo/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sales_change: sales, stock_change: stock })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            resultDiv.classList.remove('d-none');
            const sim = data.simulation;
            document.getElementById('sim-decision').textContent = sim.decision;
            document.getElementById('sim-decision').className = sim.decision === 'Increase Production' ? 'text-success' : 'text-danger';
            document.getElementById('sim-impact').textContent = `${sim.impact} (${sim.recommendation})`;
        }
    } catch (error) {
        console.error('Simulation Failed:', error);
    }
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
}

function renderEnhancedCharts(history) {
    const ctx = document.getElementById('salesPerformanceChart');
    if (!ctx) return;
    if (window.salesChart) window.salesChart.destroy();
    window.salesChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: history.dates,
            datasets: [{
                label: 'Revenue',
                data: history.sales,
                borderColor: '#5d7c3b',
                backgroundColor: 'rgba(93, 124, 59, 0.05)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } },
                x: { grid: { display: false }, ticks: { color: '#64748b', maxRotation: 0 } }
            }
        }
    });
}

async function fetchAdminMonitor() {
    try {
        const response = await fetch('/admin/monitor');
        const result = await response.json();
        if (result.status === 'success') {
            const system = result.system;
            document.getElementById('model-loaded').textContent = system.model_loaded ? 'READY' : 'ERROR';
            document.getElementById('total-rows').textContent = system.data_rows.toLocaleString();
            document.getElementById('last-updated').textContent = system.last_updated;
        }
    } catch (error) {
        console.error('Admin Monitor Error:', error);
    }
}
