import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Upload, Database, AlertCircle, MessageSquare, 
  Send, Activity, Layers, Hash, FileCheck, Maximize2, FileText, Download, Info
} from 'lucide-react';
import { 
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';

export default function App() {
  // Existing States
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatQuery, setChatQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatting, setIsChatting] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // States for Dynamic Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [dynamicChartData, setDynamicChartData] = useState({ columns: [], sample_data: [], chart_data: [], chart_insights: null });
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [isPlotted, setIsPlotted] = useState(false);

  const loadChartData = async (selectedX, selectedY) => {
    if (!report?.filepath || !selectedX || !selectedY) return;

    try {
      const response = await axios.get('http://127.0.0.1:8000/api/dataset/visualize', {
        params: {
          file_path: report.filepath,
          x_axis: selectedX,
          y_axis: selectedY
        }
      });

      setDynamicChartData({
        columns: response.data.columns || [],
        sample_data: response.data.sample_data || [],
        chart_data: response.data.chart_data || [],
        chart_insights: response.data.chart_insights || null
      });
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  // Fetch Dynamic Data when Modal Opens
  useEffect(() => {
    if (isModalOpen && report?.filepath) {
      axios.get('http://127.0.0.1:8000/api/dataset/visualize', {
        params: { file_path: report.filepath }
      })
      .then(response => {
        setDynamicChartData({
          columns: response.data.columns || [],
          sample_data: response.data.sample_data || [],
          chart_data: response.data.chart_data || [],
          chart_insights: response.data.chart_insights || null
        });

        if (response.data.columns && response.data.columns.length >= 2) {
          setXAxis(response.data.columns[0]);
          setYAxis(response.data.columns[1]);
          setIsPlotted(false);
        }
      })
      .catch(err => console.error('Error fetching chart data:', err));
    }
  }, [isModalOpen, report?.filepath]);

  const chartDataToRender = useMemo(() => {
    return dynamicChartData.chart_data?.length ? dynamicChartData.chart_data : [];
  }, [dynamicChartData.chart_data]);

  const chartInsights = useMemo(() => {
    return isPlotted ? dynamicChartData.chart_insights : null;
  }, [dynamicChartData.chart_insights, isPlotted]);

  const qualityScore = report?.data_quality_score ?? 0;
  const qualityScoreLabel = report?.data_quality_label || 'Unknown';
  const missingRate = report?.data_quality_breakdown?.missing_rate;
  const duplicateRate = report?.data_quality_breakdown?.duplicate_rate;
  const qualityCircleCircumference = 2 * Math.PI * 40;
  const qualityOffset = qualityCircleCircumference * (1 - qualityScore / 100);

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
        ...response.data
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
        'http://127.0.0.1:8000/api/chat',
        {
          query,
          file_path: report.filepath,
          dataset_summary: report.dataset_summary || {}
        }
      );
      setChatHistory(prev => [...prev, { role: 'ai', content: response.data.response }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'Agentic automation system unavailable. Please verify backend connection.' }]);
    } finally {
      setIsChatting(false);
    }
  };

  // Live function for triggering the backend PDF generator
  const handleGenerateReport = async () => {
    if (!report?.filepath) return;
    
    setIsGeneratingReport(true);
    try {
      const response = await axios.get(
        `http://127.0.0.1:8000/api/report/generate?file_path=${encodeURIComponent(report.filepath)}`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Executive_Comprehensive_Report.pdf');
      document.body.appendChild(link);
      link.click();
      
      link.parentNode.removeChild(link);
    } catch (error) {
      console.error('Error generating report:', error);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-white p-6 font-sans relative flex flex-col">
      {/* Top Navbar */}
      <header className="flex items-center justify-between pb-6 border-b border-white/10 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/20 rounded-lg">
            <Activity className="text-indigo-400" size={24} />
          </div>
          <h1 className="text-2xl font-semibold tracking-wide">Agentic Data Automation</h1>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
        
        {/* Left Sidebar Column */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          
          {/* Widget 1: Dataset Management */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 h-fit">
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

          {/* Widget 2: Report Generation */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 h-fit">
            <h2 className="text-lg font-medium mb-2 flex items-center gap-2">
              <FileText size={20} className="text-indigo-400" />
              Executive Report
            </h2>
            <p className="text-sm text-gray-400 mb-5">
              Compile dataset statistics and variance relationships into a formal PDF report.
            </p>
            <button 
              onClick={handleGenerateReport}
              disabled={!report || isGeneratingReport}
              className="w-full py-3 bg-white/10 hover:bg-white/15 border border-white/10 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isGeneratingReport ? (
                <>
                  <Activity size={18} className="animate-spin text-indigo-400" /> Compiling PDF...
                </>
              ) : (
                <>
                  <Download size={18} className="text-indigo-400" /> Generate PDF Report
                </>
              )}
            </button>
          </div>

        </div>

        {/* Main Interface */}
        <div className="lg:col-span-3 space-y-6 flex flex-col">
          
          {/* High-Level Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Rows', value: report?.total_rows ?? '--', icon: Layers, color: 'text-blue-400' },
              { label: 'Total Variables', value: report?.columns ?? '--', icon: Hash, color: 'text-emerald-400' },
              { label: 'Duplicate Rows', value: report?.duplicates ?? '--', icon: Database, color: 'text-yellow-400' },
              { label: 'Anomalies Detected', value: report?.anomaly_count ?? '--', icon: AlertCircle, color: 'text-rose-400' },
              { label: 'Data Quality', value: report?.data_quality_score != null ? `${report.data_quality_score}%` : '--', icon: Info, color: 'text-cyan-400' },
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

          {/* NEW: Dynamic Dataset Summary Banner */}
          {report?.summary && (
            <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-2xl p-5 flex flex-col gap-6">
              <div className="grid grid-cols-1 xl:grid-cols-[220px_minmax(0,1fr)] gap-4 items-center">
                <div className="bg-slate-950/30 border border-white/10 rounded-3xl p-4 flex items-center justify-center">
                  <div className="relative w-28 h-28">
                    <svg viewBox="0 0 100 100" className="w-full h-full">
                      <circle cx="50" cy="50" r="40" stroke="#334155" strokeWidth="12" fill="none" />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="#38bdf8"
                        strokeWidth="12"
                        fill="none"
                        strokeDasharray={qualityCircleCircumference}
                        strokeDashoffset={qualityOffset}
                        strokeLinecap="round"
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-2xl font-semibold text-white">{qualityScore}%</span>
                      <span className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Quality</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-8 rounded-full bg-cyan-400/40" />
                    <div>
                      <h3 className="text-base font-medium text-indigo-100">Automated Dataset Overview</h3>
                      <p className="text-indigo-200/75 text-sm leading-relaxed">{report.summary}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                      <div className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-1">Quality Grade</div>
                      <div className="text-lg font-semibold text-white">{qualityScoreLabel}</div>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                      <div className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-1">Missing Rate</div>
                      <div className="text-lg font-semibold text-white">{missingRate != null ? `${(missingRate * 100).toFixed(1)}%` : '--'}</div>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                      <div className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-1">Duplicate Rate</div>
                      <div className="text-lg font-semibold text-white">{duplicateRate != null ? `${(duplicateRate * 100).toFixed(1)}%` : '--'}</div>
                    </div>
                  </div>
                </div>
              </div>
              {report.top_missing_columns?.length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                  <div className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">Columns Most Affected by Missing Data</div>
                  <ul className="space-y-2 text-sm text-gray-200">
                    {report.top_missing_columns.map((column, idx) => (
                      <li key={idx} className="flex justify-between gap-4">
                        <span>{column.column}</span>
                        <span className="font-semibold">{column.missing_values}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Interactive Modules */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-1">
            
            {/* Glowing Recharts Component */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 flex flex-col min-h-[500px] xl:h-[calc(100vh-260px)]">
              
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-medium text-gray-200">Operations Variance Trend</h3>
                <button 
                  onClick={() => setIsModalOpen(true)}
                  className="bg-indigo-600/80 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-sm transition-colors flex items-center gap-2"
                >
                  <Maximize2 size={14} /> Expand Analysis
                </button>
              </div>

              <div className="flex-1 w-full min-h-[0]">
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
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl flex flex-col min-h-[500px] xl:h-[calc(100vh-260px)]">
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

      {/* The Glassmorphism Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-[min(98vw,1200px)] h-[95vh] max-h-[95vh] bg-[#0B0E14]/95 border border-white/10 rounded-2xl p-6 shadow-2xl flex flex-col overflow-hidden">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-white">Dynamic Data Explorer</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-white transition-colors text-xl font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto">
              <div className="flex flex-col gap-6 mb-6 bg-white/5 p-4 rounded-xl border border-white/10">
                <div className="flex flex-col">
                  <label className="text-sm text-gray-400 mb-2">X-Axis (Independent Variable)</label>
                  <select
                    className="bg-[#0B0E14] border border-gray-700 text-white p-2.5 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
                    value={xAxis}
                    onChange={(e) => {
                      setXAxis(e.target.value);
                      setIsPlotted(false);
                      setDynamicChartData(prev => ({ ...prev, chart_data: [], chart_insights: null }));
                    }}
                  >
                    {dynamicChartData.columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col">
                  <label className="text-sm text-gray-400 mb-2">Y-Axis (Dependent Variable)</label>
                  <select
                    className="bg-[#0B0E14] border border-gray-700 text-white p-2.5 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
                    value={yAxis}
                    onChange={(e) => {
                      setYAxis(e.target.value);
                      setIsPlotted(false);
                      setDynamicChartData(prev => ({ ...prev, chart_data: [], chart_insights: null }));
                    }}
                  >
                    {dynamicChartData.columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col justify-end">
                  <button
                    onClick={async () => {
                      await loadChartData(xAxis, yAxis);
                      setIsPlotted(true);
                    }}
                    disabled={!xAxis || !yAxis}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed h-[46px]"
                  >
                    Generate Plot
                  </button>
                </div>
              </div>

              <div className="flex-1 bg-[#0B0E14]/50 rounded-xl border border-white/10 flex flex-col p-4 overflow-hidden">
                {!isPlotted ? (
                  <div className="h-full flex flex-col items-center justify-center">
                    <Activity className="text-gray-600 mb-4 opacity-50" size={48} />
                    <p className="text-gray-400 text-lg">
                      Select your variables and click <span className="text-indigo-400 font-medium">Generate Plot</span>
                    </p>
                  </div>
                ) : (
                  <div className="h-full w-full flex flex-col gap-4 overflow-y-auto pb-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div className="bg-slate-950/40 border border-white/10 rounded-2xl p-4">
                        <h4 className="text-sm text-gray-400 mb-2">Top Insight</h4>
                        {chartInsights ? (
                          <div className="space-y-3 text-sm text-gray-200">
                            <div>
                              <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Highest {yAxis}</div>
                              <div className="mt-1 font-semibold text-white">{chartInsights.highest.value}</div>
                              <div className="text-gray-400">{xAxis}: {chartInsights.highest.x}</div>
                            </div>
                            <div>
                              <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Lowest {yAxis}</div>
                              <div className="mt-1 font-semibold text-white">{chartInsights.lowest.value}</div>
                              <div className="text-gray-400">{xAxis}: {chartInsights.lowest.x}</div>
                            </div>
                            <div>
                              <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Largest spread</div>
                              <div className="mt-1 font-semibold text-white">{chartInsights.largestSpread.group}</div>
                              <div className="text-gray-400">Range: {chartInsights.largestSpread.range.toFixed(2)}</div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-sm text-gray-400">No dataset insights available.</div>
                        )}
                      </div>
                      <div className="bg-slate-950/40 border border-white/10 rounded-2xl p-4">
                        <h4 className="text-sm text-gray-400 mb-2">Dataset Summary</h4>
                        {chartInsights ? (
                          <div className="space-y-3 text-sm text-gray-200">
                            <div>
                              <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Total records</div>
                              <div className="mt-1 font-semibold text-white">{chartInsights.totalRecords}</div>
                            </div>
                            <div>
                              <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Groups</div>
                              <div className="mt-1 font-semibold text-white">{chartInsights.totalGroups}</div>
                            </div>
                            <div>
                              <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Highest average {yAxis}</div>
                              <div className="mt-1 font-semibold text-white">{chartInsights.highestAverage?.avg?.toFixed(2)}</div>
                              <div className="text-gray-400">Group: {chartInsights.highestAverage?.group}</div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-sm text-gray-400">No dataset summary available.</div>
                        )}
                      </div>
                    </div>

                    <div className="h-[340px] w-full min-h-[0] bg-slate-950/40 border border-white/10 rounded-2xl p-4 flex flex-col">
                      <div className="flex items-center justify-between mb-4 gap-4">
                        <h3 className="text-gray-300 font-medium text-center flex-1">
                          Variance Profile: {xAxis} vs {yAxis}
                        </h3>
                        <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                          Points: {chartDataToRender.length}
                        </div>
                      </div>
                      <div className="flex-1 w-full min-h-[0]">
                        {chartDataToRender.length === 0 ? (
                          <div className="h-full flex items-center justify-center text-sm text-gray-400">
                            No chart data found for the selected variables.
                          </div>
                        ) : (
                          <ResponsiveContainer width="100%" height={320}>
                            <LineChart data={chartDataToRender} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                              <XAxis
                                type="category"
                                dataKey={xAxis}
                                stroke="#ffffff50"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#94a3b8', fontSize: 12 }}
                                minTickGap={30}
                              />
                              <YAxis
                                type="number"
                                stroke="#ffffff50"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#94a3b8', fontSize: 12 }}
                                domain={["auto", "auto"]}
                              />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #ffffff10', borderRadius: '12px', color: '#fff' }}
                                itemStyle={{ color: '#e2e8f0' }}
                                labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                              />
                              <Line
                                type="monotone"
                                dataKey={`${yAxis}Average`}
                                stroke="#6366f1"
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4 }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}