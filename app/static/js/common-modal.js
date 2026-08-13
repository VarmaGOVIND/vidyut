document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('deleteConfirmModal');
    if (!modal) return;

    let deleteUrl = '';
    let deleteMessage = 'Are you sure you want to delete this item?';

    const closeModal = function() {
        modal.classList.remove('active');
        setTimeout(function() {
            deleteUrl = '';
        }, 200);
    };

    const openModal = function(url, message) {
        deleteUrl = url;
        deleteMessage = message || 'Are you sure you want to delete this item?';
        const messageEl = modal.querySelector('.delete-message');
        if (messageEl) {
            messageEl.textContent = deleteMessage;
        }
        modal.classList.add('active');
    };

    document.querySelectorAll('[data-delete-url]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const url = this.dataset.deleteUrl;
            const message = this.dataset.deleteMessage || 'Are you sure you want to delete this item?';
            if (url) {
                openModal(url, message);
            }
        });
    });

    const cancelBtn = modal.querySelector('.delete-modal-btn.cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }

    const closeBtn = modal.querySelector('.delete-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    const deleteBtn = modal.querySelector('.delete-modal-btn.delete');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            if (deleteUrl) {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = deleteUrl;
                document.body.appendChild(form);
                form.submit();
            }
        });
    }

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
});