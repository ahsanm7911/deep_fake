document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const detectBtn = document.getElementById('detect-btn');
    const generatePdfBtn = document.getElementById('generate-pdf');
    const resultDiv = document.getElementById('result');
    const resultText = document.getElementById('result-text');
    const confidenceBar = document.getElementById('confidence-bar');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Drag-and-drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('active'));
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('active'));
    });
    dropzone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            fileInput.files = e.dataTransfer.files;
            previewImage(file);
        }
    });
    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) {
            previewImage(fileInput.files[0]);
        }
    });
    function previewImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove('d-none');
            dropzone.querySelector('.dropzone-content').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    // Detect button click
    detectBtn.addEventListener('click', async () => {
        if (!fileInput.files[0]) {
            alert('Please upload an image.');
            return;
        }
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Please log in to access this feature.');
            window.location.href = '/login/';
            return;
        }
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        detectBtn.disabled = true;
        loadingSpinner.classList.remove('d-none');
        try {
            const response = await fetch('/api/detect', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!response.ok) {
                if (response.status === 401) {
                    alert('Session expired. Please log in again.');
                    window.location.href = '/login/';
                }
                throw new Error('Detection failed');
            }
            const result = await response.json();
            resultText.textContent = `${result.result} (Confidence: ${(result.confidence * 100).toFixed(2)}%)`;
            resultText.className = `badge ${result.result === 'Real' ? 'badge-real' : 'badge-fake'}`;
            confidenceBar.style.width = `${result.confidence * 100}%`;
            confidenceBar.className = `progress-bar ${result.result === 'Real' ? 'bg-success' : 'bg-danger'}`;
            confidenceBar.setAttribute('aria-valuenow', result.confidence * 100);
            resultDiv.classList.remove('d-none');
            generatePdfBtn.classList.remove('d-none');
        } catch (error) {
            console.error('Error:', error);
            alert('Detection failed.');
        } finally {
            detectBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
        }
    });

    // Generate PDF button click
    generatePdfBtn.addEventListener('click', async () => {
        const result = resultText.textContent;
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Please log in to access this feature.');
            window.location.href = '/login/';
            return;
        }
        generatePdfBtn.disabled = true;
        loadingSpinner.classList.remove('d-none');
        try {
            const response = await fetch('/api/generate-pdf', {
                method: 'POST',
                body: JSON.stringify({ image: fileInput.files[0].name, result }),
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!response.ok) {
                if (response.status === 401) {
                    alert('Session expired. Please log in again.');
                    window.location.href = '/login/';
                }
                throw new Error('PDF generation failed');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'deepfake_report.pdf';
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error:', error);
            alert('PDF generation failed.');
        } finally {
            generatePdfBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
        }
    });
});