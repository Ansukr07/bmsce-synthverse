import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Home, MapPin, Target, Zap, Activity, Brain, FileBarChart, Repeat, Droplets, Circle, AlertTriangle, ChevronDown, Wallet, Bell, Search, Settings } from 'lucide-react'
import Welcome from './pages/Welcome.jsx'
import Location from './pages/Location.jsx'
import Calibration from './pages/Calibration.jsx'
import Inference from './pages/Inference.jsx'
import Visualization from './pages/Visualization.jsx'
import AIAnalytics from './pages/AIAnalytics.jsx'
import JunctionReport from './pages/JunctionReport.jsx'
import BehaviorPatterns from './pages/BehaviorPatterns.jsx'
import FloodDetection from './pages/FloodDetection.jsx'
import PotholeDetection from './pages/PotholeDetection.jsx'
import DisasterRerouting from './pages/DisasterRerouting.jsx'
import LandingPage from './pages/LandingPage.jsx'

const NAV_PIPELINE = [
  { to: '/dashboard',                    label: 'Welcome',          icon: Home },
  { to: '/dashboard/location',           label: 'Location',         icon: MapPin },
  { to: '/dashboard/calibration',        label: 'Calibration',      icon: Target },
  { to: '/dashboard/inference',          label: 'Inference',        icon: Zap },
  { to: '/dashboard/visualization',     label: 'Visualization',    icon: Activity },
]

const NAV_ANALYSIS = [
  { to: '/dashboard/ai-analytics',      label: 'AI Analytics',     icon: Brain },
  { to: '/dashboard/junction-report',   label: 'Junction Report',  icon: FileBarChart },
  { to: '/dashboard/behavior-patterns', label: 'Behavior Patterns',icon: Repeat },
  { to: '/dashboard/flood-detection',   label: 'Flood Detection',  icon: Droplets },
  { to: '/dashboard/pothole-detection', label: 'Pothole Detection', icon: Circle },
  { to: '/dashboard/disaster-rerouting',label: 'Disaster Rerouting',icon: AlertTriangle },
]

const ALL_NAV = [...NAV_PIPELINE, ...NAV_ANALYSIS]

export default function App() {
  const location = useLocation();

  if (location.pathname === '/' || location.pathname === '/landing') {
    return (
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/landing" element={<LandingPage />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-title">TrafficLab</div>
          <div className="sidebar-logo-sub">ANALYTICS ENGINE</div>
          <div className="sidebar-version">v1.2.0</div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Pipeline</div>
          {NAV_PIPELINE.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/dashboard'}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon size={16} className="nav-icon" />
              {label}
            </NavLink>
          ))}

          <div className="nav-section-label" style={{ marginTop: 12 }}>Analysis</div>
          {NAV_ANALYSIS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon size={16} className="nav-icon" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-dot">API Connected</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header d-flex align-center justify-between" style={{ background: "#0b0c10", borderBottom: "1px solid #14151a", padding: "16px 24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", background: "rgba(255,255,255,0.05)", padding: "4px 12px 4px 4px", borderRadius: "20px" }}>
              <img src="https://i.pravatar.cc/100?img=33" alt="avatar" style={{ width: "24px", height: "24px", borderRadius: "50%" }} />
              <div style={{ display: "flex", flexDirection: "column" }}>
                <div style={{ fontSize: "10px", color: "#8a8d9a" }}>@ryan.997 <span style={{ background: "#222329", padding: "2px 4px", borderRadius: "4px", fontSize: "8px", color: "#fff" }}>PRO</span></div>
                <div style={{ fontSize: "12px", fontWeight: "600", color: "#fff" }}>Ryan Crawford <ChevronDown size={10} style={{ marginLeft: "4px" }} /></div>
              </div>
            </div>
            <button style={{ background: "#efeaff", color: "#5b21b6", border: "none", padding: "8px 16px", borderRadius: "12px", fontWeight: "600", display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
              Deposit <Wallet size={14} />
            </button>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ position: "relative", width: "36px", height: "36px", borderRadius: "50%", background: "#111216", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid #222329", color: "#8a8d9a", cursor: "pointer" }}>
                <Bell size={16} />
                <div style={{ position: "absolute", top: "6px", right: "8px", width: "6px", height: "6px", background: "#7c3aed", borderRadius: "50%" }} />
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#111216", border: "1px solid #222329", padding: "8px 16px", borderRadius: "16px", color: "#8a8d9a" }}>
                <Search size={16} /> <span style={{ fontSize: "12px" }}>Search..</span> <div style={{ background: "#222329", padding: "2px 6px", fontSize: "10px", borderRadius: "4px" }}>⌘K</div>
              </div>
              <button style={{ background: "#111216", border: "1px solid #222329", color: "#fff", padding: "8px 16px", borderRadius: "16px", fontSize: "12px", fontWeight: "500", display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                Settings <Settings size={14} color="#8a8d9a" />
              </button>
            </div>
          </div>
        </header>
        <div className="page-body">
          <Routes>
            <Route path="/dashboard"                     element={<Welcome />} />
            <Route path="/dashboard/location"            element={<Location />} />
            <Route path="/dashboard/calibration"         element={<Calibration />} />
            <Route path="/dashboard/inference"           element={<Inference />} />
            <Route path="/dashboard/visualization"       element={<Visualization />} />
            <Route path="/dashboard/ai-analytics"        element={<AIAnalytics />} />
            <Route path="/dashboard/junction-report"     element={<JunctionReport />} />
            <Route path="/dashboard/behavior-patterns"   element={<BehaviorPatterns />} />
            <Route path="/dashboard/flood-detection"     element={<FloodDetection />} />
            <Route path="/dashboard/pothole-detection"   element={<PotholeDetection />} />
            <Route path="/dashboard/disaster-rerouting"  element={<DisasterRerouting />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
