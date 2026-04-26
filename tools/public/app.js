/* Report Template Designer - front-end logic.
 *
 * State model
 * -----------
 * `design` is the single source of truth.
 *
 *     design = {
 *         name, title,
 *         data:   {main, details},
 *         page:   {size, width?, margin, orientation},
 *         theme:  {preset, font, fontSize, color, accent,
 *                  borderColor, borderStyle, uppercase},
 *         blocks: [{id, type, config}, ...]
 *     }
 *
 * The UI just maps the design into form widgets and calls
 * /api/design/render whenever the design changes.
 */

(() => {

  // -------------------------------------------------------------- helpers

  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const uid = (prefix = 'b') =>
    prefix + Math.random().toString(36).slice(2, 9);

  const debounce = (fn, ms = 200) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  const setStatus = (msg, kind = '') => {
    const el = $('#status');
    el.textContent = msg || '';
    el.className = 'status' + (kind ? ' ' + kind : '');
    if (msg && kind === 'success') {
      setTimeout(() => {
        if (el.textContent === msg) {
          el.textContent = '';
          el.className = 'status';
        }
      }, 2400);
    }
  };

  const api = {
    get: async (path) => {
      const r = await fetch(path);
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || r.statusText);
      return j;
    },
    post: async (path, body) => {
      const r = await fetch(path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
      });
      const j = await r.json();
      if (!r.ok) {
        const err = new Error(j.error || r.statusText);
        err.status = r.status;
        err.payload = j;
        throw err;
      }
      return j;
    },
  };

  // -------------------------------------------------------------- state

  const state = {
    schema:   null,           // /api/block-types response
    designs:  null,           // /api/designs response
    design:   null,           // current design (live)
    openPath: null,           // current path on disk if loaded
    expanded: new Set(),      // ids of expanded block items
    zoom:     1.0,
  };

  // -------------------------------------------------------------- bootstrap

  async function boot() {
    const [schema, designs] = await Promise.all([
      api.get('/api/block-types'),
      api.get('/api/designs'),
    ]);
    state.schema = schema;
    state.designs = designs.designs;

    initThemePresets();
    initPalette();
    initEvents();

    loadDesign(deepClone(designs.designs['Sales Invoice (POS receipt)']));
  }

  function deepClone(o) { return JSON.parse(JSON.stringify(o)); }

  // -------------------------------------------------------------- design ops

  function loadDesign(design, openPath = null) {
    state.design = normalize(design);
    state.openPath = openPath;
    state.expanded.clear();
    syncMetaForm();
    syncThemeForm();
    syncPageForm();
    renderBlockList();
    refreshPreview();
    updateDocName();
  }

  function normalize(design) {
    design = design || {};
    design.name   = design.name   || 'newTemplate';
    design.title  = design.title  || '';
    design.data   = design.data   || {main: 'mainData', details: 'detailsData'};
    design.page   = Object.assign({size: 'a4', margin: '20mm', orientation: 'portrait'}, design.page || {});
    design.theme  = Object.assign({preset: 'pos'}, design.theme || {});
    design.blocks = (design.blocks || []).map(b => ({
      id:     b.id || uid(),
      type:   b.type,
      config: deepClone(b.config || {}),
    }));
    return design;
  }

  function updateDocName() {
    const d = state.design;
    const path = state.openPath ? state.openPath : `(unsaved) ${d.name}.html`;
    $('#docName').textContent = path;
    document.title = `${d.name || 'untitled'} - Report Designer`;
  }

  // -------------------------------------------------------------- meta tab

  function syncMetaForm() {
    const d = state.design;
    $('#metaTitle').value      = d.title || '';
    $('#metaName').value       = d.name  || '';
    $('#dataMain').value       = d.data.main || '';
    $('#dataDetails').value    = d.data.details || '';
    $('#dataMainPreview').textContent    = d.data.main || 'mainData';
    $('#dataDetailsPreview').textContent = d.data.details || 'detailsData';
  }

  // -------------------------------------------------------------- theme tab

  function initThemePresets() {
    const sel = $('#themePreset');
    sel.innerHTML = '';
    state.schema.themePresets.forEach(p => {
      const o = document.createElement('option');
      o.value = p; o.textContent = p;
      sel.appendChild(o);
    });
  }

  function syncThemeForm() {
    const t = state.design.theme;
    const defaults = state.schema.themeDefaults[t.preset] || {};
    $('#themePreset').value     = t.preset || 'pos';
    $('#themeFont').value       = t.font      || defaults.font || '';
    $('#themeFontSize').value   = t.fontSize  || defaults.fontSize || '';
    $('#themeColor').value      = normaliseColor(t.color || defaults.color);
    $('#themeAccent').value     = normaliseColor(t.accent || defaults.accent);
    $('#themeBorderColor').value= normaliseColor(t.borderColor || defaults.borderColor);
    $('#themeBorderStyle').value= t.borderStyle || defaults.borderStyle || 'solid';
    $('#themeUppercase').checked= !!(t.uppercase ?? defaults.uppercase);
  }

  function normaliseColor(c) {
    if (!c) return '#000000';
    if (c.startsWith('#') && c.length === 7) return c;
    if (c.startsWith('#') && c.length === 4) {
      return '#' + c.slice(1).split('').map(x => x + x).join('');
    }
    return '#000000';
  }

  function readThemeForm() {
    const t = {};
    t.preset      = $('#themePreset').value;
    t.font        = $('#themeFont').value || undefined;
    t.fontSize    = $('#themeFontSize').value || undefined;
    t.color       = $('#themeColor').value;
    t.accent      = $('#themeAccent').value;
    t.borderColor = $('#themeBorderColor').value;
    t.borderStyle = $('#themeBorderStyle').value;
    t.uppercase   = $('#themeUppercase').checked;
    Object.keys(t).forEach(k => t[k] === undefined && delete t[k]);
    state.design.theme = t;
  }

  // -------------------------------------------------------------- page tab

  function syncPageForm() {
    const p = state.design.page;
    $('#pageSize').value        = p.size || 'a4';
    $('#pageMargin').value      = p.margin || '';
    $('#pageOrientation').value = p.orientation || 'portrait';
    $('#pageWidth').value       = p.width || '';
    $('#pageWidthRow').hidden   = p.size !== 'custom';
  }

  function readPageForm() {
    const p = {};
    p.size        = $('#pageSize').value;
    p.margin      = $('#pageMargin').value || undefined;
    p.orientation = $('#pageOrientation').value;
    if (p.size === 'custom') p.width = $('#pageWidth').value || undefined;
    Object.keys(p).forEach(k => p[k] === undefined && delete p[k]);
    state.design.page = p;
    $('#pageWidthRow').hidden = p.size !== 'custom';
  }

  // -------------------------------------------------------------- palette

  function initPalette() {
    const cats = state.schema.categories;
    const blocks = state.schema.blockTypes;

    // dropdown menu palette
    const menu = $('#paletteList');
    menu.innerHTML = '';
    cats.forEach(cat => {
      const items = blocks.filter(b => b.category === cat.id);
      if (!items.length) return;
      const lbl = document.createElement('div');
      lbl.className = 'palette-cat';
      lbl.textContent = cat.label;
      menu.appendChild(lbl);
      items.forEach(bt => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'palette-item';
        btn.innerHTML =
          `<span class="palette-icon">${escapeHtml(bt.icon || '?')}</span>` +
          `<span>${escapeHtml(bt.label)}</span>`;
        btn.addEventListener('click', () => {
          addBlock(bt.type);
          closeMenus();
        });
        menu.appendChild(btn);
      });
    });

    // full-screen palette dialog (shown if user clicks "+ Add" empty area)
    const grid = $('#paletteFull');
    grid.innerHTML = '';
    blocks.forEach(bt => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'palette-card';
      btn.innerHTML =
        `<span class="palette-icon">${escapeHtml(bt.icon || '?')}</span>` +
        `<div class="palette-card-text">` +
          `<div class="palette-card-title">${escapeHtml(bt.label)}</div>` +
          `<div class="palette-card-desc">${escapeHtml(bt.description || '')}</div>` +
        `</div>`;
      btn.addEventListener('click', () => {
        addBlock(bt.type);
        closeModal('paletteDialog');
      });
      grid.appendChild(btn);
    });
  }

  function addBlock(type, atIndex) {
    const schema = state.schema.blockTypes.find(b => b.type === type);
    if (!schema) return;
    const block = {
      id: uid(),
      type,
      config: deepClone(schema.defaultConfig || {}),
    };
    if (typeof atIndex === 'number') {
      state.design.blocks.splice(atIndex, 0, block);
    } else {
      state.design.blocks.push(block);
    }
    state.expanded.add(block.id);
    renderBlockList();
    refreshPreview();
  }

  // -------------------------------------------------------------- block list

  function renderBlockList() {
    const list = $('#blockList');
    list.innerHTML = '';
    const blocks = state.design.blocks;

    $('#blockListEmpty').hidden = blocks.length > 0;

    blocks.forEach((blk, idx) => {
      const schema = state.schema.blockTypes.find(b => b.type === blk.type);
      const tpl = $('#tplBlockItem').content.cloneNode(true);
      const root = tpl.querySelector('.block-item');
      root.dataset.id = blk.id;
      root.dataset.index = idx;
      const head = tpl.querySelector('.block-head');
      tpl.querySelector('.block-icon').textContent = schema?.icon || '?';
      tpl.querySelector('.block-title').textContent =
        blockSummary(blk, schema);

      head.addEventListener('click', () => toggleBlock(blk.id));
      tpl.querySelector('.del').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteBlock(blk.id);
      });

      // drag-reorder handlers (HTML5 native)
      attachDragHandlers(root);

      const body = tpl.querySelector('.block-body');
      if (state.expanded.has(blk.id)) {
        body.hidden = false;
        root.classList.add('open');
        renderBlockEditor(body, blk, schema);
      }

      // hover preview highlight
      root.addEventListener('mouseenter', () => highlightInPreview(blk.id));
      root.addEventListener('mouseleave', () => highlightInPreview(null));

      list.appendChild(tpl);
    });
  }

  function blockSummary(blk, schema) {
    const cfg = blk.config || {};
    if (blk.type === 'title')          return 'Title - ' + (cfg.text || '');
    if (blk.type === 'text')           return 'Text - ' + ((cfg.content || '').slice(0, 30));
    if (blk.type === 'footer')         return 'Footer - ' + ((cfg.text || '').split('\n')[0].slice(0, 30));
    if (blk.type === 'company-header') return 'Company header (' + (cfg.fields || []).length + ' fields)';
    if (blk.type === 'info-row')       return 'Info row (' + (cfg.items || []).length + ' items)';
    if (blk.type === 'party-block')    return 'Party block (' + (cfg.columns || []).length + ' cols)';
    if (blk.type === 'meta-table')     return 'Meta table (' + (cfg.rows || []).length + ' rows)';
    if (blk.type === 'items-table')    return 'Items table (' + (cfg.columns || []).length + ' cols)';
    if (blk.type === 'totals-table')   return 'Totals (' + (cfg.rows || []).length + ' rows)';
    if (blk.type === 'grand-total')    return 'Grand total - ' + (cfg.label || '');
    if (blk.type === 'divider')        return 'Divider (' + (cfg.style || 'solid') + ')';
    if (blk.type === 'spacer')         return 'Spacer (' + (cfg.height || '') + ')';
    if (blk.type === 'image')          return 'Image - ' + (cfg.field || '');
    if (blk.type === 'html')           return 'Raw HTML';
    return schema?.label || blk.type;
  }

  function toggleBlock(id) {
    if (state.expanded.has(id)) state.expanded.delete(id);
    else state.expanded.add(id);
    renderBlockList();
  }

  function deleteBlock(id) {
    state.design.blocks = state.design.blocks.filter(b => b.id !== id);
    state.expanded.delete(id);
    renderBlockList();
    refreshPreview();
  }

  // -------------------------------------------------------------- per-block editor

  function renderBlockEditor(host, blk, schema) {
    host.innerHTML = '';
    if (!schema) {
      host.textContent = `[unknown block type: ${blk.type}]`;
      return;
    }
    schema.fields.forEach(f => host.appendChild(buildField(f, blk.config, blk)));
  }

  function buildField(f, config, blk) {
    if (f.type === 'list') return buildListField(f, config, blk);

    const wrap = document.createElement('label');
    wrap.className = 'field' + (f.type === 'checkbox' ? ' check' : '');

    let input;
    if (f.type === 'select') {
      input = document.createElement('select');
      (f.options || []).forEach(o => {
        const opt = document.createElement('option');
        opt.value = String(o.value);
        opt.textContent = o.label;
        input.appendChild(opt);
      });
      input.value = String(config[f.k] ?? (f.options?.[0]?.value ?? ''));
    } else if (f.type === 'checkbox') {
      input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = !!config[f.k];
    } else if (f.type === 'textarea') {
      input = document.createElement('textarea');
      input.rows = f.rows || 4;
      input.value = config[f.k] ?? '';
      if (f.placeholder) input.placeholder = f.placeholder;
    } else if (f.type === 'csv') {
      input = document.createElement('input');
      input.type = 'text';
      input.value = (config[f.k] || []).join(', ');
      if (f.placeholder) input.placeholder = f.placeholder;
    } else {
      input = document.createElement('input');
      input.type = 'text';
      input.value = config[f.k] ?? '';
      if (f.placeholder) input.placeholder = f.placeholder;
    }

    input.addEventListener('input',  () => commitField(f, input, config, blk));
    input.addEventListener('change', () => commitField(f, input, config, blk));

    if (f.type === 'checkbox') {
      wrap.appendChild(input);
      const span = document.createElement('span');
      span.textContent = f.label || f.k;
      wrap.appendChild(span);
    } else {
      const span = document.createElement('span');
      span.textContent = f.label || f.k;
      wrap.appendChild(span);
      wrap.appendChild(input);
    }
    return wrap;
  }

  function commitField(f, input, config, blk) {
    let value;
    if (f.type === 'checkbox') {
      value = input.checked;
    } else if (f.type === 'select' && (f.options || []).some(o => typeof o.value === 'number')) {
      value = parseInt(input.value, 10);
    } else if (f.type === 'csv') {
      value = input.value.split(',').map(s => s.trim()).filter(Boolean);
    } else {
      value = input.value;
    }
    config[f.k] = value;

    // Update list-row title preview
    const item = $(`.block-item[data-id="${blk.id}"] .block-title`);
    if (item) {
      const schema = state.schema.blockTypes.find(b => b.type === blk.type);
      item.textContent = blockSummary(blk, schema);
    }
    refreshPreviewDebounced();
  }

  function buildListField(f, config, blk) {
    const wrap = document.createElement('div');
    wrap.className = 'list-field';

    const label = document.createElement('div');
    label.className = 'list-label';
    label.textContent = f.label || f.k;
    wrap.appendChild(label);

    const items = (config[f.k] = config[f.k] || []);
    const itemsHost = document.createElement('div');
    itemsHost.className = 'list-items';
    wrap.appendChild(itemsHost);

    const renderItems = () => {
      itemsHost.innerHTML = '';
      items.forEach((item, idx) => {
        const tpl = $('#tplListItem').content.cloneNode(true);
        const row = tpl.querySelector('.list-item');
        const fieldsHost = tpl.querySelector('.list-item-fields');
        f.fields.forEach(sub => {
          fieldsHost.appendChild(buildField(sub, item, blk));
        });
        tpl.querySelector('.list-del').addEventListener('click', () => {
          items.splice(idx, 1);
          renderItems();
          refreshPreview();
          // refresh title summary
          const titleEl = $(`.block-item[data-id="${blk.id}"] .block-title`);
          if (titleEl) {
            const schema = state.schema.blockTypes.find(b => b.type === blk.type);
            titleEl.textContent = blockSummary(blk, schema);
          }
        });
        itemsHost.appendChild(tpl);
      });
    };
    renderItems();

    const add = document.createElement('button');
    add.type = 'button';
    add.className = 'list-add';
    add.textContent = '+ Add ' + (f.label || 'item').toLowerCase();
    add.addEventListener('click', () => {
      const empty = {};
      f.fields.forEach(sub => {
        if (sub.type === 'csv') empty[sub.k] = [];
        else if (sub.type === 'checkbox') empty[sub.k] = false;
        else empty[sub.k] = '';
      });
      items.push(empty);
      renderItems();
      refreshPreview();
      const titleEl = $(`.block-item[data-id="${blk.id}"] .block-title`);
      if (titleEl) {
        const schema = state.schema.blockTypes.find(b => b.type === blk.type);
        titleEl.textContent = blockSummary(blk, schema);
      }
    });
    wrap.appendChild(add);

    return wrap;
  }

  // -------------------------------------------------------------- drag reorder

  let dragId = null;

  function attachDragHandlers(root) {
    root.addEventListener('dragstart', (e) => {
      dragId = root.dataset.id;
      root.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      try { e.dataTransfer.setData('text/plain', dragId); } catch (_) {}
    });
    root.addEventListener('dragend', () => {
      root.classList.remove('dragging');
      $$('.block-item').forEach(el => el.classList.remove('drag-over'));
      dragId = null;
    });
    root.addEventListener('dragover', (e) => {
      if (!dragId || dragId === root.dataset.id) return;
      e.preventDefault();
      root.classList.add('drag-over');
    });
    root.addEventListener('dragleave', () => {
      root.classList.remove('drag-over');
    });
    root.addEventListener('drop', (e) => {
      e.preventDefault();
      root.classList.remove('drag-over');
      if (!dragId || dragId === root.dataset.id) return;

      const blocks = state.design.blocks;
      const from = blocks.findIndex(b => b.id === dragId);
      const to   = blocks.findIndex(b => b.id === root.dataset.id);
      if (from < 0 || to < 0) return;

      const [moved] = blocks.splice(from, 1);
      blocks.splice(to, 0, moved);
      renderBlockList();
      refreshPreview();
    });
  }

  // -------------------------------------------------------------- preview

  const refreshPreviewDebounced = debounce(refreshPreview, 200);

  async function refreshPreview() {
    const design = deepClone(state.design);
    try {
      const res = await api.post('/api/design/render', {design});
      const frame = $('#frame');
      const doc = frame.contentDocument || frame.contentWindow.document;
      doc.open();
      doc.write(injectHoverScript(res.rendered));
      doc.close();
      $('#rawHtml').value = res.html;
      setStatus('');
    } catch (e) {
      setStatus(e.message, 'error');
    }
  }

  function injectHoverScript(html) {
    const script = `
<style>
  [data-block-id] { position: relative; }
  [data-block-id].rt-hover {
    outline: 2px solid #6366f1;
    outline-offset: 2px;
    background: rgba(99,102,241,0.06);
  }
</style>
<script>
(function() {
  window.addEventListener('message', function(ev) {
    if (!ev.data || ev.data.kind !== 'rt-highlight') return;
    document.querySelectorAll('[data-block-id]').forEach(function(el) {
      el.classList.toggle('rt-hover', el.getAttribute('data-block-id') === ev.data.id);
    });
  });
})();
<\/script>`;
    if (html.includes('</head>')) return html.replace('</head>', script + '</head>');
    return script + html;
  }

  function highlightInPreview(id) {
    const frame = $('#frame');
    if (!frame.contentWindow) return;
    frame.contentWindow.postMessage({kind: 'rt-highlight', id}, '*');
  }

  // -------------------------------------------------------------- modals

  function openModal(id)  { $(`#${id}`).classList.remove('hidden'); }
  function closeModal(id) { $(`#${id}`).classList.add('hidden'); }
  function closeMenus()   { $$('.menu.open').forEach(m => m.classList.remove('open')); }

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
    ));
  }

  // ------- file picker (open) -------

  let fileItems = [];

  async function openFilePicker() {
    try {
      const res = await api.get('/api/templates');
      fileItems = res.templates;
      renderFileList(fileItems);
      $('#fileFilter').value = '';
      openModal('openDialog');
      $('#fileFilter').focus();
    } catch (e) {
      setStatus(e.message, 'error');
    }
  }

  function renderFileList(items) {
    const list = $('#fileList');
    list.innerHTML = '';
    let lastFolder = null;
    items.forEach(item => {
      if (item.folder !== lastFolder) {
        lastFolder = item.folder;
        const head = document.createElement('div');
        head.className = 'file-group';
        head.textContent = item.folder || '(root)';
        list.appendChild(head);
      }
      const row = document.createElement('div');
      row.className = 'file-row';
      const badge = item.hasDesign
        ? '<span class="badge">designer</span>'
        : '<span class="badge raw">raw</span>';
      row.innerHTML =
        `<span class="file-name">${escapeHtml(item.name)}</span>` +
        badge +
        `<span class="file-bytes">${item.bytes} B</span>`;
      row.addEventListener('click', () => openPath(item.path, item.hasDesign));
      list.appendChild(row);
    });
  }

  async function openPath(path, hasDesign) {
    try {
      if (hasDesign) {
        const res = await api.post('/api/design/load', {path});
        if (res.design) {
          loadDesign(res.design, res.path);
          closeModal('openDialog');
          setStatus(`Opened ${res.path}`, 'success');
          return;
        }
      }
      // fall back: raw HTML editing not yet wired in this build; instead,
      // load a minimal "Raw HTML" wrapper so the file is still editable
      // structurally inside the designer.
      const t = await api.get('/api/template?path=' + encodeURIComponent(path));
      const wrapper = {
        name: path.split('/').pop().replace(/\.html$/, ''),
        title: '(imported)',
        data: {main: 'mainData', details: 'detailsData'},
        page: {size: 'a4', margin: '0', orientation: 'portrait'},
        theme: {preset: 'a4-minimal'},
        blocks: [{id: uid(), type: 'html', config: {content: t.content}}],
      };
      loadDesign(wrapper, path);
      closeModal('openDialog');
      setStatus(`Opened ${path} as raw HTML block. Save to convert.`, 'success');
    } catch (e) {
      setStatus(e.message, 'error');
    }
  }

  // ------- new from preset -------

  function openNewDialog() {
    const list = $('#newPresetList');
    list.innerHTML = '';
    Object.entries(state.designs).forEach(([name, design]) => {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'preset-card';
      card.innerHTML =
        `<span class="preset-name">${escapeHtml(name)}</span>` +
        `<span class="preset-meta">${escapeHtml(design.page?.size || 'a4')} - ${(design.blocks || []).length} blocks</span>`;
      card.addEventListener('click', () => {
        loadDesign(deepClone(design));
        closeModal('newDialog');
      });
      list.appendChild(card);
    });
    openModal('newDialog');
  }

  // ------- save -------

  async function saveCurrent() {
    if (!state.openPath) return openSaveAs();
    try {
      const res = await api.post('/api/design/save', {
        design: state.design,
        path:   state.openPath,
        overwrite: true,
      });
      setStatus(`Saved to ${res.path} (${res.bytes} bytes)`, 'success');
    } catch (e) {
      setStatus(e.message, 'error');
    }
  }

  async function openSaveAs() {
    try {
      const res = await api.get('/api/templates');
      const sel = $('#saveFolder');
      sel.innerHTML = '';
      const folders = ['generated', ...res.folders.filter(f => f !== 'generated')];
      folders.forEach(f => {
        const o = document.createElement('option');
        o.value = f; o.textContent = f;
        sel.appendChild(o);
      });
      $('#saveName').value = (state.design.name || 'newTemplate') + '.html';
      $('#saveOverwrite').checked = false;
      openModal('saveAsDialog');
    } catch (e) {
      setStatus(e.message, 'error');
    }
  }

  async function confirmSaveAs() {
    const folder = $('#saveFolder').value;
    let name = $('#saveName').value.trim();
    if (!name) {
      setStatus('Filename is required', 'error');
      return;
    }
    if (!name.toLowerCase().endsWith('.html')) name += '.html';
    const path = folder ? `${folder}/${name}` : name;
    const overwrite = $('#saveOverwrite').checked;

    try {
      const res = await api.post('/api/design/save-as', {
        design: state.design,
        path,
        overwrite,
      });
      state.openPath = res.path;
      updateDocName();
      closeModal('saveAsDialog');
      setStatus(`Saved to ${res.path}`, 'success');
    } catch (e) {
      if (e.status === 409) {
        setStatus(`File exists. Tick "Overwrite" to replace.`, 'error');
      } else {
        setStatus(e.message, 'error');
      }
    }
  }

  // -------------------------------------------------------------- events

  function initEvents() {
    // tabs
    $$('.tab').forEach(t => t.addEventListener('click', () => {
      $$('.tab').forEach(x => x.classList.remove('active'));
      $$('.tab-pane').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      $(`.tab-pane[data-pane="${t.dataset.tab}"]`).classList.add('active');
    }));

    // preview tabs
    $$('.preview-tab').forEach(t => t.addEventListener('click', () => {
      $$('.preview-tab').forEach(x => x.classList.remove('active'));
      $$('.preview-body').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      $(`.preview-body[data-pview="${t.dataset.preview}"]`).classList.add('active');
    }));

    // zoom
    $$('.preview-zoom button').forEach(b => b.addEventListener('click', () => {
      const dir = b.dataset.zoom;
      state.zoom = Math.max(0.4, Math.min(2.0, state.zoom + (dir === 'in' ? 0.1 : -0.1)));
      $('#frame').style.transform = `scale(${state.zoom})`;
      $('#frame').style.width = `${100 / state.zoom}%`;
      $('#zoomLabel').textContent = Math.round(state.zoom * 100) + '%';
    }));

    // menus
    $$('.menu .menu-btn').forEach(btn => btn.addEventListener('click', (e) => {
      const m = btn.parentElement;
      const open = m.classList.contains('open');
      closeMenus();
      if (!open) m.classList.add('open');
      e.stopPropagation();
    }));
    document.addEventListener('click', closeMenus);

    // file menu actions
    $$('.menu[data-menu="file"] button[data-act]').forEach(btn => {
      btn.addEventListener('click', () => {
        const act = btn.dataset.act;
        closeMenus();
        if (act === 'new')      openNewDialog();
        if (act === 'open')     openFilePicker();
        if (act === 'save')     saveCurrent();
        if (act === 'save-as')  openSaveAs();
      });
    });

    // modal close
    $$('[data-close]').forEach(el => {
      el.addEventListener('click', () => {
        const modal = el.closest('.modal');
        if (modal) modal.classList.add('hidden');
      });
    });

    // save-as confirm
    $('#saveAsConfirm').addEventListener('click', confirmSaveAs);

    // file filter
    $('#fileFilter').addEventListener('input', () => {
      const q = $('#fileFilter').value.toLowerCase();
      const filtered = !q ? fileItems : fileItems.filter(
        f => f.path.toLowerCase().includes(q) || f.name.toLowerCase().includes(q)
      );
      renderFileList(filtered);
    });

    // theme inputs
    ['themePreset','themeFont','themeFontSize','themeColor','themeAccent',
     'themeBorderColor','themeBorderStyle','themeUppercase'].forEach(id => {
      const el = $('#' + id);
      el.addEventListener('input',  onThemeChange);
      el.addEventListener('change', onThemeChange);
    });

    // page inputs
    ['pageSize','pageWidth','pageMargin','pageOrientation'].forEach(id => {
      const el = $('#' + id);
      el.addEventListener('input',  onPageChange);
      el.addEventListener('change', onPageChange);
    });

    // meta inputs
    ['metaTitle','metaName','dataMain','dataDetails'].forEach(id => {
      const el = $('#' + id);
      el.addEventListener('input', onMetaChange);
    });

    // keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (e.shiftKey) openSaveAs(); else saveCurrent();
      }
      if (e.key === 'Escape') {
        $$('.modal').forEach(m => m.classList.add('hidden'));
        closeMenus();
      }
    });
  }

  function onThemeChange() {
    if ($('#themePreset').value !== state.design.theme.preset) {
      // user picked a new preset: reset overrides to that preset's defaults
      const preset = $('#themePreset').value;
      state.design.theme = {preset};
      syncThemeForm();
    } else {
      readThemeForm();
    }
    refreshPreviewDebounced();
  }

  function onPageChange() {
    readPageForm();
    refreshPreviewDebounced();
  }

  function onMetaChange() {
    state.design.title = $('#metaTitle').value;
    state.design.name  = $('#metaName').value;
    state.design.data  = {
      main:    $('#dataMain').value || 'mainData',
      details: $('#dataDetails').value || 'detailsData',
    };
    $('#dataMainPreview').textContent    = state.design.data.main;
    $('#dataDetailsPreview').textContent = state.design.data.details;
    updateDocName();
    refreshPreviewDebounced();
  }

  // -------------------------------------------------------------- go

  boot().catch(e => {
    setStatus('Failed to start: ' + e.message, 'error');
    console.error(e);
  });

})();
