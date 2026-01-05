
const state = {
  products: [],
  cart: []
};

const formatZAR = (n) => `R${n.toFixed(0)}`;

async function loadProducts() {
  const res = await fetch('assets/products.json');
  const data = await res.json();
  state.products = data;
  renderProducts();
}

function renderProducts() {
  const gSel = document.getElementById('filter-grade').value;
  const sSel = document.getElementById('filter-subject').value;
  const grid = document.getElementById('product-grid');
  grid.innerHTML = '';
  const filtered = state.products.filter(p => {
    const gradeMatch = gSel === 'all' ? true : String(p.grade) === String(gSel);
    const subjectMatch = sSel === 'all' ? true : p.subject === sSel;
    return gradeMatch && subjectMatch;
  });
  for (const p of filtered) {
    const el = document.createElement('div');
    el.className = 'product-card';
    el.innerHTML = `
      <div class="thumb">${p.subject} · Grade ${p.grade}</div>
      <div class="body">
        <h3>${p.title}</h3>
        <div class="meta">Pack ID: ${p.id}</div>
        <div class="price">${formatZAR(p.price)}</div>
        <div class="actions">
          <button class="btn btn-primary" data-id="${p.id}">Add to Cart</button>
          <a class="btn btn-outline" href="https://wa.me/27716816131?text=Hi!%20I%20want%20to%20order%20Pack%20${p.id}%20(${encodeURIComponent(p.title)})%20for%20${formatZAR(p.price)}" target="_blank" rel="noopener">Order on WhatsApp</a>
        </div>
      </div>`;
    el.querySelector('button').addEventListener('click', () => addToCart(p.id));
    grid.appendChild(el);
  }
}

function addToCart(id) {
  const p = state.products.find(x => x.id === id);
  if (!p) return;
  const exists = state.cart.find(x => x.id === id);
  if (exists) { exists.qty += 1; } else { state.cart.push({ ...p, qty: 1 }); }
  renderCart();
}

function removeFromCart(id) {
  state.cart = state.cart.filter(x => x.id !== id);
  renderCart();
}

function renderCart() {
  const list = document.getElementById('cart-list');
  const totalEl = document.getElementById('cart-total');
  list.innerHTML = '';
  let total = 0;
  for (const item of state.cart) {
    total += item.price * item.qty;
    const row = document.createElement('div');
    row.className = 'cart-item';
    row.innerHTML = `
      <span>${item.title} × ${item.qty}</span>
      <span>${formatZAR(item.price * item.qty)}</span>
      <button class="btn" aria-label="Remove">✕</button>
    `;
    row.querySelector('button').addEventListener('click', () => removeFromCart(item.id));
    list.appendChild(row);
  }
  totalEl.textContent = formatZAR(total);
}

function checkoutWhatsApp() {
  if (state.cart.length === 0) return alert('Your cart is empty.');
  const ids = state.cart.map(x => x.id).join(', ');
  const total = state.cart.reduce((s, x) => s + x.price * x.qty, 0);
  const text = `Order: ${ids}. Total: ${formatZAR(total)}.`;
  const url = `https://wa.me/27716816131?text=${encodeURIComponent(text)}`;
  window.open(url, '_blank');
}

function checkoutPayFast() {
  if (state.cart.length === 0) return alert('Your cart is empty.');
  const total = state.cart.reduce((s, x) => s + x.price * x.qty, 0);
  // NOTE: For production, use a server-side script to create a PayFast signature and redirect
  // the user to the hosted payment page. Here we just show instructions.
  alert('PayFast checkout: In production, you will be redirected to a hosted payment page. For this demo, please use WhatsApp checkout.');
}

function submitLead(e) {
  e.preventDefault();
  const name = document.getElementById('lead-name').value.trim();
  const email = document.getElementById('lead-email').value.trim();
  const grade = document.getElementById('lead-grade').value;
  const status = document.getElementById('lead-status');
  // Placeholder: integrate with Google Apps Script Web App to log leads to Google Sheets
  status.textContent = 'Thanks! We'll email your discount code shortly.';
  (async () => {
    try {
      // Example POST to Apps Script Web App (replace with your script URL)
      // await fetch('https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec', {
      //   method: 'POST', headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ name, email, grade })
      // });
    } catch (err) { console.error(err); }
  })();
  return false;
}

document.addEventListener('DOMContentLoaded', () => {
  loadProducts();
  document.getElementById('filter-grade').addEventListener('change', renderProducts);
  document.getElementById('filter-subject').addEventListener('change', renderProducts);
  document.getElementById('checkout-whatsapp').addEventListener('click', checkoutWhatsApp);
  document.getElementById('checkout-payfast').addEventListener('click', checkoutPayFast);
});
