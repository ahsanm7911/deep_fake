document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            },
        });
        if (response.ok) {
            const data = await response.text();
            // Parse token from response if needed (handled by template script)
            // Redirect is handled by template script
        } else {
            const errorData = await response.json();
            alert(errorData.error || 'Login failed.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during login.');
    }
    alert("Form submitted.")
});