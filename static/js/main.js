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
        const response = await fetch('/ceo/dashboard');
        const result = await response.json();
        
        if (result.status === 'success') {
            const data = result.data;
            
            // 1. Metrics
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

            // 2. Decision & Reasons
            const dText = document.getElementById('ai-decision-text');
            dText.textContent = data.decision;
            dText.className = `my-3 ${data.decision === 'Increase Production' ? 'text-success' : 'text-danger'}`;
            
            const cBadge = document.getElementById('ai-confidence');
            cBadge.textContent = `Confidence: ${data.confidence}`;
            cBadge.className = `badge rounded-pill bg-${data.confidence === 'High' ? 'success' : 'warning text-dark'}`;

            const rContainer = document.getElementById('reasons-container');
            rContainer.innerHTML = data.reasons.map(r => `<div class="mb-1">● ${r}</div>`).join('');

            // 3. Recommendations
            const recList = document.getElementById('recommendations-list');
            recList.innerHTML = data.recommendations.map(r => `<li class="mb-2 border-start border-primary ps-2">${r}</li>`).join('');

            // 4. Early Warnings
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
