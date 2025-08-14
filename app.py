import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(
    page_title="총알피하기 • Bullet Dodger",
    page_icon="🎮",
    layout="centered",
)

st.title("총알피하기 • Bullet Dodger")
st.caption("←→↑↓ / WASD 이동 · Shift 가속 · P 일시정지 · R 재시작 · 모바일 좌하단 조이스틱")

# 앱 옵션 (필요하면 사이드바에서 난이도 커스텀)
with st.sidebar:
    st.header("옵션")
    base_speed = st.slider("플레이어 기본 속도", 120, 360, 220, 10)
    base_bullet = st.slider("총알 기본 속도", 80, 260, 140, 5)
    accel_scale = st.slider("시간 경과 속도 배율 (최대)", 1.0, 3.5, 3.2, 0.1)
    spawn_max = st.slider("초당 최대 스폰 수", 3, 12, 6, 1)
    canvas_ratio = st.select_slider("화면 비율", options=["16:9","4:3","3:2","1:1"], value="16:9")

ratio_map = {"16:9": 9/16, "4:3": 3/4, "3:2": 2/3, "1:1": 1}
height = int(760 * ratio_map[canvas_ratio])

html_code = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    :root {{ color-scheme: dark; }}
    html, body {{ margin:0; padding:0; background:#0b0f19; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }}
    .wrap {{ width: 100%; max-width: 980px; margin: 0 auto; }}
    .frame {{ position: relative; width: 100%; aspect-ratio: {1/ratio_map[canvas_ratio]:.5} / 1; background:#000; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,.35); border:1px solid #2b2f3a; }}
    canvas {{ width:100%; height:100%; display:block; background:#000; }}
    .overlay {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,.55); backdrop-filter: blur(4px); }}
    .panel {{ text-align:center; color:#eee; padding:24px; }}
    .title {{ font-size: 22px; font-weight: 800; margin-bottom: 8px; }}
    .desc {{ color:#c9ced9; margin-bottom: 14px; }}
    .btn {{ display:inline-block; padding:10px 16px; border-radius: 14px; border:1px solid #2b2f3a; background:#1b2230; color:#e9eef7; text-decoration:none; font-weight:700; margin:0 6px; }}
    .btn.primary {{ background:#2762ff; border-color:#2762ff; }}
    .hud {{ position:absolute; left:10px; top:10px; display:flex; flex-direction:column; gap:8px; pointer-events:none; }}
    .chip {{ display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px; background:rgba(22,26,38,.7); color:#e7ebf3; font-size:12px; }}
    .chip small {{ color:#aeb6c7; }}
    .joy-area {{ position:absolute; left:0; bottom:0; width:42%; height:38%; }}
    .joy-ring {{ position:absolute; left:16px; bottom:16px; width:100px; height:100px; border-radius:999px; border:2px solid rgba(120,130,160,.5); background:rgba(20,24,34,.45); }}
  </style>
</head>
<body>
<div class=\"wrap\">
  <div class=\"frame\">
    <canvas id=\"game\"></canvas>
    <div class=\"hud\">
      <span class=\"chip\">⏱️ <b id=\"time\">0.00s</b></span>
      <span class=\"chip\">🏆 BEST <small id=\"best\">0.00s</small></span>
    </div>
    <div id=\"overlay\" class=\"overlay\">
      <div class=\"panel\">
        <div class=\"title\">총알을 피해 최대한 오래 살아남기</div>
        <div class=\"desc\">키보드(←→↑↓/WASD) 또는 모바일 좌하단 조이스틱. Shift 가속 · P 일시정지 · R 재시작</div>
        <a href=\"#\" class=\"btn primary\" id=\"btnStart\">게임 시작</a>
        <a href=\"#\" class=\"btn\" id=\"btnReset\">초기화</a>
      </div>
    </div>
    <div class=\"joy-area\" id=\"joyArea\"><div class=\"joy-ring\"></div></div>
  </div>
</div>

<script>
(function() {{
  const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const overlay = document.getElementById('overlay');
  const btnStart = document.getElementById('btnStart');
  const btnReset = document.getElementById('btnReset');
  const timeEl = document.getElementById('time');
  const bestEl = document.getElementById('best');
  const joyArea = document.getElementById('joyArea');

  let status = 'menu'; // menu | playing | paused | gameover
  let timeSurvived = 0;
  let bestTime = Number(localStorage.getItem('bd_bestTime')||0);
  let lastTs = 0; let running = false;
  let bullets = [];
  let keys = {{}};
  let player = null;
  let joy = {{ active:false, startX:0, startY:0, dx:0, dy:0 }};

  bestEl.textContent = bestTime.toFixed(2)+ 's';

  function resize() {{
    const rect = canvas.parentElement.getBoundingClientRect();
    const width = Math.floor(rect.width);
    const height = Math.floor(rect.height);
    canvas.style.width = width+'px';
    canvas.style.height = height+'px';
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
  }}
  resize();
  new ResizeObserver(resize).observe(canvas.parentElement);
  window.addEventListener('resize', resize);

  function initGame() {{
    bullets = [];
    timeSurvived = 0;
    lastTs = performance.now();
    const w = canvas.width, h = canvas.height;
    const pr = Math.floor(Math.min(w,h)*0.02)+10;
    player = {{ x:w/2, y:h/2, r:pr, speed: {base_speed} }};
    updateHUD();
  }}
  function updateHUD() {{
    timeEl.textContent = timeSurvived.toFixed(2)+'s';
    bestEl.textContent = bestTime.toFixed(2)+'s';
  }}

  function play() {{ status='playing'; running=true; lastTs=performance.now(); requestAnimationFrame(tick); overlay.style.display='none'; }}
  function pauseToggle() {{ if (status==='playing') {{ status='paused'; running=false; overlay.style.display='flex'; overlay.querySelector('.title').textContent='일시정지'; }} else if (status==='paused') {{ status='playing'; running=true; lastTs=performance.now(); overlay.style.display='none'; requestAnimationFrame(tick); }} }}
  function restart() {{ initGame(); status='playing'; running=true; overlay.style.display='none'; requestAnimationFrame(tick); }}
  function gameOver() {{ running=false; status='gameover'; overlay.style.display='flex'; overlay.querySelector('.title').textContent='게임 오버!'; bestTime = Math.max(bestTime, timeSurvived); localStorage.setItem('bd_bestTime', String(bestTime)); updateHUD(); }}

  function spawnBullet(t) {{
    const w = canvas.width, h = canvas.height;
    const margin = Math.max(w,h)*0.02 + 10;
    const side = Math.floor(Math.random()*4);
    let x=0,y=0;
    if (side===0) {{ x=-margin; y=Math.random()*h; }}
    if (side===1) {{ x=w+margin; y=Math.random()*h; }}
    if (side===2) {{ x=Math.random()*w; y=-margin; }}
    if (side===3) {{ x=Math.random()*w; y=h+margin; }}

    const jitter = 0.6;
    const tx = player.x + (Math.random()-0.5) * jitter * w;
    const ty = player.y + (Math.random()-0.5) * jitter * h;
    const dx = tx-x, dy = ty-y; const len = Math.hypot(dx,dy)||1;

    const tSec = t/1000;
    const scale = 1 + Math.min({accel_scale}, tSec/35);
    const speed = {base_bullet} * scale + Math.random()*60;
    const r = 6 + Math.random() * (10 * Math.min({accel_scale}, scale));

    bullets.push({{ x, y, r, vx: (dx/len)*speed, vy:(dy/len)*speed }});
  }}

  function tick(ts) {{
    if (!running) return;
    const dt = (ts - lastTs)/1000; lastTs = ts;
    timeSurvived += dt; updateHUD();

    // spawn
    const spawnPerSec = 1.0 + Math.min({spawn_max-1}, timeSurvived/8);
    let spawnProb = spawnPerSec * dt; let spawns=0;
    while (Math.random() < spawnProb && spawns < {spawn_max}) {{ spawnBullet(ts); spawns++; }}

    // update player
    let mvx=0, mvy=0;
    if (keys['arrowleft']||keys['a']) mvx -= 1;
    if (keys['arrowright']||keys['d']) mvx += 1;
    if (keys['arrowup']||keys['w']) mvy -= 1;
    if (keys['arrowdown']||keys['s']) mvy += 1;
    if (joy.active) {{ const l=Math.hypot(joy.dx,joy.dy); if (l>8) {{ mvx += joy.dx/l; mvy += joy.dy/l; }} }}
    const mlen=Math.hypot(mvx,mvy)||1; const boost = keys['shift']?1.25:1.0;
    player.x += (mvx/mlen) * player.speed * boost * dt * dpr;
    player.y += (mvy/mlen) * player.speed * boost * dt * dpr;

    const w = canvas.width, h = canvas.height;
    player.x = Math.max(player.r, Math.min(w-player.r, player.x));
    player.y = Math.max(player.r, Math.min(h-player.r, player.y));

    // update bullets & collision
    for (let i=bullets.length-1;i>=0;i--) {{
      const b=bullets[i]; b.x += b.vx*dt*dpr; b.y += b.vy*dt*dpr;
      if (b.x < -2*w || b.x > 3*w || b.y < -2*h || b.y > 3*h) {{ bullets.splice(i,1); continue; }}
      const dist = Math.hypot(b.x-player.x, b.y-player.y);
      if (dist < b.r + player.r) {{ gameOver(); return; }}
    }}

    // draw
    ctx.clearRect(0,0,w,h);
    const g = ctx.createLinearGradient(0,0,0,h); g.addColorStop(0,'#0f172a'); g.addColorStop(1,'#111827');
    ctx.fillStyle=g; ctx.fillRect(0,0,w,h);
    ctx.globalAlpha=0.2; ctx.strokeStyle='#1f2937'; ctx.lineWidth=1*dpr; const step=40*dpr;
    for (let x=0;x<w;x+=step) {{ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,h); ctx.stroke(); }}
    for (let y=0;y<h;y+=step) {{ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(w,y); ctx.stroke(); }}
    ctx.globalAlpha=1;

    ctx.fillStyle='#ef4444';
    for (const b of bullets) {{ ctx.beginPath(); ctx.arc(b.x,b.y,b.r,0,Math.PI*2); ctx.fill(); }}

    ctx.beginPath(); ctx.fillStyle='#60a5fa'; ctx.arc(player.x,player.y,player.r,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='#93c5fd'; ctx.lineWidth=3*dpr; ctx.stroke();

    requestAnimationFrame(tick);
  }}

  // input
  window.addEventListener('keydown', e => {{
    keys[e.key.toLowerCase()] = true;
    if (e.key.toLowerCase()==='p') pauseToggle();
    if (e.key.toLowerCase()==='r') restart();
  }});
  window.addEventListener('keyup', e => {{ keys[e.key.toLowerCase()] = false; }});

  function jt(e) {{ return (e.changedTouches? e.changedTouches[0] : e); }}
  const onStart = e => {{ const t=jt(e); joy.active=true; joy.startX=t.clientX; joy.startY=t.clientY; joy.dx=0; joy.dy=0; }};
  const onMove  = e => {{ if(!joy.active) return; const t=jt(e); joy.dx=t.clientX-joy.startX; joy.dy=t.clientY-joy.startY; }};
  const onEnd   = () => {{ joy.active=false; joy.dx=0; joy.dy=0; }};
  joyArea.addEventListener('touchstart', onStart, {{passive:true}});
  joyArea.addEventListener('touchmove', onMove, {{passive:true}});
  joyArea.addEventListener('touchend', onEnd);
  joyArea.addEventListener('mousedown', onStart);
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onEnd);

  btnStart.addEventListener('click', (e)=>{{ e.preventDefault(); play(); }});
  btnReset.addEventListener('click', (e)=>{{ e.preventDefault(); initGame(); }});

  initGame();
}})();
</script>
</body>
</html>
"""

# Streamlit에 삽입 (height는 비율에 맞춰 계산)
html(html_code, height=height, scrolling=False)

st.markdown("""
**Tip**  
- GitHub 저장소로 푸시 후 [Streamlit Community Cloud](https://streamlit.io/cloud)에 연결하면 곧바로 URL로 배포됩니다.  
- 최고 기록은 로컬 브라우저 `localStorage`에 저장됩니다.
""")
