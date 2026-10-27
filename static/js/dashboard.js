/* Gráficos del tablero: todos los valores provienen del servidor. */
(function () {
  const source = document.getElementById('dashboard-data');
  if (!source) return;
  const data = JSON.parse(source.textContent);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const colors = {critico: '#b95342', alto: '#d29a63', medio: '#baa25e', bajo: '#65ad91', nd: '#a5b0a9'};
  const commitmentColors = {'Sin iniciar': '#a5b0a9', 'En curso': '#688cb8', 'Cumplido': '#65ad91', 'Atrasado': '#c27463'};
  const charts = [];
  const format = new Intl.NumberFormat('es-CO', {maximumFractionDigits: 1});
  const truncate = (text, limit) => text.length > limit ? text.slice(0, limit - 1) + '…' : text;
  const commonOptions = {
    responsive: true, maintainAspectRatio: false,
    animation: {duration: reducedMotion ? 0 : 450},
    plugins: {
      legend: {position: 'bottom', labels: {usePointStyle: true, pointStyle: 'rectRounded', boxWidth: 8, boxHeight: 8, padding: 16, font: {size: 10}}},
      tooltip: {backgroundColor: '#173c33', padding: 11, titleFont: {size: 11}, bodyFont: {size: 11}, cornerRadius: 7}
    }
  };
  const scoreScales = () => ({
    x: {min: 0, max: 25, border: {display: false}, grid: {color: '#edf1ee'}, ticks: {stepSize: 5, font: {size: 10}}},
    y: {border: {display: false}, grid: {display: false}, ticks: {font: {size: 11}, color: '#425a4b'}}
  });
  function chart(id, config) {
    const canvas = document.getElementById(id);
    if (canvas) charts.push(new Chart(canvas, config));
  }
  chart('factorsChart', {
    type: 'bar',
    data: {labels: data.tecnica.map(f => f.nombre), datasets: [
      {label: 'Lectura técnica', data: data.tecnica.map(f => f.indice), backgroundColor: '#5f9f8b', borderRadius: 3, maxBarThickness: 12},
      {label: data.lectura_gente, data: data.comunidad.map(f => f.indice), backgroundColor: '#b59fcb', borderRadius: 3, maxBarThickness: 12}
    ]},
    options: {...commonOptions, indexAxis: 'y', scales: scoreScales(),
      plugins: {...commonOptions.plugins, tooltip: {...commonOptions.plugins.tooltip,
        callbacks: {label: ctx => ctx.dataset.label + ': ' + format.format(ctx.parsed.x) + ' / 25'}
      }}
    }
  });
  chart('risksChart', {
    type: 'bar',
    data: {labels: data.riesgos.map(v => truncate(v.nombre, window.innerWidth < 768 ? 23 : 45)), datasets: [
      {label: 'Puntaje efectivo', data: data.riesgos.map(v => v.efectivo), backgroundColor: data.riesgos.map(v => colors[v.clase] || colors.nd), borderRadius: 4, maxBarThickness: 18}
    ]},
    options: {...commonOptions, indexAxis: 'y', scales: scoreScales(),
      onResize: (instance, size) => {
        instance.data.labels = data.riesgos.map(v => truncate(v.nombre, size.width < 420 ? 22 : 45));
      },
      plugins: {...commonOptions.plugins, legend: {display: false}, tooltip: {...commonOptions.plugins.tooltip,
        callbacks: {
          title: items => items.length ? data.riesgos[items[0].dataIndex].nombre : '',
          label: ctx => data.riesgos[ctx.dataIndex].nivel + ' · ' + format.format(ctx.parsed.x) + ' / 25'
        }
      }}
    }
  });
  const weekSeries = [
    {key: 'validadas', label: 'Validados', color: '#73b29d'},
    {key: 'pendientes', label: 'Pendientes', color: '#d2b36f'},
    {key: 'descartadas', label: 'Descartados', color: '#b9c1bd'},
    {key: 'otros', label: 'Otros', color: '#b59fcb'}
  ].filter(s => s.key !== 'otros' || data.actividad.semanas.some(w => w.otros > 0));
  chart('activityChart', {
    type: 'bar',
    data: {labels: data.actividad.semanas.map(s => s.etiqueta), datasets: weekSeries.map(s => ({
      label: s.label, data: data.actividad.semanas.map(w => w[s.key]), backgroundColor: s.color, borderRadius: 2, maxBarThickness: 30
    }))},
    options: {...commonOptions,
      scales: {
        x: {stacked: true, border: {display: false}, grid: {display: false}, ticks: {font: {size: 9}, maxRotation: 45, minRotation: 0}},
        y: {stacked: true, beginAtZero: true, border: {display: false}, grid: {color: '#edf1ee'}, ticks: {precision: 0, font: {size: 10}}}
      },
      plugins: {...commonOptions.plugins, tooltip: {...commonOptions.plugins.tooltip, mode: 'index', intersect: false}}
    }
  });
  chart('commitmentsChart', {
    type: 'doughnut',
    data: {labels: data.actividad.compromisos.map(c => c.estado), datasets: [{
      data: data.actividad.compromisos.map(c => c.cantidad),
      backgroundColor: data.actividad.compromisos.map(c => commitmentColors[c.estado] || '#a5b0a9'),
      borderColor: '#fff', borderWidth: 4, hoverOffset: reducedMotion ? 0 : 3
    }]},
    options: {...commonOptions, cutout: '78%', plugins: {...commonOptions.plugins, legend: {display: false}}}
  });
  let map;
  if (document.getElementById('dashboardMap')) {
    map = L.map('dashboardMap', {scrollWheelZoom: false}).setView([4.6, -74.8], 5);
    const status = document.getElementById('dashboard-map-status');
    const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 13, attribution: '&copy; colaboradores de OpenStreetMap'
    });
    tiles.on('tileerror', function () { status.textContent = 'El mapa base requiere conexión. Las ubicaciones y sus fichas siguen disponibles en la lista.'; });
    tiles.addTo(map);
    const bounds = [];
    data.lugares.forEach(function (place) {
      if (!Number.isFinite(place.lat) || !Number.isFinite(place.lon)) return;
      const icon = L.divIcon({className: '', html: '<div class="dashboard-map-pin" style="--pin-color:' + (colors[place.clase] || colors.nd) + '"></div>', iconSize: [16, 16], iconAnchor: [8, 8]});
      const popup = document.createElement('div');
      const name = document.createElement('strong'); name.textContent = place.nombre;
      const location = document.createElement('span'); location.textContent = place.ubicacion;
      const info = document.createElement('p'); info.textContent = place.nivel + (place.puntaje === null ? '' : ' · ' + place.puntaje + ' / 25') + ' · ' + place.senales + ' señales validadas';
      const link = document.createElement('a'); link.href = place.url; link.textContent = 'Consultar ficha →';
      popup.append(name, location, info, link);
      L.marker([place.lat, place.lon], {icon: icon, title: place.nombre, alt: place.nombre}).addTo(map).bindPopup(popup);
      bounds.push([place.lat, place.lon]);
    });
    if (bounds.length) map.fitBounds(bounds, {padding: [28, 28], maxZoom: 8});
  }
  function showTab(hash) {
    const button = Array.from(document.querySelectorAll('[data-bs-toggle="tab"]')).find(b => b.dataset.bsTarget === hash);
    if (!button) return false;
    bootstrap.Tab.getOrCreateInstance(button).show();
    return true;
  }
  document.querySelectorAll('[data-dashboard-tab]').forEach(link => link.addEventListener('click', function (event) {
    event.preventDefault();
    if (showTab(link.dataset.dashboardTab)) {
      history.replaceState(null, '', link.dataset.dashboardTab);
      const selected = document.querySelector('[data-bs-target="' + link.dataset.dashboardTab + '"]');
      selected.focus();
      selected.scrollIntoView({block: 'center', behavior: reducedMotion ? 'instant' : 'smooth'});
    }
  }));
  function resize() {
    charts.forEach(c => c.resize());
    if (map) map.invalidateSize();
  }
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(b => b.addEventListener('shown.bs.tab', resize));
  window.addEventListener('hashchange', () => showTab(location.hash));
  if (location.hash) showTab(location.hash);
  // La pestaña recordada puede estar oculta durante la creación de gráficos.
  requestAnimationFrame(resize);
  window.addEventListener('beforeprint', resize);
  window.addEventListener('afterprint', resize);
})();
