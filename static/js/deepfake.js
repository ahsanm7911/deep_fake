console.log("deepfake.js loaded.")
document.addEventListener('DOMContentLoaded', function() {
    // Verify elements exist
    const dropZone = document.getElementById('dropZone');
    const imageInput = document.getElementById('imageInput');
    const detectButton = document.getElementById('detectButton');
    const resultDiv = document.getElementById('result');
    const progressBar = document.querySelector('.progress');
    const progressBarInner = progressBar ? progressBar.querySelector('.progress-bar') : null;
    const recentActivity = document.getElementById('recentActivity');

    console.log("Drop Zone: ", dropZone)
    console.log("Image Input: ", imageInput)
    console.log("Detect Button: ", detectButton)
    console.log("Result Div: ", resultDiv)
    console.log("Progress Bar: ", progressBar)
    console.log("Progress Bar Inner: ", progressBarInner)
    console.log("Recent Activity: ", recentActivity)
    if (!dropZone || !imageInput || !detectButton || !resultDiv || !progressBarInner || !recentActivity) {
        console.error('Missing DOM elements:', {
            dropZone: !!dropZone,
            imageInput: !!imageInput,
            detectButton: !!detectButton,
            resultDiv: !!resultDiv,
            progressBarInner: !!progressBarInner,
            recentActivity: !!recentActivity
        });
        return;
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
            console.log('File dropped:', files[0].name);
        }
    });

    // Handle file input change
    imageInput.addEventListener('change', () => {
        if (imageInput.files.length > 0) {
            displayPreview(imageInput.files[0]);
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
            const badgeClass = result === 'Real' ? 'bg-success' : 'bg-danger';

            resultDiv.innerHTML = `
                <span class="badge ${badgeClass}">${result}</span>
                <p>Confidence: ${confidence}%</p>
            `;
            progressBarInner.style.width = `${confidence}%`;
            progressBarInner.classList.remove('bg-success', 'bg-danger');
            progressBarInner.classList.add(result === 'Real' ? 'bg-success' : 'bg-danger');
            console.log('Result displayed:', { result, confidence });

            // Update recent activity
            const timestamp = new Date().toLocaleString();
            const activityItem = `
                <div class="list-group-item">
                    <i class="fas fa-image me-2"></i>
                    Image detected as <strong>${result}</strong> (${confidence}% confidence) at ${timestamp}
                </div>
            `;
            recentActivity.innerHTML = activityItem + recentActivity.innerHTML;
            if (recentActivity.children.length > 5) {
                recentActivity.removeChild(recentActivity.lastChild);
            }
            console.log('Recent activity updated');
        })
        .catch(error => {
            resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            detectButton.disabled = false;
            console.error('Fetch error:', error.message);
        });
    });

    console.log('deepfake.js loaded successfully');
});