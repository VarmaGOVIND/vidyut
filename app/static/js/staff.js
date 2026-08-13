document.addEventListener('DOMContentLoaded', function() {
  let deleteUrl = '';
  const modal = document.getElementById('deleteConfirmModal');

  if (!modal) return;

  const closeModal = () => {
    modal.classList.remove('active');
    deleteUrl = '';
  };

  document.querySelectorAll('.delete-staff-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      deleteUrl = this.dataset.url;
      modal.classList.add('active');
    });
  });

  document.querySelector('.delete-modal-close').addEventListener('click', closeModal);
  
  document.querySelector('.btn-cancel').addEventListener('click', closeModal);

  document.querySelector('.btn-delete').addEventListener('click', function() {
    if (deleteUrl) {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = deleteUrl;
      document.body.appendChild(form);
      form.submit();
    }
  });

  modal.addEventListener('click', function(event) {
    if (event.target === modal) {
      closeModal();
    }
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && modal.classList.contains('active')) {
      closeModal();
    }
  });
});