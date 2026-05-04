// IASW Frontend - SPA-style router modelled after the demo video
const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:8000/api`;

// -------------- Auth helpers --------------
const getToken = () => localStorage.getItem('token');
const getRole = () => localStorage.getItem('role');
const getUsername = () => localStorage.getItem('username');
const getFullName = () => localStorage.getItem('full_name') || getUsername() || '';
const authHeaders = () => { const t = getToken(); return t ? { Authorization: `Bearer ${t}` } : {}; };

function logout() {
    if (getToken()) {
        fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST', headers: { ...authHeaders() } }).catch(() => {});
    }
    localStorage.clear();
    window.location.href = 'login.html';
}

// -------------- Navigation schemas per role --------------
const NAVS = {
    staff: [
        { id: 'dashboard', label: 'Dashboard', icon: iconHome() },
        { id: 'new-request', label: 'New Request', icon: iconPlus() },
        { id: 'all-requests', label: 'All Requests', icon: iconList() },
    ],
    account_holder: [
        { id: 'dashboard', label: 'Dashboard', icon: iconHome() },
        { id: 'new-request', label: 'New Request', icon: iconPlus() },
        { id: 'account', label: 'My Account', icon: iconUser() },
        { id: 'all-requests', label: 'My Requests', icon: iconList() },
    ],
    checker: [
        { id: 'dashboard', label: 'Dashboard', icon: iconHome() },
        { id: 'review-queue', label: 'Review Queue', icon: iconClipboard() },
        { id: 'my-reviews', label: 'My Reviews', icon: iconHistory() },
        { id: 'users', label: 'Users', icon: iconUsers() },
    ],
};

const ROLE_COPY = {
    staff: { chip: 'Staff Portal', chipClass: '', logoClass: '', avatarClass: '', roleSub: 'Staff Member', help: { title: 'Need Help?', text: 'Contact support for assistance with requests.' } },
    account_holder: { chip: 'Account Portal', chipClass: '', logoClass: '', avatarClass: '', roleSub: 'Account Holder', help: { title: 'Need Help?', text: 'Submit a change request and track its progress here.' } },
    checker: { chip: 'Checker Workbench', chipClass: 'checker', logoClass: 'checker', avatarClass: 'checker', roleSub: 'Checker', help: { title: 'Review Tips', text: 'Always verify document authenticity before approving.' } },
};

let state = {
    route: 'dashboard',
    currentRequest: null,
    pending: [],
    myReviews: [],
    allRequests: [],
    pendingPoll: null,
    decision: null,
    decisionNotes: '',
};

// -------------- Boot --------------
document.addEventListener('DOMContentLoaded', () => {
    if (!getToken()) { window.location.href = 'login.html'; return; }
    initChrome();
    renderNav();
    navigate(defaultRoute());
});

function defaultRoute() {
    const role = getRole();
    if (role === 'checker') return 'review-queue';
    if (role === 'account_holder') return 'account';
    return 'dashboard';
}

function initChrome() {
    const role = getRole();
    const copy = ROLE_COPY[role] || ROLE_COPY.staff;
    document.getElementById('role-chip').textContent = copy.chip;
    document.getElementById('role-chip').className = 'role-chip ' + copy.chipClass;
    document.getElementById('tb-logo').className = 'topbar-logo ' + copy.logoClass;
    const logoStroke = copy.logoClass === 'checker' ? '#10b981' : '#3d5afe';
    document.getElementById('tb-logo').innerHTML = role === 'checker'
        ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${logoStroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>`
        : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${logoStroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>`;
    const name = getFullName();
    document.getElementById('user-name').textContent = role === 'checker' ? 'admin' : (getUsername() || 'user');
    document.getElementById('user-role-sub').textContent = copy.roleSub;
    document.getElementById('user-avatar').textContent = (name[0] || 'U').toUpperCase();
    document.getElementById('user-avatar').className = 'avatar ' + copy.avatarClass;
    document.getElementById('help-title').textContent = copy.help.title;
    document.getElementById('help-text').textContent = copy.help.text;
}

function renderNav() {
    const role = getRole();
    const items = NAVS[role] || NAVS.staff;
    const host = document.getElementById('nav-list');
    host.innerHTML = items.map(it => `
        <button class="nav-item ${it.id === state.route ? 'active' : ''}" onclick="navigate('${it.id}')">
            <span>${it.icon}</span>
            <span>${it.label}</span>
            <span class="chev">›</span>
        </button>
    `).join('');
}

function navigate(route, arg) {
    state.route = route;
    renderNav();
    const main = document.getElementById('main');
    main.innerHTML = '';
    stopPendingPoll();
    try {
        switch (route) {
            case 'dashboard': return renderDashboard(main);
            case 'new-request': return renderNewRequest(main);
            case 'all-requests': return renderAllRequests(main);
            case 'request-detail': return renderRequestDetail(main, arg);
            case 'review-queue': return renderReviewQueue(main);
            case 'review-detail': return renderReviewDetail(main, arg);
            case 'my-reviews': return renderMyReviews(main);
            case 'users': return renderUsers(main);
            case 'account': return renderAccount(main);
            default: main.innerHTML = `<div class="card">Unknown route: ${escapeHtml(route)}</div>`;
        }
    } catch (err) {
        console.error('navigate() failed:', err);
        main.innerHTML = `<div class="alert alert-error"><strong>Render error:</strong> ${escapeHtml(err.message)}<br/><small>See browser console for details.</small></div>`;
    }
}

// ================== DASHBOARD ==================
function renderDashboard(host) {
    const role = getRole();
    host.innerHTML = `
        ${breadcrumb([cap(role.replace('_', ' ')), 'Dashboard'])}
        <div class="page-head">
            <div>
                <h1 class="page-title">Welcome, ${escapeHtml(getFullName())}</h1>
                <div class="page-sub">${role === 'checker' ? 'Requests waiting for your review.' : 'Here’s an overview of your recent activity.'}</div>
            </div>
        </div>
        <div class="card" id="dash-card">
            <div class="loading-center"><div class="spinner"></div>Loading...</div>
        </div>
    `;
    loadDashboardStats();
}

async function loadDashboardStats() {
    const role = getRole();
    const card = document.getElementById('dash-card');
    try {
        if (role === 'checker') {
            const r = await fetch(`${API_BASE_URL}/checker/pending-requests`, { headers: authHeaders() });
            const d = await r.json();
            const count = (d.pending_requests || []).length;
            card.innerHTML = `
                <div class="card-title">Queue Summary</div>
                <div class="card-sub">Live view of the review workload</div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:6px;">
                    ${statTile('Pending', count, 'processing')}
                    ${statTile('High Risk', (d.pending_requests || []).filter(x => x.confidence_score < 70).length, 'danger')}
                    ${statTile('AI Approve', (d.pending_requests || []).filter(x => x.ai_recommendation === 'approve').length, 'success')}
                </div>
                <div style="margin-top:18px;"><button class="btn btn-primary" onclick="navigate('review-queue')">Open Review Queue</button></div>
            `;
        } else {
            card.innerHTML = `
                <div class="card-title">Recent Activity</div>
                <div class="card-sub">Your submissions at a glance</div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:6px;">
                    ${statTile('In Progress', '–', 'processing')}
                    ${statTile('Completed (7d)', '–', 'success')}
                    ${statTile('Rejected (7d)', '–', 'danger')}
                </div>
                <div style="margin-top:18px;"><button class="btn btn-primary" onclick="navigate('new-request')">Start New Request</button></div>
            `;
        }
    } catch (e) {
        card.innerHTML = `<div class="alert alert-error">Failed to load dashboard: ${e.message}</div>`;
    }
}

function statTile(label, value, tone) {
    const color = tone === 'success' ? 'var(--success)' : tone === 'danger' ? 'var(--danger)' : 'var(--brand)';
    return `
        <div style="padding:16px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--panel-soft);">
            <div style="font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;">${label}</div>
            <div style="font-size:28px;font-weight:700;color:${color};margin-top:6px;">${value}</div>
        </div>
    `;
}

// ================== NEW REQUEST ==================
function renderNewRequest(host) {
    const role = getRole();
    host.innerHTML = `
        ${breadcrumb([cap(role.replace('_', ' ')), 'Requests', 'New Request'])}
        <div class="page-head">
            <div>
                <h1 class="page-title">New Request</h1>
                <div class="page-sub">Submit a new customer account change request</div>
            </div>
        </div>
        <div class="form-card">
            <h3>New Change Request</h3>
            <div class="card-sub">Submit a customer account change request with supporting documentation</div>
            <div id="submit-alert"></div>
            <form id="submit-form">
                <div class="field">
                    <label>Customer ID</label>
                    <input type="text" id="customer_id" placeholder="e.g., C001" required>
                    <div class="hint">Enter the customer's account identifier</div>
                </div>
                <div class="field">
                    <label>Change Type</label>
                    <select id="change_type" required>
                        <option value="">Select a change type</option>
                        <option value="legal_name">Legal Name Change</option>
                        <option value="address">Address Change</option>
                        <option value="date_of_birth">Date of Birth Correction</option>
                        <option value="contact_email">Contact / Email Update</option>
                    </select>
                </div>
                <div class="field">
                    <label>Document Type</label>
                    <select id="document_type">
                        <option value="">Select change type first</option>
                    </select>
                    <div class="hint" id="doc-hint">Only document types valid for the selected change type are shown</div>
                </div>
                <div class="field-row">
                    <div class="field">
                        <label>Current Value</label>
                        <input type="text" id="old_value" placeholder="Enter current value" required>
                    </div>
                    <div class="field">
                        <label>New Value</label>
                        <input type="text" id="new_value" placeholder="Enter new value" required>
                    </div>
                </div>
                <div class="field">
                    <label>Supporting Document</label>
                    <div class="dropzone" id="dropzone">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block;margin:0 auto 8px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        <div><strong>Click to upload</strong> or drag and drop</div>
                        <div style="font-size:12px;margin-top:6px;">PDF, JPG or PNG (max 10 MB)</div>
                        <input type="file" id="document" accept=".pdf,.jpg,.jpeg,.png" hidden required>
                    </div>
                    <div id="file-pill-host"></div>
                </div>
                <input type="hidden" id="staff_id_hidden" value="${getUsername()}">
                <button type="submit" class="btn btn-primary btn-block" id="submit-btn" style="margin-top:8px;">Submit Request <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></button>
            </form>
        </div>
    `;
    setupNewRequestForm();
}

function setupNewRequestForm() {
    const docMap = {
        legal_name: ['Marriage Certificate', 'Gazette Notification', 'Court Order'],
        address: ['Utility Bill', 'Rental Agreement', 'Bank Statement'],
        date_of_birth: ['Birth Certificate', 'Passport', 'Aadhaar'],
        contact_email: ['Signed Request Form'],
    };
    const ctSel = document.getElementById('change_type');
    const dtSel = document.getElementById('document_type');
    ctSel.addEventListener('change', () => {
        const opts = docMap[ctSel.value] || [];
        dtSel.innerHTML = opts.length
            ? opts.map(o => `<option value="${o}">${o}</option>`).join('')
            : '<option value="">Select change type first</option>';
    });

    const zone = document.getElementById('dropzone');
    const input = document.getElementById('document');
    const pillHost = document.getElementById('file-pill-host');
    zone.addEventListener('click', () => input.click());
    ['dragover', 'dragenter'].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add('dragover'); }));
    ['dragleave', 'drop'].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.remove('dragover'); }));
    zone.addEventListener('drop', e => {
        if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; showFilePill(); }
    });
    input.addEventListener('change', showFilePill);
    function showFilePill() {
        if (!input.files.length) { pillHost.innerHTML = ''; return; }
        const f = input.files[0];
        pillHost.innerHTML = `
            <div class="file-pill">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <div class="meta"><div class="fname">${escapeHtml(f.name)}</div><div class="fsize">${(f.size/1024).toFixed(1)} KB</div></div>
                <button type="button" class="remove icon-btn" onclick="clearFile()" title="Remove">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>`;
    }
    window.clearFile = () => { input.value = ''; pillHost.innerHTML = ''; };

    document.getElementById('submit-form').addEventListener('submit', submitNewRequest);

    if (getRole() === 'account_holder') {
        const cid = localStorage.getItem('customer_id');
        if (cid) document.getElementById('customer_id').value = cid;
    }
}

async function submitNewRequest(e) {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    const alertHost = document.getElementById('submit-alert');
    alertHost.innerHTML = '';
    btn.disabled = true; btn.textContent = 'Processing...';
    try {
        const fd = new FormData();
        fd.append('customer_id', document.getElementById('customer_id').value);
        fd.append('change_type', document.getElementById('change_type').value);
        fd.append('old_value', document.getElementById('old_value').value);
        fd.append('new_value', document.getElementById('new_value').value);
        fd.append('staff_id', document.getElementById('staff_id_hidden').value);
        fd.append('notes', '');
        fd.append('document', document.getElementById('document').files[0]);
        const r = await fetch(`${API_BASE_URL}/change-request/submit`, { method: 'POST', headers: { ...authHeaders() }, body: fd });
        const d = await r.json();
        if (r.ok) {
            toast('success', 'Request submitted', `Confidence ${d.confidence_score?.toFixed(0) || 0}% · AI recommends ${(d.recommendation || 'review').toUpperCase()}`);
            navigate('request-detail', { request_id: d.request_id });
        } else if (r.status === 401) {
            logout();
        } else {
            alertHost.innerHTML = `<div class="alert alert-error">${d.detail?.error || d.detail || 'Submission failed'}</div>`;
            btn.disabled = false; btn.textContent = 'Submit Request';
        }
    } catch (err) {
        alertHost.innerHTML = `<div class="alert alert-error">${err.message}</div>`;
        btn.disabled = false; btn.textContent = 'Submit Request';
    }
}

// ================== ALL REQUESTS ==================
async function renderAllRequests(host) {
    const role = getRole();
    host.innerHTML = `
        ${breadcrumb([cap(role.replace('_', ' ')), 'Requests'])}
        <div class="page-head">
            <div>
                <h1 class="page-title">${role === 'account_holder' ? 'My Requests' : 'All Requests'}</h1>
                <div class="page-sub">Manage and track all submitted requests</div>
            </div>
            <div class="page-head-actions">
                <button class="btn btn-primary" onclick="navigate('new-request')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    New Request
                </button>
            </div>
        </div>
        <div class="filters-bar">
            <div class="chip"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>Filters</div>
            <div class="filter-search">
                <svg class="input-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input id="req-search" type="text" placeholder="Search by Customer ID">
            </div>
            <select class="chip-select" id="req-type-filter" style="padding:6px 10px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--panel);">
                <option value="">All Change Types</option>
                <option value="legal_name">Legal Name Change</option>
                <option value="address">Address Change</option>
                <option value="date_of_birth">Date of Birth</option>
                <option value="contact_email">Contact / Email</option>
            </select>
            <select class="chip-select" id="req-status-filter" style="padding:6px 10px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--panel);">
                <option value="">All Statuses</option>
                <option value="ai_verified_pending_human">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
            </select>
        </div>
        <div id="requests-table" class="table-wrap">
            <div class="loading-center"><div class="spinner"></div>Loading requests...</div>
        </div>
    `;
    document.getElementById('req-search').addEventListener('input', renderRequestsTable);
    document.getElementById('req-type-filter').addEventListener('change', renderRequestsTable);
    document.getElementById('req-status-filter').addEventListener('change', renderRequestsTable);
    await loadAllRequests();
    renderRequestsTable();
}

async function loadAllRequests() {
    try {
        const r = await fetch(`${API_BASE_URL}/my-requests`, { headers: authHeaders() });
        if (r.ok) {
            const d = await r.json();
            state.allRequests = (d.requests || []).map(x => ({ ...x, status: x.status || 'ai_verified_pending_human' }));
        } else {
            state.allRequests = [];
        }
    } catch { state.allRequests = []; }
}

function renderRequestsTable() {
    const host = document.getElementById('requests-table');
    const q = document.getElementById('req-search')?.value?.toLowerCase() || '';
    const ct = document.getElementById('req-type-filter')?.value || '';
    const st = document.getElementById('req-status-filter')?.value || '';
    const rows = state.allRequests.filter(r =>
        (!q || (r.customer_id || '').toLowerCase().includes(q)) &&
        (!ct || r.change_type === ct) &&
        (!st || r.status === st)
    );
    if (!rows.length) {
        host.innerHTML = `
            <div class="empty">
                <div class="empty-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>
                <div style="font-weight:600;color:var(--text);">No requests yet</div>
                <div>Submit a new request to get started</div>
            </div>`;
        return;
    }
    host.innerHTML = `
        <table class="data">
            <thead>
                <tr>
                    <th>Request ID</th>
                    <th>Customer</th>
                    <th>Change Type</th>
                    <th>Status</th>
                    <th>Risk Tier</th>
                    <th>Confidence</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                ${rows.map(r => rowHtml(r)).join('')}
            </tbody>
        </table>`;
}

function rowHtml(r) {
    const conf = Number(r.confidence_score || 0);
    const risk = conf >= 85 ? 'low' : conf >= 65 ? 'med' : 'high';
    const riskLabel = risk === 'low' ? 'LOW' : risk === 'med' ? 'MED' : 'HIGH';
    const status = (r.status || 'ai_verified_pending_human').toLowerCase();
    return `
        <tr>
            <td><a class="link" onclick="navigate('request-detail', {request_id:'${r.request_id}'})">${r.request_id.slice(0, 12)}...</a></td>
            <td>${escapeHtml(r.customer_id)}</td>
            <td>${formatChangeType(r.change_type)}</td>
            <td><span class="status status-${status}">${status === 'ai_verified_pending_human' ? 'Pending' : status}</span></td>
            <td><span class="risk-chip risk-${risk}">${riskLabel}</span></td>
            <td>${conf ? conf.toFixed(0) + '%' : '–'}</td>
            <td>${fmtDate(r.created_at)}</td>
        </tr>`;
}

// ================== REQUEST DETAIL (staff/account holder progress view) ==================
async function renderRequestDetail(host, arg) {
    const id = arg?.request_id;
    host.innerHTML = `
        ${breadcrumb([cap(getRole().replace('_', ' ')), 'Requests', 'Request Details'])}
        <div class="page-head">
            <div style="display:flex;align-items:center;gap:14px;">
                <button class="icon-btn" onclick="navigate('all-requests')" title="Back"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg></button>
                <div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <h1 class="page-title" style="font-family:'SF Mono',Menlo,monospace;">${id ? id.slice(0, 16) + '...' : 'Request'}</h1>
                        <span class="status" id="detail-status">Processing</span>
                    </div>
                    <div class="page-sub" id="detail-created">Created now</div>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Request Progress
            </div>
            <div class="timeline" id="timeline"></div>
        </div>
    `;
    pollRequestStatus(id);
}

function pollRequestStatus(id) {
    const poll = async () => {
        try {
            const r = await fetch(`${API_BASE_URL}/my-requests/${encodeURIComponent(id)}`, { headers: authHeaders() });
            if (r.ok) {
                const d = await r.json();
                renderTimeline(d.request);
            } else {
                renderTimeline(null);
            }
        } catch { renderTimeline(null); }
    };
    poll();
    state.pendingPoll = setInterval(poll, 2500);
}
function stopPendingPoll() { if (state.pendingPoll) { clearInterval(state.pendingPoll); state.pendingPoll = null; } }

function renderTimeline(req) {
    const host = document.getElementById('timeline');
    if (!host) return;
    const has = !!req;
    const statusChip = document.getElementById('detail-status');
    const created = document.getElementById('detail-created');
    const steps = [
        { id: 'intake', title: 'Intake Received', desc: 'Request created and validated' },
        { id: 'upload', title: 'Document Uploaded', desc: 'Supporting document uploaded and validated' },
        { id: 'queued', title: 'Queued', desc: 'Waiting for worker to pick up the task' },
        { id: 'ai', title: 'AI Processing', desc: 'Document being analyzed by AI pipeline',
          sub: ['Document Validation', 'OCR Extraction', 'Classification', 'Field Extraction', 'Forgery Detection', 'Confidence Scoring', 'Summary Generation'] },
        { id: 'verified', title: 'AI Verified', desc: 'AI analysis complete, pending human review' },
        { id: 'review', title: 'In Review', desc: 'Human checker reviewing the request' },
        { id: 'done', title: 'Completed', desc: 'Request finalized and RPS updated' },
    ];
    // Determine current stage from req status
    let current = 'ai';
    if (has) {
        const s = (req.status || '').toLowerCase();
        if (s === 'approved' || s === 'rejected') current = 'done';
        else if (s === 'ai_verified_pending_human') current = 'verified';
        else current = 'ai';
        statusChip.textContent = s === 'approved' ? 'APPROVED' : s === 'rejected' ? 'REJECTED' : s === 'ai_verified_pending_human' ? 'AI VERIFIED PENDING HUMAN' : 'PROCESSING';
        statusChip.className = 'status status-' + s;
        created.textContent = 'Created ' + fmtDate(req.created_at);
    } else {
        statusChip.textContent = 'PROCESSING';
        statusChip.className = 'status status-processing';
    }
    const order = steps.map(s => s.id);
    const curIdx = order.indexOf(current);
    host.innerHTML = steps.map((s, i) => {
        const cls = i < curIdx ? 'done' : i === curIdx ? 'active' : 'pending';
        const check = cls === 'done' ? `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>` : '';
        let sub = '';
        if (s.sub && cls !== 'pending') {
            const subDone = cls === 'done';
            sub = `<div class="timeline-sub">${s.sub.map(x => `<div class="sub-item ${subDone ? 'done' : ''}"><span class="sub-check">${subDone ? `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>` : ''}</span>${x}</div>`).join('')}</div>`;
        }
        const inProg = i === curIdx ? `<span class="pill">In Progress</span>` : '';
        return `
            <div class="timeline-item ${cls}">
                <div class="timeline-dot">${check}</div>
                <div style="flex:1;">
                    <div class="timeline-title">${s.title} ${inProg}</div>
                    <div class="timeline-desc">${s.desc}</div>
                    ${sub}
                </div>
            </div>`;
    }).join('');
}

// ================== CHECKER: REVIEW QUEUE ==================
async function renderReviewQueue(host) {
    host.innerHTML = `
        ${breadcrumb(['Checker', 'Review Queue'])}
        <div class="page-head">
            <div>
                <h1 class="page-title">Review Queue</h1>
                <div class="page-sub" id="queue-count">Loading…</div>
            </div>
            <div class="page-head-actions">
                <button class="btn btn-secondary" onclick="renderReviewQueue(document.getElementById('main'))">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                    Refresh
                </button>
            </div>
        </div>
        <div class="filters-bar">
            <div class="chip"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>Filters</div>
            <button class="chip" data-filter="risk-high"><span class="chip-dot" style="background:var(--danger);"></span>HIGH Risk</button>
            <button class="chip" data-filter="risk-med"><span class="chip-dot" style="background:var(--warning);"></span>MEDIUM Risk</button>
            <button class="chip" data-filter="risk-low"><span class="chip-dot" style="background:var(--success);"></span>LOW Risk</button>
            <div style="width:1px;height:24px;background:var(--border);"></div>
            <button class="chip" data-filter="ai-approve"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>AI: APPROVE</button>
            <button class="chip" data-filter="ai-manual"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/></svg>AI: MANUAL REVIEW</button>
            <button class="chip" data-filter="ai-reject"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>AI: REJECT</button>
        </div>
        <div class="table-wrap" id="queue-table">
            <div class="loading-center"><div class="spinner"></div>Loading queue...</div>
        </div>
    `;
    try {
        const r = await fetch(`${API_BASE_URL}/checker/pending-requests`, { headers: authHeaders() });
        if (r.status === 401) return logout();
        const d = await r.json();
        state.pending = d.pending_requests || [];
    } catch { state.pending = []; }
    document.getElementById('queue-count').textContent = `${state.pending.length} item${state.pending.length === 1 ? '' : 's'} waiting for review`;
    renderQueueTable();
}

function renderQueueTable() {
    const host = document.getElementById('queue-table');
    if (!state.pending.length) {
        host.innerHTML = `
            <table class="data">
                <thead><tr><th>Request</th><th>Change Type</th><th>Risk Tier</th><th>AI Recommendation</th><th>Score</th><th>Flags</th><th>Wait Time</th><th>Action</th></tr></thead>
                <tbody></tbody>
            </table>
            <div class="empty">
                <div class="empty-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>
                <div style="font-weight:600;color:var(--text);">Queue is empty</div>
                <div>All items have been reviewed</div>
            </div>`;
        return;
    }
    host.innerHTML = `
        <table class="data">
            <thead><tr>
                <th>Request</th><th>Change Type</th><th>Risk Tier</th><th>AI Recommendation</th>
                <th>Score</th><th>Flags</th><th>Wait Time</th><th>Action</th>
            </tr></thead>
            <tbody>
                ${state.pending.map(p => {
                    const conf = Number(p.confidence_score || 0);
                    const risk = conf >= 85 ? 'low' : conf >= 65 ? 'med' : 'high';
                    const riskLabel = risk === 'low' ? 'LOW' : risk === 'med' ? 'MED' : 'HIGH';
                    const rec = (p.ai_recommendation || 'review').toUpperCase();
                    const flags = p.forgery_check_passed ? '–' : '<span class="risk-chip risk-high">Forgery</span>';
                    return `
                        <tr>
                            <td><a class="link" onclick="navigate('review-detail', {request_id:'${p.request_id}'})">${p.request_id.slice(0, 12)}...</a><div style="font-size:12px;color:var(--muted);">${escapeHtml(p.customer_id)}</div></td>
                            <td>${formatChangeType(p.change_type)}</td>
                            <td><span class="risk-chip risk-${risk}">${riskLabel}</span></td>
                            <td><span class="status status-${rec === 'APPROVE' ? 'approved' : rec === 'REJECT' ? 'rejected' : 'pending'}">${rec}</span></td>
                            <td><strong>${conf.toFixed(0)}%</strong></td>
                            <td>${flags}</td>
                            <td>${timeAgo(p.created_at)}</td>
                            <td><button class="btn btn-secondary" onclick="navigate('review-detail', {request_id:'${p.request_id}'})">Review</button></td>
                        </tr>`;
                }).join('')}
            </tbody>
        </table>`;
}

// ================== CHECKER: REVIEW DETAIL ==================
async function renderReviewDetail(host, arg) {
    const id = arg?.request_id;
    host.innerHTML = `
        ${breadcrumb(['Checker', 'Review Details'])}
        <div class="page-head">
            <div style="display:flex;align-items:flex-start;gap:14px;">
                <button class="icon-btn" onclick="navigate('review-queue')" title="Back"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg></button>
                <div>
                    <h1 class="page-title">Review Request</h1>
                    <div class="page-sub" style="font-family:'SF Mono',Menlo,monospace;">ID: ${id || ''}</div>
                </div>
            </div>
            <div class="page-head-actions"><button class="btn btn-ghost" onclick="navigate('review-queue')">Release to Queue</button></div>
        </div>
        <div id="review-host"><div class="loading-center"><div class="spinner"></div>Loading request...</div></div>
    `;
    try {
        const r = await fetch(`${API_BASE_URL}/my-requests/${encodeURIComponent(id)}`, { headers: authHeaders() });
        if (r.status === 401) return logout();
        if (!r.ok) { document.getElementById('review-host').innerHTML = `<div class="card">Request not found.</div>`; return; }
        const d = await r.json();
        const req = d.request;
        state.currentRequest = req;
        renderReviewDetailContent(req);
    } catch (err) {
        document.getElementById('review-host').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
}

function renderReviewDetailContent(req) {
    const conf = Number(req.confidence_score || 0);
    const risk = conf >= 85 ? 'low' : conf >= 65 ? 'med' : 'high';
    const riskLabel = risk === 'low' ? 'LOW' : risk === 'med' ? 'MED' : 'HIGH';
    const ocr = Math.round((req.field_scores || []).find(f => (f.field_name || '').toLowerCase().includes('ocr'))?.confidence_score || Math.max(50, conf - 6));
    const extraction = Math.round((req.field_scores || []).filter(f => !(f.field_name || '').toLowerCase().includes('ocr')).reduce((a, b) => a + (b.confidence_score || 0), 0) / Math.max(1, (req.field_scores || []).filter(f => !(f.field_name || '').toLowerCase().includes('ocr')).length) || conf);
    const auth = req.forgery_check_passed ? Math.min(99, conf + 1) : 40;
    const rec = (req.ai_recommendation || 'review').toUpperCase();
    const scoreClass = v => v >= 85 ? 'high' : v >= 65 ? 'med' : 'low';

    document.getElementById('review-host').innerHTML = `
        <div class="grid-2">
            <div>
                <div class="card">
                    <div class="card-title"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>Request Details</div>
                    <div class="kv-grid" style="margin-top:14px;">
                        <div><div class="kv-label">Customer ID</div><div class="kv-value">${escapeHtml(req.customer_id)}</div></div>
                        <div><div class="kv-label">Change Type</div><div class="kv-value">${formatChangeType(req.change_type)}</div></div>
                        <div><div class="kv-label">Document Type</div><div class="kv-value">${escapeHtml(req.document_type || 'Marriage Certificate')}</div></div>
                        <div><div class="kv-label">Created</div><div class="kv-value">${fmtDate(req.created_at)}</div></div>
                    </div>
                    <div class="kv-grid" style="margin-top:18px;">
                        <div class="value-box"><div class="kv-label">Requested Old Value</div><div class="kv-value">${escapeHtml(req.old_value || '–')}</div></div>
                        <div class="value-box new"><div class="kv-label">Requested New Value</div><div class="kv-value">${escapeHtml(req.new_value || '–')}</div></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>Document Preview</div>
                    <div class="doc-preview"><div class="placeholder">Document archived to FileNet<br/><span style="font-size:12px;">Ref: ${escapeHtml(req.filenet_reference || 'n/a')}</span></div></div>
                </div>
                <div class="card">
                    <div class="card-title">AI Summary</div>
                    <p class="muted" style="line-height:1.55;">${escapeHtml(req.ai_summary || 'No summary available.')}</p>
                </div>
            </div>
            <div>
                <div class="card">
                    <div class="card-title"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>Confidence Scores</div>
                    <div style="margin-top:10px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="kv-label">Overall Score</div>
                            <div class="score-val ${scoreClass(conf)}">${conf.toFixed(0)}%</div>
                        </div>
                        <div class="progress"><div class="progress-fill" style="width:${conf}%;background:${conf>=85?'var(--success)':conf>=65?'var(--warning)':'var(--danger)'};"></div></div>
                    </div>
                    <div style="margin-top:14px;">
                        <div class="score-row"><span class="score-label">OCR Confidence</span><span class="score-val ${scoreClass(ocr)}">${ocr}%</span></div>
                        <div class="score-row"><span class="score-label">Extraction</span><span class="score-val ${scoreClass(extraction)}">${extraction}%</span></div>
                        <div class="score-row"><span class="score-label">Authenticity</span><span class="score-val ${scoreClass(auth)}">${auth}%</span></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">AI Assessment</div>
                    <div class="score-row"><span class="score-label">Risk Tier</span><span class="risk-chip risk-${risk}">${riskLabel}</span></div>
                    <div class="score-row"><span class="score-label">Recommendation</span><span class="status status-${rec === 'APPROVE' ? 'approved' : rec === 'REJECT' ? 'rejected' : 'pending'}">${rec}</span></div>
                </div>
                <div class="card">
                    <div class="card-title">Your Decision</div>
                    ${['approved', 'rejected'].includes((req.status || '').toLowerCase()) ? `
                        <div class="alert alert-info" style="margin-top:8px;">
                            This request was already <strong>${escapeHtml((req.status || '').toUpperCase())}</strong>${req.checker_id ? ` by ${escapeHtml(req.checker_id)}` : ''}${req.processed_at ? ` on ${fmtDate(req.processed_at)}` : ''}.
                        </div>
                    ` : `
                        <div class="decision-grid">
                            <button class="decision-btn" data-decision="approve"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>Approve</button>
                            <button class="decision-btn" data-decision="reject"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Reject</button>
                            <button class="decision-btn" data-decision="more"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>More Info</button>
                            <button class="decision-btn" data-decision="escalate"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>Escalate</button>
                        </div>
                        <button class="btn btn-success btn-block" id="submit-decision" style="margin-top:14px;" disabled>Submit Decision</button>
                    `}
                </div>
            </div>
        </div>
    `;
    document.querySelectorAll('.decision-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.decision-btn').forEach(x => x.classList.remove('selected', 'approve', 'reject', 'more', 'escalate'));
            btn.classList.add('selected', btn.dataset.decision);
            state.decision = btn.dataset.decision;
            const sub = document.getElementById('submit-decision');
            sub.disabled = false;
            sub.className = 'btn btn-block ' + (state.decision === 'approve' ? 'btn-success' : state.decision === 'reject' ? 'btn-danger' : 'btn-primary');
        });
    });
    const submitBtn = document.getElementById('submit-decision');
    if (submitBtn) submitBtn.addEventListener('click', submitDecision);
}

async function submitDecision() {
    if (!state.decision || !state.currentRequest) return;
    if (state.decision === 'more' || state.decision === 'escalate') {
        toast('success', 'Action recorded', state.decision === 'more' ? 'Requested additional information.' : 'Request escalated to supervisor.');
        return;
    }
    const decision = state.decision;
    openModal({
        title: decision === 'approve' ? 'Approve Request' : 'Reject Request',
        msg: decision === 'approve'
            ? 'You are about to APPROVE this request and execute the RPS update.'
            : 'You are about to REJECT this request. No changes will be made to RPS.',
        onConfirm: async () => {
            closeModal();
            try {
                const r = await fetch(`${API_BASE_URL}/checker/decision`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...authHeaders() },
                    body: JSON.stringify({
                        request_id: state.currentRequest.request_id,
                        checker_id: getUsername(),
                        decision, notes: null,
                    }),
                });
                const d = await r.json();
                if (r.ok) {
                    toast('success', 'Decision submitted', decision === 'approve' ? 'Request has been approved.' : 'Request has been rejected.');
                    navigate('review-queue');
                } else if (r.status === 401) { logout(); }
                else { toast('error', 'Decision failed', d.detail || 'Please try again.'); }
            } catch (err) {
                toast('error', 'Connection error', err.message);
            }
        },
    });
}

// ================== MY REVIEWS ==================
async function renderMyReviews(host) {
    host.innerHTML = `
        ${breadcrumb(['Checker', 'My Reviews'])}
        <div class="page-head">
            <div><h1 class="page-title">My Reviews</h1><div class="page-sub" id="reviews-count">Loading…</div></div>
            <div class="page-head-actions">
                <button class="btn btn-secondary" onclick="navigate('my-reviews')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                    Refresh
                </button>
            </div>
        </div>
        <div class="filters-bar">
            <div class="chip"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>Filters</div>
            <div class="filter-search">
                <svg class="input-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input id="rev-search" type="text" placeholder="Search by Request or Customer ID">
            </div>
            <select id="rev-status-filter" style="padding:6px 10px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--panel);">
                <option value="">All Decisions</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
            </select>
            <select id="rev-mine-filter" style="padding:6px 10px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--panel);">
                <option value="mine">Mine</option>
                <option value="all">All checkers</option>
            </select>
        </div>
        <div class="table-wrap" id="reviews-table"><div class="loading-center"><div class="spinner"></div>Loading reviews…</div></div>
    `;
    try {
        const r = await fetch(`${API_BASE_URL}/my-requests`, { headers: authHeaders() });
        if (r.status === 401) return logout();
        const d = await r.json();
        state.myReviews = (d.requests || []).filter(x => ['approved', 'rejected'].includes((x.status || '').toLowerCase()));
    } catch { state.myReviews = []; }
    ['rev-search', 'rev-status-filter', 'rev-mine-filter'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', renderReviewsTable);
        if (el) el.addEventListener('change', renderReviewsTable);
    });
    renderReviewsTable();
}

function renderReviewsTable() {
    const host = document.getElementById('reviews-table');
    const countEl = document.getElementById('reviews-count');
    const q = (document.getElementById('rev-search')?.value || '').toLowerCase();
    const st = document.getElementById('rev-status-filter')?.value || '';
    const mineFilter = document.getElementById('rev-mine-filter')?.value || 'mine';
    const me = getUsername();
    let rows = state.myReviews;
    if (mineFilter === 'mine') rows = rows.filter(r => r.checker_id === me);
    if (st) rows = rows.filter(r => (r.status || '').toLowerCase() === st);
    if (q) rows = rows.filter(r => r.request_id.toLowerCase().includes(q) || (r.customer_id || '').toLowerCase().includes(q));
    if (countEl) countEl.textContent = `${rows.length} review${rows.length === 1 ? '' : 's'}`;
    if (!rows.length) {
        host.innerHTML = `
            <div class="empty">
                <div class="empty-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
                <div style="font-weight:600;color:var(--text);">No reviews yet</div>
                <div>Decisions you submit will appear here.</div>
            </div>`;
        return;
    }
    host.innerHTML = `
        <table class="data">
            <thead><tr>
                <th>Request</th><th>Customer</th><th>Change Type</th><th>Decision</th>
                <th>Score</th><th>Checker</th><th>Decided</th>
            </tr></thead>
            <tbody>
                ${rows.map(r => {
                    const conf = Number(r.confidence_score || 0);
                    const status = (r.status || '').toLowerCase();
                    return `
                        <tr>
                            <td><a class="link" onclick="navigate('review-detail', {request_id:'${r.request_id}'})">${r.request_id.slice(0, 12)}...</a></td>
                            <td>${escapeHtml(r.customer_id)}</td>
                            <td>${formatChangeType(r.change_type)}</td>
                            <td><span class="status status-${status}">${status.toUpperCase()}</span></td>
                            <td><strong>${conf.toFixed(0)}%</strong></td>
                            <td>${escapeHtml(r.checker_id || '–')}</td>
                            <td>${fmtDate(r.processed_at || r.created_at)}</td>
                        </tr>`;
                }).join('')}
            </tbody>
        </table>`;
}

// ================== USERS (checker) ==================
async function renderUsers(host) {
    host.innerHTML = `
        ${breadcrumb(['Checker', 'Users'])}
        <div class="page-head"><div><h1 class="page-title">Users</h1><div class="page-sub">All users in the system</div></div></div>
        <div id="users-table" class="table-wrap"><div class="loading-center"><div class="spinner"></div>Loading users...</div></div>
    `;
    try {
        const r = await fetch(`${API_BASE_URL}/users`, { headers: authHeaders() });
        if (r.status === 401) return logout();
        const d = await r.json();
        document.getElementById('users-table').innerHTML = `
            <table class="data">
                <thead><tr><th>User ID</th><th>Username</th><th>Full Name</th><th>Role</th><th>Email</th><th>Customer ID</th><th>Status</th></tr></thead>
                <tbody>${(d.users || []).map(u => `
                    <tr>
                        <td>${escapeHtml(u.user_id)}</td>
                        <td><strong>${escapeHtml(u.username)}</strong></td>
                        <td>${escapeHtml(u.full_name || '–')}</td>
                        <td><span class="status ${u.role === 'checker' ? 'status-processing' : 'status-approved'}">${escapeHtml(u.role)}</span></td>
                        <td>${escapeHtml(u.email || '–')}</td>
                        <td>${escapeHtml(u.customer_id || '–')}</td>
                        <td>${u.active ? 'Active' : 'Inactive'}</td>
                    </tr>`).join('')}</tbody>
            </table>`;
    } catch (err) {
        document.getElementById('users-table').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
}

// ================== ACCOUNT (account holder) ==================
async function renderAccount(host) {
    host.innerHTML = `
        ${breadcrumb(['Account', 'My Account'])}
        <div class="page-head"><div><h1 class="page-title">My Account</h1><div class="page-sub">Your current customer record in core banking</div></div>
            <div class="page-head-actions"><button class="btn btn-primary" onclick="navigate('new-request')">Request a Change</button></div>
        </div>
        <div id="acc-host" class="card"><div class="loading-center"><div class="spinner"></div>Loading...</div></div>
    `;
    try {
        const r = await fetch(`${API_BASE_URL}/account/details`, { headers: authHeaders() });
        if (r.status === 401) return logout();
        const d = await r.json();
        document.getElementById('acc-host').innerHTML = `
            <div class="card-title">Customer Record</div>
            <div class="kv-list" style="margin-top:8px;">
                <div class="row"><span class="k">Customer ID</span><span class="v">${escapeHtml(d.customer_id)}</span></div>
                <div class="row"><span class="k">Name</span><span class="v">${escapeHtml(d.name)}</span></div>
                <div class="row"><span class="k">Email</span><span class="v">${escapeHtml(d.email)}</span></div>
                <div class="row"><span class="k">Address</span><span class="v">${escapeHtml(d.address)}</span></div>
                <div class="row"><span class="k">Date of Birth</span><span class="v">${escapeHtml(d.dob)}</span></div>
                <div class="row"><span class="k">Phone</span><span class="v">${escapeHtml(d.phone || '–')}</span></div>
                <div class="row"><span class="k">Account Number</span><span class="v">${escapeHtml(d.account_number || '–')}</span></div>
                <div class="row"><span class="k">Account Type</span><span class="v">${escapeHtml(d.account_type || '–')}</span></div>
                ${d.balance != null ? `<div class="row"><span class="k">Balance</span><span class="v" style="color:var(--success);font-weight:700;">₹${d.balance.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span></div>` : ''}
            </div>
        `;
    } catch (err) {
        document.getElementById('acc-host').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
}

// ================== Helpers ==================
function breadcrumb(parts) {
    return `<div class="breadcrumb">${parts.map((p, i) => `${i ? '<span class="chev">›</span>' : ''}<span class="${i === parts.length - 1 ? 'current' : ''}">${escapeHtml(p)}</span>`).join('')}</div>`;
}
function cap(s) { return (s || '').split(' ').map(w => w[0]?.toUpperCase() + w.slice(1)).join(' '); }
function escapeHtml(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function formatChangeType(t) { return ({ legal_name: 'Legal Name Change', address: 'Address Change', date_of_birth: 'Date of Birth Correction', contact_email: 'Contact / Email Update' })[t] || (t || '').replace(/_/g, ' '); }
function fmtDate(d) { if (!d) return '–'; try { return new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }); } catch { return d; } }
function timeAgo(d) {
    if (!d) return '–';
    const delta = Math.max(0, (Date.now() - new Date(d).getTime()) / 1000);
    if (delta < 60) return `${Math.round(delta)}s`;
    if (delta < 3600) return `${Math.round(delta / 60)}m`;
    if (delta < 86400) return `${Math.round(delta / 3600)}h`;
    return `${Math.round(delta / 86400)}d`;
}
function toast(kind, title, msg) {
    const host = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = 'toast ' + kind;
    el.innerHTML = `
        <div class="toast-icon">${kind === 'success'
            ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
            : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`}</div>
        <div style="flex:1;"><div class="toast-title">${escapeHtml(title)}</div><div class="toast-msg">${escapeHtml(msg || '')}</div></div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    host.appendChild(el);
    setTimeout(() => el.remove(), 4500);
}

function openModal({ title, msg, onConfirm }) {
    const m = document.getElementById('modal');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-msg').textContent = msg;
    const btn = document.getElementById('modal-confirm');
    const fresh = btn.cloneNode(true); btn.parentNode.replaceChild(fresh, btn);
    fresh.addEventListener('click', onConfirm);
    m.classList.add('open');
}
function closeModal() { document.getElementById('modal').classList.remove('open'); }

// Icons
function iconHome() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`; }
function iconPlus() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`; }
function iconList() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`; }
function iconUser() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`; }
function iconUsers() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`; }
function iconClipboard() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2h6a2 2 0 0 1 2 2v2H7V4a2 2 0 0 1 2-2z"/><path d="M5 4h2v4h10V4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg>`; }
function iconHistory() { return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`; }
