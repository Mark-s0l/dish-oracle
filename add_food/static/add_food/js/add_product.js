document.querySelector('form').addEventListener('submit', function() {
    const btn = document.getElementById('submit_button');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div>';
});