document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        document.getElementById('pieChartError').style.display = 'block';
        document.getElementById('lineChartError').style.display = 'block';
        document.getElementById('barChartError').style.display = 'block';
        return;
    }

    // Pie Chart: Real vs. Fake Distribution
    const resultPieChart = new Chart(document.getElementById('resultPieChart'), {
        type: 'pie',
        data: {
            labels: ['Real', 'Fake'],
            datasets: [{
                data: [{{ real_count }}, {{ fake_count }}],
                backgroundColor: ['#28a745', '#dc3545'],
                borderColor: ['#fff', '#fff'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });

    // Line Chart: Confidence Trends
    const confidenceLineChart = new Chart(document.getElementById('confidenceLineChart'), {
        type: 'line',
        data: {
            labels: [{% for item in confidence_data %}'{{ item.timestamp }}',{% endfor %}],
            datasets: [{
                label: 'Confidence (%)',
                data: [{% for item in confidence_data %}{{ item.confidence }},{% endfor %}],
                borderColor: '#5941F2',
                backgroundColor: 'rgba(89, 65, 242, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100 },
                x: { ticks: { maxTicksLimit: 10 } }
            }
        }
    });

    // Bar Chart: Detections Per Day
    const detectionsBarChart = new Chart(document.getElementById('detectionsBarChart'), {
        type: 'bar',
        data: {
            labels: [{% for item in detections_per_day %}'{{ item.date }}',{% endfor %}],
            datasets: [{
                label: 'Detections',
                data: [{% for item in detections_per_day %}{{ item.count }},{% endfor %}],
                backgroundColor: '#00c4ff',
                borderColor: '#5941F2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
});