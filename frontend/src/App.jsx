import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('landing'); // 'landing' | 'editor'
  const [history, setHistory] = useState([]);
  const [activeFileName, setActiveFileName] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [segments, setSegments] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const fileInputRef = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/history');
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const seek = (seconds) => {
    if (audioRef.current) {
      audioRef.current.currentTime += seconds;
    }
  };

  const handleSeekTo = (time) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  // Function to handle file validation and setting
  const validateAndSetFile = (selectedFile) => {
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a', 'audio/mp3', 'audio/mpeg3', 'audio/x-mpeg-3', 'audio/x-mp3'];
    // Simple extension check as mime types can vary
    const validExtensions = ['.mp3', '.wav', '.m4a', '.mp4'];
    const extension = '.' + selectedFile.name.split('.').pop().toLowerCase();

    if (validExtensions.includes(extension) || validTypes.includes(selectedFile.type)) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please upload a valid audio file (MP3, WAV, M4A, MP4).');
      setFile(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:8000/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setTranscript(response.data.transcript);
      setActiveFileName(response.data.filename);
      setAudioUrl(response.data.audio_url);
      setSegments(response.data.segments);
      setView('editor');
      fetchHistory(); // Refresh history
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'An error occurred during transcription.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setTranscript('');
    setActiveFileName('');
    setAudioUrl('');
    setSegments([]);
    setView('landing');
    setError(null);
    setIsPlaying(false);
  };

  const handleExport = () => {
    if (!transcript) return;
    const element = document.createElement("a");
    const fileContent = new Blob([transcript], { type: 'text/plain' });
    element.href = URL.createObjectURL(fileContent);
    element.download = `${activeFileName || 'transcript'}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleViewHistory = (item) => {
    setTranscript(item.transcript);
    setActiveFileName(item.filename);
    setAudioUrl(item.audio_path);
    setSegments(item.segments || []);
    setView('editor');
    setIsPlaying(false);
  };

  const handleDeleteHistory = async (e, id) => {
    e.stopPropagation();
    try {
      await axios.delete(`http://127.0.0.1:8000/history/${id}`);
      fetchHistory();
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  if (view === 'editor') {
    return (
      <div className="bg-background-light dark:bg-background-dark text-slate-800 dark:text-slate-200 h-screen flex flex-col overflow-hidden font-display">
        {/* Hidden Audio Element */}
        <audio
          ref={audioRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onEnded={() => setIsPlaying(false)}
        />

        {/* Top Navigation Bar */}
        <header className="h-16 border-b border-primary/10 bg-white dark:bg-[#151c2c] px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-3 cursor-pointer" onClick={handleReset}>
            <div className="w-10 h-10 bg-primary flex items-center justify-center rounded-lg">
              <span className="material-icons text-white">record_voice_over</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">EchoText <span className="text-primary font-medium text-sm ml-1 uppercase tracking-widest">Editor</span></h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-full text-xs font-semibold">
              <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
              Autosaved to History
            </div>
            <div className="relative group">
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-all font-medium"
              >
                <span className="material-icons text-sm">file_download</span>
                Export .txt
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 flex overflow-hidden">
          {/* Audio Control Sidebar (Left) */}
          <aside className="w-80 border-r border-primary/10 bg-white dark:bg-[#151c2c] flex flex-col p-6 space-y-8 hidden md:flex">
            <div className="space-y-4">
              <div className="relative w-full aspect-video rounded-xl bg-primary/5 border border-primary/10 overflow-hidden flex flex-center items-center justify-center group/audio">
                <span className="material-icons text-primary text-5xl opacity-50">audiotrack</span>
                {audioUrl && (
                  <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/20 to-transparent">
                    <div className="h-1 bg-white/20 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all duration-100"
                        style={{ width: `${(currentTime / (audioRef.current?.duration || 1)) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
              <div className="text-center">
                <p className="text-xs font-semibold text-primary/60 mt-2 uppercase tracking-tighter truncate">{activeFileName || 'audio_file.mp3'}</p>
              </div>
            </div>

            {/* Audio Controls */}
            <div className="flex items-center justify-center gap-6">
              <button
                onClick={() => seek(-10)}
                className="text-slate-400 hover:text-primary transition-colors"
              >
                <span className="material-icons text-2xl">replay_10</span>
              </button>
              <button
                onClick={togglePlay}
                className="w-14 h-14 bg-primary text-white rounded-full shadow-lg shadow-primary/30 flex items-center justify-center hover:scale-105 active:scale-95 transition-all"
              >
                <span className="material-icons text-4xl">{isPlaying ? 'pause' : 'play_arrow'}</span>
              </button>
              <button
                onClick={() => seek(10)}
                className="text-slate-400 hover:text-primary transition-colors"
              >
                <span className="material-icons text-2xl">forward_10</span>
              </button>
            </div>

            <div className="text-center text-[10px] text-slate-500 font-mono">
              {formatTime(currentTime)} / {audioRef.current ? formatTime(audioRef.current.duration) : '00:00'}
            </div>
          </aside>

          {/* Transcription Workspace (Right) */}
          <section className="flex-1 bg-background-light dark:bg-[#101622] overflow-y-auto p-12">
            <div className="max-w-4xl mx-auto pb-24">
              <div className="flex-1">
                {segments.length > 0 ? (
                  <div className="flex flex-wrap gap-x-1.5 gap-y-1">
                    {segments.map((seg, idx) => {
                      const isActive = currentTime >= seg.start && currentTime < seg.end;
                      return (
                        <span
                          key={idx}
                          onClick={() => handleSeekTo(seg.start)}
                          className={`text-lg leading-relaxed font-display transition-all cursor-pointer rounded px-1
                                          ${isActive ? 'bg-primary/20 text-primary scale-105 shadow-sm' : 'text-slate-700 dark:text-slate-300 hover:bg-primary/5'}
                                      `}
                        >
                          {seg.text}
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-lg leading-relaxed text-slate-700 dark:text-slate-300 font-display whitespace-pre-wrap">
                    {transcript}
                  </p>
                )}
              </div>
            </div>
          </section>
        </main>

        {/* Footer Status Bar */}
        <footer className="h-10 border-t border-primary/10 bg-white dark:bg-[#151c2c] px-6 flex items-center justify-between text-[11px] font-medium text-slate-500">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5"><span className="material-icons text-xs text-primary">check_circle</span> Click text to play audio from that time</span>
          </div>
        </footer>
      </div>
    );
  }

  // Helper to format time
  function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Landing Page View
  return (
    <div className="bg-background-light dark:bg-background-dark text-slate-800 dark:text-slate-200 min-h-screen flex flex-col font-display transition-colors duration-300">
      {/* Header */}
      <header className="w-full border-b border-slate-200 dark:border-border-dark py-4 px-8 bg-white/50 dark:bg-background-dark/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary p-1.5 rounded-lg">
              <span className="material-icons text-white text-xl">graphic_eq</span>
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">EchoText</span>
          </div>
          <nav className="flex items-center gap-6">
            <button className="bg-primary hover:bg-primary/90 text-white px-5 py-2 rounded-lg text-sm font-semibold transition-all">
              Upgrade Pro
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-grow flex flex-col items-center justify-center px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-10 max-w-2xl">
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white mb-4 tracking-tight">
            Turn Audio into Text <br /><span className="text-primary">in Seconds.</span>
          </h1>
          <p className="text-slate-600 dark:text-slate-400 text-lg">
            Simple, fast, and accurate transcription for meetings, podcasts, and interviews.
          </p>
        </div>

        {/* Upload Container */}
        <div className="w-full max-w-3xl bg-white dark:bg-surface-dark p-8 rounded-xl shadow-xl border border-slate-200 dark:border-border-dark">
          {/* Drag & Drop Area */}
          {!file ? (
            <div
              className="upload-dashed group relative flex flex-col items-center justify-center p-12 mb-8 cursor-pointer transition-all hover:bg-primary/5"
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".mp3,.wav,.m4a,.mp4"
                onChange={handleFileSelect}
              />
              <div className="bg-primary/10 dark:bg-primary/20 p-4 rounded-full mb-4 group-hover:scale-110 transition-transform">
                <span className="material-icons text-primary text-4xl">cloud_upload</span>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">Drag & drop your audio file</h3>
              <p className="text-slate-500 dark:text-slate-400 mb-6">MP3, WAV, M4A (Max 50MB)</p>
              <button className="bg-primary text-white px-8 py-3 rounded-lg font-bold shadow-lg shadow-primary/20 hover:shadow-primary/40 active:scale-95 transition-all">
                Select File
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-12 mb-8 border border-primary/20 bg-primary/5 rounded-xl">
              <div className="bg-primary p-4 rounded-full mb-4">
                <span className="material-icons text-white text-4xl">audiotrack</span>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">{file.name}</h3>
              <p className="text-slate-500 dark:text-slate-400 mb-6">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>

              <div className="flex gap-4">
                <button
                  onClick={handleReset}
                  className="px-6 py-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-300 font-semibold"
                  disabled={isLoading}
                >
                  Change File
                </button>
                <button
                  onClick={handleUpload}
                  disabled={isLoading}
                  className="bg-primary text-white px-8 py-2 rounded-lg font-bold shadow-lg shadow-primary/20 hover:shadow-primary/40 active:scale-95 transition-all flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <span>Transcribe Now</span>
                      <span className="material-icons text-sm">arrow_forward</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 flex items-center gap-2">
              <span className="material-icons text-sm">error</span>
              {error}
            </div>
          )}

          {/* Recent Section */}
          <div className="mt-8 border-t border-slate-200 dark:border-border-dark pt-8">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-icons text-primary text-lg">history</span>
                Recent Activity
              </div>
              {history.length > 0 && <span className="text-xs font-medium text-slate-400">{history.length} items saved</span>}
            </h2>

            {history.length > 0 ? (
              <div className="space-y-3">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleViewHistory(item)}
                    className="flex items-center justify-between p-4 bg-slate-50 dark:bg-background-dark/30 hover:bg-primary/5 dark:hover:bg-primary/10 rounded-xl border border-slate-200 dark:border-slate-800 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <span className="material-icons text-base">description</span>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate max-w-[200px]">{item.filename}</h4>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider">{new Date(item.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDeleteHistory(e, item.id)}
                      className="p-2 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                    >
                      <span className="material-icons text-base">delete_outline</span>
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 bg-slate-50 dark:bg-background-dark rounded-xl border border-dashed border-slate-300 dark:border-slate-700 text-center text-slate-500 text-sm">
                No recent transcriptions
              </div>
            )}
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 px-8 border-t border-slate-200 dark:border-border-dark bg-white dark:bg-background-dark">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 opacity-50">
            <span className="material-icons text-sm">graphic_eq</span>
            <span className="text-sm font-medium">© 2024 EchoText Inc.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
