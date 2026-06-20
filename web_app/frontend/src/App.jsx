import { useState, useEffect, useRef } from 'react';
import { Play, Square, Settings2, Terminal, RefreshCw, RotateCcw, Zap } from 'lucide-react';

export default function App() {
  const [config, setConfig] = useState({
    sheet_id: '1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc',
    source_tab: 'Đạt _ Đức',
    target_tab: 'Đạt_Mỹ',
    start_row: 1197,
    end_row: 1500,
    auto_mode: false
  });

  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState(["Hệ thống đã sẵn sàng."]);
  const endOfLogsRef = useRef(null);

  useEffect(() => {
    endOfLogsRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Check initial status
  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setIsRunning(data.is_running))
      .catch(() => setLogs(prev => [...prev, "❌ Không thể kết nối tới Backend (/api)"]));
  }, []);

  const handleStart = async () => {
    if (isRunning) return;
    setLogs(["🚀 Đang gửi yêu cầu bắt đầu dịch..."]);
    setIsRunning(true);
    
    try {
      const res = await fetch('/api/translate-range', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await res.json();
      if (data.status === 'error') {
        setLogs(prev => [...prev, `❌ Lỗi: ${data.message}`]);
        setIsRunning(false);
        return;
      }
      
      const eventSource = new EventSource('/api/logs');
      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close();
          setIsRunning(false);
          setLogs(prev => [...prev, "✅ Tiến trình hoàn tất!"]);
        } else if (event.data !== 'ping') {
          setLogs(prev => [...prev, event.data]);
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        setIsRunning(false);
        setLogs(prev => [...prev, "⚠️ Mất kết nối luồng log (SSE)."]);
      };
      
    } catch (err) {
      setLogs(prev => [...prev, `❌ Lỗi kết nối: ${err.message}`]);
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    try {
      setLogs(prev => [...prev, "⏳ Đang gửi lệnh dừng tiến trình..."]);
      await fetch('/api/stop', { method: 'POST' });
    } catch (err) {
      setLogs(prev => [...prev, `❌ Lỗi khi gửi lệnh dừng: ${err.message}`]);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 font-sans p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        
        <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
              AutoTranslate Pro
            </h1>
            <p className="text-neutral-400 mt-1">Hệ thống dịch và đẩy Google Sheets tốc độ cao</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              {isRunning && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${isRunning ? 'bg-emerald-500' : 'bg-neutral-600'}`}></span>
            </span>
            <span className="text-sm font-medium text-neutral-400 uppercase tracking-wider">
              {isRunning ? 'Đang chạy' : 'Sẵn sàng'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          <div className="lg:col-span-4 space-y-4">
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <Settings2 className="w-5 h-5 text-indigo-400" />
                  <h2 className="text-lg font-semibold">Cấu hình</h2>
                </div>
                <div className="flex items-center space-x-2 bg-neutral-950 p-1.5 rounded-lg border border-neutral-800">
                  <span className={`text-xs font-semibold uppercase ${config.auto_mode ? 'text-amber-400' : 'text-neutral-500'}`}>Auto Mode</span>
                  <button 
                    onClick={() => setConfig({...config, auto_mode: !config.auto_mode})}
                    disabled={isRunning}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${config.auto_mode ? 'bg-amber-500' : 'bg-neutral-700'} ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${config.auto_mode ? 'translate-x-4' : 'translate-x-1'}`} />
                  </button>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">ID Bảng tính (Sheet ID)</label>
                  <input 
                    type="text" 
                    value={config.sheet_id}
                    onChange={e => setConfig({...config, sheet_id: e.target.value})}
                    disabled={isRunning}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors disabled:opacity-50"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Tab Nguồn</label>
                    <input 
                      type="text" 
                      value={config.source_tab}
                      onChange={e => setConfig({...config, source_tab: e.target.value})}
                      disabled={isRunning}
                      className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Tab Đích</label>
                    <input 
                      type="text" 
                      value={config.target_tab}
                      onChange={e => setConfig({...config, target_tab: e.target.value})}
                      disabled={isRunning}
                      className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                    />
                  </div>
                </div>

                <div className={`grid ${config.auto_mode ? 'grid-cols-1' : 'grid-cols-2'} gap-4`}>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Từ dòng</label>
                    <input 
                      type="number" 
                      value={config.start_row}
                      onChange={e => setConfig({...config, start_row: parseInt(e.target.value) || 0})}
                      disabled={isRunning}
                      className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                    />
                  </div>
                  {!config.auto_mode && (
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Đến dòng</label>
                      <input 
                        type="number" 
                        value={config.end_row}
                        onChange={e => setConfig({...config, end_row: parseInt(e.target.value) || 0})}
                        disabled={isRunning}
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-neutral-800">
                {!isRunning ? (
                  <button
                    onClick={handleStart}
                    className={`w-full flex items-center justify-center space-x-2 py-3 rounded-lg font-medium transition-all shadow-lg text-white
                      ${config.auto_mode 
                        ? 'bg-amber-600 hover:bg-amber-500 hover:shadow-amber-500/25' 
                        : 'bg-indigo-600 hover:bg-indigo-500 hover:shadow-indigo-500/25'}`}
                  >
                    {config.auto_mode ? <Zap className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current" />}
                    <span>{config.auto_mode ? 'Bật Lính Gác (Auto Mode)' : 'Bắt đầu Dịch (Batch)'}</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStop}
                    className="w-full flex items-center justify-center space-x-2 py-3 rounded-lg font-medium transition-all shadow-lg bg-red-600 hover:bg-red-500 text-white hover:shadow-red-500/25"
                  >
                    <Square className="w-5 h-5 fill-current" />
                    <span>Dừng Tiến Trình</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="lg:col-span-8 flex flex-col">
            <div className="bg-[#0c0c0c] border border-neutral-800 rounded-xl overflow-hidden shadow-2xl flex-1 flex flex-col min-h-[500px]">
              
              <div className="bg-neutral-900 border-b border-neutral-800 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Terminal className="w-4 h-4 text-neutral-400" />
                  <span className="text-sm font-mono text-neutral-300">Live Console {config.auto_mode && <span className="text-amber-500 ml-1">(Auto-Mode)</span>}</span>
                </div>
                <button 
                  onClick={() => setLogs([])}
                  className="text-xs text-neutral-500 hover:text-neutral-300 flex items-center space-x-1 transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Clear</span>
                </button>
              </div>

              <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-1">
                {logs.map((log, idx) => {
                  let colorClass = "text-neutral-300";
                  if (log.includes("❌") || log.includes("🛑")) colorClass = "text-red-400";
                  if (log.includes("✅")) colorClass = "text-emerald-400";
                  if (log.includes("👉")) colorClass = "text-blue-400";
                  if (log.includes("🚀") || log.includes("🎉")) colorClass = "text-purple-400";
                  if (log.includes("☁️")) colorClass = "text-cyan-400";
                  if (log.includes("⚠️") || log.includes("⏳")) colorClass = "text-amber-400";
                  
                  return (
                    <div key={idx} className={`${colorClass} break-all whitespace-pre-wrap leading-relaxed`}>
                      {log}
                    </div>
                  );
                })}
                <div ref={endOfLogsRef} />
              </div>
              
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
