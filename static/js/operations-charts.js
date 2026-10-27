/* Distribuciones agregadas: sin texto de reportes ni datos personales. */
(function () {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const colors = {'Validada': '#65ad91', 'Por validar': '#c8a76a', 'Descartada': '#a5b0a9', 'Sin iniciar': '#a5b0a9', 'En curso': '#688cb8', 'Cumplido': '#65ad91', 'Atrasado': '#c27463'};
  const charts = [];
  const shorten = (text, length) => text.length > length ? text.slice(0, length - 1) + '…' : text;
  document.querySelectorAll('[data-operation-chart]').forEach(function (canvas) {
    const rows = JSON.parse(canvas.dataset.chartValues);
    const donut = canvas.dataset.operationChart === 'doughnut';
    const total = rows.reduce((sum, row) => sum + row.cantidad, 0);
    const config = {
      type: donut ? 'doughnut' : 'bar',
      data: {labels: rows.map(r => r.etiqueta), datasets: [{label: 'Cantidad', data: rows.map(r => r.cantidad),
        backgroundColor: donut ? rows.map(r => colors[r.etiqueta] || '#a5b0a9') : '#6b9e8b',
        borderColor: '#fff', borderWidth: donut ? 3 : 0, borderRadius: donut ? 0 : 4, maxBarThickness: 19}]},
      options: {responsive: true, maintainAspectRatio: false, animation: {duration: reduced ? 0 : 400},
        plugins: {legend: {display: false}, tooltip: {backgroundColor: '#173c33', padding: 10, titleFont: {size: 11}, bodyFont: {size: 11}, callbacks: {
          title: items => items.length ? rows[items[0].dataIndex].etiqueta : '',
          label: context => donut ? context.parsed + ' de ' + total + ' (' + new Intl.NumberFormat('es-CO', {maximumFractionDigits: 1}).format(context.parsed / total * 100) + '%)' : context.parsed.x + ' registros'
        }}}
      }
    };
    if (donut) config.options.cutout = '76%';
    else {
      config.options.indexAxis = 'y';
      config.options.onResize = (instance, size) => { instance.data.labels = rows.map(r => shorten(r.etiqueta, size.width < 450 ? 23 : 45)); };
      config.options.scales = {
        x: {beginAtZero: true, suggestedMax: Math.max(1, ...rows.map(r => r.cantidad)), border: {display: false}, grid: {color: '#edf1ee'}, ticks: {precision: 0, font: {size: 10}}},
        y: {border: {display: false}, grid: {display: false}, ticks: {font: {size: 10}, color: '#425a4b'}}
      };
    }
    charts.push(new Chart(canvas, config));
  });
  function resize() { charts.forEach(chart => chart.resize()); }
  window.addEventListener('beforeprint', resize);
  window.addEventListener('afterprint', resize);
})();
