document.addEventListener('DOMContentLoaded', function() {
  let cart = [];
  const searchInput = document.getElementById('productSearch');
  const searchResults = document.getElementById('searchResults');
  const cartTableBody = document.getElementById('cartTableBody');
  const grandTotalEl = document.getElementById('grandTotal');
  const cartItemsInput = document.getElementById('cartItemsInput');
  const completeSaleBtn = document.getElementById('completeSaleBtn');
  const posForm = document.getElementById('posForm');

  if (!searchInput) return;

  searchInput.addEventListener('input', function() {
    const query = this.value.trim();
    if (query.length < 2) {
      searchResults.innerHTML = '';
      return;
    }
    fetch(`/billing/api/products/search?q=${query}`)
      .then(res => res.json())
      .then(data => {
        searchResults.innerHTML = '';
        if (data.length === 0) {
          searchResults.innerHTML = '<div class="p-3 text-muted">No batches found.</div>';
          return;
        }
        data.forEach(item => {
          const div = document.createElement('div');
          div.className = 'batch-item p-3 border-bottom';
          div.style.cursor = 'pointer';
          div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <strong>${item.name}</strong> <small class="text-muted">(${item.sku})</small><br>
                <small class="text-primary">Supplier: ${item.supplier} | Rate: ₹${item.purchase_rate} | Stock: ${item.qty_remaining}</small>
              </div>
              <button class="btn btn-sm btn-primary add-btn" 
                data-batch-id="${item.batch_id}" 
                data-product-id="${item.product_id}" 
                data-name="${item.name}" 
                data-price="${item.selling_price}" 
                data-qty="${item.qty_remaining}">
                Add
              </button>
            </div>
          `;
          searchResults.appendChild(div);
        });

        document.querySelectorAll('.add-btn').forEach(btn => {
          btn.addEventListener('click', function(e) {
            e.stopPropagation();
            addToCart({
              batch_id: this.dataset.batchId,
              product_id: this.dataset.productId,
              name: this.dataset.name,
              price: parseFloat(this.dataset.price),
              qty: 1,
              max_qty: parseInt(this.dataset.qty)
            });
          });
        });
      });
  });

  function addToCart(item) {
    const existing = cart.find(c => c.batch_id === item.batch_id);
    if (existing) {
      if (existing.qty < existing.max_qty) {
        existing.qty += 1;
      } else {
        alert('Maximum stock reached for this batch.');
      }
    } else {
      cart.push(item);
    }
    renderCart();
  }

  function removeFromCart(index) {
    cart.splice(index, 1);
    renderCart();
  }

  function updateQty(index, val) {
    const qty = parseInt(val);
    if (qty > cart[index].max_qty) {
      alert('Cannot exceed available stock in this batch.');
      cart[index].qty = cart[index].max_qty;
    } else if (qty < 1) {
      cart[index].qty = 1;
    } else {
      cart[index].qty = qty;
    }
    renderCart();
  }

  function renderCart() {
    cartTableBody.innerHTML = '';
    let total = 0;
    if (cart.length === 0) {
      cartTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Cart is empty.</td></tr>';
    } else {
      cart.forEach((item, index) => {
        const itemTotal = item.qty * item.price;
        total += itemTotal;
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${item.name}</strong><br><small class="text-muted">Batch ID: ${item.batch_id}</small></td>
          <td><input type="number" class="form-control form-control-sm" style="width:70px;" value="${item.qty}" min="1" max="${item.max_qty}" onchange="updateQty(${index}, this.value)"></td>
          <td>₹${item.price.toFixed(2)}</td>
          <td class="fw-bold">₹${itemTotal.toFixed(2)}</td>
          <td><button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${index})"><i class="fa-solid fa-trash"></i></button></td>
        `;
        cartTableBody.appendChild(tr);
      });
    }
    grandTotalEl.textContent = `₹${total.toFixed(2)}`;
    cartItemsInput.value = JSON.stringify(cart);
  }

  if (completeSaleBtn) {
    completeSaleBtn.addEventListener('click', function() {
      if (cart.length === 0) {
        alert('Cart is empty!');
        return;
      }
      posForm.submit();
    });
  }
});