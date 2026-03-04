import { useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import * as THREE from "three";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthPage from "./pages/auth/AuthPage";

// ─── Shaders ─────────────────────────────────────────────────────────────────

const earthVert = `
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
void main() {
  vec4 mp = modelMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * viewMatrix * mp;
  vNormal = (modelMatrix * vec4(normal, 0.0)).xyz;
  vUv = uv;
  vPosition = mp.xyz;
}`;

const earthFrag = `
uniform sampler2D uDay;
uniform sampler2D uNight;
uniform sampler2D uClouds;
uniform vec3 uSun;
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
void main() {
  vec3 viewDir = normalize(vPosition - cameraPosition);
  vec3 n = normalize(vNormal);
  float sun = dot(uSun, n);
  float dayMix = smoothstep(-0.25, 0.5, sun);
  vec3 color = mix(texture2D(uNight, vUv).rgb, texture2D(uDay, vUv).rgb, dayMix);
  float cloud = smoothstep(0.5, 1.0, texture2D(uClouds, vUv).g) * dayMix;
  color = mix(color, vec3(1.0), cloud);
  float fresnel = pow(dot(viewDir, n) + 1.0, 2.0);
  float atmMix = smoothstep(-0.5, 1.0, sun);
  vec3 atmColor = mix(vec3(0.02, 0.05, 0.12), vec3(0.62, 0.85, 1.0), atmMix);
  color = mix(color, atmColor, fresnel * atmMix);
  gl_FragColor = vec4(color, 1.0);
}`;

const atmVert = `
varying vec3 vNormal;
varying vec3 vPosition;
void main() {
  vec4 mp = modelMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * viewMatrix * mp;
  vNormal = (modelMatrix * vec4(normal, 0.0)).xyz;
  vPosition = mp.xyz;
}`;

const atmFrag = `
uniform vec3 uSun;
varying vec3 vNormal;
varying vec3 vPosition;
void main() {
  vec3 viewDir = normalize(vPosition - cameraPosition);
  vec3 n = normalize(vNormal);
  float sun = dot(uSun, n);
  float atmMix = smoothstep(-0.5, 1.0, sun);
  vec3 color = mix(vec3(0.02,0.05,0.12), vec3(0.62,0.85,1.0), atmMix) * (1.0 + atmMix);
  float edge = smoothstep(0.0, 0.5, dot(viewDir, n));
  float alpha = edge * smoothstep(-0.5, 0.0, sun);
  gl_FragColor = vec4(color, alpha);
}`;

// ─── Canvas Terre 3D ──────────────────────────────────────────────────────────

function EarthBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Scene + Camera
    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 3.5;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000510, 1);

    // Lumières
    const sun = new THREE.DirectionalLight(0xffffff, 5);
    sun.position.set(5, 5, 5);
    scene.add(sun);
    scene.add(new THREE.AmbientLight(0x404040, 0.5));

    // Textures
    const loader   = new THREE.TextureLoader();
    const maxAniso = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);

    const dayTex    = loader.load("/textures/2k_earth_daymap.jpg");
    dayTex.colorSpace = THREE.SRGBColorSpace;
    dayTex.anisotropy = maxAniso;

    const nightTex  = loader.load("/textures/night.jpg");
    nightTex.colorSpace = THREE.SRGBColorSpace;
    nightTex.anisotropy = maxAniso;

    const cloudsTex = loader.load("/textures/specularClouds.jpg");
    cloudsTex.anisotropy = maxAniso;

    const sunDir = new THREE.Vector3(1, 1, 1).normalize();

    // Terre
    const geo     = new THREE.SphereGeometry(1, 64, 64);
    const earthMat = new THREE.ShaderMaterial({
      vertexShader: earthVert,
      fragmentShader: earthFrag,
      uniforms: {
        uDay:    { value: dayTex },
        uNight:  { value: nightTex },
        uClouds: { value: cloudsTex },
        uSun:    { value: sunDir },
      },
    });
    const earth = new THREE.Mesh(geo, earthMat);
    earth.rotation.x = THREE.MathUtils.degToRad(23.5);
    scene.add(earth);

    // Atmosphère
    const atmMat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      transparent: true,
      vertexShader: atmVert,
      fragmentShader: atmFrag,
      uniforms: { uSun: { value: sunDir } },
    });
    const atm = new THREE.Mesh(geo, atmMat);
    atm.scale.setScalar(1.04);
    scene.add(atm);

    // Étoiles
    const starPositions = new Float32Array(4000 * 3).map(() => (Math.random() - 0.5) * 300);
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.2, sizeAttenuation: true })));

    // Resize
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("resize", onResize);

    // Animation — rotation automatique sans OrbitControls
    const clock = new THREE.Clock();
    let id;
    const tick = () => {
      const t = clock.getElapsedTime();
      earth.rotation.y = t * 0.07;
      renderer.render(scene, camera);
      id = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0, left: 0,
        width: "100vw", height: "100vh",
        zIndex: 0,
        display: "block",
      }}
    />
  );
}

// ─── Dashboard placeholder ────────────────────────────────────────────────────

function Dashboard() {
  return (
    <div style={{
      position: "relative", zIndex: 10,
      display: "flex", alignItems: "center", justifyContent: "center",
      width: "100vw", height: "100vh",
      color: "#38bdf8", fontFamily: "'Outfit', sans-serif", fontSize: "1.2rem",
    }}>
      ✅ Tableau de bord — accès protégé
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        {/* Terre 3D fixe en arrière-plan */}
        <EarthBackground />

        {/* Interface React par-dessus */}
        <div style={{
          position: "fixed",
          inset: 0,
          zIndex: 10,
          overflow: "hidden",
        }}>
          <Routes>
            <Route path="/login"     element={<AuthPage />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="*"          element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}