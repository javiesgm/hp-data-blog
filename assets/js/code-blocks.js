/* GBIF Data Blog – code blocks: a header with the language name and a Copy button.
   Works on the HTML that Jekyll/Rouge writes for fenced code: <div class="language-sql highlighter-rouge">. */
(function () {
  var NAMES = { r: 'R', python: 'Python', py: 'Python', sql: 'SQL', shell: 'Shell', bash: 'Shell', sh: 'Shell',
    console: 'Shell', json: 'JSON', scala: 'Scala', html: 'HTML', xml: 'XML', yaml: 'YAML', yml: 'YAML',
    javascript: 'JavaScript', js: 'JavaScript', css: 'CSS', java: 'Java', markdown: 'Markdown', csv: 'CSV' };

  function label(el) {
    var m = (el.className || '').match(/language-([\w+-]+)/);
    var lang = m ? m[1].toLowerCase() : '';
    if (!lang || lang === 'plaintext' || lang === 'text') return 'Code';
    return NAMES[lang] || lang.charAt(0).toUpperCase() + lang.slice(1);
  }

  function codeText(el) {
    // the code column only, never the line numbers
    var code = el.querySelector('.rouge-code pre') || el.querySelector('pre code') || el.querySelector('pre');
    return code ? code.innerText.replace(/\n$/, '') : '';
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy') ? resolve() : reject(); } catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  document.querySelectorAll('.content div.highlighter-rouge').forEach(function (block) {
    if (block.querySelector('.code-header')) return;
    var header = document.createElement('div');
    header.className = 'code-header';
    var name = document.createElement('span');
    name.className = 'code-header__lang';
    name.textContent = label(block);
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'code-header__copy';
    btn.setAttribute('aria-label', 'Copy ' + name.textContent + ' to clipboard');
    btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="1.5"/><path d="M5 15V5a1.5 1.5 0 0 1 1.5-1.5H15"/></svg><span>Copy</span>';
    btn.addEventListener('click', function () {
      var span = btn.querySelector('span');
      copy(codeText(block)).then(function () {
        span.textContent = 'Copied'; btn.classList.add('is-done');
      }, function () {
        span.textContent = 'Press Ctrl+C';
      });
      setTimeout(function () { span.textContent = 'Copy'; btn.classList.remove('is-done'); }, 2000);
    });
    header.appendChild(name);
    header.appendChild(btn);
    block.insertBefore(header, block.firstChild);
  });
})();
