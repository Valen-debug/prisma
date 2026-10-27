/* Al consultar una pestaña se prioriza su contenido sobre el resumen gráfico. */
(function () {
  const charts = document.getElementById('signals-charts');
  const content = document.getElementById('signals-content');
  if (!charts || !content) return;
  const tabs = Array.from(document.querySelectorAll('.tabs [data-bs-toggle="tab"]'));
  function prioritizeContent() {
    if (content.nextElementSibling === charts) return;
    content.after(charts);
    content.classList.add('signals-content-first');
    requestAnimationFrame(function () {
      charts.querySelectorAll('canvas').forEach(function (canvas) {
        const instance = Chart.getChart(canvas);
        if (instance) instance.resize();
      });
    });
  }
  tabs.forEach(function (tab) {
    // También responde al pulsar la pestaña que ya está activa.
    tab.addEventListener('click', prioritizeContent);
    tab.addEventListener('shown.bs.tab', prioritizeContent);
  });
  function selectLinkedTab() {
    const linkedTab = tabs.find(tab => tab.dataset.bsTarget === location.hash);
    if (linkedTab) {
      prioritizeContent();
      bootstrap.Tab.getOrCreateInstance(linkedTab).show();
    }
  }
  window.addEventListener('hashchange', selectLinkedTab);
  selectLinkedTab();
})();
