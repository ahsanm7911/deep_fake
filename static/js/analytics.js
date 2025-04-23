<!-- static/js/analytics.js -->
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in to view analytics.');
        window.location.href = '/login/';
        return;
    }

    try {
        const response = await fetch('/api/analytics', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            if (response.status === 401) {
                alert('Session expired. Please log in again.');
                window.location.href = '/login/';
            }
            throw new Error('Failed to fetch analytics data');
        }
        const data = await response.json();

        // Total Scans
        document.getElementById('total-scans').textContent = data.total_scans;

        // Fake/Real Percentage Bar Chart
        const fakeRealChart = new Chart(document.getElementById('fakeRealChart'), {
            type: 'bar',
            data: {
                labels: ['Real', 'Fake'],
                datasets: [{
                    label: 'Percentage of Scans',
                    data: [data.real_percentage, data.fake_percentage],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderColor: ['#28a745', '#dc3545'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: 'Percentage (%)' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Real vs Fake Scans' }
                }
            }
        });

        // Scan Trend Line Chart
        const trendChart = new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: {
                labels: data.trend_labels,
                datasets: [{
                    label: 'Scans Over Time',
                    data: data.trend_data,
                    borderColor: '#007bff',
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Number of Scans' } },
                    x: { title: { display: true, text: 'Date' } }
                },
                plugins: {
                    title: { display: true, text: 'Scan Trend (Last 30 Days)' }
                }
            }
        });

        // Confidence Score Histogram
        const confidenceChart = new Chart(document.getElementById('confidenceChart'), {
            type: 'bar',
            data: {
                labels: data.confidence_bins,
                datasets: [
                    {
                        label: 'Real',
                        data: data.real_confidence,
                        backgroundColor: 'rgba(40, 167, 69, 0.5)',
                        borderColor: '#28a745',
                        borderWidth: 1
                    },
                    {
                        label: 'Fake',
                        data: data.fake_confidence,
                        backgroundColor: 'rgba(220, 53, 69, 0.5)',
                        borderColor: '#dc3545',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Frequency' } },
                    x: { title: { display: true, text: 'Confidence Score (%)' } }
                },
                plugins: {
                    title: { display: true, text: 'Confidence Score Distribution' }
                }
            }
        });
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to load analytics data.');
    }
});