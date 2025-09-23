(() => {
  const slidesEl = document.getElementById('slides');
  const slideEls = Array.from(slidesEl.querySelectorAll('.slide'));
  const btnPrev = document.getElementById('btnPrev');
  const btnNext = document.getElementById('btnNext');
  const btnFullscreen = document.getElementById('btnFullscreen');
  const progressBar = document.getElementById('progressBar');
  const counter = document.getElementById('counter');
  const helpDialog = document.getElementById('helpDialog');
  const btnHelp = document.getElementById('btnHelp');
  const btnCloseHelp = document.getElementById('btnCloseHelp');
  const imgDialog = document.getElementById('imgDialog');
  const imgDialogImg = document.getElementById('imgDialogImg');
  const imgDialogCaption = document.getElementById('imgDialogCaption');
  const btnCloseImg = document.getElementById('btnCloseImg');

  let index = 0;

  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

  function applyIndex(i, fromHash = false) {
    index = clamp(i, 0, slideEls.length - 1);
    slideEls.forEach((s, idx) => s.classList.toggle('active', idx === index));
    const pct = ((index + 1) / slideEls.length) * 100;
    progressBar.style.width = pct + '%';
    counter.textContent = `${index + 1} / ${slideEls.length}`;
    const title = slideEls[index].dataset.title || `Slide ${index + 1}`;
    document.title = `${title} — AI Tech Training`;
    if (!fromHash) location.hash = `#${index + 1}`;
  }

  function next() { applyIndex(index + 1); }
  function prev() { applyIndex(index - 1); }
  function first() { applyIndex(0); }
  function last() { applyIndex(slideEls.length - 1); }

  // Initialize from hash
  function initFromHash() {
    const h = location.hash.replace('#', '');
    const num = parseInt(h, 10);
    if (!isNaN(num) && num >= 1 && num <= slideEls.length) {
      applyIndex(num - 1, true);
    } else {
      applyIndex(0, true);
    }
  }

  // Fullscreen toggle
  function toggleFullscreen() {
    const elem = document.documentElement;
    if (!document.fullscreenElement) {
      (elem.requestFullscreen && elem.requestFullscreen()) ||
      (elem.webkitRequestFullscreen && elem.webkitRequestFullscreen());
    } else {
      (document.exitFullscreen && document.exitFullscreen()) ||
      (document.webkitExitFullscreen && document.webkitExitFullscreen());
    }
  }

  // Key bindings
  function onKey(e) {
    // Avoid double-advance when Space activates focused buttons/links
    const interactiveSelectors = 'button, a, input, textarea, select, [contenteditable="true"], summary, details';
    const isInteractive = (el) => el && (el.closest && el.closest(interactiveSelectors));
    if (e.key === ' ' && (isInteractive(e.target) || isInteractive(document.activeElement))) {
      // Let the control handle Space (e.g., button click), we won't also advance
      return;
    }
    switch (e.key) {
      case 'ArrowRight':
      case 'PageDown':
      case ' ': // Space
        e.preventDefault();
        next();
        break;
      case 'ArrowLeft':
      case 'PageUp':
        e.preventDefault();
        prev();
        break;
      case 'Home':
        e.preventDefault();
        first();
        break;
      case 'End':
        e.preventDefault();
        last();
        break;
      case 'f':
      case 'F':
        e.preventDefault();
        toggleFullscreen();
        break;
      case '?':
      case 'h':
      case 'H':
        helpDialog.showModal();
        break;
      default:
        break;
    }
  }

  // Click handlers
  btnNext.addEventListener('click', next);
  btnPrev.addEventListener('click', prev);
  btnFullscreen.addEventListener('click', toggleFullscreen);
  btnHelp.addEventListener('click', () => helpDialog.showModal());
  btnCloseHelp.addEventListener('click', () => helpDialog.close());

  // Hash change support (deep links)
  window.addEventListener('hashchange', initFromHash);
  // Attach keyboard handler once at document level to avoid double-advances
  document.addEventListener('keydown', onKey);

  // Activate first slide after DOM is ready
  window.addEventListener('DOMContentLoaded', () => {
    // Position slides stacked; CSS handles visibility via .active
    slideEls.forEach((s, idx) => s.classList.toggle('active', idx === 0));
    initFromHash();
    slidesEl.focus();

    // Make all SVG images zoomable via dialog (support querystrings like ?v=1)
    const imgs = document.querySelectorAll('img');
    imgs.forEach(img => {
      try {
        const url = new URL(img.src, document.baseURI);
        const pathname = url.pathname || '';
        if (pathname.toLowerCase().endsWith('.svg')) {
          img.classList.add('zoomable');
          img.addEventListener('click', () => {
            imgDialogImg.src = img.src;
            imgDialogImg.alt = img.alt || 'Image';
            const cap = img.closest('figure')?.querySelector('figcaption')?.textContent || '';
            imgDialogCaption.textContent = cap;
            imgDialog.showModal();
          });
        }
      } catch (e) {
        // ignore invalid URLs (e.g., data URIs)
      }
    });
    btnCloseImg?.addEventListener('click', () => imgDialog.close());
    imgDialog?.addEventListener('click', (e) => {
      if (e.target === imgDialog) imgDialog.close();
    });
  });
})();
