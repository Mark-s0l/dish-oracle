document.addEventListener('DOMContentLoaded', function () {
  initStars();
});

document.addEventListener('htmx:afterSwap', function () {
  initStars();
});

function initStars() {
  const form = document.querySelector('.rate-step form');
  if (!form) return;

  const labels = Array.from(form.querySelectorAll('label'));

  labels.forEach((label, i) => {
    label.addEventListener('mouseenter', () => {
      labels.forEach((l, j) => {
        l.classList.toggle('star-active', j <= i);
        l.style.transform = j === i ? 'scale(1.15)' : '';
      });
    });
  });

  form.addEventListener('mouseleave', () => {
    labels.forEach(l => l.style.transform = '');
    updateStars(labels);
  });

  labels.forEach((label) => {
    label.addEventListener('click', () => {
      setTimeout(() => updateStars(labels), 0);
    });
  });
}

function updateStars(labels) {
  const checkedIndex = labels.findIndex(l => l.querySelector('input:checked'));
  labels.forEach((l, j) => {
    l.classList.toggle('star-active', j <= checkedIndex);
  });
}
