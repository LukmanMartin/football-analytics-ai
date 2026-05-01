from flask import Flask, send_file, render_template_string

app = Flask(__name__)

HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Analítica de Fútbol — Demo</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {
    --green: #00ff87;
    --dark: #080c0a;
    --mid: #0f1a13;
    --card: #131f16;
    --border: #1e3324;
    --text: #c8d8cc;
    --muted: #556b5c;
    --red: #ff4444;
    --blue: #4488ff;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--dark);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
  }
  body::before {
    content:'';
    position:fixed; inset:0;
    background-image:
      linear-gradient(rgba(0,255,135,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,135,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events:none;
    z-index:0;
  }

  header {
    position:relative; z-index:10;
    padding: 28px 48px;
    display:flex; align-items:center; gap:16px;
    border-bottom: 1px solid var(--border);
    background: rgba(8,12,10,0.9);
    backdrop-filter: blur(10px);
  }
  .logo-icon {
    width:40px; height:40px;
    background: var(--green);
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    display:flex; align-items:center; justify-content:center;
    font-size:18px;
  }
  header h1 { font-family:'Bebas Neue', sans-serif; font-size:2rem; letter-spacing:3px; color:var(--green); }
  header span { color:var(--muted); font-size:0.8rem; letter-spacing:2px; text-transform:uppercase; margin-left:auto; }

  main { position:relative; z-index:1; max-width:1300px; margin:0 auto; padding:48px 32px; }

  /* HERO */
  .hero {
    text-align:center; margin-bottom:56px;
    padding: 64px 32px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius:16px;
    position:relative; overflow:hidden;
  }
  .hero::before {
    content:'';
    position:absolute; inset:0;
    background: radial-gradient(ellipse at 50% 0%, rgba(0,255,135,0.08) 0%, transparent 60%);
    pointer-events:none;
  }
  .hero-badge {
    display:inline-block;
    padding:6px 16px; border-radius:20px;
    background:rgba(0,255,135,0.1); border:1px solid rgba(0,255,135,0.3);
    color:var(--green); font-size:0.75rem; letter-spacing:2px; text-transform:uppercase;
    margin-bottom:20px;
  }
  .hero h2 { font-family:'Bebas Neue', sans-serif; font-size:3rem; letter-spacing:4px; color:var(--text); margin-bottom:12px; }
  .hero p { color:var(--muted); font-size:1rem; max-width:600px; margin:0 auto 32px; line-height:1.6; }
  .hero-links { display:flex; gap:16px; justify-content:center; flex-wrap:wrap; }
  .btn-primary {
    padding:14px 32px;
    background:var(--green); color:var(--dark);
    border:none; border-radius:8px;
    font-family:'Bebas Neue', sans-serif; font-size:1.1rem; letter-spacing:2px;
    cursor:pointer; text-decoration:none;
    transition:all 0.2s;
    display:inline-flex; align-items:center; gap:8px;
  }
  .btn-primary:hover { background:#00cc6a; transform:translateY(-2px); }
  .btn-secondary {
    padding:14px 32px;
    background:transparent; color:var(--green);
    border:1px solid var(--border); border-radius:8px;
    font-family:'Bebas Neue', sans-serif; font-size:1.1rem; letter-spacing:2px;
    cursor:pointer; text-decoration:none;
    transition:all 0.2s;
    display:inline-flex; align-items:center; gap:8px;
  }
  .btn-secondary:hover { border-color:var(--green); background:rgba(0,255,135,0.05); transform:translateY(-2px); }

  .section-label {
    font-family:'Bebas Neue', sans-serif;
    font-size:0.85rem; letter-spacing:4px; color:var(--green);
    margin-bottom:20px; text-transform:uppercase;
  }

  /* STATS */
  .stats-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }
  .stat-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:10px; padding:24px;
    position:relative; overflow:hidden;
    transition: transform 0.2s;
  }
  .stat-card:hover { transform:translateY(-2px); }
  .stat-card::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
  .stat-card.team1::after { background:var(--red); }
  .stat-card.team2::after { background:var(--blue); }
  .stat-label { font-size:0.7rem; letter-spacing:2px; color:var(--muted); text-transform:uppercase; margin-bottom:10px; }
  .stat-value { font-family:'Bebas Neue', sans-serif; font-size:2.4rem; color:var(--text); }
  .stat-value span { font-size:1rem; color:var(--muted); }

  /* POSSESSION BAR */
  .possession-bar-wrap {
    background:var(--card); border:1px solid var(--border);
    border-radius:12px; padding:28px; margin-bottom:24px;
  }
  .possession-teams { display:flex; justify-content:space-between; margin-bottom:14px; }
  .possession-team .pct { font-family:'Bebas Neue', sans-serif; font-size:2rem; }
  .possession-team.t1 .pct { color:var(--red); }
  .possession-team.t2 .pct { color:var(--blue); text-align:right; }
  .possession-visual { height:14px; border-radius:7px; overflow:hidden; display:flex; }
  .possession-t1 { background:var(--red); }
  .possession-t2 { background:var(--blue); }

  /* RESULTS GRID */
  .results-grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:48px; }

  .video-card { background:var(--card); border:1px solid var(--border); border-radius:12px; overflow:hidden; }
  .video-card video { width:100%; display:block; }
  .video-label {
    padding:16px 20px;
    font-size:0.75rem; letter-spacing:2px; color:var(--muted); text-transform:uppercase;
    border-top:1px solid var(--border);
    display:flex; justify-content:space-between; align-items:center;
  }
  .download-btn {
    padding:8px 16px;
    background:transparent; border:1px solid var(--border);
    color:var(--green); border-radius:6px;
    font-size:0.75rem; cursor:pointer; text-decoration:none;
    transition:all 0.2s; letter-spacing:1px;
  }
  .download-btn:hover { background:rgba(0,255,135,0.1); border-color:var(--green); }

  .chart-card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:24px; }
  .chart-title { font-family:'Bebas Neue', sans-serif; font-size:1rem; letter-spacing:3px; color:var(--green); margin-bottom:20px; }
  canvas { max-height:220px; }

  /* HOW IT WORKS */
  .how-section { margin-bottom:48px; }
  .steps-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
  .step-card {
    background:var(--card); border:1px solid var(--border);
    border-radius:12px; padding:28px;
    position:relative;
  }
  .step-num {
    font-family:'Bebas Neue', sans-serif; font-size:3rem; color:rgba(0,255,135,0.1);
    position:absolute; top:16px; right:20px;
  }
  .step-icon { font-size:2rem; margin-bottom:12px; }
  .step-card h3 { font-size:1rem; font-weight:600; margin-bottom:8px; color:var(--text); }
  .step-card p { font-size:0.85rem; color:var(--muted); line-height:1.6; }

  /* FOOTER */
  footer {
    border-top:1px solid var(--border);
    padding:32px 48px;
    text-align:center;
    color:var(--muted); font-size:0.8rem;
    position:relative; z-index:1;
  }
  footer a { color:var(--green); text-decoration:none; }

  @media(max-width:900px) {
    .results-grid, .steps-grid { grid-template-columns:1fr; }
    .stats-grid { grid-template-columns:repeat(2,1fr); }
    header { padding:20px 24px; }
    header span { display:none; }
    main { padding:32px 16px; }
    .hero { padding:40px 20px; }
    .hero h2 { font-size:2rem; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-icon">⚽</div>
  <h1>Analítica de Fútbol</h1>
  <span>Visión por Computador · IA Analítica</span>
</header>

<main>

  <!-- HERO -->
  <div class="hero">
    <div class="hero-badge">⚡ Demo en vivo</div>
    <h2>Análisis de Vídeo Deportivo con IA</h2>
    <p>Sistema que detecta jugadores, rastrea su identidad y calcula estadísticas de posesión, pases y pérdidas de balón automáticamente mediante visión por computador.</p>
    <div class="hero-links">
      <a class="btn-primary" href="/video">▶ Ver vídeo procesado</a>
      <a class="btn-secondary" href="https://github.com/tu-usuario/tu-repo" target="_blank">⬡ Ver código en GitHub</a>
    </div>
  </div>

  <!-- RESULTADOS -->
  <div style="margin-bottom:48px;">
    <div class="section-label">Estadísticas del Análisis</div>

    <div class="stats-grid">
      <div class="stat-card team1">
        <div class="stat-label">Posesión Equipo 1</div>
        <div class="stat-value">45.8<span>%</span></div>
      </div>
      <div class="stat-card team2">
        <div class="stat-label">Posesión Equipo 2</div>
        <div class="stat-value">54.2<span>%</span></div>
      </div>
      <div class="stat-card team1">
        <div class="stat-label">Pases Equipo 1</div>
        <div class="stat-value">11</div>
      </div>
      <div class="stat-card team2">
        <div class="stat-label">Pases Equipo 2</div>
        <div class="stat-value">8</div>
      </div>
      <div class="stat-card team1">
        <div class="stat-label">Pérdidas Equipo 1</div>
        <div class="stat-value">3</div>
      </div>
      <div class="stat-card team2">
        <div class="stat-label">Pérdidas Equipo 2</div>
        <div class="stat-value">3</div>
      </div>
      <div class="stat-card team1">
        <div class="stat-label">Jugadores T1</div>
        <div class="stat-value">10</div>
      </div>
      <div class="stat-card team2">
        <div class="stat-label">Jugadores T2</div>
        <div class="stat-value">7</div>
      </div>
    </div>

    <div class="possession-bar-wrap">
      <div class="chart-title">Posesión del Balón</div>
      <div class="possession-teams">
        <div class="possession-team t1">
          <div style="font-size:0.85rem;">Equipo 1</div>
          <div class="pct">45.8%</div>
        </div>
        <div class="possession-team t2" style="text-align:right;">
          <div style="font-size:0.85rem;">Equipo 2</div>
          <div class="pct">54.2%</div>
        </div>
      </div>
      <div class="possession-visual">
        <div class="possession-t1" style="width:45.8%"></div>
        <div class="possession-t2" style="width:54.2%"></div>
      </div>
    </div>

    <div class="results-grid">
      <div class="video-card">
        <video controls>
          <source src="/video" type="video/mp4">
        </video>
        <div class="video-label">
          <span>Vídeo procesado</span>
          <a class="download-btn" href="/video" download="analitica_futbol.mp4">⬇ Descargar</a>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:16px;">
        <div class="chart-card">
          <div class="chart-title">Pases por Equipo</div>
          <canvas id="chartPasses"></canvas>
        </div>
        <div class="chart-card">
          <div class="chart-title">Pérdidas de Balón</div>
          <canvas id="chartLosses"></canvas>
        </div>
      </div>
    </div>
  </div>

  <!-- CÓMO FUNCIONA -->
  <div class="how-section">
    <div class="section-label">Cómo Funciona</div>
    <div class="steps-grid">
      <div class="step-card">
        <div class="step-num">01</div>
        <div class="step-icon">🎯</div>
        <h3>Detección con YOLO</h3>
        <p>Un modelo YOLOv8 entrenado específicamente para fútbol detecta jugadores, árbitros y el balón en cada fotograma con alta precisión.</p>
      </div>
      <div class="step-card">
        <div class="step-num">02</div>
        <div class="step-icon">🔗</div>
        <h3>Tracking con ByteTrack</h3>
        <p>El algoritmo ByteTrack mantiene la identidad única de cada jugador entre fotogramas, incluso ante oclusiones o salidas de plano.</p>
      </div>
      <div class="step-card">
        <div class="step-num">03</div>
        <div class="step-icon">👕</div>
        <h3>Clasificación por Equipo</h3>
        <p>K-Means clustering agrupa automáticamente a los jugadores por el color de su camiseta, sin necesidad de etiquetado manual.</p>
      </div>
      <div class="step-card">
        <div class="step-num">04</div>
        <div class="step-icon">⚽</div>
        <h3>Asignación de Posesión</h3>
        <p>Se calcula qué jugador está más cerca del balón en cada fotograma y se acumula la posesión por equipo a lo largo del partido.</p>
      </div>
      <div class="step-card">
        <div class="step-num">05</div>
        <div class="step-icon">📊</div>
        <h3>Cálculo de Estadísticas</h3>
        <p>Cada cambio de poseedor detecta pases exitosos o pérdidas de balón, generando métricas acumulativas por equipo.</p>
      </div>
      <div class="step-card">
        <div class="step-num">06</div>
        <div class="step-icon">🎬</div>
        <h3>Vídeo Anotado</h3>
        <p>Se genera un vídeo de salida con elipses de color por equipo, IDs de jugadores, marcador de balón y estadísticas en pantalla.</p>
      </div>
    </div>
  </div>

</main>

<footer>
  <p>Proyecto Final · Python · Tokio School 2026 · 
  <a href="https://github.com/tu-usuario/tu-repo" target="_blank">GitHub</a></p>
</footer>

<script>
const chartOpts = {
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#556b5c' }, grid: { color: '#1e3324' } },
    y: { ticks: { color: '#556b5c' }, grid: { color: '#1e3324' }, beginAtZero: true }
  }
};

new Chart(document.getElementById('chartPasses'), {
  type: 'bar',
  data: {
    labels: ['Equipo 1', 'Equipo 2'],
    datasets: [{
      data: [11, 8],
      backgroundColor: ['rgba(255,68,68,0.7)', 'rgba(68,136,255,0.7)'],
      borderColor: ['#ff4444', '#4488ff'],
      borderWidth: 2, borderRadius: 6
    }]
  },
  options: chartOpts
});

new Chart(document.getElementById('chartLosses'), {
  type: 'bar',
  data: {
    labels: ['Equipo 1', 'Equipo 2'],
    datasets: [{
      data: [3, 3],
      backgroundColor: ['rgba(255,68,68,0.4)', 'rgba(68,136,255,0.4)'],
      borderColor: ['#ff4444', '#4488ff'],
      borderWidth: 2, borderRadius: 6
    }]
  },
  options: chartOpts
});
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/video')
def serve_video():
    return send_file(
        'static/visión_por_computador_e_IA_analítica.mp4',
        mimetype='video/mp4'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)