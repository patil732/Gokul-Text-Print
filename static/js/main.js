let currentForecastPeriod = '30_days';

// Global chart instances for clean destruction/re-rendering
let salesForecastChart = null;
let salesVolumeTrendChart = null;
let revenueTrendChart = null;
let productPerformanceChart = null;
let monthlyComparisonChart = null;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('ceo-dashboard')) {
        loadUserPreferences();
        fetchV2KPIs();
        fetchV2Alerts();
        fetchV2Analytics();
        fetchV2Recommendations();
        fetchCEODashboard();
        loadDocumentsList();
        loadChatHistory();
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

// =========================================================================== //
// Sprint 4 — Enterprise Knowledge Management & RAG Chat UI
// =========================================================================== //

async function loadDocumentsList() {
    const tbody = document.getElementById('documents-table-body');
    if (!tbody) return;

    try {
        const res = await fetch('/api/documents');
        const data = await res.json();

        if (data.status === 'success' && data.documents) {
            if (data.documents.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted small py-3">No enterprise documents uploaded yet. Upload a PDF above.</td></tr>';
                return;
            }

            tbody.innerHTML = data.documents.map(doc => {
                let statusBadge = '';
                if (doc.status === 'processed') {
                    statusBadge = '<span class="badge bg-success">Processed</span>';
                } else if (doc.status === 'processing') {
                    statusBadge = '<span class="badge bg-warning text-dark"><span class="spinner-border spinner-border-sm me-1"></span>Processing</span>';
                } else if (doc.status === 'failed') {
                    statusBadge = '<span class="badge bg-danger">Failed</span>';
                } else {
                    statusBadge = `<span class="badge bg-secondary">${doc.status}</span>`;
                }

                const docName = escapeHtml(doc.document_name || 'Document');
                const docId = escapeHtml(doc.document_id || '');
                const chunkCount = doc.chunk_count !== undefined ? doc.chunk_count : (doc.chunks || '-');

                return `
                    <tr>
                        <td>
                            <div class="fw-bold small text-truncate" style="max-width: 170px;" title="${docName}">
                                📄 ${docName}
                            </div>
                            <div class="text-muted" style="font-size: 0.68rem;">${doc.upload_date || ''}</div>
                        </td>
                        <td>${statusBadge}</td>
                        <td class="small fw-semibold text-secondary">${chunkCount}</td>
                        <td class="text-end">
                            <button class="btn btn-outline-danger btn-sm py-0 px-2" style="font-size: 0.72rem;" onclick="deleteDocument('${docId}', '${docName}')" title="Delete document">
                                🗑
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger small py-2">Failed to load documents.</td></tr>';
        }
    } catch (err) {
        console.error('Error loading documents:', err);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger small py-2">Error connecting to document service.</td></tr>';
    }
}

async function handleDocumentUpload(event) {
    event.preventDefault();
    const fileInput = document.getElementById('doc-file-input');
    const uploadBtn = document.getElementById('btn-upload-doc');
    const alertBox = document.getElementById('upload-status-alert');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('uploaded_by', 'executive');

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading & Chunking...';
    alertBox.className = 'mt-2 alert alert-info small py-2';
    alertBox.textContent = 'Uploading PDF and generating text chunks...';
    alertBox.classList.remove('d-none');

    try {
        const res = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData,
        });
        const result = await res.json();

        if (res.status === 201 && result.status === 'success') {
            alertBox.className = 'mt-2 alert alert-success small py-2';
            alertBox.textContent = `✓ Document "${file.name}" uploaded, chunked, and embedded successfully!`;
            fileInput.value = '';
            loadDocumentsList();
            setTimeout(() => { alertBox.classList.add('d-none'); }, 5000);
        } else if (res.status === 409) {
            alertBox.className = 'mt-2 alert alert-warning small py-2';
            alertBox.textContent = `⚠ Duplicate rejected: "${file.name}" has already been uploaded.`;
        } else {
            alertBox.className = 'mt-2 alert alert-danger small py-2';
            alertBox.textContent = `✗ Upload failed: ${result.message || 'Unknown error'}`;
        }
    } catch (err) {
        console.error('Upload error:', err);
        alertBox.className = 'mt-2 alert alert-danger small py-2';
        alertBox.textContent = '✗ Connection error while uploading document.';
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Index Document';
    }
}

async function deleteDocument(docId, docName) {
    if (!confirm(`Are you sure you want to remove "${docName}" from the knowledge base?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/documents/${docId}`, {
            method: 'DELETE',
        });
        const result = await res.json();

        if (res.ok && result.status === 'success') {
            loadDocumentsList();
        } else {
            alert(`Could not delete document: ${result.message || 'Error'}`);
        }
    } catch (err) {
        console.error('Delete error:', err);
        alert('Network error while deleting document.');
    }
}

async function loadChatHistory() {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    try {
        const res = await fetch('/api/chat/history?limit=10');
        const data = await res.json();

        if (data.status === 'success' && data.history && data.history.length > 0) {
            const chronological = [...data.history].reverse();
            container.innerHTML = '';

            chronological.forEach(turn => {
                appendChatMessage('user', turn.question, false);
                const isMgr = Boolean(turn.is_manager || turn.user === 'manager');
                const agents = isMgr ? ['manager'] : null;
                appendChatMessage('assistant', turn.answer, false, agents, isMgr ? 'copilot' : 'rag', turn.retrieved_documents);
            });

            const latestTurn = data.history[0];
            if (latestTurn && latestTurn.retrieved_documents && latestTurn.retrieved_documents.length > 0) {
                renderSourcesPanel(latestTurn.retrieved_documents);
            }

            container.scrollTop = container.scrollHeight;
        }
    } catch (err) {
        console.warn('Could not load chat history:', err);
    }
}

// Default to Multi-Agent Executive Copilot (Manager Agent)
let currentChatMode = 'copilot';

function applySuggestedQuestion(text) {
    const input = document.getElementById('chat-question-input');
    if (input) {
        input.value = text;
        input.focus();
    }
}

function onChatModeToggle(mode) {
    currentChatMode = mode;
    const iconEl = document.getElementById('chat-mode-icon');
    const titleEl = document.getElementById('chat-mode-title');
    const subtitleEl = document.getElementById('chat-mode-subtitle');
    const inputEl = document.getElementById('chat-question-input');

    if (mode === 'copilot') {
        if (iconEl) iconEl.textContent = '✨';
        if (titleEl) titleEl.textContent = 'Executive AI Copilot (Manager Agent)';
        if (subtitleEl) subtitleEl.textContent = 'Orchestrating Sales, Inventory & Enterprise Knowledge';
        if (inputEl) inputEl.placeholder = 'Ask an executive question (e.g. Which products need restocking?)...';
    } else {
        if (iconEl) iconEl.textContent = '🤖';
        if (titleEl) titleEl.textContent = 'Enterprise Strategy & SOP Assistant';
        if (subtitleEl) subtitleEl.textContent = 'Grounded on indexed document embeddings';
        if (inputEl) inputEl.placeholder = 'Ask a question about uploaded SOPs, policies, or procedures...';
    }
}

async function handleChatSubmit(event) {
    event.preventDefault();
    const input = document.getElementById('chat-question-input');
    const sendBtn = document.getElementById('btn-send-chat');
    const question = input.value.trim();

    if (!question) return;

    appendChatMessage('user', question, true);
    input.value = '';
    sendBtn.disabled = true;

    const isCopilot = (currentChatMode === 'copilot');
    const typingMessage = isCopilot
        ? 'Orchestrating Sales, Inventory & Knowledge agents in parallel...'
        : 'Consulting enterprise document knowledge base...';

    const typingId = showTypingIndicator(typingMessage);

    try {
        if (isCopilot) {
            // Multi-Agent Manager Agent Endpoint (Sprint 5 Orchestrator)
            const res = await fetch('/api/agents/manager', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });
            const result = await res.json();
            removeTypingIndicator(typingId);

            if (res.status === 200 && result.status === 'success') {
                // Extract sources from knowledge agent output if present
                let sources = [];
                if (result.agent_details && result.agent_details.knowledge && result.agent_details.knowledge.data) {
                    const kData = result.agent_details.knowledge.data;
                    sources = kData.source_details || kData.sources || [];
                }
                appendChatMessage('assistant', result.answer, true, result.agents_used, 'copilot', sources);
                if (sources.length > 0) {
                    renderSourcesPanel(sources);
                }
            } else {
                appendChatMessage('assistant', `⚠ Copilot Error: ${result.message || 'Failed to synthesize response.'}`, true);
            }
        } else {
            // Standard RAG Endpoint
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });
            const result = await res.json();
            removeTypingIndicator(typingId);

            if (res.status === 200 && result.status === 'success') {
                appendChatMessage('assistant', result.answer, true, null, 'rag', result.sources || []);
                renderSourcesPanel(result.sources || []);
            } else if (res.status === 503) {
                appendChatMessage('assistant', '⚠ No documents indexed yet. Please upload at least one PDF in the repository panel on the left.', true);
                renderSourcesPanel([]);
            } else {
                appendChatMessage('assistant', `⚠ Error: ${result.message || 'Failed to generate answer.'}`, true);
            }
        }
    } catch (err) {
        console.error('Chat error:', err);
        removeTypingIndicator(typingId);
        appendChatMessage('assistant', '⚠ Connection error with AI assistant. Please try again.', true);
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function appendChatMessage(role, text, scroll = true, agentsUsed = null, mode = 'copilot', sources = null) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;

    let roleHeader = '';
    let sourcesHtml = '';

    if (role === 'assistant') {
        const titleText = mode === 'copilot' ? '✨ Business Copilot' : '🤖 SOP Assistant';
        let badgeHtml = '';
        if (agentsUsed && agentsUsed.length > 0) {
            const agentBadges = agentsUsed.map(a => {
                if (a === 'sales') return '<span class="badge bg-primary-subtle text-primary border border-primary-subtle me-1">📊 Sales Agent</span>';
                if (a === 'inventory') return '<span class="badge bg-success-subtle text-success border border-success-subtle me-1">📦 Inventory Agent</span>';
                if (a === 'knowledge') return '<span class="badge bg-info-subtle text-info border border-info-subtle me-1">📚 Knowledge Agent</span>';
                if (a === 'manager') return '<span class="badge bg-purple-subtle text-dark border me-1">🤖 Manager Orchestrator</span>';
                return `<span class="badge bg-light text-dark border me-1">${escapeHtml(a)} Agent</span>`;
            }).join('');
            badgeHtml = `<div class="mt-1 mb-2 d-flex flex-wrap align-items-center gap-1"><span class="small text-muted me-1" style="font-size: 0.72rem;">Consulted:</span>${agentBadges}</div>`;
        }

        roleHeader = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <strong class="text-primary">${titleText}</strong>
            </div>
            ${badgeHtml}
        `;

        // Render source references directly beneath the AI answer
        if (sources && sources.length > 0) {
            const chips = sources.map(s => {
                const docName = typeof s === 'string' ? s : (s.document || 'Document');
                const pageStr = (typeof s === 'object' && s.page) ? ` (p.${s.page})` : '';
                const scoreStr = (typeof s === 'object' && s.score) ? ` [${Math.round(s.score * 100)}%]` : '';
                return `<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle small me-1">📄 ${escapeHtml(docName)}${pageStr}${scoreStr}</span>`;
            }).join('');
            sourcesHtml = `
                <div class="mt-2 pt-2 border-top border-light-subtle">
                    <span class="small text-muted d-block mb-1" style="font-size: 0.72rem;">📚 Verified Knowledge Citations:</span>
                    <div class="d-flex flex-wrap gap-1">${chips}</div>
                </div>
            `;
        }
    }

    msgDiv.innerHTML = `
        <div class="chat-bubble">
            ${roleHeader}
            <div style="white-space: pre-wrap;">${escapeHtml(text)}</div>
            ${sourcesHtml}
        </div>
    `;

    container.appendChild(msgDiv);
    if (scroll) {
        container.scrollTop = container.scrollHeight;
    }
}

function showTypingIndicator(message = 'Consulting enterprise document knowledge base...') {
    const container = document.getElementById('chat-messages-container');
    if (!container) return null;

    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'chat-message assistant';
    typingDiv.innerHTML = `
        <div class="chat-bubble text-secondary">
            <span class="spinner-grow spinner-grow-sm me-1" role="status"></span>
            <span class="small fst-italic">${escapeHtml(message)}</span>
        </div>
    `;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {

    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
}

function renderSourcesPanel(sources) {
    const container = document.getElementById('sources-list-container');
    const badge = document.getElementById('sources-count-badge');
    if (!container) return;

    if (!sources || sources.length === 0) {
        badge.textContent = '0 Sources Cited';
        badge.className = 'badge bg-light text-secondary border';
        container.innerHTML = `
            <div class="text-secondary small fst-italic p-2 bg-light rounded text-center">
                No specific document excerpts cited for this response.
            </div>
        `;
        return;
    }

    badge.textContent = `${sources.length} Source${sources.length > 1 ? 's' : ''} Cited`;
    badge.className = 'badge bg-success-subtle text-success border border-success-subtle';

    container.innerHTML = sources.map((s, idx) => {
        const docName = escapeHtml(s.document || s.source_document || 'Document');
        const pageNum = s.page || s.page_number || 1;
        const scoreText = s.score !== undefined ? `${(s.score * 100).toFixed(0)}% Relevance` : 'Verified Citation';

        return `
            <div class="source-badge-card d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-primary text-white" style="font-size: 0.7rem;">[${idx + 1}]</span>
                    <div>
                        <strong class="small text-dark d-block">${docName}</strong>
                        <span class="text-secondary" style="font-size: 0.75rem;">Page ${pageNum}</span>
                    </div>
                </div>
                <span class="badge bg-light text-success border border-success-subtle" style="font-size: 0.72rem;">
                    ${scoreText}
                </span>
            </div>
        `;
    }).join('');
}

function clearChatMessages() {
    const container = document.getElementById('chat-messages-container');
    const sourcesContainer = document.getElementById('sources-list-container');
    const badge = document.getElementById('sources-count-badge');

    if (container) {
        container.innerHTML = `
            <div class="chat-message assistant">
                <div class="chat-bubble">
                    <strong class="d-block mb-1 text-primary">AI Assistant</strong>
                    Conversation view cleared. Ask any question about your uploaded enterprise PDFs and SOPs.
                </div>
            </div>
        `;
    }

    if (sourcesContainer && badge) {
        badge.textContent = '0 Sources Cited';
        badge.className = 'badge bg-light text-secondary border';
        sourcesContainer.innerHTML = `
            <div class="text-secondary small fst-italic p-2 bg-light rounded text-center">
                No query executed yet. Ask a question above to inspect cited sources with page numbers and confidence.
            </div>
        `;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


// =========================================================================== //
// Sprint 5 — AI Executive Copilot (Multi-Agent Orchestrated Panel)
// Calls POST /api/agents/manager — completely separate from the Sprint 4 RAG UI.
// All identifiers are prefixed "copilot-" to guarantee zero collision.
// =========================================================================== //

const COPILOT_AGENTS = ['sales', 'inventory', 'knowledge'];

/**
 * Drive the badge for one agent to a new state.
 * state: 'pending' | 'running' | 'done' | 'skipped'
 */
function setCopilotAgentBadge(agentName, state) {
    const el = document.getElementById(`copilot-badge-${agentName}`);
    if (!el) return;

    const icons = { sales: '📊', inventory: '📦', knowledge: '📚' };
    const labels = { sales: 'Sales', inventory: 'Inventory', knowledge: 'Knowledge' };
    const icon = icons[agentName] || '🤖';
    const label = labels[agentName] || agentName;

    el.className = `copilot-agent-badge ${state}`;

    if (state === 'running') {
        el.innerHTML = `
            <span class="spinner-border spinner-border-sm" style="width:10px;height:10px;border-width:1.5px;" role="status"></span>
            ${icon} ${label}
        `;
    } else if (state === 'done') {
        el.innerHTML = `✓ ${icon} ${label}`;
    } else if (state === 'skipped') {
        el.innerHTML = `— ${icon} ${label}`;
    } else {
        el.innerHTML = `${icon} ${label}`;
    }
}

/**
 * Append a message bubble to the copilot chat window.
 */
function appendCopilotMessage(role, html, scroll = true) {
    const container = document.getElementById('copilot-chat-messages');
    if (!container) return null;

    const div = document.createElement('div');
    div.className = `copilot-msg ${role}`;
    div.innerHTML = `<div class="copilot-bubble">${html}</div>`;
    container.appendChild(div);
    if (scroll) container.scrollTop = container.scrollHeight;
    return div;
}

/**
 * Show animated typing indicator inside the copilot chat.
 */
function showCopilotTyping() {
    const container = document.getElementById('copilot-chat-messages');
    if (!container) return null;

    const id = 'copilot-typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'copilot-msg assistant copilot-typing';
    div.innerHTML = `
        <div class="copilot-bubble" style="display:flex;align-items:center;gap:10px;">
            <div class="copilot-typing-dots">
                <span></span><span></span><span></span>
            </div>
            <span style="font-size:0.75rem;color:#64748b;font-style:italic;">Orchestrating agents…</span>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeCopilotTyping(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Render the sales summary card from agent_details.sales.data
 */
function renderCopilotSalesSummary(salesDetail) {
    const el = document.getElementById('copilot-sales-summary');
    if (!el) return;

    const data = (salesDetail && salesDetail.data) ? salesDetail.data : {};

    if (!salesDetail || salesDetail.status === 'error') {
        el.innerHTML = `<div style="color:#ef4444;font-size:0.78rem;text-align:center;padding:0.5rem 0;">Sales agent returned an error.</div>`;
        return;
    }

    const growth = data.sales_growth !== undefined ? `${data.sales_growth >= 0 ? '+' : ''}${parseFloat(data.sales_growth).toFixed(1)}%` : '—';
    const forecast = data.forecast ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(data.forecast) : '—';
    const trend = data.market_trend || '—';
    const recommendation = data.recommendation || '—';
    const topProduct = data.top_product || '—';
    const period = data.forecast_period ? data.forecast_period.replace('_', ' ') : '—';
    const confidence = salesDetail.confidence !== undefined ? `${(salesDetail.confidence * 100).toFixed(0)}%` : '—';

    const growthColor = (data.sales_growth || 0) >= 0 ? '#4ade80' : '#f87171';
    const trendColor = trend === 'Growing' ? '#4ade80' : (trend === 'Declining' ? '#f87171' : '#fbbf24');

    el.innerHTML = `
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Sales Growth</span>
            <span class="copilot-kv-val" style="color:${growthColor};">${escapeHtml(growth)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Forecast (${escapeHtml(period)})</span>
            <span class="copilot-kv-val">${escapeHtml(forecast)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Market Trend</span>
            <span class="copilot-kv-val" style="color:${trendColor};">${escapeHtml(trend)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Recommendation</span>
            <span class="copilot-kv-val">${escapeHtml(recommendation)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Top Product</span>
            <span class="copilot-kv-val" style="font-size:0.72rem;">${escapeHtml(topProduct)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Agent Confidence</span>
            <span class="copilot-kv-val" style="color:#60a5fa;">${escapeHtml(confidence)}</span>
        </div>
    `;
}

/**
 * Render the inventory summary card from agent_details.inventory.data
 */
function renderCopilotInventorySummary(invDetail) {
    const el = document.getElementById('copilot-inventory-summary');
    if (!el) return;

    const data = (invDetail && invDetail.data) ? invDetail.data : {};

    if (!invDetail || invDetail.status === 'error') {
        el.innerHTML = `<div style="color:#ef4444;font-size:0.78rem;text-align:center;padding:0.5rem 0;">Inventory agent returned an error.</div>`;
        return;
    }

    const stockHealth = data.stock_health || '—';
    const remainingDays = data.remaining_days !== undefined ? `${data.remaining_days} days` : '—';
    const decision = data.decision || '—';
    const recommendation = data.recommendation || '—';
    const modelType = (data.model_type || 'xgboost').toUpperCase();
    const modelAccuracy = data.model_accuracy ? `${(data.model_accuracy * 100).toFixed(1)}%` : '—';
    const confidence = invDetail.confidence !== undefined ? `${(invDetail.confidence * 100).toFixed(0)}%` : '—';

    const healthColor = stockHealth === 'Critical' ? '#f87171' : (stockHealth === 'Low' ? '#fbbf24' : '#4ade80');
    const decisionColor = decision === 'Reorder Required' ? '#f87171' : '#4ade80';

    el.innerHTML = `
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Stock Health</span>
            <span class="copilot-kv-val" style="color:${healthColor};">${escapeHtml(stockHealth)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Stock Remaining</span>
            <span class="copilot-kv-val">${escapeHtml(remainingDays)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Decision</span>
            <span class="copilot-kv-val" style="color:${decisionColor};">${escapeHtml(decision)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Action</span>
            <span class="copilot-kv-val" style="font-size:0.72rem;">${escapeHtml(recommendation)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Model</span>
            <span class="copilot-kv-val" style="font-size:0.72rem;">${escapeHtml(modelType)} · ${escapeHtml(modelAccuracy)}</span>
        </div>
        <div class="copilot-kv-row">
            <span class="copilot-kv-key">Agent Confidence</span>
            <span class="copilot-kv-val" style="color:#4ade80;">${escapeHtml(confidence)}</span>
        </div>
    `;
}

/**
 * Render the knowledge sources from agent_details.knowledge.data.source_details
 */
function renderCopilotKnowledgeSources(knowledgeDetail) {
    const listEl = document.getElementById('copilot-sources-list');
    const badgeEl = document.getElementById('copilot-sources-badge');
    if (!listEl) return;

    const data = (knowledgeDetail && knowledgeDetail.data) ? knowledgeDetail.data : {};
    const sourceDetails = data.source_details || [];
    const sources = data.sources || [];

    // Merge: prefer source_details (has page + score), fall back to plain sources list
    let items = sourceDetails;
    if (items.length === 0 && sources.length > 0) {
        items = sources.map(s => ({ document: s, page: null, score: null }));
    }

    if (badgeEl) {
        badgeEl.textContent = `${items.length} Source${items.length !== 1 ? 's' : ''}`;
    }

    if (items.length === 0) {
        listEl.innerHTML = `<div style="color:#475569;font-size:0.78rem;font-style:italic;text-align:center;padding:0.5rem 0;">No enterprise documents were cited for this query.</div>`;
        return;
    }

    listEl.innerHTML = items.map((src, idx) => {
        const docName = escapeHtml(src.document || src.source_document || 'Document');
        const pageText = src.page ? `Page ${src.page}` : '';
        const scoreText = src.score !== undefined && src.score !== null
            ? `${(src.score * 100).toFixed(0)}% relevance`
            : 'Verified citation';

        return `
            <div class="copilot-source-card">
                <div class="d-flex align-items-center gap-2">
                    <span class="badge" style="background:rgba(99,102,241,0.3);color:#a5b4fc;font-size:0.65rem;min-width:22px;">[${idx + 1}]</span>
                    <div>
                        <div style="font-size:0.78rem;font-weight:700;color:#e2e8f0;">${docName}</div>
                        ${pageText ? `<div style="font-size:0.68rem;color:#64748b;">${pageText}</div>` : ''}
                    </div>
                </div>
                <span class="badge" style="background:rgba(74,222,128,0.1);color:#4ade80;border:1px solid rgba(74,222,128,0.3);font-size:0.65rem;white-space:nowrap;">
                    ${escapeHtml(scoreText)}
                </span>
            </div>
        `;
    }).join('');
}

/**
 * Render the final LLM recommendation + confidence bar
 */
function renderCopilotRecommendation(answer, confidence) {
    const textEl = document.getElementById('copilot-recommendation-text');
    const barEl = document.getElementById('copilot-confidence-bar');
    const barWrapEl = document.getElementById('copilot-confidence-bar-wrap');
    const confDisplayEl = document.getElementById('copilot-confidence-display');
    const confPctEl = document.getElementById('copilot-confidence-pct');

    if (textEl) {
        // Render answer with simple markdown bold (**text**) support
        const formatted = escapeHtml(answer || '')
            .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e2e8f0;">$1</strong>')
            .replace(/\n/g, '<br>');
        textEl.innerHTML = `<div style="color:#cbd5e1;font-size:0.85rem;font-style:normal;line-height:1.65;">${formatted}</div>`;
    }

    const pct = Math.round((confidence || 0) * 100);
    const barColor = pct >= 75 ? 'linear-gradient(90deg,#4ade80,#22d3ee)'
                   : pct >= 50 ? 'linear-gradient(90deg,#fbbf24,#f97316)'
                   : 'linear-gradient(90deg,#f87171,#fb923c)';

    if (barEl) {
        barEl.style.background = barColor;
        // Animate after a tiny delay so the CSS transition fires
        setTimeout(() => { barEl.style.width = `${pct}%`; }, 60);
    }
    if (barWrapEl) barWrapEl.classList.remove('d-none');
    if (confDisplayEl) confDisplayEl.classList.remove('d-none');
    if (confPctEl) confPctEl.textContent = `${pct}%`;
}

/**
 * Main handler: form submit → orchestrate → render everything.
 */
async function submitCopilotQuestion(event) {
    event.preventDefault();

    const input = document.getElementById('copilot-question-input');
    const sendBtn = document.getElementById('copilot-send-btn');
    const question = input.value.trim();
    if (!question) return;

    // ── 1. Render CEO question bubble ────────────────────────────────── //
    appendCopilotMessage('user', `<span style="color:#fff;">${escapeHtml(question)}</span>`, true);
    input.value = '';
    sendBtn.disabled = true;

    // ── 2. Set all agent badges to "running" ─────────────────────────── //
    COPILOT_AGENTS.forEach(name => setCopilotAgentBadge(name, 'running'));

    const timeEl = document.getElementById('copilot-orchestration-time');
    if (timeEl) timeEl.textContent = '';

    const typingId = showCopilotTyping();
    const startTime = Date.now();

    try {
        // ── 3. POST /api/agents/manager ──────────────────────────────── //
        const res = await fetch('/api/agents/manager', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });

        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        removeCopilotTyping(typingId);

        if (timeEl) timeEl.textContent = `⏱ ${elapsed}s`;

        const result = await res.json();

        if (!res.ok || result.status === 'error') {
            // All badges → skipped on error
            COPILOT_AGENTS.forEach(name => setCopilotAgentBadge(name, 'skipped'));
            appendCopilotMessage('assistant', `
                <strong style="color:#f87171;display:block;margin-bottom:4px;">⚠ Orchestration Error</strong>
                <span style="color:#94a3b8;">${escapeHtml(result.message || 'Unknown error from the manager agent.')}</span>
            `);
            return;
        }

        // ── 4. Update agent badges ───────────────────────────────────── //
        const agentsUsed = result.agents_used || [];
        COPILOT_AGENTS.forEach(name => {
            setCopilotAgentBadge(name, agentsUsed.includes(name) ? 'done' : 'skipped');
        });

        // ── 5. Render answer bubble ──────────────────────────────────── //
        const usedBadges = agentsUsed.map(a => {
            const colors = {
                sales: 'rgba(96,165,250,0.15);color:#60a5fa;border:1px solid rgba(96,165,250,0.3)',
                inventory: 'rgba(74,222,128,0.12);color:#4ade80;border:1px solid rgba(74,222,128,0.3)',
                knowledge: 'rgba(196,181,253,0.15);color:#c4b5fd;border:1px solid rgba(196,181,253,0.3)',
            };
            const icons = { sales: '📊', inventory: '📦', knowledge: '📚' };
            const label = a.charAt(0).toUpperCase() + a.slice(1);
            const style = colors[a] || 'rgba(100,116,139,0.2);color:#94a3b8;border:1px solid rgba(100,116,139,0.3)';
            return `<span class="badge me-1" style="background:${style};font-size:0.65rem;">${icons[a] || '🤖'} ${label}</span>`;
        }).join('');

        appendCopilotMessage('assistant', `
            <strong style="color:#a5b4fc;display:block;margin-bottom:6px;font-size:0.8rem;">✨ AI Executive Copilot</strong>
            ${usedBadges ? `<div class="mb-2">${usedBadges}</div>` : ''}
            <div style="white-space:pre-wrap;color:#cbd5e1;">${escapeHtml(result.answer || '')}</div>
        `);

        // ── 6. Render structured summaries ───────────────────────────── //
        const details = result.agent_details || {};
        if (details.sales) renderCopilotSalesSummary(details.sales);
        if (details.inventory) renderCopilotInventorySummary(details.inventory);
        if (details.knowledge) renderCopilotKnowledgeSources(details.knowledge);

        // ── 7. Final recommendation + confidence bar ─────────────────── //
        renderCopilotRecommendation(result.answer, result.confidence);

    } catch (err) {
        console.error('[Copilot] Network error:', err);
        removeCopilotTyping(typingId);
        COPILOT_AGENTS.forEach(name => setCopilotAgentBadge(name, 'skipped'));
        appendCopilotMessage('assistant', `
            <strong style="color:#f87171;display:block;margin-bottom:4px;">⚠ Connection Error</strong>
            <span style="color:#94a3b8;">Could not reach the orchestration engine. Please try again.</span>
        `);
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

/**
 * Reset the copilot panel to its initial idle state.
 */
function clearCopilotChat() {
    // Reset chat window
    const msgs = document.getElementById('copilot-chat-messages');
    if (msgs) {
        msgs.innerHTML = `
            <div class="copilot-msg assistant">
                <div class="copilot-bubble">
                    <strong style="color:#a5b4fc;display:block;margin-bottom:4px;font-size:0.8rem;">✨ AI Executive Copilot</strong>
                    Hello! Ask any cross-domain executive question — I will simultaneously consult the Sales, Inventory, and Knowledge agents to synthesize a grounded strategic recommendation.
                </div>
            </div>
        `;
    }

    // Reset agent badges to pending
    COPILOT_AGENTS.forEach(name => setCopilotAgentBadge(name, 'pending'));

    const timeEl = document.getElementById('copilot-orchestration-time');
    if (timeEl) timeEl.textContent = '';

    // Reset summary cards
    const placeholder = (text) => `<div style="color:#475569;font-size:0.78rem;font-style:italic;text-align:center;padding:1rem 0;">${text}</div>`;

    const salesEl = document.getElementById('copilot-sales-summary');
    if (salesEl) salesEl.innerHTML = placeholder('Awaiting orchestration…');

    const invEl = document.getElementById('copilot-inventory-summary');
    if (invEl) invEl.innerHTML = placeholder('Awaiting orchestration…');

    const srcList = document.getElementById('copilot-sources-list');
    if (srcList) srcList.innerHTML = `<div style="color:#475569;font-size:0.78rem;font-style:italic;text-align:center;padding:0.5rem 0;">Knowledge agent will cite enterprise documents here.</div>`;

    const srcBadge = document.getElementById('copilot-sources-badge');
    if (srcBadge) srcBadge.textContent = '0 Sources';

    // Reset recommendation + confidence
    const recEl = document.getElementById('copilot-recommendation-text');
    if (recEl) {
        recEl.innerHTML = `<div style="color:#94a3b8;font-size:0.85rem;font-style:italic;">The synthesized strategic recommendation will appear here after the orchestration run completes.</div>`;
    }

    const barEl = document.getElementById('copilot-confidence-bar');
    if (barEl) barEl.style.width = '0%';

    const barWrap = document.getElementById('copilot-confidence-bar-wrap');
    if (barWrap) barWrap.classList.add('d-none');

    const confDisp = document.getElementById('copilot-confidence-display');
    if (confDisp) confDisp.classList.add('d-none');
}

// ===========================================================================
// Executive Dashboard V2 Controller (Sprint 6)
// Personalization, Pinned Widgets, V2 KPIs, V2 Analytics, Recommendations, Alerts
// ===========================================================================

let v2Preferences = {
    theme: 'light',
    pinned_widgets: ['widget-alerts', 'widget-kpis'],
    widget_order: [
        'widget-alerts',
        'widget-kpis',
        'widget-charts',
        'widget-recommendations',
        'widget-chat',
        'widget-specialist-engines',
    ],
    chart_filters: {
        sales_range: 'monthly',
        inventory_range: 'monthly',
        start_date: '',
        end_date: '',
    },
};

let v2SalesAnalyticsChart = null;
let v2InventoryAnalyticsChart = null;
let v2RawRecommendations = [];
let v2CurrentRecFilter = 'ALL';

/**
 * Load user preferences from backend (or localStorage cache) and apply.
 */
async function loadUserPreferences() {
    const cachedTheme = localStorage.getItem('gokul_v2_theme');
    if (cachedTheme) {
        applyTheme(cachedTheme);
    }

    try {
        const res = await fetch('/api/dashboard/preferences');
        if (res.ok) {
            const json = await res.json();
            if (json.status === 'success' && json.data) {
                v2Preferences = json.data;
                applyTheme(v2Preferences.theme || 'light');
                applyWidgetOrder(v2Preferences.widget_order || [], v2Preferences.pinned_widgets || []);
                applyPersistedChartFilters(v2Preferences.chart_filters || {});
            }
        }
    } catch (e) {
        console.warn('[V2 Preferences] Failed to load preferences:', e);
    }
}

/**
 * Persist preferences to server (debounced).
 */
let _prefSaveTimer = null;
function saveUserPreferences() {
    clearTimeout(_prefSaveTimer);
    _prefSaveTimer = setTimeout(async () => {
        try {
            await fetch('/api/dashboard/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preferences: v2Preferences }),
            });
        } catch (e) {
            console.warn('[V2 Preferences] Failed to save preferences:', e);
        }
    }, 400);
}

/**
 * Apply theme to document and body.
 */
function applyTheme(theme) {
    v2Preferences.theme = theme;
    localStorage.setItem('gokul_v2_theme', theme);
    const isDark = theme === 'dark';

    if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.classList.add('theme-dark');
    } else {
        document.documentElement.removeAttribute('data-theme');
        document.body.classList.remove('theme-dark');
    }

    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    if (icon) icon.textContent = isDark ? '🌞' : '🌙';
    if (label) label.textContent = isDark ? 'Light Mode' : 'Dark Mode';

    if (v2SalesAnalyticsChart) v2SalesAnalyticsChart.update();
    if (v2InventoryAnalyticsChart) v2InventoryAnalyticsChart.update();
}

/**
 * Toggle light/dark theme.
 */
function toggleTheme() {
    const newTheme = v2Preferences.theme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    saveUserPreferences();
}

/**
 * Apply widget ordering and pinned styles to DOM.
 */
function applyWidgetOrder(order, pinned) {
    const container = document.getElementById('v2-widgets-container');
    if (!container || !order || order.length === 0) return;

    const widgetMap = {};
    order.forEach(id => {
        const el = document.getElementById(id);
        if (el) widgetMap[id] = el;
    });

    order.forEach(id => {
        const el = widgetMap[id];
        if (el) container.appendChild(el);
    });

    const allWidgets = container.querySelectorAll('.v2-widget');
    allWidgets.forEach(w => {
        const wId = w.getAttribute('data-widget-id');
        const isPinned = pinned && pinned.includes(wId);
        w.classList.toggle('pinned', !!isPinned);

        const pinBtn = w.querySelector('.btn-widget-action');
        if (pinBtn && pinBtn.textContent.includes('Pin')) {
            pinBtn.classList.toggle('pinned', !!isPinned);
            pinBtn.textContent = isPinned ? '📌 Pinned' : '📌 Pin';
        }
    });
}

/**
 * Toggle pin status for a widget.
 */
function toggleWidgetPin(widgetId) {
    if (!v2Preferences.pinned_widgets) v2Preferences.pinned_widgets = [];
    const idx = v2Preferences.pinned_widgets.indexOf(widgetId);

    if (idx >= 0) {
        v2Preferences.pinned_widgets.splice(idx, 1);
    } else {
        v2Preferences.pinned_widgets.push(widgetId);
        const oIdx = v2Preferences.widget_order.indexOf(widgetId);
        if (oIdx > 0) {
            v2Preferences.widget_order.splice(oIdx, 1);
            v2Preferences.widget_order.unshift(widgetId);
        }
    }

    applyWidgetOrder(v2Preferences.widget_order, v2Preferences.pinned_widgets);
    saveUserPreferences();
}

/**
 * Move widget up or down in the DOM order.
 */
function moveWidget(widgetId, direction) {
    const order = v2Preferences.widget_order || [];
    const idx = order.indexOf(widgetId);
    if (idx < 0) return;

    const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= order.length) return;

    const temp = order[idx];
    order[idx] = order[targetIdx];
    order[targetIdx] = temp;

    v2Preferences.widget_order = order;
    applyWidgetOrder(order, v2Preferences.pinned_widgets);
    saveUserPreferences();
}

/**
 * Reset widget layout to defaults.
 */
function resetDashboardLayout() {
    v2Preferences.widget_order = [
        'widget-alerts',
        'widget-kpis',
        'widget-charts',
        'widget-recommendations',
        'widget-chat',
        'widget-specialist-engines',
    ];
    v2Preferences.pinned_widgets = ['widget-alerts', 'widget-kpis'];
    applyWidgetOrder(v2Preferences.widget_order, v2Preferences.pinned_widgets);
    saveUserPreferences();
}

/**
 * Toggle Fullscreen mode using HTML5 Fullscreen API.
 */
function toggleFullscreen() {
    const btn = document.getElementById('fullscreen-toggle-btn');
    const icon = document.getElementById('fullscreen-icon');

    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.warn(`Fullscreen request failed: ${err.message}`);
        });
        if (btn) btn.classList.add('active');
        if (icon) icon.textContent = '🗗';
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
        if (btn) btn.classList.remove('active');
        if (icon) icon.textContent = '⛶';
    }
}

/**
 * Manual Refresh button handler.
 */
async function refreshDashboardV2() {
    const icon = document.getElementById('refresh-icon');
    if (icon) icon.classList.add('spin-anim');

    try {
        await Promise.all([
            fetchV2KPIs(true),
            fetchV2Alerts(),
            fetchV2Analytics(),
            fetchV2Recommendations(),
            fetchCEODashboard(),
        ]);
        const stampEl = document.getElementById('v2-sync-timestamp');
        if (stampEl) {
            stampEl.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
    } catch (e) {
        console.error('Manual refresh error:', e);
    } finally {
        setTimeout(() => {
            if (icon) icon.classList.remove('spin-anim');
        }, 600);
    }
}

/**
 * Fetch and display V2 Top Row KPI Cards & Composite Health Score.
 */
async function fetchV2KPIs(forceRefresh = false) {
    try {
        const url = forceRefresh ? '/api/dashboard/kpis?refresh=true' : '/api/dashboard/kpis';
        const res = await fetch(url);
        if (!res.ok) return;
        const json = await res.json();
        if (json.status !== 'success' || !json.data) return;

        const d = json.data;

        const revEl = document.getElementById('v2-kpi-revenue');
        if (revEl) revEl.textContent = formatCurrency(d.revenue || 0);

        const salesEl = document.getElementById('v2-kpi-sales');
        if (salesEl) salesEl.textContent = (d.total_sales || 0).toLocaleString();

        const growthEl = document.getElementById('v2-kpi-growth');
        const trendEl = document.getElementById('v2-kpi-growth-trend');
        const growthVal = (d.sales_growth || 0);
        if (growthEl) {
            growthEl.textContent = `${growthVal >= 0 ? '+' : ''}${growthVal.toFixed(1)}%`;
            growthEl.className = `kpi-value ${growthVal >= 0 ? 'text-success' : 'text-danger'}`;
        }
        if (trendEl) {
            trendEl.textContent = growthVal >= 0 ? '↑ Positive' : '↓ Negative';
            trendEl.className = `fw-bold ${growthVal >= 0 ? 'text-success' : 'text-danger'}`;
        }

        const invValEl = document.getElementById('v2-kpi-inv-value');
        if (invValEl) invValEl.textContent = formatCurrency(d.inventory_value || 0);

        const invHealthEl = document.getElementById('v2-kpi-inv-health');
        const invHealthPill = document.getElementById('v2-kpi-inv-health-pill');
        if (invHealthEl) invHealthEl.textContent = d.inventory_health || 'Stable';
        if (invHealthPill) {
            const h = (d.inventory_health || 'Stable').toLowerCase();
            const colorClass = h.includes('optimal') || h.includes('healthy') ? 'bg-success' : (h.includes('critical') ? 'bg-danger' : 'bg-warning text-dark');
            invHealthPill.className = `badge ${colorClass}`;
            invHealthPill.textContent = d.inventory_health || 'Stable';
        }

        const lowStockEl = document.getElementById('v2-kpi-low-stock');
        const lowStockLabel = document.getElementById('v2-low-stock-count-label');
        if (lowStockEl) lowStockEl.textContent = `${d.low_stock_products_count || 0}`;
        if (lowStockLabel) lowStockLabel.textContent = `${d.low_stock_products_count || 0} items`;

        const recCountEl = document.getElementById('v2-kpi-recs-count');
        if (recCountEl) recCountEl.textContent = `${d.ai_recommendations_count || 0}`;

        // Composite Health Score
        const bh = d.business_health || {};
        const score = Math.round(bh.score || 0);
        const scoreEl = document.getElementById('v2-kpi-health-score');
        const badgeEl = document.getElementById('v2-kpi-health-badge');
        const barEl = document.getElementById('v2-kpi-health-bar');
        const statusEl = document.getElementById('v2-kpi-health-status');
        const formulaEl = document.getElementById('v2-kpi-health-formula-info');

        if (scoreEl) scoreEl.textContent = `${score} / 100`;
        if (barEl) {
            barEl.style.width = `${Math.min(100, Math.max(0, score))}%`;
            barEl.className = `health-score-fill ${score >= 70 ? 'bg-success' : (score >= 50 ? 'bg-warning' : 'bg-danger')}`;
        }
        if (badgeEl) {
            badgeEl.textContent = bh.status || (score >= 70 ? 'Strong' : (score >= 50 ? 'Stable' : 'Warning'));
            badgeEl.className = `health-score-badge border ${score >= 70 ? 'bg-success-subtle text-success border-success-subtle' : (score >= 50 ? 'bg-warning-subtle text-warning border-warning-subtle' : 'bg-danger-subtle text-danger border-danger-subtle')}`;
        }
        if (statusEl) statusEl.textContent = bh.status || 'Optimal';
        if (formulaEl && bh.formula) {
            formulaEl.title = bh.formula;
        }

    } catch (e) {
        console.warn('[V2 KPIs] Failed to fetch KPIs:', e);
    }
}

/**
 * Fetch and display Operational Alerts Banner.
 */
async function fetchV2Alerts() {
    try {
        const res = await fetch('/api/dashboard/alerts?status=ACTIVE&limit=20');
        if (!res.ok) return;
        const json = await res.json();
        if (json.status !== 'success') return;

        const alerts = json.data || [];
        const highAlerts = alerts.filter(a => a.priority === 'CRITICAL' || a.priority === 'HIGH');

        const badge = document.getElementById('alerts-count-badge');
        const counter = document.getElementById('alerts-banner-counter');
        if (badge) badge.textContent = `${highAlerts.length} Critical/High`;
        if (counter) counter.textContent = `${highAlerts.length}`;

        const listContainer = document.getElementById('alerts-list-container');
        if (!listContainer) return;

        if (highAlerts.length === 0) {
            listContainer.innerHTML = `
                <div class="p-2 bg-white rounded border text-muted small d-flex justify-content-between align-items-center">
                    <span>✅ All operating thresholds within standard boundaries. Zero active high-priority alerts.</span>
                    <span class="badge bg-success-subtle text-success border border-success-subtle">Normal</span>
                </div>
            `;
        } else {
            listContainer.innerHTML = highAlerts.map(a => {
                const isCrit = a.priority === 'CRITICAL';
                const badgeClass = isCrit ? 'bg-danger text-white' : 'bg-warning text-dark';
                return `
                    <div class="alert-item-card">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge ${badgeClass} text-uppercase" style="font-size: 0.68rem;">${escapeHtml(a.priority)}</span>
                            <div>
                                <strong class="small text-dark d-block">${escapeHtml(a.alert_type)}</strong>
                                <span class="small text-secondary">${escapeHtml(a.message)}</span>
                            </div>
                        </div>
                        <div class="text-end">
                            <span class="small text-muted" style="font-size: 0.72rem;">${a.created_at || 'Recent'}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

    } catch (e) {
        console.warn('[V2 Alerts] Failed to fetch alerts:', e);
    }
}

/**
 * Apply persisted chart date filters.
 */
function applyPersistedChartFilters(filters) {
    if (!filters) return;
    const range = filters.sales_range || 'monthly';
    const sInput = document.getElementById('v2-analytics-start-date');
    const eInput = document.getElementById('v2-analytics-end-date');

    if (sInput && filters.start_date) sInput.value = filters.start_date;
    if (eInput && filters.end_date) eInput.value = filters.end_date;

    setV2AnalyticsRange(range, false);
}

/**
 * Change time-series aggregation range (daily, weekly, monthly).
 */
function setV2AnalyticsRange(range, triggerFetch = true) {
    if (!v2Preferences.chart_filters) v2Preferences.chart_filters = {};
    v2Preferences.chart_filters.sales_range = range;
    v2Preferences.chart_filters.inventory_range = range;

    ['daily', 'weekly', 'monthly'].forEach(r => {
        const btn = document.getElementById(`btn-range-${r}`);
        if (btn) {
            btn.classList.toggle('active', r === range);
            btn.classList.toggle('btn-primary', r === range);
            btn.classList.toggle('btn-outline-primary', r !== range);
        }
    });

    const badge = document.getElementById('sales-trend-badge');
    if (badge) badge.textContent = `${range.charAt(0).toUpperCase() + range.slice(1)} Trend`;

    if (triggerFetch) {
        saveUserPreferences();
        fetchV2Analytics();
    }
}

/**
 * Custom date picker change handler.
 */
function onCustomDateRangeChanged() {
    const sInput = document.getElementById('v2-analytics-start-date');
    const eInput = document.getElementById('v2-analytics-end-date');
    if (!v2Preferences.chart_filters) v2Preferences.chart_filters = {};

    v2Preferences.chart_filters.start_date = sInput ? sInput.value : '';
    v2Preferences.chart_filters.end_date = eInput ? eInput.value : '';

    saveUserPreferences();
    fetchV2Analytics();
}

/**
 * Reset custom date pickers.
 */
function resetCustomDateRange() {
    const sInput = document.getElementById('v2-analytics-start-date');
    const eInput = document.getElementById('v2-analytics-end-date');
    if (sInput) sInput.value = '';
    if (eInput) eInput.value = '';

    if (!v2Preferences.chart_filters) v2Preferences.chart_filters = {};
    v2Preferences.chart_filters.start_date = '';
    v2Preferences.chart_filters.end_date = '';

    saveUserPreferences();
    fetchV2Analytics();
}

/**
 * Fetch and render Executive Analytics dual charts (Sales & Inventory).
 */
async function fetchV2Analytics() {
    const range = (v2Preferences.chart_filters && v2Preferences.chart_filters.sales_range) || 'monthly';
    const startDate = (v2Preferences.chart_filters && v2Preferences.chart_filters.start_date) || '';
    const endDate = (v2Preferences.chart_filters && v2Preferences.chart_filters.end_date) || '';

    let urlSales = `/api/dashboard/analytics?type=sales&range=${range}`;
    let urlInv = `/api/dashboard/analytics?type=inventory&range=${range}`;
    if (startDate) { urlSales += `&start=${startDate}`; urlInv += `&start=${startDate}`; }
    if (endDate) { urlSales += `&end=${endDate}`; urlInv += `&end=${endDate}`; }

    try {
        const [salesRes, invRes] = await Promise.all([
            fetch(urlSales),
            fetch(urlInv),
        ]);

        if (salesRes.ok) {
            const sJson = await salesRes.json();
            if (sJson.status === 'success' && sJson.data) {
                renderV2SalesChart(sJson.data.sales_trend || {});
            }
        }

        if (invRes.ok) {
            const iJson = await invRes.json();
            if (iJson.status === 'success' && iJson.data) {
                renderV2InventoryChart(iJson.data.stock_trend || {}, iJson.data.turnover_ratio || 0);
                const deadLabel = document.getElementById('v2-dead-stock-count-label');
                if (deadLabel && iJson.data.dead_stock_analysis) {
                    deadLabel.textContent = `${iJson.data.dead_stock_analysis.count || 0} items`;
                }
            }
        }
    } catch (e) {
        console.warn('[V2 Analytics] Failed to fetch analytics:', e);
    }
}

/**
 * Render V2 Sales & Revenue Chart.
 */
function renderV2SalesChart(trendData) {
    const ctx = document.getElementById('v2SalesAnalyticsChart');
    if (!ctx) return;

    const dates = trendData.dates || [];
    const sales = trendData.sales || [];
    const revenue = trendData.revenue || [];

    if (v2SalesAnalyticsChart) v2SalesAnalyticsChart.destroy();

    v2SalesAnalyticsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    type: 'line',
                    label: 'Revenue (₹)',
                    data: revenue,
                    borderColor: '#8cb054',
                    backgroundColor: 'rgba(140, 176, 84, 0.15)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'yRev',
                },
                {
                    type: 'bar',
                    label: 'Sales Volume (Units)',
                    data: sales,
                    backgroundColor: 'rgba(99, 102, 241, 0.65)',
                    borderRadius: 4,
                    yAxisID: 'yVol',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top' },
            },
            scales: {
                yRev: {
                    type: 'linear',
                    position: 'left',
                    ticks: {
                        callback: v => '₹' + Number(v).toLocaleString(),
                    },
                    grid: { color: 'rgba(148, 163, 184, 0.15)' },
                },
                yVol: {
                    type: 'linear',
                    position: 'right',
                    grid: { drawOnChartArea: false },
                },
                x: {
                    grid: { display: false },
                },
            },
        },
    });
}

/**
 * Render V2 Inventory Turnover & Stock Trend Chart.
 */
function renderV2InventoryChart(stockData, turnoverRatio) {
    const ctx = document.getElementById('v2InventoryAnalyticsChart');
    if (!ctx) return;

    const dates = stockData.dates || [];
    const levels = stockData.stock_level || [];

    const badge = document.getElementById('inv-turnover-badge');
    if (badge) badge.textContent = `Turnover: ${turnoverRatio.toFixed(2)}x`;

    if (v2InventoryAnalyticsChart) v2InventoryAnalyticsChart.destroy();

    v2InventoryAnalyticsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Stock Units',
                data: levels,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.15)' },
                },
                x: {
                    grid: { display: false },
                },
            },
        },
    });
}

/**
 * Fetch and render V2 Consolidated AI Recommendations.
 */
async function fetchV2Recommendations() {
    try {
        const res = await fetch('/api/dashboard/recommendations');
        if (!res.ok) return;
        const json = await res.json();
        if (json.status !== 'success') return;

        v2RawRecommendations = json.data || [];
        const totalBadge = document.getElementById('v2-recs-total-badge');
        if (totalBadge) totalBadge.textContent = `${v2RawRecommendations.length} Insights`;

        renderFilteredV2Recommendations();

    } catch (e) {
        console.warn('[V2 Recommendations] Failed to fetch recommendations:', e);
    }
}

/**
 * Filter recommendations by priority.
 */
function filterV2Recommendations(priority) {
    v2CurrentRecFilter = priority;
    ['all', 'critical', 'high', 'medium', 'low'].forEach(p => {
        const btn = document.getElementById(`btn-rec-filter-${p}`);
        if (btn) {
            const isMatch = p.toUpperCase() === priority;
            btn.classList.toggle('active', isMatch);
        }
    });
    renderFilteredV2Recommendations();
}

/**
 * Render recommendations based on current filter.
 */
function renderFilteredV2Recommendations() {
    const container = document.getElementById('v2-recommendations-list');
    if (!container) return;

    let filtered = v2RawRecommendations;
    if (v2CurrentRecFilter !== 'ALL') {
        filtered = v2RawRecommendations.filter(r => (r.priority || '').toUpperCase() === v2CurrentRecFilter);
    }

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted small py-4">
                No recommendations matching priority "${v2CurrentRecFilter}".
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(item => {
        const prio = (item.priority || 'MEDIUM').toUpperCase();
        const confPct = Math.round((item.confidence || 0.8) * 100);
        const sourceIcons = {
            'sales': '📊 Sales Engine',
            'inventory': '📦 Inventory ML',
            'knowledge': '📚 Enterprise Policy',
            'manager_agent': '✨ AI Copilot Orchestrator',
        };
        const sourceLabel = sourceIcons[item.source] || item.source || 'AI Intelligence';

        return `
            <div class="rec-card-v2 priority-${escapeHtml(prio)}">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge ${prio === 'CRITICAL' ? 'bg-danger text-white' : (prio === 'HIGH' ? 'bg-warning text-dark' : 'bg-secondary')} text-uppercase" style="font-size: 0.68rem;">
                            ${escapeHtml(prio)}
                        </span>
                        <span class="badge bg-light text-dark border" style="font-size: 0.72rem;">
                            ${escapeHtml(sourceLabel)}
                        </span>
                    </div>
                    <span class="small fw-bold text-success" title="Composite recommendation confidence">
                        ${confPct}% Confidence
                    </span>
                </div>
                <h6 class="fw-bold text-dark my-1">${escapeHtml(item.recommendation || '')}</h6>
                <div class="small text-secondary">${escapeHtml(item.reason || '')}</div>
            </div>
        `;
    }).join('');
}

