
// Config placeholders (fill when back-end is ready)
const PRICE = {10:99, 20:199, 30:299};
const PACKS = [10,20,30];
const AVAILABILITY_URL = 'YOUR_AVAILABILITY_JSON_URL';
const ASK_FORM_URL = 'YOUR_ASK_FORM_WEBAPP_URL';

// CAPS subject sets (editable). You can comment out any you don't offer yet.
const SUBJECTS = {
  12: [
    "Mathematics","Mathematical Literacy","Physical Sciences","Life Sciences",
    "Accounting","Economics","Business Studies","Geography","History",
    "English HL","English FAL","Afrikaans HL","Afrikaans FAL",
    "Information Technology (IT)","Computer Applications Technology (CAT)",
    "Engineering Graphics & Design (EGD)","Mechanical Technology",
    "Electrical Technology","Civil Technology","Tourism","Consumer Studies",
    "Visual Arts","Dramatic Arts","Agricultural Sciences"
  ],
  11: [
    "Mathematics","Mathematical Literacy","Physical Sciences","Life Sciences",
    "Accounting","Economics","Business Studies","Geography","History",
    "English HL","English FAL","Afrikaans HL","Afrikaans FAL",
    "IT","CAT","EGD","Mechanical Technology","Electrical Technology",
    "Civil Technology","Tourism","Consumer Studies","Visual Arts",
    "Dramatic Arts","Agricultural Sciences"
  ],
  10: [
    "Mathematics","Mathematical Literacy","Physical Sciences","Life Sciences",
    "Accounting","Economics","Business Studies","Geography","History",
    "English HL","English FAL","Afrikaans HL","Afrikaans FAL",
    "IT","CAT","EGD","Mechanical Technology","Electrical Technology",
    "Civil Technology","Tourism","Consumer Studies","Visual Arts",
    "Dramatic Arts","Agricultural Sciences"
  ],
  9: ["Mathematics","Natural Sciences","Social Sciences","Economic Management Sciences","English HL/FAL","Afrikaans HL/FAL","Technology","EMS","Creative Arts","Life Orientation"],
  8: ["Mathematics","Natural Sciences","Social Sciences","English HL/FAL","Afrikaans HL/FAL","Technology","EMS","Creative Arts","Life Orientation"]
};

function skuFor(grade, subject, count){
  const sub = subject.replace(/\s+/g,'-');
  const prefix = `G${String(grade).padStart(2,'0')}`;
  return `${prefix}-${sub}-${count}PACK`.toUpperCase();
}

function populateSubjects(grade){
  const select = document.getElementById('subjectSelect');
  const list = SUBJECTS[grade] || [];
  select.innerHTML = '';
  list.forEach(sub=>{
    const opt = document.createElement('option');
    opt.value = sub;
    opt.textContent = sub;
    select.appendChild(opt);
  });
}

function renderCards(){
  const grade = document.getElementById('gradeSelect').value;
  const subject = document.getElementById('subjectSelect').value;
  const grid = document.getElementById('packGrid');
  grid.innerHTML = '';
  PACKS.forEach((count,i) => {
    const sku = skuFor(grade, subject, count);
    const card = document.createElement('div');
    card.className = 'card'+(count===20?' reco':'');
    card.innerHTML = `
      <div class="pack-title">
        <h3>${subject} — ${count} Papers</h3>
        <span class="badge">SKU: ${sku}</span>
      </div>
      <div class="price">R${PRICE[count]}</div>
      <p class="hint">Most recent papers first. Includes QP + Memo where available.</p>
      <div class="actions">
        <button class="btn primary" data-sku="${sku}">Buy with PayFast</button>
        <a class="btn white" href="https://wa.me/27716816131?text=Hi!%20I%20want%20${encodeURIComponent(sku)}">WhatsApp</a>
      </div>
    `;
    grid.appendChild(card);
  });
}

function attachHandlers(){
  document.getElementById('gradeSelect').addEventListener('change', e=>{
    populateSubjects(e.target.value);
    renderCards();
  });
  document.getElementById('subjectSelect').addEventListener('change', renderCards);
  document.getElementById('packGrid').addEventListener('click', (e)=>{
    const btn = e.target.closest('button[data-sku]');
    if(!btn) return;
    const sku = btn.getAttribute('data-sku');
    // TODO: Redirect to Hosted Checkout using your backend/Apps Script
    alert(`Proceeding to PayFast checkout for ${sku}`);
  });

  // Inquiry form
  const askForm = document.getElementById('askForm');
  if(askForm){
    askForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const status = document.getElementById('askStatus');
      status.textContent = 'Sending…';
      const data = Object.fromEntries(new FormData(askForm).entries());
      try{
        const r = await fetch(ASK_FORM_URL, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
        if(r.ok){
          status.textContent = 'Thanks! We will reply shortly.';
          askForm.reset();
        } else {
          status.textContent = 'Could not send. Please WhatsApp us.';
        }
      }catch(err){
        status.textContent = 'Network error. Please WhatsApp us.';
      }
    });
  }

  // Testimonials carousel
  const slides = [...document.querySelectorAll('.slide')];
  let idx = 0;
  const show = i => slides.forEach((s,j)=> s.classList.toggle('active', j===i));
  document.querySelector('.carousel .prev').addEventListener('click',()=>{ idx=(idx-1+slides.length)%slides.length; show(idx);});
  document.querySelector('.carousel .next').addEventListener('click',()=>{ idx=(idx+1)%slides.length; show(idx);});
  setInterval(()=>{ idx=(idx+1)%slides.length; show(idx); }, 6000);

  // Availability badges (optional)
  try{
    fetch(AVAILABILITY_URL).then(r=>r.ok?r.json():null).then(data=>{
      if(!data) return;
      document.querySelectorAll('.badge').forEach(b=>{
        const sku = b.textContent.replace('SKU: ','');
        const entry = data.bundles && data.bundles.find(x=>x.sku===sku);
        if(entry && entry.ready){ b.textContent += ' · Ready'; }
      });
    });
  }catch(err){ /* ignore */ }
}

document.addEventListener('DOMContentLoaded', ()=>{
  populateSubjects(document.getElementById('gradeSelect').value);
  renderCards();
  attachHandlers();
});
