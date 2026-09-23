document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('comicForm');
    const submitBtn = document.getElementById('generateBtn');
    const loadingDiv = document.getElementById('loading');

    if (form) {
        form.addEventListener('submit', (e) => {
            // Form validation is handled by HTML5 'required' attributes natively
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.7';
            submitBtn.textContent = 'Generating... Please wait';
            
            loadingDiv.classList.remove('hidden');
            
            // Allow the form to submit normally after updating UI
        });
    }
});
