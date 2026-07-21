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
        // Fetch ERP metrics and ML predictions in parallel
        const [dashRes, salesRes, invRes] = await Promise.all([
            fetch('/ceo/dashboard'),
            fetch('/api/ml/sales/predict'),
            fetch('/api/ml/inventory/predict')
        ]);

        const result = await dashRes.json();
        const salesData = await salesRes.json();
        const invData = await invRes.json();

        if (result.status === 'success') {
            const data = result.data;

            // 1. Overview Metrics
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

            // 2. Sales Intelligence Panel
            if (salesData.status === 'success') {
                const sDec = document.getElementById('sales-decision-text');
                sDec.textContent = salesData.decision;
                sDec.className = `my-2 ${salesData.decision === 'Increase Production' ? 'text-success' : 'text-danger'}`;

                const sConf = document.getElementById('sales-confidence');
                sConf.textContent = `Confidence: ${salesData.confidence} (${(salesData.probability * 100).toFixed(1)}%)`;
                sConf.className = `badge rounded-pill bg-${salesData.confidence === 'High' ? 'success' : 'warning text-dark'}`;

                const sStatus = salesData.model_status || {};
                document.getElementById('sales-model-type').textContent = (sStatus.model_type || 'xgboost').toUpperCase();
                document.getElementById('sales-model-version').textContent = sStatus.version || 'v1.0';
                document.getElementById('sales-model-accuracy').textContent = sStatus.accuracy ? `${(sStatus.accuracy * 100).toFixed(1)}%` : 'N/A';
                document.getElementById('sales-predict-timestamp').textContent = salesData.timestamp || 'Just now';

                const sReasons = salesData.reasons || data.reasons || [];
                document.getElementById('sales-reasons-container').innerHTML = sReasons.map(r => `<div class="mb-1">● ${r}</div>`).join('') || '<div class="text-muted">No specific drivers returned.</div>';
            }

            // 3. Inventory Intelligence Panel
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

            // 4. Recommendations & Warnings
            const recList = document.getElementById('recommendations-list');
            recList.innerHTML = data.recommendations.map(r => `<li class="mb-2 border-start border-primary ps-2">${r}</li>`).join('');

            const warnContainer = document.getElementById('warnings-container');
            if (data.warnings.length > 0) {
                warnContainer.innerHTML = data.warnings.map(w => `<div class="alert-box small mb-2">⚠ ${w}</div>`).join('');
            } else {
                warnContainer.innerHTML = '<p class="text-secondary small">System stability normal. No warnings.</p>';
            }

            renderEnhancedCharts(data.history);
        }
    } catch (error) {
        console.error('CEO Dashboard Error:', error);
    }
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
    const ctx = document.getElementById('salesPerformanceChart').getContext('2d');
    if (window.salesChart) window.salesChart.destroy();
    window.salesChart = new Chart(ctx, {
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
