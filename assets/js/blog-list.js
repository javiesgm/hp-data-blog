/* GBIF Data Blog – post list behaviour (used by _layouts/archive.html).
   - Filters the .feature cards on the URL: ?category= ?author= ?tag= ?series= ?q=
   - Search box (q) narrows further as you type
   - Cards / List switch, remembered in this browser
   No dependencies. */
(function () {
  var list = document.getElementById('blog-list');
  if (!list) return;
  var cards = Array.prototype.slice.call(list.querySelectorAll('.feature'));
  var input = document.getElementById('blog-search-input');
  var filterBox = document.getElementById('blog-filter');
  var empty = document.getElementById('blog-list-empty');
  var params = new URLSearchParams(window.location.search);
  var home = (document.querySelector('.navbar-logo') || {}).getAttribute ? document.querySelector('.navbar-logo').getAttribute('href') : '/';

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  cards.forEach(function (c) { c._text = norm(c.getAttribute('data-search')); });

  // ---- active filter from the URL (one at a time, like the old Hugo pages) ----
  var filter = null;
  [['author', 'Posts by'], ['series', 'Series'], ['tag', 'Tagged'], ['category', 'Topic']].some(function (f) {
    var v = params.get(f[0]);
    if (v) { filter = { key: f[0], value: v, prefix: f[1] }; return true; }
    return false;
  });

  function matchesFilter(c) {
    if (!filter) return true;
    var v = filter.value;
    switch (filter.key) {
      case 'category': return (c.getAttribute('data-categories') || '').split('|').indexOf(v) > -1;
      case 'author': return (c.getAttribute('data-authors') || '').indexOf('|' + v + '|') > -1;
      case 'tag': return (c.getAttribute('data-tags') || '').indexOf('|' + v + '|') > -1;
      case 'series': return c.getAttribute('data-series') === v;
    }
    return true;
  }

  // Human label for the filter chip, read from the first matching card
  function filterLabel() {
    if (!filter) return '';
    if (filter.key === 'category') return filter.value;
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      if (!matchesFilter(c)) continue;
      if (filter.key === 'series') return c.getAttribute('data-series-name');
      var slugs = (c.getAttribute(filter.key === 'author' ? 'data-authors' : 'data-tags') || '').split('|').filter(Boolean);
      var names = (c.getAttribute(filter.key === 'author' ? 'data-author-names' : 'data-tag-names') || '').split('|');
      var idx = slugs.indexOf(filter.value);
      if (idx > -1 && names[idx]) return names[idx];
    }
    return filter.value;
  }

  function apply() {
    var terms = input ? norm(input.value).split(/\s+/).filter(Boolean) : [];
    var shown = 0;
    cards.forEach(function (c) {
      var ok = matchesFilter(c) && terms.every(function (t) { return c._text.indexOf(t) > -1; });
      c.classList.toggle('is-search-hidden', !ok);
      c.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    if (filterBox) {
      var count = shown + (shown === 1 ? ' post' : ' posts');
      if (filter) {
        filterBox.innerHTML = '<span class="blog-filter__label">' + esc(filter.prefix) + '</span> ' +
          '<span class="tag is-medium blog-filter__chip">' + esc(filterLabel()) +
          '<a class="delete is-small" href="' + esc(home) + '" aria-label="Clear filter"></a></span>' +
          '<span class="blog-filter__count">' + count + '</span>';
      } else {
        filterBox.innerHTML = '<span class="blog-filter__count">' + (terms.length ? count + ' found' : count) + '</span>';
      }
    }
    if (empty) empty.hidden = shown > 0;
    if (filter && filter.key === 'author') document.title = filterLabel() + ' - ' + document.title.replace(/^.* - /, '');
  }

  if (input) {
    var q = params.get('q');
    if (q) input.value = q;
    input.addEventListener('input', function () {
      apply();
      try {
        var url = new URL(window.location.href);
        if (input.value) url.searchParams.set('q', input.value); else url.searchParams.delete('q');
        window.history.replaceState(null, '', url);
      } catch (e) {}
    });
    input.addEventListener('keydown', function (e) { if (e.key === 'Escape') { input.value = ''; input.dispatchEvent(new Event('input')); } });
    document.addEventListener('keydown', function (e) {
      var tag = (document.activeElement && document.activeElement.tagName) || '';
      if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(tag)) { e.preventDefault(); input.focus(); }
    });
  }

  // ---- cards / list switch ----
  var buttons = Array.prototype.slice.call(list.querySelectorAll('.blog-view-btn'));
  function setView(view, remember) {
    list.classList.toggle('is-list', view === 'list');
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-view') === view)); });
    if (remember) { try { localStorage.setItem('blog-view', view); } catch (e) {} }
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () { setView(b.getAttribute('data-view'), true); });
  });
  var saved = null;
  try { saved = localStorage.getItem('blog-view'); } catch (e) {}
  setView(params.get('view') || saved || 'cards', false);

  // Mark the topic chip of the active ?category= (or "All" when there is no filter)
  Array.prototype.slice.call(document.querySelectorAll('.blog-topics a')).forEach(function (a) {
    var c = null;
    try { c = new URL(a.href).searchParams.get('category'); } catch (e) {}
    var on = filter ? (filter.key === 'category' && c === filter.value) : (c === null && a.classList.contains('blog-topics__all'));
    a.classList.toggle('is-active', on);
    if (on) a.setAttribute('aria-current', 'true');
  });

  // The theme's own ?category= script runs on load; run after it so both agree
  apply();
  window.addEventListener('load', apply);
})();
