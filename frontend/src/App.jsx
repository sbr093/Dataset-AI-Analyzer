import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Upload, Database, AlertCircle, MessageSquare, 
  Send, Activity, Layers, Hash, FileCheck, Maximize2
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';

export default function App() {
  // Existing States
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatQuery, setChatQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatting, setIsChatting] = useState(false);

  // States for Dynamic Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [dynamicChartData, setDynamicChartData] = useState({ columns: [], data: [] });
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [isPlotted, setIsPlotted] = useState(false);

  // Fetch Dynamic Data when Modal Opens
  useEffect(() => {
    if (isModalOpen) {
      fetch('http://localhost:8000/api/dataset/visualize')
        .then(res => res.json())
        .then(data => {
          setDynamicChartData(data);
          if (data.columns && data.columns.length >= 2) {
            setXAxis(data.columns[0]);
            setYAxis(data.columns[1]);
          }
        })
        .catch(err => console.error("Error fetching chart data:", err));
    }
  }, [isModalOpen]);

  // NEW: Process Data to Find the Min and Max Range for the Chart
  const chartDataToRender = useMemo(() => {
    if (!dynamicChartData.data || dynamicChartData.data.length === 0 || !xAxis || !yAxis) return [];

    const groupedData = {};

    // Group by X-axis and find Min/Max for the Y-axis
    dynamicChartData.data.forEach(row => {
      const xValue = row[xAxis];
      const yValue = Number(row[yAxis]);

      if (xValue !== undefined && !isNaN(yValue)) {
        if (!groupedData[xValue]) {
          groupedData[xValue] = { min: yValue, max: yValue };
        }
        groupedData[xValue].min = Math.min(groupedData[xValue].min, yValue);
        groupedData[xValue].max = Math.max(groupedData[xValue].max, yValue);
      }
    });

    // Convert grouped data into an array formatted for a Recharts Range Area
    return Object.entries(groupedData).map(([key, value]) => ({
      [xAxis]: key,
      // Recharts accepts an array of [bottomBoundary, topBoundary] to draw a range band
      [`${yAxis}Range`]: [value.min, value.max] 
    }));
  }, [dynamicChartData.data, xAxis, yAxis]);

  // Structural mock data for the aesthetic Recharts implementation
  const staticChartData = [
    { name: 'Mon', anomalies: 12, baseline: 45 },
    { name: 'Tue', anomalies: 19, baseline: 52 },
    { name: 'Wed', anomalies: 15, baseline: 48 },
    { name: 'Thu', anomalies: 28, baseline: 50 },
    { name: 'Fri', anomalies: 14, baseline: 47 },
    { name: 'Sat', anomalies: 45, baseline: 42 },
    { name: 'Sun', anomalies: 22, baseline: 44 },
  ];

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setReport({
        ...response.data,
        filepath: `data/${file.name}`,
        columns: 11,
        missing: 0,
        duplicates: 14
      });
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!chatQuery.trim() || !report?.filepath) return;

    const query = chatQuery;
    setChatQuery('');
    setChatHistory(prev => [...prev, { role: 'user', content: query }]);
    setIsChatting(true);

    try {
      const response = await axios.post(
        `http://127.0.0.1:8000/api/chat?query=${encodeURIComponent(query)}&file_path=${encodeURIComponent(report.filepath)}`
      );
      setChatHistory(prev => [...prev, { role: 'ai', content: response.data.response }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'Agentic automation system unavailable. Please verify backend connection.' }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-white p-6 font-sans relative">
      {/* Top Navbar */}
      <header className="flex items-center justify-between pb-6 border-b border-white/10 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/20 rounded-lg">
            <Activity className="text-indigo-400" size={24} />
          </div>
          <h1 className="text-2xl font-semibold tracking-wide">Agentic Data Automation</h1>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - File Upload Interface */}
        <div className="lg:col-span-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 h-fit">
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <Database size={20} className="text-indigo-400" />
            Dataset Management
          </h2>
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-white/20 rounded-xl p-6 text-center hover:bg-white/5 transition-colors cursor-pointer">
              <input 
                type="file" 
                accept=".csv"
                onChange={(e) => setFile(e.target.files[0])}
                className="hidden" 
                id="file-upload" 
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <Upload size={32} className="text-gray-400 mb-2" />
                <span className="text-sm text-gray-300">
                  {file ? file.name : 'Click to select CSV'}
                </span>
              </label>
            </div>
            <button 
              type="submit"
              disabled={!file || loading}
              className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? 'Processing Backend Calculations...' : 'Process Dataset'}
            </button>
          </form>
          {report && (
            <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center gap-2 text-emerald-400 text-sm">
              <FileCheck size={18} />
              Dataset structured and analyzed
            </div>
          )}
        </div>

        {/* Main Interface */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* High-Level Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Rows', value: report?.total_rows || '--', icon: Layers, color: 'text-blue-400' },
              { label: 'Total Variables', value: report?.columns || '--', icon: Hash, color: 'text-emerald-400' },
              { label: 'Duplicate Rows', value: report?.duplicates || '--', icon: Database, color: 'text-yellow-400' },
              { label: 'Anomalies Detected', value: report?.anomaly_count || '--', icon: AlertCircle, color: 'text-rose-400' },
            ].map((metric, idx) => (
              <div key={idx} className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-5 flex flex-col">
                <div className="flex items-center gap-2 mb-2 text-gray-400">
                  <metric.icon size={18} className={metric.color} />
                  <span className="text-sm">{metric.label}</span>
                </div>
                <span className="text-3xl font-bold">{metric.value}</span>
              </div>
            ))}
          </div>

          {/* Interactive Modules */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            
            {/* Glowing Recharts Component */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6">
              
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-medium text-gray-200">Operations Variance Trend</h3>
                <button 
                  onClick={() => setIsModalOpen(true)}
                  className="bg-indigo-600/80 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-sm transition-colors flex items-center gap-2"
                >
                  <Maximize2 size={14} /> Expand Analysis
                </button>
              </div>

              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={staticChartData}>
                    <defs>
                      <linearGradient id="colorAnomalies" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis dataKey="name" stroke="#ffffff50" axisLine={false} tickLine={false} />
                    <YAxis stroke="#ffffff50" axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #ffffff10', borderRadius: '12px', color: '#fff' }} 
                      itemStyle={{ color: '#e2e8f0' }}
                    />
                    <Area type="monotone" dataKey="anomalies" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorAnomalies)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Custom Query AI Chatbot */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl flex flex-col h-[400px]">
              <div className="p-4 border-b border-white/10 flex items-center gap-2">
                <MessageSquare size={18} className="text-indigo-400" />
                <h3 className="font-medium text-gray-200">Custom Analysis Agent</h3>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatHistory.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-gray-500 text-sm text-center px-4">
                    <MessageSquare size={32} className="mb-2 opacity-50" />
                    <p>Submit a custom query to trigger advanced data analysis.</p>
                  </div>
                ) : (
                  chatHistory.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-2xl p-3 text-sm ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white/10 text-gray-200 rounded-bl-none'}`}>
                        {msg.content}
                      </div>
                    </div>
                  ))
                )}
                {isChatting && (
                  <div className="flex justify-start">
                    <div className="bg-white/10 rounded-2xl rounded-bl-none p-4 w-16 flex justify-center items-center gap-1">
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={handleChat} className="p-4 pt-2">
                <div className="relative flex items-center">
                  <input
                    type="text"
                    value={chatQuery}
                    onChange={(e) => setChatQuery(e.target.value)}
                    placeholder={report ? "Ask a question about the dataset..." : "Upload a dataset first..."}
                    disabled={!report || isChatting}
                    className="w-full bg-white/5 border border-white/10 rounded-full py-3 pl-4 pr-12 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
                  />
                  <button 
                    type="submit" 
                    disabled={!report || !chatQuery.trim() || isChatting}
                    className="absolute right-2 p-2 bg-indigo-600 rounded-full hover:bg-indigo-500 transition-colors disabled:opacity-50"
                  >
                    <Send size={16} />
                  </button>
                </div>
              </form>
            </div>

          </div>
        </div>
      </div>

      {/* NEW: The Glassmorphism Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-11/12 h-5/6 bg-[#0B0E14]/95 border border-white/10 rounded-2xl p-6 shadow-2xl flex flex-col">
            
            {/* Header & Close Button */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-white">Dynamic Data Explorer</h2>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-white transition-colors text-xl font-bold"
              >
                ✕
              </button>
            </div>

            {/* Dropdown Controls */}
            <div className="flex gap-6 mb-6 bg-white/5 p-4 rounded-xl border border-white/10">
              <div className="flex flex-col flex-1">
                <label className="text-sm text-gray-400 mb-2">X-Axis (Independent Variable)</label>
                <select 
                  className="bg-[#0B0E14] border border-gray-700 text-white p-2.5 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
                  value={xAxis}
                  onChange={(e) => {
                    setXAxis(e.target.value);
                    setIsPlotted(false); // Reset plot state on change
                  }}
                >
                  {dynamicChartData.columns.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col flex-1">
                <label className="text-sm text-gray-400 mb-2">Y-Axis (Dependent Variable)</label>
                <select 
                  className="bg-[#0B0E14] border border-gray-700 text-white p-2.5 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
                  value={yAxis}
                  onChange={(e) => {
                    setYAxis(e.target.value);
                    setIsPlotted(false); // Reset plot state on change
                  }}
                >
                  {dynamicChartData.columns.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>

              {/* NEW: The Plot Button */}
              <div className="flex flex-col justify-end">
                <button 
                  onClick={() => setIsPlotted(true)}
                  disabled={!xAxis || !yAxis || isPlotted}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed h-[46px]"
                >
                  Generate Plot
                </button>
              </div>
            </div>

            {/* Dynamic Chart Container */}
            <div className="flex-1 bg-[#0B0E14]/50 rounded-xl border border-white/10 flex flex-col p-4">
              {!isPlotted ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Activity className="text-gray-600 mb-4 opacity-50" size={48} />
                  <p className="text-gray-400 text-lg">Select your variables and click <span className="text-indigo-400 font-medium">Generate Plot</span></p>
                </div>
              ) : (
                <div className="h-full w-full flex flex-col">
                  <h3 className="text-gray-300 font-medium mb-4 text-center">
                    Variance Profile: {xAxis} vs {yAxis}
                  </h3>
                  <div className="flex-1 w-full min-h-[0]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartDataToRender} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorDynamic" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6}/>
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                        <XAxis 
                          dataKey={xAxis} 
                          stroke="#ffffff50" 
                          axisLine={false} 
                          tickLine={false}
                          tick={{ fill: '#94a3b8', fontSize: 12 }}
                          minTickGap={30}
                        />
                        <YAxis 
                          stroke="#ffffff50" 
                          axisLine={false} 
                          tickLine={false}
                          tick={{ fill: '#94a3b8', fontSize: 12 }}
                        />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #ffffff10', borderRadius: '12px', color: '#fff' }} 
                          itemStyle={{ color: '#e2e8f0' }}
                          labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                          formatter={(value) => {
                            // Format the tooltip so it cleanly says [Min, Max] instead of a raw array
                            return Array.isArray(value) ? `Min: ${value[0]} - Max: ${value[1]}` : value;
                          }}
                        />
                        {/* UPDATE: dataKey mapped to our dynamic range array */}
                        <Area 
                          type="monotone" 
                          dataKey={`${yAxis}Range`} 
                          stroke="#6366f1" 
                          strokeWidth={2} 
                          fillOpacity={1} 
                          fill="url(#colorDynamic)" 
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>
      )}

    </div>
  );
}