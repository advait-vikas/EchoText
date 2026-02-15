import React, { useState, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileAudio, CheckCircle, AlertCircle, Loader2, Download, RefreshCw } from 'lucide-react';

function App() {
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a', 'audio/mp3', 'audio/mpeg3', 'audio/x-mpeg-3', 'audio/x-mp3'];
    // Simple extension check as mime types can vary
    const validExtensions = ['.mp3', '.wav', '.m4a', '.mp4'];
    const extension = '.' + file.name.split('.').pop().toLowerCase();

    if (validExtensions.includes(extension) || validTypes.includes(file.type)) {
      setFile(file);
      setError(null);
      setTranscript('');
    } else {
      setError('Please upload a valid audio file (MP3, WAV, M4A, MP4).');
      setFile(null);
    }
  };

  const handleTranscribe = async () => {
    if (!file) return;

    setIsLoading(true);
    setError(null);
    setTranscript('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Assuming backend runs on 8000
      const response = await axios.post('http://127.0.0.1:8000/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setTranscript(response.data.transcript);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'An error occurred during transcription. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([transcript], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = "transcript.txt";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleReset = () => {
    setFile(null);
    setTranscript('');
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-12"
      >
        <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-pink-600">
          Audio to Text
        </h1>
        <p className="text-gray-400 text-lg">
          Transform your audio files into accurate text transcripts instantly using AI.
        </p>
      </motion.div>

      <div className="grid gap-8">
        <motion.div
          className="glass-panel"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <div
            className={`file-drop-zone ${dragActive ? 'active' : ''} ${file ? 'border-violet-500 bg-violet-500/10' : ''}`}
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
              onChange={handleChange}
            />

            <AnimatePresence mode="wait">
              {file ? (
                <motion.div
                  key="file-selected"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex flex-col items-center justify-center space-y-4"
                >
                  <div className="w-16 h-16 rounded-full bg-violet-600 flex items-center justify-center">
                    <FileAudio className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">{file.name}</h3>
                    <p className="text-gray-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                  <div className="flex gap-4 mt-4">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleReset(); }}
                      className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                      disabled={isLoading}
                    >
                      Change File
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleTranscribe(); }}
                      disabled={isLoading}
                      className="btn-primary flex items-center gap-2"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <span>Transcribe Now</span>
                        </>
                      )}
                    </button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="upload-prompt"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center space-y-4"
                >
                  <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center">
                    <Upload className="w-8 h-8 text-gray-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">Upload Audio File</h3>
                    <p className="text-gray-400 mt-2">Drag & drop or click to browse</p>
                    <p className="text-gray-500 text-sm mt-1">Supports MP3, WAV, M4A</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-6 p-4 rounded-lg bg-red-500/20 border border-red-500/50 flex items-center gap-3 text-red-200"
            >
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </motion.div>
          )}
        </motion.div>

        <AnimatePresence>
          {transcript && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-panel"
            >
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <h2 className="text-2xl font-bold text-white">Transcription Complete</h2>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleDownload}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors border border-white/20"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors border border-white/20"
                  >
                    <RefreshCw className="w-4 h-4" />
                    New
                  </button>
                </div>
              </div>
              <div className="relative">
                <textarea
                  readOnly
                  value={transcript}
                  className="w-full h-64 bg-black/40 border border-white/10 rounded-xl p-6 text-gray-300 leading-relaxed focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all resize-none custom-scrollbar"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
