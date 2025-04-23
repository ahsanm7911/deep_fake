document.getElementById('detect-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('image-upload');
    if (!fileInput.files[0]) {
        alert('Please upload an image.');
        return;
    }
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    try {
        const response = await fetch('/api/detect', {
            method: 'POST',
            body: formData,
            headers: {
                // Add authentication header if needed, e.g., 'Authorization': 'Bearer <token>'
            }
        });
        if (!response.ok) {
            throw new Error('Detection failed');
        }
        const result = await response.json(); // Expected: { result: "Real" or "Fake", confidence: 0.95 }
        document.getElementById('result-text').textContent = `${result.result} (Confidence: ${(result.confidence * 100).toFixed(2)}%)`;
        document.getElementById('result').style.display = 'block';
        document.getElementById('generate-pdf').style.display = 'inline-block';
    } catch (error) {
        console.error('Error:', error);
        alert('Detection failed.');
    }
});

document.getElementById('generate-pdf').addEventListener('click', async () => {
    const fileInput = document.getElementById('image-upload');
    const result = document.getElementById('result-text').textContent;
    try {
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            body: JSON.stringify({ image: fileInput.files[0].name, result }),
            headers: {
                'Content-Type': 'application/json',
                // Add authentication header if needed
            }
        });
        if (!response.ok) {
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
    }
});