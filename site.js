(() => {
  document.getElementById('year').textContent = new Date().getFullYear();
  const film = document.getElementById('window-film');
  const button = document.querySelector('.motion-toggle');
  const label = button.querySelector('.motion-label');
  const icon = button.querySelector('.motion-icon');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const small = window.matchMedia('(max-width: 900px)');
  let userPaused = false;
  let inView = true;
  let ready = document.readyState === 'complete';
  const saveData = navigator.connection?.saveData;
  function sync() {
    button.setAttribute('aria-pressed', String(userPaused));
    label.textContent = film.paused ? 'Play scene' : 'Pause scene';
    icon.textContent = film.paused ? '▷' : 'Ⅱ';
  }
  async function update() {
    if (!ready) return;
    if (reduced.matches || saveData) {
      film.pause(); film.classList.remove('is-playing'); button.hidden = true; return;
    }
    if (userPaused || !inView || document.hidden) { film.pause(); sync(); return; }
    const source = small.matches ? film.dataset.mobileSrc : film.dataset.src;
    if (film.getAttribute('src') !== source) {
      film.classList.remove('is-playing');
      film.src = source;
    }
    try { await film.play(); } catch { /* The still is the complete fallback. */ }
    sync();
  }
  film.addEventListener('playing', () => { film.classList.add('is-playing'); button.hidden = false; sync(); });
  film.addEventListener('canplay', () => { if (!reduced.matches && !saveData) button.hidden = false; sync(); });
  film.addEventListener('error', () => { film.classList.remove('is-playing'); button.hidden = true; });
  button.addEventListener('click', () => { userPaused = !film.paused; update(); });
  reduced.addEventListener('change', update);
  small.addEventListener('change', update);
  document.addEventListener('visibilitychange', update);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; update(); }, { threshold: .01 }).observe(document.querySelector('.opening'));
  }
  if (ready) update();
  else window.addEventListener('load', () => { ready = true; update(); }, { once: true });
})();
