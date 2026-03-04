import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const IconUser    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>;
const IconMail    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 7 10-7"/></svg>;
const IconLock    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>;
const IconEye     = ({ off }) => off
  ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
  : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>;
const IconWave    = () => <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="1.5"><path d="M2 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/><path d="M2 18c2-4 4-4 6 0s4 4 6 0 4-4 6 0" opacity=".5"/></svg>;
const IconDroplet = () => <svg width="44" height="44" viewBox="0 0 24 24" fill="#38bdf8" fillOpacity=".15" stroke="#38bdf8" strokeWidth="1.5"><path d="M12 2C6 9 4 13 4 16a8 8 0 0 0 16 0c0-3-2-7-8-14z"/></svg>;

export default function AuthPage() {
  const [mode,      setMode]      = useState("login");
  const [form,      setForm]      = useState({ username: "", email: "", password: "" });
  const [showPwd,   setShowPwd]   = useState(false);
  const [error,     setError]     = useState("");
  const [busy,      setBusy]      = useState(false);
  const [particles, setParticles] = useState([]);

  const { login, register } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();
  const from = location.state?.from?.pathname || "/dashboard";

  useEffect(() => {
    setParticles(Array.from({ length: 18 }, (_, i) => ({
      id: i,
      x: Math.random() * 100, y: Math.random() * 100,
      size: Math.random() * 6 + 2,
      dur: Math.random() * 12 + 8,
      delay: Math.random() * 6,
      opacity: Math.random() * 0.4 + 0.1,
    })));
  }, []);

  const field = (key, val) => { setForm(f => ({ ...f, [key]: val })); if (error) setError(""); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      if (mode === "login") await login(form.username, form.password);
      else await register(form.username, form.email, form.password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const switchMode = () => {
    setMode(m => m === "login" ? "register" : "login");
    setForm({ username: "", email: "", password: "" });
    setError("");
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ─── RESET COMPLET ─────────────────────────────────────────────────── */
        /* Pourquoi ? Le navigateur ajoute margin/padding par défaut → espace blanc */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        /* ─── RACINE : plein écran total, transparent pour voir la Terre ─────── */
        .auth-root {
          position: fixed;          /* colle aux 4 coins de la fenêtre */
          inset: 0;                 /* top:0 right:0 bottom:0 left:0 */
          display: flex;
          font-family: 'Outfit', sans-serif;
          background: transparent;  /* la Terre 3D (derrière) reste visible */
          overflow: hidden;
        }

        /* ─── PANNEAU GAUCHE : glassmorphism transparent ────────────────────── */
        /* Pourquoi glassmorphism ? Pour voir la Terre derrière tout en restant lisible */
        .auth-left {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          padding: 60px;
          position: relative;
          background: rgba(6, 14, 31, 0.55);   /* semi-transparent */
          backdrop-filter: blur(2px);           /* flou pour lisibilité */
          -webkit-backdrop-filter: blur(2px);
          border-right: 1px solid rgba(56,189,248,.12);
          overflow: hidden;
        }

        .auth-left::before {
          content: '';
          position: absolute; top: -200px; left: -200px;
          width: 600px; height: 600px;
          background: radial-gradient(circle, rgba(56,189,248,.10) 0%, transparent 70%);
          pointer-events: none;
        }

        /* grid overlay */
        .grid-overlay {
          position: absolute; inset: 0;
          background-image:
            linear-gradient(rgba(56,189,248,.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56,189,248,.04) 1px, transparent 1px);
          background-size: 60px 60px;
          pointer-events: none;
        }

        /* ─── PANNEAU DROIT : glassmorphism transparent ─────────────────────── */
        .auth-right {
          width: 480px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(8, 15, 34, 0.70);    /* semi-transparent */
          backdrop-filter: blur(8px);           /* plus de flou côté form */
          -webkit-backdrop-filter: blur(20px);
          border-left: 1px solid rgba(56,189,248,.10);
          padding: 40px;
        }

        .auth-card { width: 100%; max-width: 400px; }

        .card-header { margin-bottom: 36px; }

        .card-title { font-size: 26px; font-weight: 700; color: #f0f9ff; margin-bottom: 6px; }
        .card-sub   { font-size: 14px; color: #475569; }

        .brand { display: flex; align-items: center; gap: 14px; margin-bottom: 48px; position: relative; z-index: 1; }
        .brand-logo {
          width: 48px; height: 48px;
          background: linear-gradient(135deg, rgba(56,189,248,.2), rgba(14,165,233,.1));
          border: 1px solid rgba(56,189,248,.3); border-radius: 14px;
          display: flex; align-items: center; justify-content: center;
        }
        .brand-name { font-size: 13px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase; color: #38bdf8; font-family: 'JetBrains Mono', monospace; }

        .hero-title { font-size: 48px; font-weight: 700; line-height: 1.1; color: #f0f9ff; margin-bottom: 20px; position: relative; z-index: 1; }
        .hero-title span { background: linear-gradient(90deg, #38bdf8, #7dd3fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .hero-sub { font-size: 16px; color: #94a3b8; line-height: 1.7; max-width: 360px; margin-bottom: 52px; position: relative; z-index: 1; }

        .stats { display: flex; gap: 16px; flex-wrap: wrap; position: relative; z-index: 1; }
        .stat-pill {
          background: rgba(56,189,248,.06);
          border: 1px solid rgba(56,189,248,.15);
          border-radius: 12px; padding: 14px 20px;
          display: flex; align-items: center; gap: 10px;
        }
        .stat-dot { width: 8px; height: 8px; border-radius: 50%; animation: pulse-dot 2s ease-in-out infinite; }
        .stat-dot.green  { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
        .stat-dot.blue   { background: #38bdf8; box-shadow: 0 0 8px #38bdf8; }
        .stat-dot.orange { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
        @keyframes pulse-dot { 0%, 100% { opacity:1; transform:scale(1); } 50% { opacity:.5; transform:scale(.8); } }
        .stat-label { font-size: 12px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; letter-spacing: .5px; }

        .particle { position: absolute; border-radius: 50%; background: rgba(56,189,248,1); pointer-events: none; animation: float-up linear infinite; }
        @keyframes float-up {
          0%   { transform: translateY(0)    scale(1);   opacity: var(--op); }
          50%  { transform: translateY(-40px) scale(1.2); opacity: calc(var(--op)*1.5); }
          100% { transform: translateY(0)    scale(1);   opacity: var(--op); }
        }

        /* tabs */
        .mode-tabs { display: flex; background: rgba(56,189,248,.05); border: 1px solid rgba(56,189,248,.1); border-radius: 12px; padding: 4px; margin-bottom: 32px; }
        .mode-tab  { flex:1; padding:10px; border:none; border-radius:9px; font-family:'Outfit',sans-serif; font-size:14px; font-weight:500; cursor:pointer; transition:all .25s; background:transparent; color:#475569; }
        .mode-tab.active { background: linear-gradient(135deg,#0ea5e9,#38bdf8); color:#fff; box-shadow:0 4px 12px rgba(56,189,248,.25); }

        /* form */
        .form-group { margin-bottom: 18px; }
        .form-label { display:block; font-size:12px; font-weight:600; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px; font-family:'JetBrains Mono',monospace; }
        .input-wrap { position:relative; display:flex; align-items:center; }
        .input-icon { position:absolute; left:16px; color:#334155; transition:color .2s; pointer-events:none; display:flex; }
        .form-input {
          width:100%; padding:13px 16px 13px 46px;
          background: rgba(56,189,248,.06);
          border: 1px solid rgba(56,189,248,.12);
          border-radius:12px; color:#f0f9ff;
          font-family:'Outfit',sans-serif; font-size:15px; outline:none;
          transition: border-color .2s, background .2s, box-shadow .2s;
        }
        .form-input:focus { border-color:rgba(56,189,248,.5); background:rgba(56,189,248,.10); box-shadow:0 0 0 3px rgba(56,189,248,.08); }
        .input-wrap:focus-within .input-icon { color:#38bdf8; }
        .form-input::placeholder { color:#334155; }

        .eye-btn { position:absolute; right:14px; background:none; border:none; cursor:pointer; color:#334155; transition:color .2s; display:flex; padding:4px; }
        .eye-btn:hover { color:#38bdf8; }

        /* error */
        .error-box { display:flex; align-items:center; gap:10px; background:rgba(239,68,68,.08); border:1px solid rgba(239,68,68,.25); border-radius:10px; padding:12px 16px; margin-bottom:18px; color:#fca5a5; font-size:13px; animation:shake .35s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)} 20%,60%{transform:translateX(-5px)} 40%,80%{transform:translateX(5px)} }

        /* submit */
        .submit-btn {
          width:100%; padding:15px;
          background: linear-gradient(135deg,#0ea5e9 0%,#38bdf8 100%);
          border:none; border-radius:12px; color:#fff;
          font-family:'Outfit',sans-serif; font-size:16px; font-weight:600;
          cursor:pointer; transition:transform .15s,box-shadow .15s,opacity .15s;
          margin-top:8px; position:relative; overflow:hidden;
          box-shadow:0 4px 20px rgba(56,189,248,.25);
        }
        .submit-btn::before { content:''; position:absolute; inset:0; background:linear-gradient(135deg,transparent 30%,rgba(255,255,255,.15)); opacity:0; transition:opacity .2s; }
        .submit-btn:hover:not(:disabled)::before { opacity:1; }
        .submit-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 8px 28px rgba(56,189,248,.35); }
        .submit-btn:active:not(:disabled) { transform:translateY(0); }
        .submit-btn:disabled { opacity:.6; cursor:not-allowed; }

        .btn-spinner { display:inline-block; width:16px; height:16px; border:2px solid rgba(255,255,255,.3); border-top-color:#fff; border-radius:50%; animation:spin .7s linear infinite; margin-right:8px; vertical-align:middle; }
        @keyframes spin { to { transform:rotate(360deg); } }

        .switch-link { text-align:center; margin-top:24px; font-size:14px; color:#475569; }
        .switch-link button { background:none; border:none; color:#38bdf8; cursor:pointer; font-family:'Outfit',sans-serif; font-size:14px; font-weight:500; text-decoration:underline; text-underline-offset:3px; }
        .switch-link button:hover { color:#7dd3fc; }

        .divider { display:flex; align-items:center; gap:12px; margin:20px 0; }
        .divider-line { flex:1; height:1px; background:rgba(56,189,248,.1); }
        .divider-text { font-size:11px; color:#334155; font-family:'JetBrains Mono',monospace; letter-spacing:1px; }

        /* mobile : panneau gauche caché, form plein écran */
        @media (max-width: 900px) {
          .auth-left  { display: none; }
          .auth-right { width: 100%; border: none; }
        }
      `}</style>

      <div className="auth-root">

        {/* ── GAUCHE ── */}
        <div className="auth-left">
          <div className="grid-overlay" />

          {particles.map(p => (
            <div key={p.id} className="particle" style={{
              left:`${p.x}%`, top:`${p.y}%`,
              width:p.size, height:p.size,
              "--op":p.opacity,
              animationDuration:`${p.dur}s`,
              animationDelay:`${p.delay}s`,
            }}/>
          ))}

          <div className="brand">
            <div className="brand-logo"><IconDroplet /></div>
            <div className="brand-name">AquaWatch</div>
          </div>

          <h1 className="hero-title">
            Surveillance<br /><span>Qualité de l'Eau</span>
          </h1>

          <p className="hero-sub">
            Plateforme de monitoring en temps réel des paramètres physico-chimiques
            de votre lac. Détection de pics, prédiction ML et alertes automatiques.
          </p>

          <div className="stats">
            {[
              { dot:"green",  label:"Capteurs actifs" },
              { dot:"blue",   label:"ML opérationnel" },
              { dot:"orange", label:"Alertes temps réel" },
            ].map(s => (
              <div key={s.label} className="stat-pill">
                <div className={`stat-dot ${s.dot}`}/>
                <span className="stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── DROITE ── */}
        <div className="auth-right">
          <div className="auth-card">

            <div className="card-header">
              <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:16 }}>
                <IconWave />
                <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:"#334155", letterSpacing:2 }}>
                  SYSTÈME D'AUTHENTIFICATION
                </span>
              </div>
              <h2 className="card-title">{mode === "login" ? "Bon retour 👋" : "Créer un compte"}</h2>
              <p className="card-sub">{mode === "login" ? "Connectez-vous pour accéder au tableau de bord." : "Remplissez le formulaire pour rejoindre la plateforme."}</p>
            </div>

            <div className="mode-tabs">
              <button className={`mode-tab ${mode==="login"?"active":""}`}    onClick={() => { setMode("login");    setError(""); }}>Connexion</button>
              <button className={`mode-tab ${mode==="register"?"active":""}`} onClick={() => { setMode("register"); setError(""); }}>Inscription</button>
            </div>

            {error && <div className="error-box"><span>⚠</span>{error}</div>}

            <form onSubmit={handleSubmit} noValidate>
              <div className="form-group">
                <label className="form-label">Identifiant</label>
                <div className="input-wrap">
                  <span className="input-icon"><IconUser /></span>
                  <input className="form-input" type="text" placeholder="nom d'utilisateur" value={form.username} onChange={e => field("username", e.target.value)} autoComplete="username" required />
                </div>
              </div>

              {mode === "register" && (
                <div className="form-group">
                  <label className="form-label">Adresse email</label>
                  <div className="input-wrap">
                    <span className="input-icon"><IconMail /></span>
                    <input className="form-input" type="email" placeholder="votre@email.com" value={form.email} onChange={e => field("email", e.target.value)} autoComplete="email" required />
                  </div>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Mot de passe</label>
                <div className="input-wrap">
                  <span className="input-icon"><IconLock /></span>
                  <input className="form-input" type={showPwd?"text":"password"} placeholder={mode==="register"?"min. 8 caractères":"••••••••"} value={form.password} onChange={e => field("password", e.target.value)} autoComplete={mode==="login"?"current-password":"new-password"} required />
                  <button type="button" className="eye-btn" onClick={() => setShowPwd(v => !v)}><IconEye off={showPwd}/></button>
                </div>
              </div>

              <div className="divider">
                <div className="divider-line"/><span className="divider-text">SÉCURISÉ</span><div className="divider-line"/>
              </div>

              <button type="submit" className="submit-btn" disabled={busy}>
                {busy && <span className="btn-spinner"/>}
                {busy ? "Traitement…" : mode==="login" ? "Se connecter" : "Créer le compte"}
              </button>
            </form>

            <div className="switch-link">
              {mode==="login"
                ? <>Pas encore de compte ? <button onClick={switchMode}>S'inscrire</button></>
                : <>Déjà un compte ? <button onClick={switchMode}>Se connecter</button></>
              }
            </div>
          </div>
        </div>
      </div>
    </>
  );
}