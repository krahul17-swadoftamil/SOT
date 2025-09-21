document.addEventListener('DOMContentLoaded', () => {
const controls = document.createElement('div');
controls.style.textAlign='right';
const minus = document.createElement('button'); minus.innerText='−'; minus.className='qty-btn';
const plus = document.createElement('button'); plus.innerText='+'; plus.className='qty-btn';
const qtySpan = document.createElement('div'); qtySpan.innerText='0'; qtySpan.id = `qty-${it.id}`;
const line = document.createElement('div'); line.id = `line-${it.id}`; line.innerText = formatINR(0);


minus.addEventListener('click', ()=> changeQty(it.id, -1));
plus.addEventListener('click', ()=> changeQty(it.id, +1));


controls.appendChild(minus); controls.appendChild(qtySpan); controls.appendChild(plus); controls.appendChild(line);


if (!it.available){
const badge = document.createElement('div'); badge.innerText='Unavailable'; badge.style.color='#fff'; badge.style.background='#777'; badge.style.padding='4px 8px'; badge.style.borderRadius='6px';
controls.appendChild(badge);
}


card.appendChild(img); card.appendChild(mid); card.appendChild(controls);
container.appendChild(card);
});


document.getElementById('items-loading').classList.add('hidden');
container.classList.remove('hidden');
updateSummary();
}


function changeQty(id, delta){
const it = items[id];
if (!it) return;
if (!it.available){ alert('This item is currently unavailable'); return; }


cart[id] = Math.max(0, (cart[id]||0) + delta);
document.getElementById(`qty-${id}`).innerText = cart[id];
document.getElementById(`line-${id}`).innerText = formatINR((cart[id]||0) * it.price);
updateSummary();
}


function updateSummary(){
const linesDiv = document.getElementById('summary-lines');
linesDiv.innerHTML = '';
let total = 0;
Object.keys(cart).forEach(id => {
const q = cart[id]; if (!q) return;
const it = items[id];
const lineTotal = q * it.price; total += lineTotal;


const row = document.createElement('div'); row.className = 'flex justify-between';
row.innerHTML = `<div>${it.name} × ${q}</div><div>${formatINR(lineTotal)}</div>`;
linesDiv.appendChild(row);
});
document.getElementById('total-price').innerText = formatINR(total);
}


function getCsrf(){
const cookie = document.cookie.split(';').map(c=>c.trim()).find(c=>c.startsWith('csrftoken='));
return cookie ? cookie.split('=')[1] : '';
}


document.getElementById('place-order').addEventListener('click', async () => {
// build payload
const orderItems = Object.keys(cart).filter(id=>cart[id]>0).map(id=>({ id: id, qty: cart[id] }));
if (!orderItems.length){ alert('Select items first'); return; }


try{
const res = await fetch(createUrl, {
method: 'POST', credentials: 'same-origin', headers: {
'Content-Type': 'application/json', 'X-CSRFToken': getCsrf()
}, body: JSON.stringify({ items: orderItems })
});
const data = await res.json();
if (!res.ok){ alert(data.error || 'Order failed'); return; }
// success: redirect to order detail or show success
window.location.href = data.redirect_url || "{% url 'orders:orders_list' %}";
}catch(err){ console.error(err); alert('Network error'); }
});


// initial load 
fetchItems();


// optional: poll every 20s so new items added in admin appear quickly
setInterval(fetchItems, 20000);
});

{
  "customer_name":"Kumar",
  "customer_phone":"9876543210",
  "customer_email":"k@example.com",
  "delivery_address":"123, Some Road, Chennai",
  "pincode":"600001",
  "preferences":"No onion",
  "items":[{"id":12,"quantity":2},{"id":3,"quantity":1}],
  "gst_percent":5
}

// assume cart object exists mapping id->qty and createUrl variable points to create endpoint
const checkoutModal = document.getElementById('checkout-modal');
const checkoutForm = document.getElementById('checkout-form');

document.getElementById('place-order').addEventListener('click', () => {
  // ensure items selected
  const itemsToSend = Object.keys(cart).filter(k => cart[k] > 0).map(k => ({ id: Number(k), quantity: cart[k] }));
  if (!itemsToSend.length) { alert('Select items first'); return; }
  // show modal
  checkoutModal.classList.remove('hidden');
  checkoutModal.style.display = 'flex';
});

document.getElementById('checkout-cancel').addEventListener('click', () => {
  checkoutModal.classList.add('hidden');
  checkoutModal.style.display = 'none';
});

checkoutForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(checkoutForm);
  const payload = {
    customer_name: form.get('customer_name'),
    customer_phone: form.get('customer_phone'),
    customer_email: form.get('customer_email'),
    delivery_address: form.get('delivery_address'),
    pincode: form.get('pincode'),
    preferences: form.get('preferences'),
    items: Object.keys(cart).filter(k => cart[k] > 0).map(k => ({ id: Number(k), quantity: cart[k] })),
    gst_percent: 5.0
  };

  // Show loading
  const submitBtn = document.getElementById('checkout-submit');
  submitBtn.disabled = true;
  submitBtn.innerText = 'Placing order...';

  try {
    const res = await fetch(createUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }

    // redirect to confirmation
    window.location.href = data.redirect_url || `/orders/confirmation/${data.order_id}/`;
  } catch (err) {
    alert('Order failed: ' + (err.message || 'Network error'));
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Place Order';
  }
});
