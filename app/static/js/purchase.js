let cart = [];
let tempNewProductName = '';

document.getElementById('supplierSearch').addEventListener('input', function() {
    const query = this.value.trim();
    if (query.length < 2) {
        document.getElementById('supplierDropdown').style.display = 'none';
        return;
    }
    fetch(`/purchase/api/suppliers/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            const dropdown = document.getElementById('supplierDropdown');
            dropdown.innerHTML = '';
            if (data.length === 0) {
                dropdown.innerHTML = '<div class="p-2 text-muted">No suppliers found</div>';
            } else {
                data.forEach(s => {
                    const div = document.createElement('div');
                    div.className = 'dropdown-item-custom';
                    div.style.cursor = 'pointer';
                    div.style.padding = '8px 12px';
                    div.innerText = s.name;
                    div.onclick = () => {
                        document.getElementById('supplierSearch').value = s.name;
                        document.getElementById('supplierId').value = s.id;
                        dropdown.style.display = 'none';
                    };
                    dropdown.appendChild(div);
                });
            }
            dropdown.style.display = 'block';
        });
});

document.getElementById('productSearch').addEventListener('input', function() {
    const query = this.value.trim();
    if (query.length < 2) {
        document.getElementById('productDropdown').style.display = 'none';
        return;
    }
    
    fetch(`/purchase/api/products/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            const dropdown = document.getElementById('productDropdown');
            dropdown.innerHTML = '';
            
            const categories = data.filter(item => item.type === 'category');
            const products = data.filter(item => item.type === 'product');
            
            if (categories.length === 0 && products.length === 0) {
                dropdown.innerHTML = `
                    <div class="dropdown-item-custom" style="cursor:pointer; padding:10px 12px; background:#f8f9fa; border-radius:4px;" onclick="openNewProductModal('${query}')">
                        <i class="fa-solid fa-plus-circle text-primary me-2"></i>
                        <strong>Create:</strong> ${query} 
                        <small class="text-muted">(New Product)</small>
                    </div>
                `;
            } else {
                categories.forEach(cat => {
                    const div = document.createElement('div');
                    div.className = 'dropdown-item-custom';
                    div.style.cursor = 'pointer';
                    div.style.padding = '8px 12px';
                    div.style.background = '#e3f2fd';
                    div.style.borderRadius = '4px';
                    div.style.marginBottom = '5px';
                    div.innerHTML = `<i class="fa-solid fa-folder text-primary me-2"></i><strong>Category:</strong> ${cat.name} <small class="text-muted">(${cat.product_count} products)</small>`;
                    div.onclick = () => {
                        document.getElementById('productSearch').value = query;
                        openNewProductModal(query);
                        setTimeout(() => {
                            document.getElementById('newProdCategory').value = cat.name;
                        }, 100);
                    };
                    dropdown.appendChild(div);
                });
                
                products.forEach(p => {
                    const div = document.createElement('div');
                    div.className = 'dropdown-item-custom';
                    div.style.cursor = 'pointer';
                    div.style.padding = '8px 12px';
                    div.style.borderBottom = '1px solid #eee';
                    div.innerHTML = `<strong>${p.name}</strong> <small class="text-muted">(${p.sku})</small> <span class="float-end">₹${p.price}</span>`;
                    div.onclick = () => {
                        addToCart(p.id, p.name, p.price, 1);
                        document.getElementById('productSearch').value = '';
                        dropdown.style.display = 'none';
                    };
                    dropdown.appendChild(div);
                });
            }
            dropdown.style.display = 'block';
        });
});

function openNewProductModal(name) {
    tempNewProductName = name;
    document.getElementById('newProdName').value = name;
    document.getElementById('newProdCategory').value = '';
    document.getElementById('newProdRate').value = '';
    document.getElementById('newProductModal').style.display = 'flex';
}

function closeNewProductModal() {
    document.getElementById('newProductModal').style.display = 'none';
    tempNewProductName = '';
}

function confirmNewProduct() {
    const name = document.getElementById('newProdName').value;
    const category = document.getElementById('newProdCategory').value || 'Uncategorized';
    const rate = parseFloat(document.getElementById('newProdRate').value);

    if (!rate || rate <= 0) {
        alert('Please enter a valid Purchase Rate.');
        return;
    }

    addToCart('new', name, rate, 1, category);
    closeNewProductModal();
    document.getElementById('productSearch').value = '';
    document.getElementById('productDropdown').style.display = 'none';
}

function addToCart(id, name, rate, qty, category = '') {
    const existingIndex = cart.findIndex(item => (item.id === id && !item.is_new) || (item.is_new && item.name === name));
    
    if (existingIndex > -1) {
        cart[existingIndex].qty += qty;
        cart[existingIndex].total = cart[existingIndex].qty * cart[existingIndex].rate;
    } else {
        cart.push({
            id: id,
            is_new: id === 'new',
            name: name,
            category: category,
            rate: rate,
            qty: qty,
            total: rate * qty,
            expiry_date: ''
        });
    }
    updateCartUI();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartUI();
}

function updateQty(index, change) {
    cart[index].qty += change;
    if (cart[index].qty <= 0) {
        removeFromCart(index);
    } else {
        cart[index].total = cart[index].qty * cart[index].rate;
        updateCartUI();
    }
}

function updateCartUI() {
    const tbody = document.getElementById('cartTableBody');
    tbody.innerHTML = '';
    let grandTotal = 0;

    if (cart.length === 0) {
        tbody.innerHTML = '<tr id="emptyCartRow"><td colspan="6" class="text-center text-muted py-4">Cart is empty. Search and add products above.</td></tr>';
        document.getElementById('completePurchaseBtn').disabled = true;
    } else {
        document.getElementById('completePurchaseBtn').disabled = false;
        
        cart.forEach((item, index) => {
            grandTotal += item.total;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div class="fw-bold">${item.name}</div>
                    ${item.is_new ? '<small class="text-primary"><i class="fa-solid fa-star"></i> New Product</small>' : ''}
                </td>
                <td>
                    <input type="date" class="form-control form-control-sm expiry-input" 
                           value="${item.expiry_date || ''}" 
                           data-index="${index}"
                           style="width:130px;">
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-sm btn-outline-secondary" onclick="updateQty(${index}, -1)">-</button>
                        <span class="fw-bold">${item.qty}</span>
                        <button class="btn btn-sm btn-outline-secondary" onclick="updateQty(${index}, 1)">+</button>
                    </div>
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm rate-input" 
                           value="${item.rate}" step="0.01" 
                           data-index="${index}"
                           style="width:100px;">
                </td>
                <td class="fw-bold">₹${item.total.toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="removeFromCart(${index})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    document.getElementById('grandTotalDisplay').innerText = '₹' + grandTotal.toFixed(2);
    document.getElementById('cartItemsInput').value = JSON.stringify(cart);
    const completeBtn = document.getElementById('completePurchaseBtn');
    if (cart.length === 0) {
        completeBtn.disabled = true;
        completeBtn.innerHTML = '<i class="fa-solid fa-ban"></i> Add Products First';
    } else {
        completeBtn.disabled = false;
        completeBtn.innerHTML = '<i class="fa-solid fa-check"></i> Complete Purchase';
    }
}

document.getElementById('purchaseForm').addEventListener('submit', function(e) {
    if (cart.length === 0) {
        e.preventDefault();
        return false;
    }
});

document.addEventListener('click', function(e) {
    if (!e.target.closest('#supplierSearch')) {
        document.getElementById('supplierDropdown').style.display = 'none';
    }
    if (!e.target.closest('#productSearch')) {
        document.getElementById('productDropdown').style.display = 'none';
    }
});