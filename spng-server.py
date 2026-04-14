import json
import sys
import os
import io
from pathlib import Path
from flask import Flask, render_template_string, send_file, abort
import numpy as np

app = Flask(__name__)

if len(sys.argv) < 2:
  print("Usage: python spng-server.py <ROOT_DIR>")
  sys.exit(1)

ROOT_DIR = Path(sys.argv[1]).resolve()

def read_png_from_spng(spng_file: Path, offset: int, length: int):
  with spng_file.open("rb") as f:
    data = np.fromfile(f, dtype=np.uint8, count=length, sep="", offset=offset)
  return data

@app.route('/')
@app.route('/view/')
@app.route('/view/<path:subpath>')
def viewer(subpath=""):
  full_path = (ROOT_DIR / subpath).resolve()
  if not str(full_path).startswith(str(ROOT_DIR)): abort(403)

  if full_path.is_dir():
    current_dir = full_path
    selected_json = None
    rel_dir_path = subpath
  else:
    current_dir = full_path.parent
    selected_json = full_path.name
    rel_dir_path = os.path.dirname(subpath)

  items = sorted(os.listdir(current_dir))
  dirs = [i for i in items if (current_dir / i).is_dir()]
  jsons = [i for i in items if i.endswith('.json')]

  max_idx = 0
  if selected_json:
    try:
      with (current_dir / selected_json).open("r", encoding="utf-8") as f:
        meta = json.load(f)
        max_idx = len(meta.get("Images", [])) - 1
    except:
      pass

  return render_template_string("""
    <html>
    <head>
      <title>E07 SPNG Explorer</title>
      <style>
        body { background: #1a1a1a; color: #ddd; font-family: sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        #sidebar { width: 300px; background: #252525; border-right: 1px solid #444; display: flex; flex-direction: column; flex-shrink: 0; box-sizing: border-box; }
        .sidebar-section { border-bottom: 1px solid #444; padding: 10px; box-sizing: border-box; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 10px; }
        h3 { font-size: 0.8em; color: #666; text-transform: uppercase; margin: 10px 0 5px 0; }

        /* Fixed Button Widths */
        .btn {
          background: #444; color: #eee; border: 1px solid #666; padding: 8px; cursor: pointer;
          border-radius: 3px; font-size: 0.8em; width: 100%; margin-bottom: 8px;
          text-align: center; display: block; text-decoration: none; box-sizing: border-box;
        }
        .btn:hover { background: #555; }
        .btn-root { background: #552222; border-color: #884444; font-weight: bold; }

        a.list-item { display: block; color: #aaa; text-decoration: none; padding: 4px; font-size: 0.85em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        a.list-item:hover { background: #333; color: #fff; }
        a.list-item.active { background: #0055ff; color: #fff; }

        #main { flex-grow: 1; display: flex; flex-direction: column; background: #000; overflow: hidden; }
        #header { background: #333; padding: 10px; text-align: center; border-bottom: 1px solid #444; z-index: 20; }

        /* Correct Scrollable Viewport */
        #viewport { flex-grow: 1; overflow: auto; display: block; text-align: center; cursor: grab; }
        #viewport:active { cursor: grabbing; }

        img.mode-fit { max-height: 100%; max-width: 100%; object-fit: contain; }
        img.mode-actual { max-height: none; max-width: none; object-fit: none; }

        input[type=range] { width: 70%; vertical-align: middle; }
      </style>
    </head>
    <body>
      <div id="sidebar">
        <div class="sidebar-section">
          <a href="/view/" class="btn btn-root">GO TO ROOT</a>
          <button class="btn" onclick="toggleMode()">VIEW MODE: FIT/ACTUAL</button>
        </div>
        <div class="scroll-area">
          <h3>PATH: /{{ rel_dir_path }}</h3>
          <a href="/view/{{ parent_path }}" class="list-item">.. (UP)</a>
          {% for d in dirs %}
            <a href="/view/{{ rel_dir_path }}/{{ d }}" class="list-item">DIR: {{ d }}/</a>
          {% endfor %}

          <h3>JSON FILES</h3>
          {% for j in jsons %}
            <a href="/view/{{ rel_dir_path }}/{{ j }}" class="list-item {{ 'active' if j == selected_json else '' }}">JSON: {{ j }}</a>
          {% endfor %}
        </div>
      </div>
      <div id="main">
        {% if selected_json %}
        <div id="header">
          <div style="font-size: 0.8em; margin-bottom: 5px; color: #888;">{{ selected_json }}</div>
          <input type="range" id="z-range" min="0" max="{{ max_idx }}" value="0" oninput="update(this.value)">
          <span style="font-size: 0.8em; margin-left: 10px;">IDX: <span id="idx">0</span> / {{ max_idx + 1 }}</span>
        </div>
        <div id="viewport" id="vbox">
          <img id="target" src="/image/{{ rel_dir_path }}/{{ selected_json }}/0" class="mode-fit" draggable="false">
        </div>
        <script>
          const range = document.getElementById('z-range');
          const idxDisp = document.getElementById('idx');
          const targetImg = document.getElementById('target');
          const viewport = document.getElementById('viewport');
          const relPath = "{{ rel_dir_path }}/{{ selected_json }}";

          function update(val) {
            val = Math.max(0, Math.min(val, {{ max_idx }}));
            idxDisp.innerText = val;
            targetImg.src = '/image/' + relPath + '/' + val;
            range.value = val;
          }

          function toggleMode() {
            if (targetImg.classList.contains('mode-fit')) {
              targetImg.classList.replace('mode-fit', 'mode-actual');
            } else {
              targetImg.classList.replace('mode-actual', 'mode-fit');
            }
          }

          // Drag to scroll
          let isDown = false;
          let startX, startY, scrollLeft, scrollTop;
          viewport.addEventListener('mousedown', (e) => {
            isDown = true;
            startX = e.pageX - viewport.offsetLeft;
            startY = e.pageY - viewport.offsetTop;
            scrollLeft = viewport.scrollLeft;
            scrollTop = viewport.scrollTop;
          });
          viewport.addEventListener('mouseleave', () => isDown = false);
          viewport.addEventListener('mouseup', () => isDown = false);
          viewport.addEventListener('mousemove', (e) => {
            if(!isDown) return;
            e.preventDefault();
            const x = e.pageX - viewport.offsetLeft;
            const y = e.pageY - viewport.offsetTop;
            const walkX = (x - startX);
            const walkY = (y - startY);
            viewport.scrollLeft = scrollLeft - walkX;
            viewport.scrollTop = scrollTop - walkY;
          });

          window.addEventListener('wheel', (e) => {
            if (e.target.closest('#sidebar')) return;
            e.preventDefault();
            let v = parseInt(range.value);
            v = (e.deltaY > 0) ? v + 1 : v - 1;
            update(v);
          }, { passive: false });

          window.addEventListener('keydown', (e) => {
            let v = parseInt(range.value);
            if (e.key === 'ArrowRight') update(v + 1);
            if (e.key === 'ArrowLeft') update(v - 1);
          });
        </script>
        {% else %}
        <div id="viewport" style="color: #666; display: flex; align-items: center; justify-content: center;">SELECT A JSON FILE</div>
        {% endif %}
      </div>
    </body>
    </html>
  """, rel_dir_path=rel_dir_path, dirs=dirs, jsons=jsons,
       selected_json=selected_json, max_idx=max_idx,
       parent_path=os.path.dirname(rel_dir_path.rstrip('/')))

@app.route('/image/<path:json_rel_path>/<int:idx>')
def get_image(json_rel_path, idx):
  json_path = (ROOT_DIR / json_rel_path).resolve()
  try:
    with json_path.open("r", encoding="utf-8") as f:
      meta = json.load(f)
    entry = meta.get("Images", [])[idx]
    parts = entry["Path"].split("&")
    spng_file = json_path.parent / parts[0]
    raw_png_data = read_png_from_spng(spng_file, int(parts[1]), int(parts[2]))
    return send_file(io.BytesIO(raw_png_data), mimetype='image/png')
  except Exception as e:
    return str(e), 500

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
