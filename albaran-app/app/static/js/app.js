/* ── Dark mode toggle ─────────────────────────────────────────────────── */
(function() {
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const label = document.getElementById('theme-label');
    if (label) label.textContent = theme === 'dark' ? 'Modo claro' : 'Modo oscuro';
  }

  // Apply correct label on load
  const current = localStorage.getItem('theme') || 'light';
  const label = document.getElementById('theme-label');
  if (label) label.textContent = current === 'dark' ? 'Modo claro' : 'Modo oscuro';

  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    applyTheme(isDark ? 'light' : 'dark');
  });
})();

/* ── Alert auto-close ──────────────────────────────────────────────────── */
document.querySelectorAll('.alert-close').forEach(btn => {
  btn.addEventListener('click', () => btn.closest('.alert').remove());
});
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(a => a.remove());
}, 5000);

/* ── Client autocomplete (step1 & search) ─────────────────────────────── */
function initClientAutocomplete(inputEl, hiddenEl, resultsEl) {
  if (!inputEl) return;
  let timer;
  inputEl.addEventListener('input', () => {
    clearTimeout(timer);
    const q = inputEl.value.trim();
    if (!q) { resultsEl.classList.remove('open'); return; }
    timer = setTimeout(async () => {
      const res = await fetch(`/clients/search-json?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      resultsEl.innerHTML = '';
      if (!data.length) { resultsEl.classList.remove('open'); return; }
      data.forEach(c => {
        const div = document.createElement('div');
        div.className = 'autocomplete-item';
        div.innerHTML = `<span class="ac-code">${c.client_code}</span> ${c.company_name}
          <span class="ac-code">${c.tax_id}</span>`;
        div.addEventListener('click', () => {
          inputEl.value = `${c.client_code} — ${c.company_name}`;
          if (hiddenEl) hiddenEl.value = c.id;
          resultsEl.classList.remove('open');
        });
        resultsEl.appendChild(div);
      });
      resultsEl.classList.add('open');
    }, 250);
  });
  document.addEventListener('click', e => {
    if (!resultsEl.contains(e.target) && e.target !== inputEl) {
      resultsEl.classList.remove('open');
    }
  });
}

const clientInput   = document.getElementById('client-search-input');
const clientHidden  = document.getElementById('existing_client_id');
const clientResults = document.getElementById('client-search-results');
initClientAutocomplete(clientInput, clientHidden, clientResults);

/* ── Machine picker ───────────────────────────────────────────────────── */
const pickerInput    = document.getElementById('machine-picker-input');
const pickerResults  = document.getElementById('machine-picker-results');
const selectedList   = document.getElementById('machine-selected-list');
const selectedIds    = new Set();

function updateMachineInputs() {
  document.querySelectorAll('.machine-id-input').forEach(el => el.remove());
  selectedIds.forEach(id => {
    const inp = document.createElement('input');
    inp.type  = 'hidden';
    inp.name  = 'machine_ids[]';
    inp.value = id;
    inp.className = 'machine-id-input';
    document.querySelector('form')?.appendChild(inp);
  });
}

function addMachine(id, code, name, status) {
  if (selectedIds.has(id)) return;
  selectedIds.add(id);
  const tag = document.createElement('div');
  tag.className = 'machine-tag';
  tag.dataset.id = id;
  const colors = { free: '#16a34a', occupied: '#dc2626', reserved: '#ea580c', repair: '#f97316' };
  const dot = `<span style="width:7px;height:7px;border-radius:50%;background:${colors[status]||'#999'};display:inline-block"></span>`;
  tag.innerHTML = `${dot} <strong>${code}</strong> — ${name}
    <button type="button" title="Quitar">×</button>`;
  tag.querySelector('button').addEventListener('click', () => {
    selectedIds.delete(id);
    tag.remove();
    updateMachineInputs();
  });
  selectedList?.appendChild(tag);
  updateMachineInputs();
}

if (pickerInput) {
  let timer;
  pickerInput.addEventListener('input', () => {
    clearTimeout(timer);
    const q = pickerInput.value.trim();
    if (!q) { pickerResults.classList.remove('open'); return; }
    timer = setTimeout(async () => {
      const res = await fetch(`/machines/search-json?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      pickerResults.innerHTML = '';
      if (!data.length) { pickerResults.classList.remove('open'); return; }
      data.forEach(m => {
        const div = document.createElement('div');
        div.className = 'machine-picker-item';
        const statusColors = {free:'var(--green)',occupied:'var(--red)',reserved:'var(--orange)',repair:'var(--orange)'};
        div.innerHTML = `
          <span class="code">${m.code}</span>
          <span class="name">${m.name}</span>
          <span style="font-size:11px;color:${statusColors[m.status]||'var(--grey-400)'};font-weight:600">
            ${m.status_label}
          </span>`;
        div.addEventListener('click', () => {
          addMachine(m.id, m.code, m.name, m.status);
          pickerInput.value = '';
          pickerResults.classList.remove('open');
        });
        pickerResults.appendChild(div);
      });
      pickerResults.classList.add('open');
    }, 200);
  });
  document.addEventListener('click', e => {
    if (!pickerResults.contains(e.target) && e.target !== pickerInput)
      pickerResults.classList.remove('open');
  });
}

/* ── Pricing mode toggle ──────────────────────────────────────────────── */
function updatePricingFields() {
  const mode = document.querySelector('input[name="pricing_mode"]:checked')?.value;
  const closedFields = document.getElementById('closed-price-fields');
  const openFields   = document.getElementById('open-price-fields');
  if (!closedFields || !openFields) return;
  if (mode === 'closed') {
    closedFields.style.display = '';
    openFields.style.display   = 'none';
  } else {
    closedFields.style.display = 'none';
    openFields.style.display   = '';
  }
}
document.querySelectorAll('input[name="pricing_mode"]').forEach(r => {
  r.addEventListener('change', updatePricingFields);
});
updatePricingFields();

/* ── Client abbrev suggestion ─────────────────────────────────────────── */
const companyNameInput = document.getElementById('company_name');
const abbrevInput      = document.getElementById('abbrev');
if (companyNameInput && abbrevInput) {
  let abbrevTouched = false;
  abbrevInput.addEventListener('input', () => { abbrevTouched = true; });
  companyNameInput.addEventListener('input', async () => {
    if (abbrevTouched) return;
    const name = companyNameInput.value.trim();
    if (!name) return;
    const res = await fetch(`/clients/suggest-abbrev?name=${encodeURIComponent(name)}`);
    const data = await res.json();
    abbrevInput.value = data.abbrev;
    // update preview
    const preview = document.getElementById('code-preview');
    if (preview) preview.textContent = `C-${data.abbrev}-###`;
  });
  abbrevInput.addEventListener('input', () => {
    const preview = document.getElementById('code-preview');
    if (preview) preview.textContent = `C-${abbrevInput.value.toUpperCase()}-###`;
  });
}

/* ── Dynamic contacts ─────────────────────────────────────────────────── */
const addContactBtn = document.getElementById('add-contact-btn');
const contactsWrap  = document.getElementById('contacts-wrap');
if (addContactBtn && contactsWrap) {
  addContactBtn.addEventListener('click', () => {
    const row = document.createElement('div');
    row.className = 'contact-row';
    row.innerHTML = `
      <input type="text" name="contact_name[]" placeholder="Nombre *">
      <input type="text" name="contact_role[]" placeholder="Cargo">
      <input type="tel"  name="contact_phone[]" placeholder="Teléfono">
      <input type="email" name="contact_email[]" placeholder="Email">
      <button type="button" class="btn btn-outline btn-sm remove-contact">×</button>`;
    row.querySelector('.remove-contact').addEventListener('click', () => row.remove());
    contactsWrap.appendChild(row);
  });
  contactsWrap.addEventListener('click', e => {
    if (e.target.classList.contains('remove-contact')) e.target.closest('.contact-row').remove();
  });
}

/* ── Close albarán modal ──────────────────────────────────────────────── */
const openCloseModal = document.getElementById('open-close-modal');
const closeModalEl   = document.getElementById('close-albaran-modal');
const closeModalBack = document.getElementById('modal-backdrop');
if (openCloseModal && closeModalEl) {
  openCloseModal.addEventListener('click', () => {
    closeModalBack.style.display = 'flex';
  });
  document.getElementById('cancel-close-btn')?.addEventListener('click', () => {
    closeModalBack.style.display = 'none';
  });
  closeModalBack.addEventListener('click', e => {
    if (e.target === closeModalBack) closeModalBack.style.display = 'none';
  });
}

/* ── Auto-calculate preview for open rentals ──────────────────────────── */
function calcOpenPreview() {
  const start = document.getElementById('rental_start')?.value;
  const end   = document.getElementById('modal_rental_end')?.value;
  const rate  = parseFloat(document.getElementById('price_rate_val')?.textContent || 0);
  const unit  = document.getElementById('price_unit_val')?.textContent || '';
  const preview = document.getElementById('calculated-preview');
  if (!preview) return;
  if (!start || !end || !rate) { preview.textContent = '—'; return; }
  const days = Math.max(1, (new Date(end) - new Date(start)) / 86400000);
  let total;
  if (unit === 'day')   total = rate * days;
  else if (unit === 'week')  total = rate * (days / 7);
  else if (unit === 'month') total = rate * (days / 30);
  else { preview.textContent = '—'; return; }
  preview.textContent = total.toLocaleString('es-ES', {minimumFractionDigits:2}) + ' €';
}
document.getElementById('modal_rental_end')?.addEventListener('input', calcOpenPreview);
