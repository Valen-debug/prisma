/* Indicador de navegación y restablecimiento al volver desde el navegador. */
(function () {
  const root = document.documentElement;
  let resetTimer;
  function reset() {
    root.classList.remove('is-navigating');
    clearTimeout(resetTimer);
  }
  document.addEventListener('click', function (event) {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.hasAttribute('download') || (link.target && link.target !== '_self') || link.dataset.bsToggle) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || !/^https?:$/.test(url.protocol)) return;
    if (url.pathname === location.pathname && url.search === location.search) return;
    root.classList.add('is-navigating');
    resetTimer = setTimeout(reset, 12000);
  });
  window.addEventListener('pageshow', reset);
  window.addEventListener('pagehide', reset);
})();

/* La barra se convierte en una cápsula flotante al superar el primer tramo. */
(function () {
  const navbar = document.getElementById('site-navbar');
  const mobileMenu = document.getElementById('mobile-navigation');
  if (!navbar || !mobileMenu) return;
  let scheduled = false;
  function updateNavbar() {
    navbar.classList.toggle('is-scrolled', window.scrollY > 60);
    scheduled = false;
  }
  window.addEventListener('scroll', function () {
    if (!scheduled) { scheduled = true; requestAnimationFrame(updateNavbar); }
  }, { passive: true });
  window.addEventListener('pageshow', updateNavbar);
  updateNavbar();
  const desktop = window.matchMedia('(min-width: 1200px)');
  function closeMobileMenu() {
    const instance = bootstrap.Offcanvas.getInstance(mobileMenu);
    if (instance) instance.hide();
  }
  desktop.addEventListener('change', function (event) { if (event.matches) closeMobileMenu(); });
  mobileMenu.addEventListener('click', function (event) {
    if (event.target.closest('a[href]')) closeMobileMenu();
  });
})();

/* Despliegue y recogida del popover sin alterar el posicionamiento de Bootstrap. */
(function () {
  const toggle = document.getElementById('analysis-menu-toggle');
  const menu = document.getElementById('analysis-menu');
  if (!toggle || !menu || !menu.animate) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let animation;
  let closing = false;
  let allowHide = false;
  toggle.addEventListener('shown.bs.dropdown', function () {
    if (animation) animation.cancel();
    if (reduced.matches) return;
    animation = menu.animate([
      {opacity: 0, clipPath: 'inset(0 0 100% 0 round 14px)'},
      {opacity: 1, clipPath: 'inset(0 0 0 0 round 14px)'}
    ], {duration: 220, easing: 'cubic-bezier(.2,.7,.3,1)'});
  });
  toggle.addEventListener('hide.bs.dropdown', function (event) {
    if (allowHide || reduced.matches) return;
    event.preventDefault();
    if (closing) return;
    closing = true;
    const currentOpacity = getComputedStyle(menu).opacity;
    const currentClip = getComputedStyle(menu).clipPath;
    if (animation) animation.cancel();
    menu.classList.add('is-closing');
    animation = menu.animate([
      {opacity: currentOpacity, clipPath: currentClip === 'none' ? 'inset(0 0 0 0 round 14px)' : currentClip},
      {opacity: 0, clipPath: 'inset(0 0 100% 0 round 14px)'}
    ], {duration: 170, easing: 'cubic-bezier(.4,0,.8,.3)', fill: 'forwards'});
    function finish() {
      allowHide = true;
      bootstrap.Dropdown.getOrCreateInstance(toggle).hide();
      allowHide = false;
      closing = false;
      menu.classList.remove('is-closing');
      animation.cancel();
    }
    animation.finished.then(finish, finish);
  });
})();
