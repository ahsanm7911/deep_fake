console.log("deepfake.js loaded.");

document.addEventListener('DOMContentLoaded', function() {
    // Verify elements exist
    const dropZone = document.getElementById('dropZone');
    const imageInput = document.getElementById('imageInput');
    const detectButton = document.getElementById('detectButton');
    const resultDiv = document.getElementById('result');
    const progressBar = document.querySelector('.progress');
    const progressBarInner = progressBar ? progressBar.querySelector('.progress-bar') : null;
    const recentActivity = document.getElementById('recentActivity');
    const downloadPdfButton = document.getElementById('downloadPdfButton');
    const resultText = document.getElementById('resultText');
    const confidenceText = document.getElementById('confidenceText');

    if (!dropZone || !imageInput || !detectButton || !resultDiv || !progressBarInner || !recentActivity) {
        console.error('Missing critical DOM elements:', {
            dropZone: !!dropZone,
            imageInput: !!imageInput,
            detectButton: !!detectButton,
            resultDiv: !!resultDiv,
            progressBarInner: !!progressBarInner,
            recentActivity: !!recentActivity,
            downloadPdfButton: !!downloadPdfButton,
            resultText: !!resultText,
            confidenceText: !!confidenceText
        });
        return;
    }

    // Log non-critical missing elements
    if (!downloadPdfButton || !resultText || !confidenceText) {
        console.warn('Non-critical DOM elements missing:', {
            downloadPdfButton: !!downloadPdfButton,
            resultText: !!resultText,
            confidenceText: !!confidenceText
        });
    }

    // Handle drag-and-drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
        console.log('Dragover event triggered');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
        console.log('Dragleave event triggered');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            imageInput.files = files;
            displayPreview(files[0]);
            detectButton.disabled = false;
            console.log('File dropped:', files[0].name);
        }
    });

    // Handle file input change
    imageInput.addEventListener('change', () => {
        if (imageInput.files.length > 0) {
            displayPreview(imageInput.files[0]);
            detectButton.disabled = false;
            console.log('File selected via input:', imageInput.files[0].name);
        }
    });

    // Click to trigger file input
    dropZone.addEventListener('click', () => {
        imageInput.click();
        console.log('Drop zone clicked to open file input');
    });

    // Display image preview
    function displayPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            dropZone.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            console.log('Preview displayed for file:', file.name);
        };
        reader.onerror = () => {
            console.error('Error reading file:', file.name);
        };
        reader.readAsDataURL(file);
    }

    // Handle detect button click
    detectButton.addEventListener('click', () => {
        if (!imageInput.files[0]) {
            resultDiv.innerHTML = '<div class="alert alert-warning">Please upload an image first.</div>';
            console.log('Detect button clicked without image');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageInput.files[0]);

        const token = localStorage.getItem('token');
        if (!token) {
            resultDiv.innerHTML = '<div class="alert alert-danger">Please log in again.</div>';
            console.error('No JWT token found in localStorage');
            return;
        }

        resultDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        detectButton.disabled = true;
        console.log('Detect button clicked, sending request to /api/detect');

        fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        })
        .then(response => {
            console.log('Fetch response status:', response.status);
            return response.json();
        })
        .then(data => {
            resultDiv.innerHTML = '';
            detectButton.disabled = false;
            console.log('Fetch response data:', data);

            if (data.error) {
                resultDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                console.error('API error:', data.error);
                return;
            }
            
            const result = data.result;
            const confidence = (data.confidence * 100).toFixed(2);
            const badgeClass = result === 'Real' ? 'alert-success' : 'alert-danger';

            let resultChild = document.createElement('div')
            let confidenceDiv = document.createElement('div')
            resultDiv.classList.add('d-flex', 'flex-row', 'align-items-center', 'justify-content-center')
            resultChild.classList.add('me-2', 'alert', badgeClass, 'p-2')
            confidenceDiv.classList.add('alert', badgeClass, 'p-2')
            resultChild.textContent = "Result: " + result
            confidenceDiv.textContent = "Confidence: " + confidence
            resultDiv.appendChild(resultChild)
            resultDiv.appendChild(confidenceDiv)
            // Update result with existing HTML from dashboard.html
            if(resultDiv.contains(resultText)){
                console.log("Result text is in result div")
            } else {
                console.log("Result text is not in result div")
            }
            resultDiv.classList.remove('d-none');
            if (resultText) {
                resultText.textContent = result;
                resultText.classList.remove('bg-success', 'bg-danger');
                resultText.classList.add(badgeClass);
            } else {
                console.warn('resultText element not found; skipping result update');
            }
            if (confidenceText) {
                confidenceText.textContent = `${confidence}%`;
            } else {
                console.warn('confidenceText element not found; skipping confidence update');
            }
            if (downloadPdfButton && data.pdf_report_url) {
                downloadPdfButton.href = data.pdf_report_url;
                downloadPdfButton.classList.remove('d-none');
                console.log('PDF download button displayed with href:', data.pdf_report_url);
            } else if (!downloadPdfButton) {
                console.warn('downloadPdfButton element not found; PDF link skipped');
            }

            // Update progress bar
            progressBarInner.style.width = `${confidence}%`;
            progressBarInner.classList.remove('bg-success', 'bg-danger');
            progressBarInner.classList.add(result === 'Real' ? 'bg-success' : 'bg-danger');
            console.log('Progress bar updated:', { width: `${confidence}%`, class: badgeClass });

            // Update recent activity
            const timestamp = new Date().toLocaleString();
            const pdfLink = data.pdf_report_url ? `<a href="${data.pdf_report_url}" target="_blank">View PDF</a>` : '';
            const activityItem = `
                <div class="list-group-item">
                    <i class="fas fa-image me-2"></i>
                    Image detected as <strong>${result}</strong> (${confidence}% confidence) at ${timestamp}
                    ${pdfLink}
                </div>
            `;
            recentActivity.innerHTML = activityItem + (recentActivity.children.length > 0 ? recentActivity.innerHTML : '');
            if (recentActivity.children.length > 5) {
                recentActivity.removeChild(recentActivity.lastChild);
            }
            if (recentActivity.querySelector('p.text-muted')) {
                recentActivity.innerHTML = activityItem;
            }
            console.log('Recent activity updated with PDF link:', { pdfLink });
        })
        .catch(error => {
            resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            detectButton.disabled = false;
            console.error('Fetch error:', error.message);
        });
    });

    console.log('deepfake.js loaded successfully');
});