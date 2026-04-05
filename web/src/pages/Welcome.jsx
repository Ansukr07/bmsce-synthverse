import { ArrowUpRight, ChevronDown, Wallet, PlaySquare, Settings, Anchor, MoreHorizontal, Maximize2, RefreshCw, BarChart2 } from 'lucide-react';

export default function Welcome() {
  return (
    <div className="stakent-dashboard" style={{ color: "#fff", padding: "0 24px 32px", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Top Header Section */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <h2 style={{ fontSize: "22px", fontWeight: "600", letterSpacing: "-0.5px" }}>Top Staking Assets</h2>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "12px", color: "#8a8d9a" }}>Recommended coins for 24 hours <span style={{ fontSize: "14px" }}>⏰</span></span>
            <div style={{ background: "#222329", padding: "4px 10px", borderRadius: "12px", fontSize: "11px", fontWeight: "600", color: "#b4b7c5" }}>3 Assets</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="stk-btn-secondary">24H <ChevronDown size={14} /></button>
          <button className="stk-btn-secondary">Proof of Stake <ChevronDown size={14} /></button>
          <button className="stk-btn-secondary">Desc <ChevronDown size={14} /></button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1.2fr", gap: "20px" }}>
        {/* Top Assets Cards */}
        {[
          { name: "Ethereum", symbol: "ETH", rate: "13.62%", change: "+ 6.26%", price: "+$2,956", icon: "💎", color: "#627eea" },
          { name: "BNB Chain", symbol: "BNB", rate: "12.72%", change: "+ 5.67%", price: "+$2,009", icon: "🟡", color: "#f3ba2f" },
          { name: "Polygon", symbol: "Matic", rate: "6.29%", change: "- 1.89%", price: "-$0,987", icon: "🟣", color: "#8247e5", down: true }
        ].map((coin, i) => (
          <div key={i} className="stk-card asset-card" style={{ padding: "20px", display: "flex", flexDirection: "column", justifyContent: "space-between", height: "180px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: coin.color, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>{coin.icon}</div>
                <div>
                  <div style={{ fontSize: "11px", color: "#8a8d9a" }}>Proof of Stake</div>
                  <div style={{ fontSize: "15px", fontWeight: "500" }}>{coin.name} <span style={{ color: "#8a8d9a", fontWeight: "400" }}>({coin.symbol})</span></div>
                </div>
              </div>
              <div style={{ width: "28px", height: "28px", borderRadius: "8px", background: "#222329", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", cursor: "pointer" }}>
                <ArrowUpRight size={14} />
              </div>
            </div>
            <div>
              <div style={{ fontSize: "11px", color: "#8a8d9a", marginBottom: "4px" }}>Reward Rate</div>
              <div style={{ fontSize: "24px", fontWeight: "600", letterSpacing: "-0.5px" }}>{coin.rate}</div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: coin.down ? "#ef4444" : "#10b981", marginTop: "2px" }}>
                <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: coin.down ? "rgba(239,68,68,0.15)" : "rgba(16,185,129,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {coin.down ? <ArrowUpRight size={10} style={{ transform: "rotate(90deg)" }} /> : <ArrowUpRight size={10} />}
                </div>
                {coin.change}
              </div>
            </div>
            {/* Faux Sparkline */}
            <div style={{ position: "relative", height: "30px", marginTop: "10px" }}>
              <svg width="100%" height="30" preserveAspectRatio="none">
                <path d={coin.down ? "M0,15 Q30,5 60,20 T120,25 T200,20" : "M0,25 Q30,25 60,10 T120,15 T200,5"} fill="none" stroke={coin.down ? "#ef4444" : "#7c3aed"} strokeWidth="2" style={{ filter: "drop-shadow(0 2px 4px rgba(124,58,237,0.3))" }} />
                <circle cx="200" cy={coin.down ? "20" : "5"} r="4" fill="#fff" stroke={coin.down ? "#ef4444" : "#7c3aed"} strokeWidth="2" />
              </svg>
              <div style={{ position: "absolute", right: 0, top: coin.down ? "-10px" : "-15px", fontSize: "11px", fontWeight: "600" }}>{coin.price}</div>
            </div>
          </div>
        ))}

        {/* Liquid Staking Portfolio */}
        <div className="stk-card" style={{ background: "linear-gradient(145deg, #1c162f 0%, #0d0e14 100%)", padding: "24px", position: "relative", overflow: "hidden" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <ZapIcon /> <span style={{ fontWeight: "600", fontSize: "14px" }}>Stakent&deg;</span>
            </div>
            <div style={{ background: "#efeaff", color: "#5b21b6", fontSize: "11px", fontWeight: "700", padding: "4px 8px", borderRadius: "12px" }}>New</div>
          </div>
          <h3 style={{ fontSize: "22px", fontWeight: "600", marginBottom: "8px", letterSpacing: "-0.5px" }}>Liquid Staking Portfolio</h3>
          <p style={{ fontSize: "13px", color: "#8a8d9a", lineHeight: "1.5", marginBottom: "24px", maxWidth: "85%" }}>
            An all-in-one portfolio that helps you make smarter investments into Ethereum Liquid Staking
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <button style={{ width: "100%", background: "#efeaff", color: "#5b21b6", border: "none", padding: "12px", borderRadius: "12px", fontWeight: "600", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", cursor: "pointer" }}>
              Connect with Wallet <Wallet size={16} />
            </button>
            <button style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", padding: "12px", borderRadius: "12px", fontWeight: "600", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", cursor: "pointer" }}>
              Enter a Wallet Address <Anchor size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Active Stakings Section */}
      <div className="stk-card" style={{ padding: "24px", marginTop: "8px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <div style={{ fontSize: "16px", fontWeight: "500", color: "#8a8d9a" }}>Your active stakings</div>
          <div style={{ display: "flex", gap: "12px", color: "#8a8d9a" }}>
            <BarChart2 size={16} cursor="pointer" />
            <RefreshCw size={16} cursor="pointer" />
            <Settings size={16} cursor="pointer" />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "32px", borderBottom: "1px solid #222329", paddingBottom: "24px", marginBottom: "24px" }}>
          <div>
            <div style={{ fontSize: "12px", color: "#8a8d9a", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              Last Update — 45 minutes ago <RefreshCw size={12} />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "28px", fontWeight: "600", letterSpacing: "-0.5px" }}>Stake Avalanche (AVAX) <span style={{ color: "#ef4444" }}>🔺</span></h2>
              <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "#222329", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}><Anchor size={14} /></div>
              <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "#222329", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}><ArrowUpRight size={14} /></div>
              <button className="stk-btn-secondary" style={{ marginLeft: "auto" }}>View Profile <ArrowUpRight size={14} /></button>
            </div>
            <div style={{ fontSize: "12px", color: "#8a8d9a", marginBottom: "4px" }}>Current Reward Balance, AVAX</div>
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div style={{ fontSize: "40px", fontWeight: "600", letterSpacing: "-1px" }}>31.39686</div>
              <button style={{ background: "#7c3aed", color: "#fff", border: "none", padding: "10px 20px", borderRadius: "12px", fontWeight: "500", cursor: "pointer" }}>Upgrade</button>
              <button className="stk-btn-secondary" style={{ padding: "10px 20px" }}>Unstake</button>
            </div>
          </div>
          
          <div style={{ background: "#111216", borderRadius: "16px", padding: "20px", border: "1px solid #222329" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
              <div>
                <div style={{ fontSize: "14px", fontWeight: "500" }}>Investment Period</div>
                <div style={{ fontSize: "11px", color: "#8a8d9a" }}>Contribution Period (Month)</div>
              </div>
              <div style={{ background: "#222329", padding: "4px 10px", borderRadius: "12px", fontSize: "11px", color: "#b4b7c5" }}>6 Month</div>
            </div>
            {/* Timeline UI */}
            <div style={{ position: "relative", height: "40px", display: "flex", alignItems: "center" }}>
              <div style={{ width: "100%", height: "2px", background: "#222329", display: "flex", justifyContent: "space-between" }}>
                {[...Array(20)].map((_, i) => <div key={i} style={{ width: "2px", height: i % 5 === 0 ? "8px" : "4px", background: "#444", transform: "translateY(-50%)" }} />)}
              </div>
              <div style={{ position: "absolute", left: "60%", top: "50%", transform: "translate(-50%, -50%)", display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div style={{ background: "#222329", padding: "4px 8px", borderRadius: "8px", fontSize: "10px", color: "#fff", marginBottom: "4px", whiteSpace: "nowrap" }}>4 Month</div>
                <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: "rgba(124,58,237,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <div style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#7c3aed" }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "24px", borderBottom: "1px solid #222329", paddingBottom: "16px", marginBottom: "16px" }}>
          <div style={{ flex: 1, display: "flex", justifyContent: "space-between", alignItems: "center", paddingRight: "24px", borderRight: "1px solid #222329" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: "500" }}>Momentum</div>
              <div style={{ fontSize: "11px", color: "#8a8d9a" }}>Growth dynamics</div>
            </div>
            <ChevronDown size={16} color="#8a8d9a" />
          </div>
          <div style={{ flex: 1, display: "flex", justifyContent: "space-between", alignItems: "center", paddingRight: "24px", borderRight: "1px solid #222329" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: "500" }}>General</div>
              <div style={{ fontSize: "11px", color: "#8a8d9a" }}>Overview</div>
            </div>
          </div>
          <div style={{ flex: 1, display: "flex", justifyContent: "space-between", alignItems: "center", paddingRight: "24px", borderRight: "1px solid #222329" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: "500" }}>Risk</div>
              <div style={{ fontSize: "11px", color: "#8a8d9a" }}>Risk assessment</div>
            </div>
            <ChevronDown size={16} color="#8a8d9a" />
          </div>
          <div style={{ flex: 1, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: "500" }}>Reward</div>
              <div style={{ fontSize: "11px", color: "#8a8d9a" }}>Expected profit</div>
            </div>
            <ChevronDown size={16} color="#8a8d9a" />
          </div>
        </div>

        <div style={{ display: "flex", gap: "24px", paddingTop: "8px" }}>
          <div className="stk-metric">
            <div className="label">Staked Tokens Trend <span>24H</span></div>
            <div className="value">-0.82%</div>
          </div>
          <div className="stk-metric">
            <div className="label">Price <span>24H</span></div>
            <div className="value">$41.99 <span style={{ fontSize: "12px", color: "#ef4444", fontWeight: "500" }}>-1.09% ↘</span></div>
          </div>
          <div className="stk-metric">
            <div className="label">Staking Ratio <span>24H</span></div>
            <div className="value">60.6%</div>
          </div>
          <div className="stk-metric" style={{ flex: 1 }}>
            <div className="label">Reward Rate</div>
            <div style={{ position: "relative", height: "32px", marginTop: "8px" }}>
              <div style={{ position: "absolute", width: "100%", top: "8px", height: "2px", background: "#222329" }}>
                <div style={{ width: "70%", height: "100%", background: "#7c3aed" }} />
              </div>
              <div style={{ position: "absolute", left: "70%", top: "-2px", fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#7c3aed" }} />
                2.23% <span style={{ color: "#8a8d9a" }}>24H Ago</span>
              </div>
              <div style={{ position: "absolute", left: "50%", top: "18px", fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#a78bfa" }} />
                1.45% <span style={{ color: "#8a8d9a" }}>48H Ago</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ZapIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" fill="#fff" />
    </svg>
  );
}
