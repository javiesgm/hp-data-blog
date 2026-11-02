/* GBIF Data Blog – search box on the post list.
   Filters the .feature cards by the text in their data-search attribute.
   Works together with the theme's ?category= filter (cards it hides stay hidden). */
(function () {
  var input = document.getElementById('blog-search-input');
  if (!input) return;
  var cards = Array.prototype.slice.call(document.querySelectorAll('.blog-list .feature'));
  var status = document.getElementById('blog-search-status');
  var empty = document.getElementById('blog-list-empty');

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  cards.forEach(function (c) { c._text = norm(c.getAttribute('data-search')); });

  function apply() {
    var terms = norm(input.value).split(/\s+/).filter(Boolean);
    var shown = 0;
    cards.forEach(function (c) {
      var match = terms.every(function (t) { return c._text.indexOf(t) > -1; });
      c.classList.toggle('is-search-hidden', !match);
      if (match && c.style.display !== 'none') shown++;
    });
    if (status) status.textContent = terms.length ? shown + (shown === 1 ? ' post' : ' posts') + ' found' : '';
    if (empty) empty.hidden = shown > 0;
    try {
      var url = new URL(window.location.href);
      if (input.value) url.searchParams.set('q', input.value); else url.searchParams.delete('q');
      window.history.replaceState(null, '', url);
    } catch (e) {}
  }

  var q = new URLSearchParams(window.location.search).get('q');
  if (q) { input.value = q; }
  input.addEventListener('input', apply);
  input.addEventListener('keydown', function (e) { if (e.key === 'Escape') { input.value = ''; apply(); } });
  document.addEventListener('keydown', function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(tag)) { e.preventDefault(); input.focus(); }
  });
  // run after the theme's category filter has hidden cards
  window.addEventListener('load', apply);
})();
