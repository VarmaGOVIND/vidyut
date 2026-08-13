document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('productSearch');
  const productTableBody = document.getElementById('productTableBody');
  const cartTableBody = document.getElementById('cartTableBody');
  const cartTotalEl = document.getElementById('cartTotal');
  const cartGrandTotalEl = document.getElementById('cartGrandTotal');
  const clearCartBtn = document.getElementById('clearCartBtn');
  const checkoutBtn = document.getElementById('checkoutBtn');

  let cart = [];
  let currentInvoiceId = null;

  function showCustomNotification(message, type = 'danger') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-4 shadow-sm`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
      <i class="fa-solid fa-circle-exclamation me-2"></i> ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => {
      if (alertDiv.parentNode) alertDiv.remove();
    }, 4000);
  }

  function loadCart() {
    const savedCart = sessionStorage.getItem('vidyut_cart');
    if (savedCart) {
      try {
        cart = JSON.parse(savedCart);
        updateCartUI();
      } catch (e) {
        sessionStorage.removeItem('vidyut_cart');
        cart = [];
      }
    }
  }

  function saveCart() {
    sessionStorage.setItem('vidyut_cart', JSON.stringify(cart));
  }

  function calculateTotal() {
    return cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  }

  loadCart();

  let searchTimeout;
  searchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const query = this.value.trim();
    if (query.length < 1) {
      productTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Type at least 1 character to search products.</td></tr>';
      return;
    }
    searchTimeout = setTimeout(() => fetchProducts(query), 300);
  });

  function fetchProducts(query) {
    fetch(`/billing/api/products/search?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        productTableBody.innerHTML = '';
        if (data.length === 0) {
          productTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No batches found.</td></tr>';
          return;
        }
        data.forEach(p => {
          let stockDisplay = '';
          let buttonHtml = '';

          if (p.stock <= 0) {
            stockDisplay = '<span class="badge bg-danger">Not in Stock</span>';
            buttonHtml = '<button class="action-btn edit-btn" disabled style="opacity: 0.5; cursor: not-allowed;"><i class="fa-solid fa-ban"></i></button>';
          } else if (p.is_expired) {
            stockDisplay = '<span class="badge bg-danger">Expired!</span>';
            buttonHtml = '<button class="action-btn edit-btn" disabled style="opacity: 0.5; cursor: not-allowed;" title="Expired product cannot be sold"><i class="fa-solid fa-ban"></i></button>';
          } else {
            stockDisplay = '<span class="' + (p.stock <= 5 ? 'text-danger fw-bold' : 'text-success') + '">' + p.stock + '</span>';
            buttonHtml = '<button class="action-btn edit-btn add-to-cart-btn" data-batch-id="' + p.batch_id + '" data-product-id="' + p.product_id + '"><i class="fa-solid fa-plus"></i></button>';
          }

          const row = document.createElement('tr');
          row.innerHTML = `
            <td><span class="sku-badge">${p.sku}</span></td>
            <td class="fw-bold">${p.name}</td>
            <td><small class="text-primary">${p.supplier}</small></td>
            <td>₹${(p.price || 0).toFixed(2)}</td>
            <td>${stockDisplay}</td>
            <td>${buttonHtml}</td>
          `;
          productTableBody.appendChild(row);
        });
        attachAddToCartListeners();
      });
  }


  function downloadInvoice() {
    if (lastSaleId) {
        window.open(`/billing/invoice/${lastSaleId}`, '_blank');
    }
}

  function attachAddToCartListeners() {
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        addToCart(this.dataset.batchId, this.dataset.productId);
      });
    });
  }

  function addToCart(batchId, productId) {
    fetch('/billing/api/cart/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: parseInt(productId), batch_id: parseInt(batchId) })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        showCustomNotification(data.error, 'danger');
      } else {
        cart = data.cart;
        saveCart();
        updateCartUI();
      }
    });
  }
  

  function updateCartUI() {
    cartTableBody.innerHTML = '';
    if (cart.length === 0) {
      cartTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Cart is empty.</td></tr>';
    } else {
      cart.forEach((item, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>
            <div class="fw-bold">${item.name}</div>
            <div class="text-muted" style="font-size: 11px;">Cost: ₹${item.cost_price.toFixed(2)} (Batch: ${item.batch_id})</div>
          </td>
          <td>
            <input type="number" class="form-control form-control-sm price-input" style="width:80px;" value="${item.price}" onchange="updatePrice(${index}, this.value)">
          </td>
          <td>
            <div class="d-flex align-items-center gap-1">
              <button class="action-btn edit-btn update-qty-btn" style="width:24px; height:24px;" data-batch-id="${item.batch_id}" data-action="decrease">-</button>
              <span class="fw-bold">${item.qty}</span>
              <button class="action-btn edit-btn update-qty-btn" style="width:24px; height:24px;" data-batch-id="${item.batch_id}" data-action="increase">+</button>
            </div>
          </td>
          <td class="fw-bold">₹${(item.price * item.qty).toFixed(2)}</td>
          <td><button class="action-btn delete-btn remove-item-btn" data-batch-id="${item.batch_id}"><i class="fa-solid fa-trash"></i></button></td>
        `;
        cartTableBody.appendChild(row);
      });
    }
    attachCartActionListeners();
    calculateCartTotals();
  }

  function attachCartActionListeners() {
    document.querySelectorAll('.update-qty-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        updateCartQty(this.dataset.batchId, this.dataset.action);
      });
    });
    document.querySelectorAll('.remove-item-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        removeFromCart(this.dataset.batchId);
      });
    });
  }

  function updateCartQty(batchId, action) {
    fetch('/billing/api/cart/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: parseInt(batchId), action: action })
    })
    .then(res => res.json())
    .then(data => {
      cart = data.cart;
      saveCart();
      updateCartUI();
    });
  }

  function calculateCartTotals() {
  let subtotal = 0;
  cart.forEach(item => {
    subtotal += item.price * item.qty;
  });

  let discount = parseFloat(document.getElementById('cartDiscount').value) || 0;
  if (discount > subtotal) discount = subtotal;

  let taxableAmount = subtotal - discount;
  
  let taxInput = document.getElementById('cartTax');
  let taxAmount = parseFloat(taxInput.value) || 0;

  if (IS_ADMIN) {
    taxInput.readOnly = false;
    taxInput.style.backgroundColor = '#fff';
  } else {
    taxInput.readOnly = true;
    taxInput.style.backgroundColor = '#e9ecef';
    taxAmount = (taxableAmount * DEFAULT_TAX_RATE) / 100;
    taxInput.value = taxAmount.toFixed(2);
  }

  let grandTotal = taxableAmount + taxAmount;

  document.getElementById('cartSubtotal').innerText = '₹' + subtotal.toFixed(2);
  document.getElementById('cartGrandTotal').innerText = '₹' + grandTotal.toFixed(2);
  
  document.getElementById('modalItemCount').innerText = cart.length;
  document.getElementById('modalTotalAmount').innerText = '₹' + grandTotal.toFixed(2);
  document.getElementById('qrAmount').innerText = '₹' + grandTotal.toFixed(2);
}

document.getElementById('cartDiscount').addEventListener('input', calculateCartTotals);
document.getElementById('cartTax').addEventListener('input', calculateCartTotals);

  function updatePrice(index, val) {
    cart[index].price = parseFloat(val) || 0;
    saveCart();
    updateCartUI();
  }

  function removeFromCart(batchId) {
    fetch('/billing/api/cart/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: parseInt(batchId), action: 'remove' })
    })
    .then(res => res.json())
    .then(data => {
      cart = data.cart;
      saveCart();
      updateCartUI();
    });
  }

  clearCartBtn.addEventListener('click', function() {
    if (cart.length === 0) return;
    document.getElementById('clearCartModal').style.display = 'flex';
  });

  document.getElementById('confirmClearBtn').addEventListener('click', function() {
    cart = [];
    sessionStorage.removeItem('vidyut_cart');
    updateCartUI();
    closeModal('clearCartModal');

    fetch('/billing/api/cart/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'clear_all' })
    }).catch(err => console.error("Backend clear failed", err));
  });

  checkoutBtn.addEventListener('click', function() {
    if (cart.length === 0) {
      showCustomNotification('Cart is empty. Add products first.', 'warning');
      return;
    }
    const grandTotalText = document.getElementById('cartGrandTotal').innerText.replace('₹', '');
    document.getElementById('modalItemCount').textContent = cart.length;
    document.getElementById('modalTotalAmount').textContent = `₹${parseFloat(grandTotalText).toFixed(2)}`;
    document.getElementById('confirmSaleModal').style.display = 'flex';
  });

  document.getElementById('proceedToPayBtn').addEventListener('click', function() {
    closeModal('confirmSaleModal');
    const grandTotalText = document.getElementById('cartGrandTotal').innerText.replace('₹', '');
    const total = parseFloat(grandTotalText);
    document.getElementById('qrAmount').textContent = `₹${total.toFixed(2)}`;
    document.getElementById('qrCodeImg').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa=vidyut@pay&pn=VIDYUT&am=${total}&cu=INR`;
    document.getElementById('qrPaymentModal').style.display = 'flex';
    document.getElementById('paymentLoading').style.display = 'none';
    document.getElementById('qrModalFooter').style.display = 'flex';
  });

  document.getElementById('simulatePayBtn').addEventListener('click', function() {
    document.getElementById('paymentLoading').style.display = 'block';
    document.getElementById('qrModalFooter').style.display = 'none';
    
    const discount = parseFloat(document.getElementById('cartDiscount').value) || 0;
    const tax = parseFloat(document.getElementById('cartTax').value) || 0;

    setTimeout(() => {
      fetch('/billing/api/checkout', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
    discount: discount, 
    tax: tax, 
    customer_id: document.getElementById('customerId').value || null 
})
      })
      .then(res => res.json())
      .then(data => {
        closeModal('qrPaymentModal');
        if (data.success) {
          currentInvoiceId = data.invoice;
          document.getElementById('successInvoiceId').textContent = data.invoice;
          document.getElementById('successModal').style.display = 'flex';
          cart = [];
          sessionStorage.removeItem('vidyut_cart');
          updateCartUI();
        } else {
          showCustomNotification(data.error || 'Error completing sale', 'danger');
          document.getElementById('paymentLoading').style.display = 'none';
          document.getElementById('qrModalFooter').style.display = 'flex';
        }
      })
      .catch(err => {
        console.error("Checkout error:", err);
        showCustomNotification("Payment processing failed. Please try again.", 'danger');
        closeModal('qrPaymentModal');
      });
    }, 2000);
  });

  document.getElementById('printInvoiceBtn').addEventListener('click', function() {
    if (currentInvoiceId) {
      window.open(`/billing/invoice/${currentInvoiceId}`, '_blank');
    }
  });

  
  window.startNewSale = function() {
    closeModal('successModal');
    currentInvoiceId = null;
    window.location.href = '/billing/pos';
  };

  window.closeModal = function(modalId) {
    document.getElementById(modalId).style.display = 'none';
  };

  window.updatePrice = updatePrice; 
  
  window.onclick = function(event) {
    if (event.target.classList.contains('custom-modal')) {
      event.target.style.display = 'none';
    }
  }
});