(function () {
  'use strict';

  let itemIndex = 0;

  const itemRowTemplate = () => {
    const idx = itemIndex++;
    const row = document.createElement('div');
    row.className = 'item-row';
    row.dataset.index = idx;
    row.innerHTML = `
      <div class="form-group">
        <label>Date</label>
        <input type="date" name="items_${idx}_date" required>
      </div>
      <div class="form-group">
        <label>Category</label>
        <select name="items_${idx}_category_id" required class="item-category"></select>
      </div>
      <div class="form-group product-filter-wrap">
        <label>Product</label>
        <input type="text" class="product-filter" placeholder="Filter products..." autocomplete="off">
        <select name="items_${idx}_product_id" required class="item-product"></select>
      </div>
      <div class="form-group">
        <label>Price</label>
        <input type="number" name="items_${idx}_price" step="any" min="0" required placeholder="0">
      </div>
      <div class="form-group">
        <label>Qty</label>
        <input type="number" name="items_${idx}_quantity" min="1" value="1" required>
      </div>
      <button type="button" class="btn btn-secondary remove-row" aria-label="Remove row">×</button>
    `;
    return row;
  };

  function getProductsByCategory() {
    const el = document.getElementById('products-by-category');
    if (!el) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (_) {
      return {};
    }
  }

  function getCategories() {
    const el = document.getElementById('categories-data');
    if (!el) return [];
    try {
      return JSON.parse(el.textContent);
    } catch (_) {
      return [];
    }
  }

  function fillCategorySelect(select, selectedId) {
    const categories = getCategories();
    select.innerHTML = '<option value="">Select category</option>' +
      categories.map(c => `<option value="${c.id}" ${c.id == selectedId ? 'selected' : ''}>${escapeHtml(c.name)}</option>`).join('');
  }

  function fillProductSelect(select, categoryId, selectedProductId, productsByCategory) {
    const products = categoryId ? (productsByCategory[categoryId] || []) : [];
    select.innerHTML = '<option value="">Select product</option>' +
      products.map(p => `<option value="${p.id}" ${p.id == selectedProductId ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function bindProductFilter(input, select, productsByCategory) {
    if (!input || !select) return;
    const categorySelect = input.closest('.item-row').querySelector('.item-category');
    function filterProducts() {
      const categoryId = categorySelect ? categorySelect.value : null;
      const products = categoryId ? (productsByCategory[categoryId] || []) : [];
      const q = (input.value || '').toLowerCase();
      const opts = select.querySelectorAll('option');
      opts.forEach((opt, i) => {
        if (i === 0) {
          opt.hidden = false;
          return;
        }
        const text = (opt.textContent || '').toLowerCase();
        opt.hidden = q && text.indexOf(q) === -1;
      });
    }
    input.addEventListener('input', filterProducts);
    input.addEventListener('focus', () => select.size = Math.max(4, select.querySelectorAll('option:not([hidden])').length));
    input.addEventListener('blur', () => { setTimeout(() => { select.size = 1; }, 150); });
  }

  function bindCategoryChange(row, productsByCategory) {
    const catSelect = row.querySelector('.item-category');
    const prodSelect = row.querySelector('.item-product');
    const filterInput = row.querySelector('.product-filter');
    if (!catSelect || !prodSelect) return;
    catSelect.addEventListener('change', () => {
      fillProductSelect(prodSelect, catSelect.value, null, productsByCategory);
      if (filterInput) filterInput.value = '';
    });
  }

  function initPaycheckForm() {
    const container = document.getElementById('paycheck-items');
    const addBtn = document.getElementById('add-item');
    if (!container || !addBtn) return;

    const productsByCategory = getProductsByCategory();
    const categories = getCategories();
    itemIndex = container.querySelectorAll('.item-row').length;

    function addRow(data) {
      const row = itemRowTemplate();
      const dateInput = row.querySelector('input[name="date"]');
      const catSelect = row.querySelector('.item-category');
      const prodSelect = row.querySelector('.item-product');
      const priceInput = row.querySelector('input[name="price"]');
      const qtyInput = row.querySelector('input[name="quantity"]');
      const filterInput = row.querySelector('.product-filter');

      fillCategorySelect(catSelect, data && data.category_id);
      fillProductSelect(prodSelect, data && data.category_id, data && data.product_id, productsByCategory);
      if (data) {
        if (data.date) dateInput.value = data.date;
        if (data.price != null) priceInput.value = data.price;
        if (data.quantity != null) qtyInput.value = data.quantity;
        if (filterInput) filterInput.placeholder = 'Filter products...';
      }

      bindCategoryChange(row, productsByCategory);
      bindProductFilter(filterInput, prodSelect, productsByCategory);

      row.querySelector('.remove-row').addEventListener('click', () => {
        if (container.querySelectorAll('.item-row').length > 1) row.remove();
      });

      container.appendChild(row);
    }

    addBtn.addEventListener('click', () => addRow(null));

    const productsByCategory = getProductsByCategory();
    document.querySelectorAll('#paycheck-items .item-row').forEach(row => {
      bindCategoryChange(row, productsByCategory);
      const filterInput = row.querySelector('.product-filter');
      const prodSelect = row.querySelector('.item-product');
      if (filterInput && prodSelect) bindProductFilter(filterInput, prodSelect, productsByCategory);
    });

    const initialRows = container.dataset.initialRows | 0;
    if (initialRows < 1) addRow(null);
    else for (let i = 0; i < initialRows; i++) addRow(null);

    const form = container.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        const rows = container.querySelectorAll('.item-row');
        rows.forEach((r, i) => {
          r.querySelectorAll('input, select').forEach(function (el) {
            if (el.name) {
              const m = el.name.match(/^items_(\d+)_(.+)$/);
              if (m) el.name = 'items_' + i + '_' + m[2];
            }
          });
        });
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPaycheckForm);
  } else {
    initPaycheckForm();
  }
})();
