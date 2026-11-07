// GreenLeaf Grocers - POS Terminal Controller

class POSController {
  constructor() {
    this.cart = {};
    this.allProducts = [];
    this.selectedCategory = 'All';
    this.discountPercent = 0.0;
    this.paymentMethod = 'Cash';

    this.initElements();
    this.initEventListeners();
    this.loadProducts();
  }

  initElements() {
    this.searchInput = document.getElementById('posSearchInput');
    this.categoryPills = document.querySelectorAll('.category-pill');
    this.productsGrid = document.getElementById('posProductsGrid');
    this.cartItemsList = document.getElementById('cartItemsList');
    this.emptyCartMsg = document.getElementById('emptyCartMsg');
    this.subtotalEl = document.getElementById('cartSubtotal');
    this.discountInput = document.getElementById('cartDiscountInput');
    this.discountAmountEl = document.getElementById('cartDiscountAmount');
    this.grandTotalEl = document.getElementById('cartGrandTotal');
    this.checkoutBtn = document.getElementById('posCheckoutBtn');
    this.clearCartBtn = document.getElementById('clearCartBtn');
    this.customerNameInput = document.getElementById('customerName');
    this.customerPhoneInput = document.getElementById('customerPhone');
    this.notesInput = document.getElementById('saleNotes');
    this.cartCountBadge = document.getElementById('cartItemCountBadge');
  }

  initEventListeners() {
    // 1. Search input with SKU barcode enter support
    if (this.searchInput) {
      this.searchInput.addEventListener('input', () => this.filterProducts());
      this.searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.handleBarcodeScan(this.searchInput.value.trim());
        }
      });
    }

    // 2. Category selection
    if (this.categoryPills) {
      this.categoryPills.forEach(pill => {
        pill.addEventListener('click', (e) => {
          this.categoryPills.forEach(p => p.classList.remove('active', 'btn-success'));
          this.categoryPills.forEach(p => p.classList.add('btn-outline-secondary'));
          
          pill.classList.remove('btn-outline-secondary');
          pill.classList.add('active', 'btn-success');
          this.selectedCategory = pill.getAttribute('data-category');
          this.filterProducts();
        });
      });
    }

    // 3. Discount input
    if (this.discountInput) {
      this.discountInput.addEventListener('input', () => {
        let val = parseFloat(this.discountInput.value) || 0.0;
        if (val < 0) val = 0;
        if (val > 100) val = 100;
        this.discountPercent = val;
        this.renderCart();
      });
    }

    // 4. Payment method radios/buttons
    document.querySelectorAll('input[name="paymentMethod"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.paymentMethod = e.target.value;
      });
    });

    // 5. Clear cart
    if (this.clearCartBtn) {
      this.clearCartBtn.addEventListener('click', () => {
        if (Object.keys(this.cart).length > 0 && confirm('Are you sure you want to clear the entire cart?')) {
          this.cart = {};
          this.renderCart();
        }
      });
    }

    // 6. Checkout
    if (this.checkoutBtn) {
      this.checkoutBtn.addEventListener('click', () => this.handleCheckout());
    }
  }

  async loadProducts() {
    try {
      const res = await fetch('/pos/api/products');
      if (res.ok) {
        this.allProducts = await res.json();
        this.renderProductCards(this.allProducts);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
    }
  }

  filterProducts() {
    const term = (this.searchInput ? this.searchInput.value.toLowerCase().trim() : '');
    const filtered = this.allProducts.filter(p => {
      const matchCat = (this.selectedCategory === 'All' || p.category === this.selectedCategory);
      const matchSearch = (!term || 
        p.name.toLowerCase().includes(term) || 
        p.sku.toLowerCase().includes(term) ||
        p.category.toLowerCase().includes(term)
      );
      return matchCat && matchSearch;
    });
    this.renderProductCards(filtered);
  }

  handleBarcodeScan(code) {
    if (!code) return;
    const found = this.allProducts.find(p => p.sku.toUpperCase() === code.toUpperCase());
    if (found) {
      this.addToCart(found);
      this.searchInput.value = '';
      this.filterProducts();
    }
  }

  renderProductCards(products) {
    if (!this.productsGrid) return;
    this.productsGrid.innerHTML = '';

    if (products.length === 0) {
      this.productsGrid.innerHTML = `
        <div class="col-12 text-center py-5">
          <i class="bi bi-search text-muted" style="font-size: 2.5rem;"></i>
          <h6 class="mt-2 text-muted">No products found matching your search.</h6>
        </div>
      `;
      return;
    }

    products.forEach(p => {
      const isOutOfStock = p.quantity <= 0;
      const isExpired = p.expiry_status === 'Expired';
      const isExpiringSoon = p.expiry_status === 'Expiring Soon';

      let statusBadge = '';
      if (isOutOfStock) {
        statusBadge = '<span class="badge badge-stock-out">Out of Stock</span>';
      } else if (p.quantity <= 10) {
        statusBadge = `<span class="badge badge-stock-low">Low: ${p.quantity} left</span>`;
      } else {
        statusBadge = `<span class="badge badge-stock-in">${p.quantity} in stock</span>`;
      }

      let expBadge = '';
      if (isExpired) {
        expBadge = '<span class="badge badge-exp-expired ms-1">Expired</span>';
      } else if (isExpiringSoon) {
        expBadge = `<span class="badge badge-exp-soon ms-1">Exp: ${p.days_to_expiry}d</span>`;
      }

      const card = document.createElement('div');
      card.className = 'col-sm-6 col-md-4 col-xl-3 mb-3';
      card.innerHTML = `
        <div class="pos-product-card ${isOutOfStock || isExpired ? 'opacity-75' : ''}" data-id="${p.id}">
          <div>
            <div class="d-flex justify-content-between align-items-start mb-1">
              <span class="badge bg-light text-dark border text-truncate" style="max-width: 110px;">${p.category}</span>
              <small class="text-muted font-monospace">${p.sku}</small>
            </div>
            <h6 class="fw-bold mb-1 text-dark" style="font-size: 0.95rem; min-height: 2.6rem;">${p.name}</h6>
            <div class="mb-2">
              ${statusBadge}
              ${expBadge}
            </div>
          </div>
          <div class="d-flex align-items-center justify-content-between pt-2 border-top">
            <span class="fs-5 fw-bold text-success">$${p.selling_price.toFixed(2)}</span>
            <button class="btn btn-sm btn-gl-primary add-to-cart-btn" ${isOutOfStock || isExpired ? 'disabled' : ''}>
              <i class="bi bi-cart-plus me-1"></i> Add
            </button>
          </div>
        </div>
      `;

      card.querySelector('.pos-product-card').addEventListener('click', (e) => {
        if (!isOutOfStock && !isExpired) {
          this.addToCart(p);
        }
      });

      this.productsGrid.appendChild(card);
    });
  }

  addToCart(product) {
    if (product.quantity <= 0) {
      alert(`Cannot add "${product.name}" - Product is out of stock!`);
      return;
    }
    if (product.expiry_status === 'Expired') {
      alert(`Cannot add "${product.name}" - Product is expired!`);
      return;
    }

    if (this.cart[product.id]) {
      if (this.cart[product.id].quantity + 1 > product.quantity) {
        alert(`Cannot add more. Maximum available stock for "${product.name}" is ${product.quantity}.`);
        return;
      }
      this.cart[product.id].quantity += 1;
      this.cart[product.id].line_total = parseFloat((this.cart[product.id].quantity * this.cart[product.id].price).toFixed(2));
    } else {
      this.cart[product.id] = {
        id: product.id,
        name: product.name,
        sku: product.sku,
        unit: product.unit,
        price: product.selling_price,
        max_stock: product.quantity,
        quantity: 1,
        line_total: product.selling_price
      };
    }

    this.renderCart();
  }

  updateQuantity(productId, delta) {
    const item = this.cart[productId];
    if (!item) return;

    const newQty = item.quantity + delta;
    if (newQty <= 0) {
      delete this.cart[productId];
    } else if (newQty > item.max_stock) {
      alert(`Available stock limit reached for "${item.name}" (${item.max_stock} units).`);
      return;
    } else {
      item.quantity = newQty;
      item.line_total = parseFloat((item.quantity * item.price).toFixed(2));
    }

    this.renderCart();
  }

  removeItem(productId) {
    if (this.cart[productId]) {
      delete this.cart[productId];
      this.renderCart();
    }
  }

  renderCart() {
    if (!this.cartItemsList) return;
    this.cartItemsList.innerHTML = '';

    const items = Object.values(this.cart);
    let subtotal = 0.0;
    let totalItemsCount = 0;

    if (items.length === 0) {
      if (this.emptyCartMsg) this.emptyCartMsg.style.display = 'block';
      if (this.checkoutBtn) this.checkoutBtn.disabled = true;
    } else {
      if (this.emptyCartMsg) this.emptyCartMsg.style.display = 'none';
      if (this.checkoutBtn) this.checkoutBtn.disabled = false;

      items.forEach(item => {
        subtotal += item.line_total;
        totalItemsCount += item.quantity;

        const row = document.createElement('div');
        row.className = 'cart-item-row';
        row.innerHTML = `
          <div style="flex: 1; min-width: 0;" class="pe-2">
            <div class="fw-semibold text-truncate text-dark" style="font-size: 0.9rem;" title="${item.name}">${item.name}</div>
            <div class="text-muted small">$${item.price.toFixed(2)} × ${item.quantity} = <strong class="text-success">$${item.line_total.toFixed(2)}</strong></div>
          </div>
          <div class="d-flex align-items-center gap-1">
            <button class="btn btn-outline-secondary btn-sm py-0 px-2 btn-qty-minus"><i class="bi bi-dash"></i></button>
            <span class="fw-bold px-1" style="min-width: 24px; text-align: center;">${item.quantity}</span>
            <button class="btn btn-outline-secondary btn-sm py-0 px-2 btn-qty-plus"><i class="bi bi-plus"></i></button>
            <button class="btn btn-outline-danger btn-sm py-0 px-2 ms-1 btn-item-remove"><i class="bi bi-trash"></i></button>
          </div>
        `;

        row.querySelector('.btn-qty-minus').addEventListener('click', () => this.updateQuantity(item.id, -1));
        row.querySelector('.btn-qty-plus').addEventListener('click', () => this.updateQuantity(item.id, 1));
        row.querySelector('.btn-item-remove').addEventListener('click', () => this.removeItem(item.id));

        this.cartItemsList.appendChild(row);
      });
    }

    subtotal = parseFloat(subtotal.toFixed(2));
    const discountAmount = parseFloat(((subtotal * this.discountPercent) / 100.0).toFixed(2));
    const grandTotal = parseFloat((subtotal - discountAmount).toFixed(2));

    if (this.subtotalEl) this.subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
    if (this.discountAmountEl) this.discountAmountEl.textContent = `-$${discountAmount.toFixed(2)}`;
    if (this.grandTotalEl) this.grandTotalEl.textContent = `$${grandTotal.toFixed(2)}`;
    if (this.cartCountBadge) this.cartCountBadge.textContent = totalItemsCount;
  }

  async handleCheckout() {
    const items = Object.values(this.cart).map(i => ({
      product_id: i.id,
      quantity: i.quantity,
      unit_price: i.price
    }));

    if (items.length === 0) {
      alert('Cart is empty. Please select products first.');
      return;
    }

    const payload = {
      customer_name: (this.customerNameInput ? this.customerNameInput.value.trim() : '') || 'Walk-in Customer',
      customer_phone: (this.customerPhoneInput ? this.customerPhoneInput.value.trim() : ''),
      discount_percent: this.discountPercent,
      payment_method: this.paymentMethod,
      notes: (this.notesInput ? this.notesInput.value.trim() : ''),
      items: items
    };

    this.checkoutBtn.disabled = true;
    const originalText = this.checkoutBtn.innerHTML;
    this.checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing Sale...';

    try {
      const res = await fetch('/pos/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok && data.success) {
        // Redirect to printable invoice
        window.location.href = data.redirect_url;
      } else {
        alert(`Checkout Failed: ${data.message || 'Unknown error occurred.'}`);
        this.checkoutBtn.disabled = false;
        this.checkoutBtn.innerHTML = originalText;
      }
    } catch (err) {
      console.error(err);
      alert('Network error while processing checkout. Please check server logs.');
      this.checkoutBtn.disabled = false;
      this.checkoutBtn.innerHTML = originalText;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('posProductsGrid')) {
    window.posApp = new POSController();
  }
});
