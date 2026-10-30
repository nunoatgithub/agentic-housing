import * as THREE from 'three';
import { RoundedBoxGeometry } from './vendor/RoundedBoxGeometry.js';
import { OrbitControls } from './vendor/OrbitControls.js';
import { LineSegments2 } from './vendor/lines/LineSegments2.js';
import { LineSegmentsGeometry } from './vendor/lines/LineSegmentsGeometry.js';
import { LineMaterial } from './vendor/lines/LineMaterial.js';

// ---------- constants ----------
const CELL = 4, T = 0.3, H = 3.0, CENTER = 7, SHEET = 46;
const DIRS = [[-1, 0], [0, 1], [1, 0], [0, -1]]; // N E S W as (row, col)
const SUN = new THREE.Vector3(-0.9, 0.55, 0.15).normalize();
const wx = c => (c - CENTER) * CELL, wz = r => (r - CENTER) * CELL;
const $ = id => document.getElementById(id);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const easeOut = t => 1 - Math.pow(1 - t, 3);
const easeInOut = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

function mulberry32(a) {
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
const hashStr = s => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };
const h1 = n => { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); };
const vn1 = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return h1(i) * (1 - u) + h1(i + 1) * u; };

// ---------- renderer / scene ----------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
// studio environment: bright soft panels so glossy surfaces pick up reflections
{
  const env = new THREE.Scene(); env.background = new THREE.Color('#333');
  const panel = (w, h, x, y, z, i) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(i, i, i), side: THREE.DoubleSide })); m.position.set(x, y, z); m.lookAt(0, 0, 0); env.add(m); };
  panel(10, 30, -28, 12, 0, 3.2); panel(14, 4, 0, 24, 0, 0.6);
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(env, 0.02).texture; pm.dispose();
}
scene.background = new THREE.Color('#e8e8e8');
const camera = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, 2, 1500);
const sun = new THREE.DirectionalLight(0xffffff, 1);
sun.position.copy(SUN).multiplyScalar(160);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 20, far: 400 });
sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.03;
scene.add(sun);
const ambient = new THREE.HemisphereLight(0xffffff, 0xdfe3ee, 0.55);
scene.add(ambient);

// ---------- the sheet of paper ----------
const GLSL_NOISE = `
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }`;
const paperMat = new THREE.ShaderMaterial({
  uniforms: { uHalf: { value: SHEET } },
  vertexShader: `varying vec2 vXZ; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vXZ = w.xz; gl_Position = projectionMatrix * viewMatrix * w; }`,
  fragmentShader: `${GLSL_NOISE}
    uniform float uHalf; varying vec2 vXZ;
    void main(){
      vec2 p = vXZ;
      float m = max(abs(p.x), abs(p.y));
      float fib = vn(p * 38.0) * 0.5 + vn(p * 6.0) * 0.5;
      vec3 paper = vec3(0.914, 0.914, 0.925) + (fib - 0.5) * 0.004;
      
      vec2 g = abs(fract((p - 2.0) / 4.0 + 0.5) - 0.5) * 4.0;
      vec2 w = fwidth(p);
      float gl = max(1.0 - smoothstep(0.0, 1.0 * w.x, g.x), 1.0 - smoothstep(0.0, 1.0 * w.y, g.y));
      paper = mix(paper, vec3(0.5, 0.57, 0.64), gl * 0.0 * (0.75 + 0.25 * vn(p * 3.0)));
      float db = uHalf - m;
      float fr = max(1.0 - smoothstep(0.0, 1.6 * w.x + 0.05, abs(db - 3.2)), 1.0 - smoothstep(0.0, 1.0 * w.x + 0.03, abs(db - 2.4)));
      
      vec3 desk = vec3(0.985, 0.984, 0.978) + (vn(p * 38.0) - 0.5) * 0.02;
      float shade = 0.0;
      desk *= 1.0 - shade * 0.05;
      gl_FragColor = vec4(paper, 1.0);
    }`,
});
const paper = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000).rotateX(-Math.PI / 2), paperMat);
paper.visible = false; scene.add(paper);
const gridPane = new THREE.Mesh(new THREE.PlaneGeometry(2 * SHEET, 2 * SHEET).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({ transparent: true, depthWrite: false, vertexShader: `varying vec2 vXZ; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vXZ = w.xz; gl_Position = projectionMatrix * viewMatrix * w; }`, fragmentShader: `varying vec2 vXZ; void main(){ vec2 p = vXZ; vec2 g = abs(fract((p - 2.0) / 4.0 + 0.5) - 0.5) * 4.0; vec2 w = fwidth(p); float gl = max(1.0 - smoothstep(0.0, w.x, g.x), 1.0 - smoothstep(0.0, w.y, g.y)); gl_FragColor = vec4(mix(vec3(0.9, 0.9, 0.93), vec3(0.62, 0.64, 0.7), gl), 0.05 + gl * 0.35); }` }));

const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(2 * SHEET, 2 * SHEET).rotateX(-Math.PI / 2), new THREE.ShadowMaterial({ color: 0x2a3550, opacity: 0.12, transparent: true, depthWrite: false }));
shadowPlane.position.y = 0.045; shadowPlane.receiveShadow = true; shadowPlane.renderOrder = 2;
shadowPlane.visible = false; scene.add(shadowPlane);

// ---------- ink ----------
const lineMats = [];
const mkLine = (width, alpha = 1) => { const m = new LineMaterial({ color: 0xffffff, linewidth: width, vertexColors: true, transparent: alpha < 1, opacity: alpha }); m.resolution.set(innerWidth, innerHeight); lineMats.push(m); return m; };
const mWall = mkLine(1.7), mFlat = mkLine(1.4), mFurn = mkLine(1.7, 1);
const INK = new THREE.Color('#1d2740'), INK2 = new THREE.Color('#6a7794'), PENCIL = new THREE.Color('#3d4864');

// hand-drawn stroke: subdivided, wobbly, and overshooting its ends a little
function stroke(out, cols, a, b, { rnd, amp = 0.02, over = 0.05, perp = null, color = INK }) {
  const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], len = Math.hypot(dx, dy, dz) || 1e-6;
  const ux = dx / len, uy = dy / len, uz = dz / len;
  const o1 = over * rnd(), o2 = over * rnd(), L = len + o1 + o2, seed = rnd() * 100;
  const p = perp || [-uz, 0, ux];
  const n = Math.max(1, Math.ceil(L / 0.45));
  let prev = null;
  for (let k = 0; k <= n; k++) {
    const t = k / n, w = (vn1(seed + t * L * 1.1) * 2 - 1) * amp, s = t * L - o1;
    const pt = [a[0] + ux * s + p[0] * w, a[1] + uy * s + p[1] * w, a[2] + uz * s + p[2] * w];
    if (prev) { out.push(...prev, ...pt); cols.push(color.r, color.g, color.b, color.r, color.g, color.b); }
    prev = pt;
  }
}
function lineObj(out, cols, mat) {
  const g = new LineSegmentsGeometry();
  g.setPositions(new Float32Array(out)); g.setColors(new Float32Array(cols));
  const l = new LineSegments2(g, mat);
  l.userData.n = out.length / 6;
  return l;
}
function mergeBoxes(boxes) {
  const pos = [], nor = [], idx = []; let off = 0;
  for (const [x0, x1, y0, y1] of boxes) {
    if (x1 - x0 < 0.01 || y1 - y0 < 0.01) continue;
    const g = new THREE.BoxGeometry(x1 - x0, y1 - y0, T).translate((x0 + x1) / 2, (y0 + y1) / 2, 0);
    const p = g.attributes.position, n = g.attributes.normal;
    for (let i = 0; i < p.count; i++) { pos.push(p.getX(i), p.getY(i), p.getZ(i)); nor.push(n.getX(i), n.getY(i), n.getZ(i)); }
    for (let i = 0; i < g.index.count; i++) idx.push(g.index.getX(i) + off);
    off += p.count; g.dispose();
  }
  const m = new THREE.BufferGeometry();
  m.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  m.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  m.setIndex(idx);
  return m;
}

// per-room light colours (c, r grid) sampled by the wall shader
const LN = 32, lightData = new Uint8Array(LN * LN * 4);
const lightTex = new THREE.DataTexture(lightData, LN, LN, THREE.RGBAFormat);
lightTex.magFilter = lightTex.minFilter = THREE.NearestFilter; lightTex.needsUpdate = true;
// wall faces: paper with pencil hatching on the shaded side, graphite for the cut tops
const wallMat = new THREE.ShaderMaterial({
  uniforms: { uSun: { value: SUN }, uLight: { value: lightTex } },
  transparent: true, depthWrite: false,
  vertexShader: `varying vec3 vN; varying vec3 vP;
    void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vP = w.xyz; vN = normalize(mat3(modelMatrix) * normal); gl_Position = projectionMatrix * viewMatrix * w; }`,
  fragmentShader: `uniform vec3 uSun; uniform sampler2D uLight; varying vec3 vN; varying vec3 vP;
    void main(){
      vec3 n = normalize(vN);
      if (n.y < -0.5) discard;
      vec3 v = normalize(cameraPosition - vP);
      float fres = pow(1.0 - abs(dot(n, v)), 2.5);
      float s = dot(n, normalize(uSun)) * 0.5 + 0.5;
      vec3 tint = vec3(0.80, 0.91, 0.98);
      float streak = smoothstep(0.0, 1.0, sin((vP.x - vP.z) * 0.9 + vP.y * 1.4)) * 0.05;
      vec3 col = mix(tint, vec3(1.0), 0.35 + 0.4 * s) + streak;
      float a = 0.74 + 0.1 * (1.0 - s) + fres * 0.16;
      if (abs(n.y) < 0.5) {
        vec2 q = vP.xz + n.xz * 0.6;
        vec2 cr = floor(q / 4.0 + 7.5);
        vec2 ctr = (cr - 7.0) * 4.0;
        vec4 L = texture2D(uLight, (cr + 0.5) / 32.0);
        float d2 = dot(vP.xz - ctr, vP.xz - ctr);
        float I = L.a / (1.0 + 0.16 * d2) * exp(-vP.y * 0.45) * 1.9;
        col = mix(col, L.rgb, clamp(I, 0.0, 0.92));
        a = min(1.0, a + I * 0.2);
      }
      if (n.y > 0.5) { col = vec3(0.86, 0.94, 1.0); a = 0.22; }
      gl_FragColor = vec4(col, a);
    }`,
});

// room wash: watercolour that blooms outward from the centre, pooling at the edges
const WASH = { bedroom: '#ff2d55', bathroom: '#1e90ff', kitchen: '#ffd60a', living: '#ff8a00', hallway: '#000000' };
const washProto = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false,
  uniforms: { uColor: { value: new THREE.Color() }, uProg: { value: 1 }, uSeed: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `${GLSL_NOISE}
    uniform vec3 uColor; uniform float uProg, uSeed; varying vec2 vUv;
    void main(){
      vec2 p = vUv - 0.5;
      float nz = vn(vUv * 5.0 + uSeed) * 0.55 + vn(vUv * 17.0 + uSeed) * 0.3;
      float reveal = smoothstep(0.0, 0.35, uProg * 1.7 - length(p) * 1.8 + (nz - 0.4) * 0.7);
      float e = max(abs(p.x), abs(p.y)) * 2.0;
      float pool = smoothstep(0.72, 1.0, e);
      vec3 c = uColor * (1.0 - pool * 0.16 - nz * 0.1);
      c = mix(c, vec3(1.0), 0.28 * (1.0 - smoothstep(0.0, 0.95, e)));
      float spot = 1.0 - smoothstep(0.0, 0.95, length(p) * 2.0);
      gl_FragColor = vec4(mix(uColor, vec3(1.0), 0.25 * spot * spot), reveal * (0.12 + 0.4 * spot));
    }`,
});

// ---------- house data ----------
let data, frames, planMemo = new Map();
const roomKey = r => `${r.id}@${r.r},${r.c}:${r.type}`;
const parseCell = s => { const m = /^([A-Z])(\d+)$/.exec(s); return m ? [m[1].charCodeAt(0) - 65, +m[2] - 1] : null; };
const wallBetween = (r1, c1, r2, c2) => (r1 === r2 ? `v,${r1},${Math.max(c1, c2)}` : `h,${Math.max(r1, r2)},${c1}`);
const sideKey = (r, c, d) => d === 0 ? `h,${r},${c}` : d === 2 ? `h,${r + 1},${c}` : d === 3 ? `v,${r},${c}` : `v,${r},${c + 1}`;
const nodeXZ = s => { const [R, C] = s.split(',').map(Number); return [wx(C) - CELL / 2, wz(R) - CELL / 2]; };
const wallGeom = key => {
  const [o, r, c] = key.split(','); const R = +r, C = +c;
  return o === 'h'
    ? { horiz: true, nodes: [`${R},${C}`, `${R},${C + 1}`] }
    : { horiz: false, nodes: [`${R},${C}`, `${R + 1},${C}`] };
};

function frameInfo(f) {
  if (f._info) return f._info;
  const cells = new Map();
  for (const r of f.rooms) cells.set(`${r.r},${r.c}`, r);
  const doorKeys = new Set(), links = []; let entrance = null;
  for (const [a, b] of f.doors) {
    const ca = parseCell(a); if (!ca || !cells.has(ca.join())) continue;
    const ent = { north: 0, east: 1, south: 2, west: 3 }[b];
    if (ent !== undefined) { entrance = sideKey(ca[0], ca[1], ent); continue; }
    const cb = parseCell(b); if (!cb || !cells.has(cb.join())) continue;
    if (Math.abs(ca[0] - cb[0]) + Math.abs(ca[1] - cb[1]) !== 1) continue;
    doorKeys.add(wallBetween(...ca, ...cb)); links.push([ca, cb]);
  }
  const walls = new Map(), deg = new Map();
  for (const r of f.rooms) for (let d = 0; d < 4; d++) {
    const key = sideKey(r.r, r.c, d);
    if (walls.has(key)) continue;
    const other = cells.get(`${r.r + DIRS[d][0]},${r.c + DIRS[d][1]}`);
    const door = doorKeys.has(key) || entrance === key;
    const win = !other && !door && r.type !== 'hallway' ? (r.type === 'bathroom' ? 2 : 1) : 0;
    const geom = wallGeom(key);
    geom.nodes.forEach(n => deg.set(n, (deg.get(n) || 0) + 1));
    walls.set(key, { key, door, win, sig: `${door ? 1 : 0}${win}`, geom });
  }
  walls.forEach(w => { w.free = w.geom.nodes.map(n => deg.get(n) === 1); w.buildSig = w.sig + w.free.map(Number).join(''); });
  return (f._info = { cells, walls, links });
}

// ---------- wall objects ----------
const wallPool = new Map(), roomPool = new Map();
function disposeObj(o) { o.traverse(c => { if (c.geometry) c.geometry.dispose(); }); }

function buildWall(o, spec) {
  while (o.body.children.length) { const c = o.body.children[0]; o.body.remove(c); disposeObj(c); }
  while (o.flat.children.length) { const c = o.flat.children[0]; o.flat.remove(c); disposeObj(c); }
  const L = CELL, e0 = spec.free[0] ? 0 : T / 2, e1 = spec.free[1] ? 0 : T / 2, x0 = -e0, x1 = L + e1, mid = L / 2, hT = T / 2;
  const rnd = mulberry32(hashStr(spec.key) + 7);
  const boxes = [], polys = [], zEdges = [], extra = [];
  const dl = mid - 0.75, dr = mid + 0.75;
  if (spec.door) {
    boxes.push([x0, dl, 0, H], [dr, x1, 0, H], [dl, dr, 2.35, H]);
    polys.push([[x0, 0], [x0, H], [x1, H], [x1, 0], [dr, 0], [dr, 2.35], [dl, 2.35], [dl, 0]]);
    zEdges.push([dl, 2.35], [dr, 2.35], [dl, 0], [dr, 0]);
  } else if (spec.win) {
    const w = spec.win === 2 ? 0.9 : 1.5, y0 = spec.win === 2 ? 1.5 : 1.0, y1 = 2.3, a = mid - w / 2, b = mid + w / 2;
    boxes.push([x0, a, 0, H], [b, x1, 0, H], [a, b, 0, y0], [a, b, y1, H]);
    polys.push([[x0, 0], [x0, H], [x1, H], [x1, 0]], [[a, y0], [a, y1], [b, y1], [b, y0]]);
    zEdges.push([a, y0], [a, y1], [b, y1], [b, y0]);
    extra.push([[mid, y0, 0], [mid, y1, 0]], [[a, (y0 + y1) / 2, 0], [b, (y0 + y1) / 2, 0]]);
  } else {
    boxes.push([x0, x1, 0, H]);
    polys.push([[x0, 0], [x0, H], [x1, H], [x1, 0]]);
  }
  if (spec.free[0]) zEdges.push([x0, H], [x0, 0]);
  if (spec.free[1]) zEdges.push([x1, H], [x1, 0]);

  const out = [], cols = [];
  const S1 = { rnd, amp: 0.016, over: 0.05, color: INK }, S2 = { rnd, amp: 0.03, over: 0.09, color: INK2 };
  const seg = (a, b, perp) => { stroke(out, cols, a, b, { ...S1, perp }); stroke(out, cols, a, b, { ...S2, perp }); };
  for (const poly of polys) for (let i = 0; i < poly.length; i++) {
    const p = poly[i], q = poly[(i + 1) % poly.length], horiz = Math.abs(q[0] - p[0]) >= Math.abs(q[1] - p[1]);
    for (const z of [hT, -hT]) seg([p[0], p[1], z], [q[0], q[1], z], horiz ? [0, 1, 0] : [1, 0, 0]);
  }
  for (const [x, y] of zEdges) seg([x, y, -hT], [x, y, hT], [0, 1, 0]);
  for (const [a, b] of extra) seg(a, b, Math.abs(b[0] - a[0]) > 0 ? [0, 1, 0] : [1, 0, 0]);

  const fill = new THREE.Mesh(mergeBoxes(boxes), wallMat);
  fill.castShadow = false; fill.renderOrder = 3;
  o.body.add(fill);

  if (spec.door) { // door leaf and swing arc, as on an architect's plan
    const o2 = [], c2 = [], side = hashStr(spec.key) % 2 ? 1 : -1, R = 1.5, Y = 0.06;
    const opt = { rnd, amp: 0.008, over: 0.02, color: PENCIL };
    stroke(o2, c2, [dl, Y, 0], [dl, Y, side * R], opt);
    let prev = [dl + R, Y, 0];
    for (let k = 1; k <= 10; k++) {
      const a = (k / 10) * Math.PI / 2, pt = [dl + R * Math.cos(a), Y, side * R * Math.sin(a)];
      stroke(o2, c2, prev, pt, { ...opt, over: 0, amp: 0.004 }); prev = pt;
    }
    o.flat.add(lineObj(o2, c2, mFlat));
  }
  o.buildSig = spec.buildSig;
}
function getWall(spec) {
  let o = wallPool.get(spec.key);
  if (!o) {
    const g = nodeXZ(spec.geom.nodes[0]);
    const group = new THREE.Group(); group.position.set(g[0], 0, g[1]); group.rotation.y = spec.geom.horiz ? 0 : -Math.PI / 2;
    const body = new THREE.Group(), flat = new THREE.Group();
    group.add(body, flat); scene.add(group);
    o = { group, body, flat, buildSig: '' }; wallPool.set(spec.key, o);
  }
  if (o.buildSig !== spec.buildSig) buildWall(o, spec);
  return o;
}
// g: 0..1 growth. anchorEnd: 0 = grows from node 0, 1 = from node 1. gone: shrinks instead of growing
function setWall(o, g, anchorEnd, gone) {
  o.shown = true;
  o.group.visible = g > 0.001;
  let sx, sy;
  if (gone) { sx = 1; sy = Math.max(0.001, g); }
  else {
    sx = Math.max(0.001, easeOut(clamp(g / 0.55)));
    sy = g < 0.55 ? 0.02 : 0.02 + 0.98 * easeOut(clamp((g - 0.55) / 0.45));
  }
  o.body.scale.set(sx, sy, 1);
  o.body.position.x = anchorEnd === 1 ? CELL * (1 - sx) : 0;
  const f = gone ? 0 : clamp((g - 0.8) / 0.2);
  o.flat.visible = f > 0;
  o.flat.children.forEach(l => { l.geometry.instanceCount = Math.ceil(l.userData.n * f); });
}

// ---------- rooms: wash + furniture ----------
function furniture(type, id) {
  const rnd = mulberry32(hashStr(id)), segs = [];
  const poly = (pts, close = true) => { for (let i = 0; i < pts.length - (close ? 0 : 1); i++) segs.push([...pts[i], ...pts[(i + 1) % pts.length]]); };
  const rect = (cx, cz, w, d) => poly([[cx - w / 2, cz - d / 2], [cx + w / 2, cz - d / 2], [cx + w / 2, cz + d / 2], [cx - w / 2, cz + d / 2]]);
  const circ = (cx, cz, r, n = 12) => poly(Array.from({ length: n }, (_, k) => [cx + r * Math.cos(k / n * 6.2832), cz + r * Math.sin(k / n * 6.2832)]));
  const line = (a, b, c, d) => segs.push([a, b, c, d]);
  if (type === 'bedroom') {
    rect(0, -0.85, 1.7, 2.0); rect(-0.42, -1.55, 0.65, 0.4); rect(0.42, -1.55, 0.65, 0.4); line(-0.85, -0.45, 0.85, -0.45);
    rect(1.35, -1.6, 0.45, 0.45); rect(-0.8, 1.65, 1.6, 0.5); line(-1.6, 1.4, 0, 1.9);
  } else if (type === 'bathroom') {
    rect(-0.4, -1.45, 2.2, 0.95); rect(-0.4, -1.45, 1.9, 0.65); circ(0.55, -1.45, 0.1);
    rect(1.35, 0.9, 0.5, 0.35); circ(1.35, 1.3, 0.28); rect(-1.3, 1.5, 0.8, 0.45); circ(-1.3, 1.5, 0.15);
  } else if (type === 'kitchen') {
    rect(0, -1.7, 3.4, 0.6); rect(-1.7, 0.3, 0.6, 2.8); rect(0.5, -1.7, 0.8, 0.4);
    circ(-0.6, -1.7, 0.14); circ(-0.2, -1.7, 0.14); rect(0.6, 0.7, 1.2, 1.2); rect(0.6, 0.0, 0.4, 0.25); rect(0.6, 1.4, 0.4, 0.25);
  } else if (type === 'living') {
    rect(0, 1.4, 2.2, 0.8); line(-0.37, 1.0, -0.37, 1.8); line(0.37, 1.0, 0.37, 1.8); rect(0, 0.3, 1.2, 0.7);
    rect(-1.4, -0.9, 0.8, 0.8); circ(1.5, -1.5, 0.3); circ(1.5, -1.5, 0.15);
  } else { rect(0, 0, 0.8, 3.0); rect(0, 0, 0.6, 2.8); }
  const rot = ((rnd() * 4) | 0) * Math.PI / 2, cs = Math.cos(rot), sn = Math.sin(rot);
  const out = [], cols = [];
  for (const [ax, az, bx, bz] of segs) {
    stroke(out, cols, [ax * cs - az * sn, 0.06, ax * sn + az * cs], [bx * cs - bz * sn, 0.06, bx * sn + bz * cs], { rnd, amp: 0.02, over: 0.03, color: PENCIL });
  }
  { const fc = new THREE.Color(WASH[type] || '#444'); for (let i = 0; i < cols.length; i += 3) { cols[i] = fc.r; cols[i + 1] = fc.g; cols[i + 2] = fc.b; } }
  return lineObj(out, cols, mFurn);
}
function getRoom(r) {
  const k = roomKey(r);
  let o = roomPool.get(k);
  if (!o) {
    const group = new THREE.Group(); group.position.set(wx(r.c), 0, wz(r.r));
    const mat = washProto.clone(); mat.uniforms = { uColor: { value: new THREE.Color(WASH[r.type] || '#ddd') }, uProg: { value: 0 }, uSeed: { value: hashStr(k) % 97 } };
    const wash = new THREE.Mesh(new THREE.PlaneGeometry(CELL, CELL).rotateX(-Math.PI / 2), mat);
    wash.position.y = 0.03; wash.renderOrder = 1; wash.userData.room = r;
    const furn = furniture(r.type, r.id);
    const PH = 0.28;
    mat.visible = false; // wash only serves as the picking target
    furn.visible = false;
    const slabMat = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(WASH[r.type] || '#ddd').lerp(new THREE.Color('#ffffff'), 0.8), emissive: new THREE.Color('#ffffff'), emissiveIntensity: 0.3, roughness: 0.06, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.01, ior: 1.5, reflectivity: 0.9,
      specularIntensity: 0.6, envMapIntensity: 1.1, transparent: true, opacity: 0, depthWrite: false,
    });
    slabMat.userData.base = 0.42;
    const outline = (h, rr) => { const p = new THREE.Path();
      p.moveTo(-h + rr, -h); p.lineTo(h - rr, -h); p.absarc(h - rr, -h + rr, rr, -Math.PI / 2, 0, false);
      p.lineTo(h, h - rr); p.absarc(h - rr, h - rr, rr, 0, Math.PI / 2, false);
      p.lineTo(-h + rr, h); p.absarc(-h + rr, h - rr, rr, Math.PI / 2, Math.PI, false);
      p.lineTo(-h, -h + rr); p.absarc(-h + rr, -h + rr, rr, Math.PI, 1.5 * Math.PI, false);
      return p; };
    const HALF = (CELL - 0.3) / 2, RR = 0.2;
    const shape = new THREE.Shape(outline(HALF, RR).getPoints(10));
    const slab = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: PH, bevelEnabled: false, curveSegments: 10 }).rotateX(-Math.PI / 2), slabMat);
    slab.renderOrder = 1; slab.castShadow = false;
    const edge = (() => {
      const pts = outline(HALF + 0.005, RR).getPoints(10).map(v => new THREE.Vector3(v.x, 0, -v.y)); pts.push(pts[0].clone());
      const mat = new THREE.LineBasicMaterial({ color: 0xffffff });
      const top = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat); top.position.y = PH + 0.005;
      const bot = new THREE.Line(top.geometry.clone(), new THREE.LineBasicMaterial({ color: 0xffffff })); bot.position.y = 0.02;
      top.renderOrder = bot.renderOrder = 2;
      const g = new THREE.Group(); g.add(top, bot); g.userData.top = top; g.userData.bot = bot; g.userData.PH = PH; return g;
    })();
        const rim = new THREE.Object3D(); rim.material = { opacity: 0 };
    const PAL = ['#ff2d55', '#1e90ff', '#ffd60a', '#ff8a00', '#000000'];
    const chip = new THREE.Group();
    const ICON = { bedroom: '#ffe14a', bathroom: '#1e6bff', kitchen: '#1e6bff', living: '#1e6bff', hallway: '#ffe14a' };
    const col = r.type === 'bedroom' ? new THREE.Color('#ff9fb3') : slabMat.color.clone(), col2 = col;
    const gm = c => new THREE.MeshPhysicalMaterial({ color: c, emissive: '#ffffff', emissiveIntensity: 0.12, roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.15, envMapIntensity: 0.7 });
    const part = (w, h, d, x, z, c, rad = 0.1, y = 0) => { const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 4, Math.min(rad, h / 2, w / 2, d / 2)), gm(c)); m.position.set(x, 0.15 + y, z); chip.add(m); return m; };
    if (r.type === 'bedroom') { part(1.7, 0.9, 2.2, 0, 0.1, col, 0.15, 0.3); part(1.9, 1.4, 0.3, 0, -1.05, col, 0.1, 0.55); part(0.65, 0.4, 0.55, -0.45, -0.55, col2, 0.15, 1.1); part(0.65, 0.4, 0.55, 0.45, -0.55, col2, 0.15, 1.1); }
    else if (r.type === 'bathroom') {
      // three embossed water drops
      const shapes = [];
      for (const [dx, dy, sc] of [[0, 0.45, 0.8], [-0.7, -0.5, 0.65], [0.7, -0.5, 0.65]]) {
        const d = new THREE.Shape();
        d.moveTo(dx, dy + 0.95 * sc);
        d.bezierCurveTo(dx + 0.15 * sc, dy + 0.55 * sc, dx + 0.6 * sc, dy + 0.15 * sc, dx + 0.6 * sc, dy - 0.25 * sc);
        d.absarc(dx, dy - 0.25 * sc, 0.6 * sc, 0, Math.PI, true);
        d.bezierCurveTo(dx - 0.6 * sc, dy + 0.15 * sc, dx - 0.15 * sc, dy + 0.55 * sc, dx, dy + 0.95 * sc);
        shapes.push(d);
      }
      const eg = new THREE.ExtrudeGeometry(shapes, { depth: 0.9, bevelEnabled: true, bevelThickness: 0.25, bevelSize: 0.07, bevelSegments: 4, curveSegments: 20 });
      eg.rotateX(-Math.PI / 2);
      const em = new THREE.Mesh(eg, new THREE.MeshPhysicalMaterial({ color: '#9cc8ff', emissive: '#ffffff', emissiveIntensity: 0.12, roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.15, envMapIntensity: 0.7 }));
      em.position.set(0, 0, 0); chip.add(em);
    }
    else if (r.type === 'kitchen') { part(2.4, 0.3, 0.7, 0, -0.9, col, 0.1); part(0.6, 0.12, 0.6, -0.6, -0.9, col2, 0.28, 0.2); part(0.6, 0.12, 0.6, 0.6, -0.9, col2, 0.28, 0.2); part(1.2, 0.26, 0.9, 0, 0.5, col, 0.12); }
    else if (r.type === 'living') { part(2.0, 0.3, 0.8, 0, 0.6, col, 0.14); part(2.0, 0.2, 0.3, 0, 0.2, col2, 0.1, 0.2); part(0.9, 0.2, 0.9, 0, -0.7, col2, 0.4); }
    else { part(0.8, 0.14, 2.4, 0, 0, col, 0.07); }
    chip.scale.set(0.34, 0.1, 0.34); chip.position.set(-1.0, PH - 0.07, 1.15);
    const cv = document.createElement('canvas'); cv.width = 512; cv.height = 128;
    const cx2 = cv.getContext('2d'); cx2.fillStyle = '#16181f'; cx2.font = '600 54px "Segoe UI", Helvetica, Arial, sans-serif'; cx2.textBaseline = 'middle';
    cx2.fillText(r.type[0].toUpperCase() + r.type.slice(1), 8, 50);
    cx2.fillStyle = '#6b7080'; cx2.font = '38px "Segoe UI", Helvetica, Arial, sans-serif'; cx2.fillText(r.id, 8, 100); // ids already read R12
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    const label = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.6).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
    label.position.set(-0.55, PH + 0.06, -1.4); label.renderOrder = 5;
    group.add(slab, edge, rim, wash, furn, chip, label); scene.add(group);
    o = { group, wash, furn, chip, label, mat, slab, edge, slabMat, rim, room: r }; roomPool.set(k, o);
  }
  return o;
}
function setDraw(line, f) { const g = line.geometry; g.setDrawRange(0, Math.ceil(g.attributes.position.count * f)); }
function setRoom(o, washP, furnP) {
  o.shown = true;
  const li = (o.room.r * LN + o.room.c) * 4, lc = o.mat.uniforms.uColor.value;
  lightData[li] = lc.r * 255; lightData[li + 1] = lc.g * 255; lightData[li + 2] = lc.b * 255; lightData[li + 3] = Math.max(0, Math.min(1, washP)) * 255;
  o.group.visible = washP > 0.001 || furnP > 0.001;
  o.mat.uniforms.uProg.value = o.room.fresh ? clamp(washP / 0.8) : washP;
  o.wash.visible = washP > 0.001;
  o.wp = washP; o.slabMat.emissive.set('#ffffff'); o.slabMat.emissiveIntensity = 0.3; o.edge.userData.top.material.color.set(o.room.fresh === 'all' ? '#e00000' : o.room.fresh ? NEW : '#ffffff'); const rise = o.room.fresh ? clamp(washP / 0.45) : clamp(washP / 0.6), fill = rise; const hall = o.room.type === "hallway"; o.label.visible = washP > 0.85 && !hall; o.chip.visible = false; o.slab.visible = o.edge.visible = !hall; o.slab.scale.y = Math.max(0.001, rise); o.edge.userData.top.position.y = 0.005 + o.edge.userData.PH * rise; setDraw(o.edge.userData.top, o.room.fresh ? clamp((washP - 0.55) / 0.45) : 1); o.fill = fill; o.slabMat.opacity = o.slabMat.userData.base * fill; o.rim.material.opacity = 0.8 * Math.min(1, washP * 3);
  o.furn.visible = false;
  o.furn.geometry.instanceCount = Math.ceil(o.furn.userData.n * furnP);
}

// ---------- transition plan between two frames ----------
function planFor(i) {
  if (planMemo.has(i)) return planMemo.get(i);
  const iA = frameInfo(frames[i]), iB = frameInfo(frames[i + 1]);
  const walls = [], gone = [], statics = new Set();
  const pending = [];
  iB.walls.forEach((w, k) => { const a = iA.walls.get(k); if (a && a.sig === w.sig) { walls.push({ spec: w, kind: 'static' }); w.geom.nodes.forEach(n => statics.add(n)); } else pending.push(w); });
  iA.walls.forEach((w, k) => { if (!iB.walls.has(k)) gone.push(w); });
  const built = new Set(statics), timing = new Map();
  const waves = [];
  while (pending.length) {
    let wave = pending.filter(w => w.geom.nodes.some(n => built.has(n)));
    if (!wave.length) { wave = [pending[0]]; built.add(pending[0].geom.nodes[0]); }
    wave.forEach(w => pending.splice(pending.indexOf(w), 1));
    waves.push(wave);
    wave.forEach(w => w.geom.nodes.forEach(n => built.add(n)));
  }
  const W = waves.length, dur = W > 1 ? Math.min(0.34, 0.5) : 0.4;
  waves.forEach((wave, wi) => {
    const t0 = W > 1 ? 0.14 + wi * (0.62 - dur) / (W - 1) : 0.2;
    wave.forEach(w => {
      const anchor = statics.has(w.geom.nodes[0]) || !statics.has(w.geom.nodes[1]) ? 0 : 1;
      const e = { spec: w, kind: 'new', anchor: waveAnchor(w, wi, waves, statics), t0, t1: t0 + dur };
      walls.push(e); timing.set(w.key, e);
    });
  });
  const rooms = [];
  const hadRoom = new Set(iA.cells.size ? [...iA.cells.values()].map(roomKey) : []);
  const haveRoom = new Set([...iB.cells.values()].map(roomKey));
  iB.cells.forEach(r => {
    if (hadRoom.has(roomKey(r))) { rooms.push({ r, kind: 'static' }); return; }
    let t = 0.4;
    for (let d = 0; d < 4; d++) { const e = timing.get(sideKey(r.r, r.c, d)); if (e) t = Math.max(t, e.t1); }
    rooms.push({ r, kind: 'new', t0: Math.min(t, 0.68) });
  });
  iA.cells.forEach(r => { if (!haveRoom.has(roomKey(r))) rooms.push({ r, kind: 'gone' }); });
  const plan = { walls, gone, rooms };
  planMemo.set(i, plan);
  return plan;
}
// which end the wall starts growing from: the end that already touches built structure
function waveAnchor(w, wi, waves, statics) {
  const earlier = new Set(statics);
  for (let k = 0; k < wi; k++) waves[k].forEach(x => x.geom.nodes.forEach(n => earlier.add(n)));
  const [n0, n1] = w.geom.nodes;
  return earlier.has(n0) || !earlier.has(n1) ? 0 : 1;
}

// thin coloured rails with ring nodes joining neighbouring rooms
const railMat = mkLine(1.8);
let railObj = null;
const NEW = '#ff8a00';
const ringGeo = new THREE.TorusGeometry(0.22, 0.05, 8, 24).rotateX(Math.PI / 2);
const ringPool = [];
let gridOnly = false, gv = 0; // only the connecting grid: blades and walls sink away, rings grow, hallways lose theirs; gv runs 0..1 between the views
const glowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 60);
  gr.addColorStop(0, 'rgba(255,255,255,0.95)'); gr.addColorStop(0.3, 'rgba(255,255,255,0.6)'); gr.addColorStop(0.65, 'rgba(255,255,255,0.15)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.clearRect(0, 0, 128, 128); g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();

const GRID_DUR = 0.6, GRID_RING = 1.7; // seconds the change of view takes; how much bigger the rings get in the grid view
function ringScale(m) {
  const e = easeInOut(gv), sc = m.userData.base * (m.userData.hall ? 1 - e : 1 + (GRID_RING - 1) * e);
  m.visible = m.userData.on && sc > 0.01; m.scale.setScalar(Math.max(0.01, sc));
}
function applyGridView() { // the blades (with their outlines and labels) and the walls sink and fade as gv goes to 1
  const k = 1 - easeInOut(gv), h = Math.max(0.001, k);
  roomPool.forEach(o => {
    o.group.scale.y = h; o.slabMat.opacity = o.slabMat.userData.base * (o.fill ?? 1) * k; o.label.material.opacity = k; // scales and fades what setRoom shows, hides nothing it shows
    o.edge.children.forEach(l => { if (l.material.transparent !== (k < 1)) { l.material.transparent = k < 1; l.material.needsUpdate = true; } l.material.opacity = k; });
  });
  wallPool.forEach(o => { o.group.scale.y = h; });
  [mWall, mFlat].forEach(m => { if (m.transparent !== (k < 1)) { m.transparent = k < 1; m.needsUpdate = true; } m.opacity = k; });
  if (gv > 0) burstPool.forEach(m => { m.visible = false; });
  ringPool.forEach(m => { if (m.userData.base !== undefined) ringScale(m); });
}
function updateRails(i, animating, p = 1) {
  const vis = new Map(); roomPool.forEach(o => { if (o.shown && o.group.visible) vis.set(o.room.r + ',' + o.room.c, o); });
  const BLACK = new THREE.Color('#000000'), tone = () => BLACK.clone(), out = [], cols = [], Y = 0.14; let ri = 0;
  const pos = o => [wx(o.room.c), wz(o.room.r)];
  vis.forEach(o => {
    let m = ringPool[ri]; if (!m) { m = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: 0x000000 })); ringPool.push(m);
      m.userData.glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: 0.8, depthTest: false, depthWrite: false })); m.userData.glow.renderOrder = 3; m.userData.glow.scale.set(3.0, 3.0, 1); m.userData.glow.visible = false; scene.add(m, m.userData.glow); }
    ri++; m.userData.on = (o.wp ?? 1) >= 0.3; m.userData.base = Math.max(0.01, clamp(((o.wp ?? 1) - 0.3) / 0.2)); m.userData.hall = o.room.type === 'hallway'; ringScale(m); m.material.color.copy(tone(o.room.type)); const [x, z] = pos(o); m.position.set(x, Y, z);
    const gl = m.userData.glow; gl.visible = false; gl.material.color.set(WASH[o.room.type] || '#444'); gl.position.set(x, Y, z);
  });
  const seen = new Set(), lid = (ca, cb) => ca.join() + '|' + cb.join(), before = new Set();
  if (animating && frames[i]) frameInfo(frames[i]).links.forEach(([ca, cb]) => before.add(lid(ca, cb)));
  const after = new Set(); frameInfo(frames[animating ? i + 1 : i] || frames[i]).links.forEach(([ca, cb]) => after.add(lid(ca, cb)));
  // only links the script defines: the destination frame's links grow in, links it drops shrink away early
  for (const k of animating ? [i, i + 1] : [i]) {
    const f = frames[k]; if (!f) continue;
    for (const [ca, cb] of frameInfo(f).links) {
      const a = vis.get(ca.join()), b = vis.get(cb.join()), id = lid(ca, cb);
      if (!a || !b || seen.has(id)) continue; seen.add(id);
      const kept = after.has(id), isNew = animating && !before.has(id);
      if (!kept && !animating) continue;
      const [x1, z1] = pos(a), [x2, z2] = pos(b), hall = a.room.type === 'hallway' || b.room.type === 'hallway', c1 = hall ? tone('hallway') : tone(a.room.type), c2 = hall ? c1 : tone(b.room.type);
      const wa = a.wp ?? 1, wb = b.wp ?? 1;
      let g = clamp((Math.min(wa, wb) - 0.5) / 0.5);
      if (!kept) g = Math.min(g, 1 - clamp(p / 0.2));
      else if (isNew && Math.min(wa, wb) >= 1) g = clamp((p - 0.55) / 0.3);
      if (g <= 0) continue;
      if (wa <= wb) { const e = c1.clone().lerp(c2, g); out.push(x1, Y, z1, x1 + (x2 - x1) * g, Y, z1 + (z2 - z1) * g); cols.push(c1.r, c1.g, c1.b, e.r, e.g, e.b); }
      else { const e = c2.clone().lerp(c1, g); out.push(x2, Y, z2, x2 + (x1 - x2) * g, Y, z2 + (z1 - z2) * g); cols.push(c2.r, c2.g, c2.b, e.r, e.g, e.b); }
    }
  }
  for (let q = ri; q < ringPool.length; q++) { ringPool[q].visible = ringPool[q].userData.glow.visible = false; ringPool[q].userData.on = false; } // a spare ring stays hidden in the grid view too
  if (railObj) { scene.remove(railObj); railObj.geometry.dispose(); railObj = null; }
  if (out.length) { railObj = lineObj(out, cols, railMat); railObj.renderOrder = 4; scene.add(railObj); }
}

// announce effect: the footprint of a new blade is drawn on the floor just before it rises
const GROW = 0.12, BURST = 0.22, BLADE_R = (CELL - 0.3) / 2;
// circle that squares up into the blade outline (superellipse)
const BURST_PTS = 65;
function shapeBurst(m, r, sq) {
  const pos = m.geometry.attributes.position, e = 2 / (2 + 6 * sq);
  for (let k = 0; k < BURST_PTS; k++) {
    const a = k / (BURST_PTS - 1) * Math.PI * 2, c = Math.cos(a), s = Math.sin(a);
    pos.setXYZ(k, r * Math.sign(c) * Math.pow(Math.abs(c), e), 0, r * Math.sign(s) * Math.pow(Math.abs(s), e));
  }
  pos.needsUpdate = true;
}
const burstPool = [];
function burstNeighbours(plan, p) {
  let n = 0;
  plan.rooms.forEach(e => {
    if (e.kind !== 'new' || e.r.type === 'hallway') return;
    // a dot grows and squares up into the blade footprint; the blade's own bottom edge then takes over
    const u = (p - (e.t0 - BURST - GROW)) / (BURST + GROW);
    if (u <= 0 || u >= 1) return;
    const grow = 1 - Math.pow(1 - u, 2);
    let m = burstPool[n]; if (!m) { m = new THREE.Line(new THREE.BufferGeometry().setFromPoints(Array.from({ length: BURST_PTS }, () => new THREE.Vector3())), new THREE.LineBasicMaterial({ color: 0xffffff, depthTest: false })); m.renderOrder = 5; m.frustumCulled = false; scene.add(m); burstPool.push(m); }
    n++; m.visible = true; m.position.set(wx(e.r.c), 0.02, wz(e.r.r));
    shapeBurst(m, Math.max(0.01, BLADE_R * grow), grow);
  });
  for (let q = n; q < burstPool.length; q++) burstPool[q].visible = false;
}

// ---------- apply a state to the scene ----------
function applyState(i, p, animating) {
  wallPool.forEach(o => { o.shown = false; });
  roomPool.forEach(o => { o.shown = false });
  lightData.fill(0);
  if (!animating) {
    const info = frameInfo(frames[i]);
    info.walls.forEach(w => setWall(getWall(w), 1, 0, false));
    info.cells.forEach(r => setRoom(getRoom(r), 1, 1));
  } else {
    const plan = planFor(i);
    plan.walls.forEach(e => {
      const o = getWall(e.spec);
      if (e.kind === 'static') setWall(o, 1, 0, false);
      else setWall(o, clamp((p - e.t0) / (e.t1 - e.t0)), e.anchor, false);
    });
    plan.gone.forEach(w => setWall(getWall(w), 1 - clamp(p / 0.2), 0, true));
    plan.rooms.forEach(e => {
      const o = getRoom(e.r);
      if (e.kind === 'static') setRoom(o, 1, 1);
      else if (e.kind === 'gone') setRoom(o, 1 - clamp(p / 0.2), 1 - clamp(p / 0.15));
      else setRoom(o, clamp((p - e.t0) / 0.3), clamp((p - e.t0 - 0.12) / 0.25));
    });
  }
  wallPool.forEach(o => { if (!o.shown) o.group.visible = false; });
  roomPool.forEach(o => { if (!o.shown) o.group.visible = false; });
  lightTex.needsUpdate = true;
  wallPool.forEach(o => { o.group.visible = false; });
  if (animating) burstNeighbours(planFor(i), p); else burstPool.forEach(m => { m.visible = false; });
  updateRails(i, animating, p);
}

// ---------- playback ----------
const BASE_DUR = 4.5;
const st = { cur: 0, T: 0, intro: false, anim: false, playing: false, once: false, speed: 2 };
function setFrame(i) {
  st.cur = clamp(i, 0, frames.length - 1); st.T = 0; st.anim = false; st.intro = false; st.once = false;
  $('scrub').value = st.cur;
  applyState(st.cur, 0, false); updateInfo();
}
// the seed house builds up room by room, spreading outwards along the links
const INTRO_DUR = 9;
function applyIntro(p) {
  const info = frameInfo(frames[0]), cells = [...info.cells.values()], key = r => r.r + ',' + r.c, adj = new Map(), order = [], seen = new Set();
  cells.forEach(r => adj.set(key(r), []));
  info.links.forEach(([a, b]) => { adj.get(a.join())?.push(b.join()); adj.get(b.join())?.push(a.join()); });
  const byKey = new Map(cells.map(r => [key(r), r]));
  for (const r of cells) {
    if (seen.has(key(r))) continue;
    const q = [key(r)]; seen.add(key(r));
    while (q.length) { const k = q.shift(); order.push(byKey.get(k)); (adj.get(k) || []).forEach(n => { if (!seen.has(n)) { seen.add(n); q.push(n); } }); }
  }
  wallPool.forEach(o => { o.shown = false; }); roomPool.forEach(o => { o.shown = false });
  lightData.fill(0);
  const N = order.length;
  order.forEach((r, k) => setRoom(getRoom(r), clamp((p - 0.7 * k / N) / 0.3), clamp((p - 0.7 * k / N - 0.1) / 0.3)));
  roomPool.forEach(o => { if (!o.shown) o.group.visible = false; });
  lightTex.needsUpdate = true;
  wallPool.forEach(o => { o.group.visible = false; });
  updateRails(0, false);
}
function startIntro() { st.intro = true; st.T = 0; st.anim = false; applyIntro(0); }
function startTransition(once) {
  if (st.cur >= frames.length - 1) { st.playing = false; syncPlay(); return false; }
  st.anim = true; st.T = 0; st.once = once; return true;
}
function syncPlay() { $('play').textContent = st.playing ? '⏸ Pause' : '▶ Play'; }
function updateInfo() {
  const f = frames[st.cur], prev = frames[Math.max(0, st.cur - 1)];
  const had = new Set(prev.rooms.map(roomKey)), has = new Set(f.rooms.map(roomKey));
  const real = r => r.type !== 'hallway', nRooms = f.rooms.filter(real).length;
  const add = f.rooms.filter(r => real(r) && !had.has(roomKey(r))).length, rem = prev.rooms.filter(r => real(r) && !has.has(roomKey(r))).length;
  $('call').textContent = f.call === 'seed' ? 'Seed house' : `${f.call}  ·  ${f.label}`;
  $('request').textContent = f.request || '';
  if (EMBED) parent.postMessage({ info: { call: f.call, rooms: nRooms, cur: st.cur, n: frames.length, scores: f.scores } }, '*');
  $('stats').innerHTML = `<b>${nRooms}</b> rooms` + (st.cur ? ` &nbsp; <span class="muted">+${add} / −${rem} this step</span>` : '') +
    ` &nbsp; <span class="muted">sheet ${st.cur + 1}/${frames.length}</span>`;
}

// ---------- camera ----------
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.09;
controls.minDistance = 22; controls.maxDistance = 260; controls.minPolarAngle = 0.001; controls.maxPolarAngle = Math.PI / 2 - 0.03;
controls.screenSpacePanning = false;
const DMIN = 25, DMAX = 260;
function syncCamSliders() {
  const off = camera.position.clone().sub(controls.target), d = off.length();
  $('zoom').value = 1000 * Math.log(DMAX / d) / Math.log(DMAX / DMIN);
  $('rot').value = Math.atan2(off.x, off.z) * 180 / Math.PI;
  $('tilt').value = 90 - Math.acos(clamp(off.y / d, -1, 1)) * 180 / Math.PI;
}
function placeCam(d, azDeg, elDeg) {
  const az = azDeg * Math.PI / 180, el = elDeg * Math.PI / 180;
  camera.position.set(Math.sin(az) * Math.cos(el) * d, Math.sin(el) * d, Math.cos(az) * Math.cos(el) * d).add(controls.target);
  controls.update();
}
function camFromSliders() { placeCam(DMAX * Math.pow(DMIN / DMAX, $('zoom').value / 1000), +$('rot').value, +$('tilt').value); }
controls.addEventListener('change', syncCamSliders);
['zoom', 'rot', 'tilt'].forEach(id => $(id).addEventListener('input', camFromSliders));
function resetView() {
  const rs = frames[frames.length - 1].rooms;
  const cx = rs.reduce((s, r) => s + wx(r.c), 0) / rs.length, cz = rs.reduce((s, r) => s + wz(r.r), 0) / rs.length;
  controls.target.set(cx, 0, cz); placeCam(205 * Math.max(1, 1.6 / (innerWidth / innerHeight)) * (EMBED ? 0.7 : 1), 0, 89); syncCamSliders();
}

// ---------- tooltip ----------
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
renderer.domElement.addEventListener('pointermove', e => {
  mouse.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const targets = []; roomPool.forEach(o => { if (o.group.visible && o.wash.visible) targets.push(o.wash); });
  const hit = ray.intersectObjects(targets, false)[0], tip = $('tip');
  if (hit) {
    const r = hit.object.userData.room;
    tip.textContent = `${r.id} · ${r.type} · ${String.fromCharCode(65 + r.r)}${r.c + 1}`;
    tip.style.display = 'block'; tip.style.left = e.clientX + 14 + 'px'; tip.style.top = e.clientY + 14 + 'px';
  } else tip.style.display = 'none';
});

// grid-only switch: a small blade left of the house's first row, with the icon on top; a click turns the grid view on or off
const gridIcon = (() => {
  const S = 1.3, RR = 0.2, PH = 0.28, g = new THREE.Group();
  const p = new THREE.Path(); // a rounded square, as the room blades
  p.moveTo(-S + RR, -S); p.lineTo(S - RR, -S); p.absarc(S - RR, -S + RR, RR, -Math.PI / 2, 0, false);
  p.lineTo(S, S - RR); p.absarc(S - RR, S - RR, RR, 0, Math.PI / 2, false);
  p.lineTo(-S + RR, S); p.absarc(-S + RR, S - RR, RR, Math.PI / 2, Math.PI, false);
  p.lineTo(-S, -S + RR); p.absarc(-S + RR, -S + RR, RR, Math.PI, 1.5 * Math.PI, false);
  const pts = p.getPoints(10);
  const slab = new THREE.Mesh(new THREE.ExtrudeGeometry(new THREE.Shape(pts), { depth: PH, bevelEnabled: false, curveSegments: 10 }).rotateX(-Math.PI / 2),
    new THREE.MeshPhysicalMaterial({ color: '#f1f2f5', emissive: '#ffffff', emissiveIntensity: 0.3, roughness: 0.06, clearcoat: 1, clearcoatRoughness: 0.01,
      transparent: true, opacity: 0.6, depthWrite: false }));
  slab.renderOrder = 1;
  const rim = new THREE.Line(new THREE.BufferGeometry().setFromPoints([...pts, pts[0]].map(v => new THREE.Vector3(v.x, 0, -v.y))), new THREE.LineBasicMaterial({ color: 0xffffff }));
  rim.position.y = PH + 0.005; rim.renderOrder = 2;
  const cv = document.createElement('canvas'); cv.width = cv.height = 128;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  const icon = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 1.9).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
  icon.position.y = PH + 0.02; icon.renderOrder = 6;
  g.add(slab, rim, icon); g.userData = { cv, tex, drawn: null, slab, rim, icon, PH, t: 0 }; scene.add(g); return g;
})();
function drawGridIcon() { // three by three rooms joined by doors: faint grey when off, solid grey when on
  const { cv, tex } = gridIcon.userData, g = cv.getContext('2d'), col = gridOnly ? '#5f6573' : 'rgba(95,101,115,0.45)', P = [24, 64, 104];
  g.clearRect(0, 0, 128, 128); g.strokeStyle = col; g.lineWidth = 6; g.lineCap = 'round';
  g.beginPath(); P.forEach(v => { g.moveTo(P[0], v); g.lineTo(P[2], v); g.moveTo(v, P[0]); g.lineTo(v, P[2]); }); g.stroke();
  g.fillStyle = gridOnly ? '#5f6573' : '#f1f2f5';
  P.forEach(x => P.forEach(y => { g.beginPath(); g.arc(x, y, 11, 0, 2 * Math.PI); g.fill(); g.stroke(); }));
  tex.needsUpdate = true; gridIcon.userData.drawn = gridOnly;
}
const ICON_GROW = 1.1; // seconds the switch's blade takes to grow
function growGridBlade(dt) { // once the seed house has fully grown in, the blade grows, then the icon on it, both from their centre; a new intro starts it again
  const u = gridIcon.userData;
  u.t = st.intro ? 0 : Math.min(1, u.t + dt * st.speed / ICON_GROW);
  const w = easeOut(clamp(u.t / 0.4)), hgt = easeOut(clamp((u.t - 0.3) / 0.4)), ic = easeOut(clamp((u.t - 0.65) / 0.35));
  u.slab.visible = w > 0.001; u.slab.scale.set(Math.max(0.001, w), Math.max(0.001, hgt), Math.max(0.001, w));
  u.rim.visible = hgt > 0.95; u.icon.position.y = u.PH + 0.02;
  u.icon.visible = ic > 0.001; u.icon.scale.set(Math.max(0.001, ic), 1, Math.max(0.001, ic));
}
function placeGridIcon() {
  const f = frames && frames[st.cur]; if (!f || !f.rooms.length) return;
  gridIcon.position.x = Math.min(...f.rooms.map(r => wx(r.c))) - CELL * 1.1; gridIcon.position.z = Math.min(...f.rooms.map(r => wz(r.r)));
  if (gridIcon.userData.drawn !== gridOnly) drawGridIcon();
}
let downAt = null;
const overIcon = e => { mouse.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(mouse, camera); return ray.intersectObject(gridIcon, true).length > 0; };
renderer.domElement.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (downAt && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) < 5 && overIcon(e)) {
    gridOnly = !gridOnly; drawGridIcon(); if (EMBED) parent.postMessage({ gridOnly }, '*');
  }
  downAt = null;
});
renderer.domElement.addEventListener('pointermove', e => { renderer.domElement.style.cursor = overIcon(e) ? 'pointer' : ''; });

// embed: frame the house being shown, filling the screen, and zoom out smoothly as it grows (until the user moves the camera)
let autoFit = true, fitSnap = true;
controls.addEventListener('start', () => { autoFit = false; });
function fitToHouse(dt) {
  const fs = st.intro ? [frames[0]] : st.anim ? [frames[st.cur], frames[st.cur + 1]] : [frames[st.cur]];
  let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
  fs.forEach(f => f && f.rooms.forEach(r => { x0 = Math.min(x0, wx(r.c)); x1 = Math.max(x1, wx(r.c)); z0 = Math.min(z0, wz(r.r)); z1 = Math.max(z1, wz(r.r)); }));
  if (x0 > x1) return;
  const hw = (x1 - x0) / 2 + CELL / 2, hh = (z1 - z0) / 2 + CELL / 2, t = Math.tan(camera.fov * Math.PI / 360);
  const d = Math.min(DMAX, Math.max(DMIN, Math.max(hw / (t * camera.aspect * 0.8), hh / (t * 0.62)))), k = fitSnap ? 1 : 1 - Math.exp(-dt * 3);
  fitSnap = false;
  const cur = camera.position.clone().sub(controls.target).length();
  controls.target.x += ((x0 + x1) / 2 - controls.target.x) * k; controls.target.z += ((z0 + z1) / 2 - controls.target.z) * k;
  placeCam(cur + (d - cur) * k, 0, 89);
}

// ---------- main loop ----------
let last = performance.now();
function loop(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (st.intro) {
    st.T += dt * st.speed / INTRO_DUR;
    if (st.T >= 1) setFrame(0); else applyIntro(st.T);
  } else if (st.playing && !st.anim) startTransition(false);
  if (st.anim) {
    st.T += dt * st.speed / BASE_DUR;
    if (st.T >= 1) {
      const wasOnce = st.once, next = st.cur + 1;
      setFrame(next);
      if (!wasOnce && st.playing) { if (!startTransition(false)) { st.playing = false; syncPlay(); } }
      else { st.playing = false; syncPlay(); }
    } else { applyState(st.cur, st.T, true); }
  }
  const gt = gridOnly ? 1 : 0;
  if (gv !== gt || gv > 0) { gv = gt > gv ? Math.min(gt, gv + dt / GRID_DUR) : Math.max(gt, gv - dt / GRID_DUR); applyGridView(); }
  placeGridIcon(); growGridBlade(dt);
  if (EMBED && autoFit) fitToHouse(dt);
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(loop);
}

// ---------- wiring ----------
const Q = new URLSearchParams(location.search), EMBED = Q.has('embed');
if (EMBED) document.body.classList.add('embed');
const TAG = /^(.+?-\w+)-h(\d+)-c(\d+)-(\w+)$/;
let curHouse, curChain;
// Group a house's frames into chains by parsing each frame's run label; the seed starts every chain.
function chainsOf(k) {
  const all = data.houses[k], seed = all[0], by = new Map();
  for (const f of all.slice(1)) {
    const m = TAG.exec(f.tag || ''); const kind = (m ? m[4] : f.call).startsWith('all') ? 'all' : 'step', key = m ? `${m[1]}-c${m[3]}-${kind}` : 'run';
    if (!by.has(key)) by.set(key, { key, name: m ? `${m[1].split('-')[0]} · c${m[3]} · ${kind === 'all' ? 'all-at-once' : 'incremental'}` : 'run', steps: new Map() });
    by.get(key).steps.set(m ? m[4] : f.call, f);
  }
  return [...by.values()].sort((a, b) => a.key.replace(/-(step|all)$/, '').localeCompare(b.key.replace(/-(step|all)$/, ''), undefined, { numeric: true }) || b.key.localeCompare(a.key)).map(c => ({ key: c.key, name: c.name, frames: [seed, ...[...c.steps.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(e => e[1])] }));
}
function loadHouse(k, chainKey) {
  curHouse = k; const chains = chainsOf(k), ch = chains.find(c => c.key === chainKey) || chains[0]; curChain = ch.key;
  $('chains').innerHTML = ''; chains.forEach(c => { const b = document.createElement('button'); b.textContent = c.name; b.title = c.key; b.classList.toggle('on', c.key === curChain); b.onclick = () => { loadHouse(k, c.key); resetView(); }; $('chains').appendChild(b); });
  frames = ch.frames;
  planMemo = new Map();
  frames.forEach(f => delete f._info);
  wallPool.forEach(o => { scene.remove(o.group); disposeObj(o.group); }); wallPool.clear();
  roomPool.forEach(o => { scene.remove(o.group); disposeObj(o.group); o.mat.dispose(); }); roomPool.clear();
  $('scrub').max = frames.length - 1;
  st.playing = false; syncPlay();
  setFrame(0); startIntro();
}
$('house').onchange = e => { loadHouse(e.target.value); resetView(); markHouse(e.target.value); };
$('scrub').oninput = e => { st.playing = false; syncPlay(); setFrame(+e.target.value); };
$('first').onclick = () => { st.playing = false; syncPlay(); setFrame(0); startIntro(); };
$('last').onclick = () => { st.playing = false; syncPlay(); setFrame(frames.length - 1); };
$('back').onclick = () => { st.playing = false; syncPlay(); setFrame(st.cur - (st.anim ? 0 : 1)); };
$('fwd').onclick = () => { st.playing = false; syncPlay(); if (st.intro) setFrame(0); if (st.anim) setFrame(st.cur + 1); else startTransition(true); };
$('play').onclick = () => { if (!st.playing && st.cur >= frames.length - 1) { setFrame(0); startIntro(); } st.playing = !st.playing; syncPlay(); };
const syncSpeed = () => { st.speed = Math.pow(2, +$('speed').value); $('speedVal').textContent = st.speed.toFixed(2) + '×'; };
$('speed').oninput = syncSpeed; syncSpeed();
addEventListener('keydown', e => {
  if (e.target.tagName === 'SELECT') return;
  if (e.code === 'Space') { e.preventDefault(); $('play').click(); }
  else if (e.code === 'ArrowRight') $('fwd').click();
  else if (e.code === 'ArrowLeft') $('back').click();
});
// the glass panel covers the bottom of the screen, so shift the picture up
function fitView() {
  const h = $('bar').offsetHeight + 22;
  camera.aspect = innerWidth / innerHeight;
  camera.setViewOffset(innerWidth, innerHeight, 0, h * 0.5, innerWidth, innerHeight);
  camera.updateProjectionMatrix();
}
addEventListener('resize', () => {
  renderer.setSize(innerWidth, innerHeight); fitView();
  lineMats.forEach(m => m.resolution.set(innerWidth, innerHeight));
});

data = await (await fetch(EMBED && Q.get('data') || 'data.json', { cache: 'no-cache' })).json();
$('source').textContent = `run folder: ${data.source}`;
Object.keys(data.houses).forEach(k => { const o = document.createElement('option'); o.value = k; o.textContent = `House ${k}`; $('house').appendChild(o); });
const hb = $('houses');
let markHouse;
Object.keys(data.houses).forEach(k => { const b = document.createElement('button'); b.dataset.k = k; b.title = `House ${k}`;
  b.innerHTML = `<svg viewBox="0 0 24 24"><path d="M3 11 12 3l9 8M5 9.5V20h14V9.5M10 20v-6h4v6"/></svg>${k}`;
  b.onclick = () => { $('house').value = k; $('house').onchange({ target: $('house') }); };
  hb.appendChild(b); });
markHouse = k => [...hb.children].forEach(b => b.classList.toggle('on', b.dataset.k === String(k)));
const h0 = EMBED && Q.get('house') || Object.keys(data.houses)[0];
loadHouse(h0, EMBED ? Q.get('chain') : undefined);
markHouse(h0);
let custom = false;
if (EMBED) {
  addEventListener('message', e => {
    const m = e.data || {};
    if (m.speed) st.speed = m.speed;
    if ('gridOnly' in m) gridOnly = m.gridOnly; // the main loop animates the change of view
    if (m.light) { // direction the light comes from: azimuth/elevation in degrees, plus the sun and ambient strengths
      const az = m.light.az * Math.PI / 180, el = m.light.el * Math.PI / 180;
      SUN.set(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
      sun.position.copy(SUN).multiplyScalar(160); sun.intensity = m.light.sun; ambient.intensity = m.light.amb;
    }
    if (m.snapshot) { renderer.render(scene, camera); parent.postMessage({ snapshot: renderer.domElement.toDataURL('image/png') }, '*'); }
    if (m.frames) { // the parent hands over the frames to show (copy of the left house, destroyed house, result)
      custom = true; frames = m.frames; planMemo = new Map();
      wallPool.forEach(o => { scene.remove(o.group); disposeObj(o.group); }); wallPool.clear();
      roomPool.forEach(o => { scene.remove(o.group); disposeObj(o.group); o.mat.dispose(); }); roomPool.clear();
      $('scrub').max = frames.length - 1; st.playing = false; setFrame(0); if (m.intro) startIntro();
    }
    if (m.goto !== undefined && !m.frames) {
      const i = clamp(m.goto, 0, frames.length - 1);
      if (!custom && i > 0) { // incremental pane: highlight everything added since the seed
        const bk = new Set(frames[0].rooms.map(r => `${r.r},${r.c}:${r.type}`));
        frames[i].rooms.forEach(r => { r.fresh = !bk.has(`${r.r},${r.c}:${r.type}`); });
      }
      if (m.animate && i === st.cur + 1 && !st.anim && !st.intro) startTransition(true); else setFrame(i);
    }
  });
  parent.postMessage({ ready: true }, '*');
}
resetView();
fitView();
window.__viewer = { st, setFrame, startTransition, scene, camera, controls, planFor, applyState };
requestAnimationFrame(loop);
