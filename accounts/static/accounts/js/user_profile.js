document.addEventListener('DOMContentLoaded', function () {
  // Django рендерит {{ form.email }} с id="id_email"
  var emailInput = document.getElementById('id_email');
  var editBtn    = document.getElementById('edit-btn');
  var submitBtn  = document.getElementById('submit-btn');

  if (!emailInput || !editBtn || !submitBtn) return;

  // Блокируем поле при загрузке страницы
  emailInput.setAttribute('readonly', true);
  emailInput.classList.remove('is-editing');
  submitBtn.classList.remove('is-visible');

  editBtn.addEventListener('click', function () {
    emailInput.removeAttribute('readonly');
    emailInput.classList.add('is-editing');
    submitBtn.classList.add('is-visible');

    emailInput.focus();
    var len = emailInput.value.length;
    emailInput.setSelectionRange(len, len);
  });
});