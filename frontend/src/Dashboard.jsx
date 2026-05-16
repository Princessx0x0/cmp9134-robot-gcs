import { useState, useEffect, useCallback } from "react";

const GRID_SIZE = 21;
const MOCK_OBSTACLES = [
  [2,3],[2,4],[5,7],[5,8],[8,2],[8,3],[10,10],[10,11],
  [13,5],[13,6],[15,15],[15,16],[17,3],[17,4],[19,18],
  [3,17],[7,13],[11,19],[6,1],[14,12],[1,9],[9,16],
  [4,6],[16,8],[18,14],[12,2],[0,15],[20,7],[8,18],[3,11]
];

const INITIAL_STATE = {
  id: "XR-900",
  position: { x: 0, y: 0 },
  battery: 100,
  status: "IDLE",
};

export default function Dashboard() {
  const [robot, setRobot] = useState(INITIAL_STATE);
  const [user] = useState({ username: "commander_01", role: "commander" });
  const [targetX, setTargetX] = useState("");
  const [targetY, setTargetY] = useState("");
  const [logs, setLogs] = useState([]);
  const [notification, setNotification] = useState(null);
  const [connected, setConnected] = useState(true);
  const [hoveredCell, setHoveredCell] = useState(null);

  const isObstacle = useCallback((x, y) =>
    MOCK_OBSTACLES.some(([ox, oy]) => ox === x && oy === y), []);

  const addLog = useCallback((command, outcome, x = null, y = null) => {
    setLogs(prev => [{
      id: Date.now(),
      timestamp: new Date().toISOString(),
      user: user.username,
      command,
      target: x !== null ? `(${x}, ${y})` : "-",
      outcome,
    }, ...prev].slice(0, 50));
  }, [user.username]);

  const showNotification = useCallback((message, type = "success") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setRobot(prev => {
        if (prev.status === "MOVING") {
          const newBattery = Math.max(0, prev.battery - 0.5);
          if (newBattery === 0) return { ...prev, battery: 0, status: "IDLE" };
          return { ...prev, battery: newBattery };
        }
        if (prev.status === "IDLE" && prev.position.x === 0 && prev.position.y === 0) {
          return { ...prev, battery: Math.min(100, prev.battery + 2) };
        }
        return prev;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (robot.battery < 20 && robot.status !== "LOW_BATTERY" && robot.status !== "IDLE") {
      setRobot(prev => ({ ...prev, status: "LOW_BATTERY" }));
      showNotification("WARNING: Battery below 20%", "warning");
    }
  }, [robot.battery, robot.status, showNotification]);

  const handleMove = () => {
    if (user.role !== "commander") {
      showNotification("Access denied — Commander role required", "error");
      return;
    }
    const x = parseInt(targetX);
    const y = parseInt(targetY);
    if (isNaN(x) || isNaN(y) || x < 0 || x > 20 || y < 0 || y > 20) {
      showNotification("Invalid coordinates — must be integers 0-20", "error");
      return;
    }
    if (robot.battery === 0) {
      showNotification("Cannot move — battery depleted", "error");
      addLog("MOVE", "REJECTED: battery 0%", x, y);
      return;
    }
    if (isObstacle(x, y)) {
      showNotification(`Obstacle at (${x}, ${y}) — command rejected`, "error");
      addLog("MOVE", "REJECTED: obstacle", x, y);
      setRobot(prev => ({ ...prev, status: "STUCK" }));
      return;
    }
    setRobot(prev => ({ ...prev, status: "MOVING", position: { x, y } }));
    addLog("MOVE", "SUCCESS", x, y);
    showNotification(`Navigating to (${x}, ${y})`, "success");
    setTimeout(() => setRobot(prev => ({ ...prev, status: "IDLE" })), 2000);
    setTargetX("");
    setTargetY("");
  };

  const handleReset = () => {
    if (user.role !== "commander") {
      showNotification("Access denied", "error");
      return;
    }
    setRobot(INITIAL_STATE);
    addLog("RESET", "SUCCESS");
    showNotification("Simulation reset", "success");
  };

  const toggleConnection = () => {
    setConnected(prev => {
      showNotification(prev ? "Signal lost — reconnecting..." : "Connection restored", prev ? "error" : "success");
      return !prev;
    });
  };

  const getBatteryColor = () => {
    if (robot.battery > 50) return "#22c55e";
    if (robot.battery > 20) return "#f59e0b";
    return "#ef4444";
  };

  const getStatusColor = () => {
    const colors = { IDLE: "#22c55e", MOVING: "#3b82f6", LOW_BATTERY: "#f59e0b", STUCK: "#ef4444" };
    return colors[robot.status] || "#6b7280";
  };

  return (
    <div style={{
      minHeight: "100vh", background: "#0a0e1a", color: "#e2e8f0",
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace", fontSize: "13px",
    }}>
      {/* Import font */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Orbitron:wght@400;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0a0e1a; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }
        input:focus { outline: none; border-color: #3b82f6 !important; }
        button:focus-visible { outline: 2px solid #3b82f6; outline-offset: 2px; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes slideIn { from{transform:translateY(-20px);opacity:0} to{transform:translateY(0);opacity:1} }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
      `}</style>

      {/* Notification */}
      {notification && (
        <div style={{
          position: "fixed", top: 16, right: 16, zIndex: 1000,
          padding: "12px 18px", borderRadius: 8, animation: "slideIn 0.2s ease",
          background: notification.type === "success" ? "#052e16" : notification.type === "warning" ? "#1c1007" : "#1a0505",
          border: `1px solid ${notification.type === "success" ? "#22c55e" : notification.type === "warning" ? "#f59e0b" : "#ef4444"}`,
          color: notification.type === "success" ? "#22c55e" : notification.type === "warning" ? "#f59e0b" : "#ef4444",
          fontSize: 12, maxWidth: 320,
        }}>
          {notification.message}
        </div>
      )}

      {/* Nav */}
      <div style={{
        background: "#0d1224", borderBottom: "1px solid #1e3a5f",
        padding: "0 24px", height: 52, display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontFamily: "Orbitron, monospace", fontSize: 15, fontWeight: 700, color: "#3b82f6", letterSpacing: 2 }}>
            GCS
          </span>
          <span style={{ color: "#1e3a5f" }}>|</span>
          <span style={{ color: "#64748b", fontSize: 11 }}>ROBOT MANAGEMENT SYSTEM</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%",
              background: connected ? "#22c55e" : "#ef4444",
              animation: connected ? "none" : "blink 1s infinite",
            }} />
            <span style={{ color: connected ? "#22c55e" : "#ef4444", fontSize: 11 }}>
              {connected ? "CONNECTED" : "SIGNAL LOST"}
            </span>
          </div>
          <div style={{ background: "#1e293b", padding: "4px 10px", borderRadius: 4, fontSize: 11 }}>
            <span style={{ color: "#64748b" }}>USER: </span>
            <span style={{ color: "#e2e8f0" }}>{user.username}</span>
            <span style={{ color: "#64748b" }}> · </span>
            <span style={{ color: user.role === "commander" ? "#3b82f6" : "#94a3b8", fontWeight: 600, textTransform: "uppercase" }}>
              {user.role}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr 260px", gap: 1, height: "calc(100vh - 52px)", background: "#1e3a5f22" }}>

        {/* Left panel */}
        <div style={{ background: "#0d1224", padding: 20, display: "flex", flexDirection: "column", gap: 16, overflowY: "auto" }}>

          {/* Robot ID */}
          <div>
            <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 8, fontWeight: 600 }}>UNIT IDENTIFIER</div>
            <div style={{ fontFamily: "Orbitron, monospace", fontSize: 18, fontWeight: 700, color: "#e2e8f0" }}>{robot.id}</div>
          </div>

          <div style={{ height: 1, background: "#1e3a5f" }} />

          {/* Status */}
          <div>
            <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 8, fontWeight: 600 }}>STATUS</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: getStatusColor(), animation: robot.status === "MOVING" ? "pulse 1s infinite" : "none" }} />
              <span style={{ color: getStatusColor(), fontWeight: 600, fontSize: 14 }}>{robot.status}</span>
            </div>
          </div>

          {/* Battery */}
          <div>
            <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 8, fontWeight: 600 }}>BATTERY</div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <span style={{ color: getBatteryColor(), fontSize: 20, fontWeight: 600, fontFamily: "Orbitron, monospace" }}>
                {Math.round(robot.battery)}%
              </span>
            </div>
            <div style={{ height: 6, background: "#1e293b", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${robot.battery}%`, background: getBatteryColor(), borderRadius: 3, transition: "all 0.5s ease" }} />
            </div>
            {robot.battery < 20 && (
              <div style={{ color: "#ef4444", fontSize: 10, marginTop: 6, animation: "blink 1s infinite" }}>
                ⚠ LOW — RETURN TO BASE
              </div>
            )}
          </div>

          {/* Position */}
          <div>
            <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 8, fontWeight: 600 }}>POSITION</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {["X", "Y"].map((axis, i) => (
                <div key={axis} style={{ background: "#0a0e1a", border: "1px solid #1e3a5f", borderRadius: 6, padding: "10px 14px" }}>
                  <div style={{ color: "#64748b", fontSize: 10, marginBottom: 4 }}>{axis}-AXIS</div>
                  <div style={{ fontFamily: "Orbitron, monospace", fontSize: 18, fontWeight: 700, color: "#3b82f6" }}>
                    {i === 0 ? robot.position.x : robot.position.y}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ height: 1, background: "#1e3a5f" }} />

          {/* Move controls */}
          <div>
            <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 12, fontWeight: 600 }}>NAVIGATION</div>
            {user.role === "commander" ? (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
                  {[["TARGET X", targetX, setTargetX], ["TARGET Y", targetY, setTargetY]].map(([label, val, setter]) => (
                    <div key={label}>
                      <div style={{ color: "#64748b", fontSize: 10, marginBottom: 4 }}>{label}</div>
                      <input
                        type="number" min="0" max="20"
                        value={val}
                        onChange={e => setter(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleMove()}
                        placeholder="0-20"
                        style={{
                          width: "100%", background: "#0a0e1a", border: "1px solid #1e3a5f",
                          borderRadius: 6, padding: "8px 10px", color: "#e2e8f0",
                          fontFamily: "inherit", fontSize: 13, transition: "border-color 0.2s",
                        }}
                      />
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleMove}
                  disabled={!connected || robot.status === "MOVING"}
                  style={{
                    width: "100%", padding: "11px 0", borderRadius: 6, border: "none",
                    background: !connected || robot.status === "MOVING" ? "#1e293b" : "#1d4ed8",
                    color: !connected || robot.status === "MOVING" ? "#475569" : "#fff",
                    fontFamily: "inherit", fontSize: 13, fontWeight: 600, cursor: !connected || robot.status === "MOVING" ? "not-allowed" : "pointer",
                    letterSpacing: 1, transition: "all 0.2s",
                  }}
                >
                  {robot.status === "MOVING" ? "NAVIGATING..." : "EXECUTE MOVE"}
                </button>
                <button
                  onClick={handleReset}
                  style={{
                    width: "100%", marginTop: 8, padding: "9px 0", borderRadius: 6,
                    border: "1px solid #7f1d1d", background: "transparent",
                    color: "#ef4444", fontFamily: "inherit", fontSize: 12, cursor: "pointer",
                    letterSpacing: 1, transition: "all 0.2s",
                  }}
                >
                  RESET SIMULATION
                </button>
              </>
            ) : (
              <div style={{ color: "#475569", fontSize: 12, padding: "12px", border: "1px solid #1e3a5f", borderRadius: 6 }}>
                View-only access. Commander role required to send commands.
              </div>
            )}
          </div>

          <div style={{ height: 1, background: "#1e3a5f" }} />

          {/* Dev toggle */}
          <button
            onClick={toggleConnection}
            style={{
              padding: "8px 0", borderRadius: 6, border: "1px solid #1e3a5f",
              background: "transparent", color: "#64748b", fontFamily: "inherit",
              fontSize: 11, cursor: "pointer", letterSpacing: 1,
            }}
          >
            {connected ? "SIMULATE DROPOUT" : "RESTORE CONNECTION"}
          </button>
        </div>

        {/* Grid */}
        <div style={{ background: "#0a0e1a", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
          <div>
            <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 12, fontWeight: 600, textAlign: "center" }}>
              ENVIRONMENT MAP — 21×21 GRID
            </div>
            {!connected && (
              <div style={{ textAlign: "center", color: "#ef4444", fontSize: 12, marginBottom: 12, animation: "blink 1s infinite" }}>
                ⚠ SIGNAL LOST — LAST KNOWN POSITION DISPLAYED
              </div>
            )}
            <div style={{
              display: "grid",
              gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`,
              gap: 1, background: "#1e3a5f22",
              border: "1px solid #1e3a5f", borderRadius: 4,
            }}>
              {Array.from({ length: GRID_SIZE }, (_, row) =>
                Array.from({ length: GRID_SIZE }, (_, col) => {
                  const isRobot = robot.position.x === col && robot.position.y === row;
                  const isObs = isObstacle(col, row);
                  const isBase = col === 0 && row === 0;
                  const isHovered = hoveredCell && hoveredCell[0] === col && hoveredCell[1] === row;
                  return (
                    <div
                      key={`${row}-${col}`}
                      onMouseEnter={() => setHoveredCell([col, row])}
                      onMouseLeave={() => setHoveredCell(null)}
                      title={`(${col}, ${row})${isRobot ? " — Robot" : isObs ? " — Obstacle" : isBase ? " — Charging Station" : ""}`}
                      style={{
                        width: 22, height: 22,
                        background: isRobot
                          ? "#3b82f6"
                          : isObs
                          ? "#1e3a5f"
                          : isBase
                          ? "#052e16"
                          : isHovered
                          ? "#1e293b"
                          : "#0d1224",
                        borderRadius: 2,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 9, fontWeight: 700,
                        color: isRobot ? "#fff" : isBase ? "#22c55e" : "transparent",
                        transition: "background 0.15s",
                        cursor: "default",
                        animation: isRobot && robot.status === "MOVING" ? "pulse 0.5s infinite" : "none",
                        border: isBase ? "1px solid #22c55e33" : "none",
                      }}
                    >
                      {isRobot ? "●" : isBase && !isRobot ? "⚡" : ""}
                    </div>
                  );
                })
              )}
            </div>
            <div style={{ display: "flex", gap: 20, marginTop: 12, justifyContent: "center" }}>
              {[
                { color: "#3b82f6", label: "Robot" },
                { color: "#1e3a5f", label: "Obstacle" },
                { color: "#22c55e", label: "Charging Station" },
                { color: "#0d1224", label: "Free Space", border: "1px solid #1e3a5f" },
              ].map(({ color, label, border }) => (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: color, border }} />
                  <span style={{ color: "#64748b", fontSize: 10 }}>{label}</span>
                </div>
              ))}
            </div>
            {hoveredCell && (
              <div style={{ textAlign: "center", color: "#64748b", fontSize: 10, marginTop: 8 }}>
                ({hoveredCell[0]}, {hoveredCell[1]})
                {isObstacle(hoveredCell[0], hoveredCell[1]) ? " — OBSTACLE" : ""}
              </div>
            )}
          </div>
        </div>

        {/* Right panel — audit log */}
        <div style={{ background: "#0d1224", padding: 20, display: "flex", flexDirection: "column", borderLeft: "1px solid #1e3a5f22" }}>
          <div style={{ color: "#3b82f6", fontSize: 10, letterSpacing: 2, marginBottom: 12, fontWeight: 600 }}>AUDIT LOG</div>
          <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
            {logs.length === 0 ? (
              <div style={{ color: "#475569", fontSize: 11, textAlign: "center", marginTop: 20 }}>No commands logged yet</div>
            ) : (
              logs.map(log => (
                <div key={log.id} style={{
                  background: "#0a0e1a", border: "1px solid #1e3a5f",
                  borderLeft: `3px solid ${log.outcome.startsWith("SUCCESS") ? "#22c55e" : "#ef4444"}`,
                  borderRadius: 4, padding: "8px 10px",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ color: log.outcome.startsWith("SUCCESS") ? "#22c55e" : "#ef4444", fontSize: 10, fontWeight: 600 }}>
                      {log.command}
                    </span>
                    <span style={{ color: "#475569", fontSize: 9 }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ color: "#64748b", fontSize: 10 }}>{log.user} · {log.target}</div>
                  <div style={{ color: "#475569", fontSize: 10, marginTop: 2 }}>{log.outcome}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
