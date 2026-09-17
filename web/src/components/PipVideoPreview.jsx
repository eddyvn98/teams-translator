import React, { useEffect, useRef, useState } from 'react';
import { Minimize2, Maximize2, X, Move } from 'lucide-react';

export default function PipVideoPreview({ mediaStream, isVisible = true, onClose }) {
  const videoRef = useRef(null);
  const [isMinimized, setIsMinimized] = useState(false);

  useEffect(() => {
    if (videoRef.current && mediaStream) {
      videoRef.current.srcObject = mediaStream;
    }
  }, [mediaStream]);

  if (!mediaStream || !isVisible) return null;

  return (
    <div
      className={`fixed right-8 bottom-24 z-30 transition-all duration-200 bg-black rounded-xl overflow-hidden shadow-2xl border border-[#dadce0] select-none ${
        isMinimized ? 'w-48 h-28' : 'w-72 h-44 sm:w-80 sm:h-48'
      }`}
    >
      {/* Video Stream */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
      />

      {/* Floating Toolbar inside PiP */}
      <div className="absolute top-2 right-2 flex items-center space-x-1 opacity-0 hover:opacity-100 transition-opacity bg-black/60 backdrop-blur-xs px-1.5 py-1 rounded-lg">
        <button
          onClick={() => setIsMinimized(!isMinimized)}
          className="p-1 text-white/80 hover:text-white rounded"
          title={isMinimized ? 'Phóng to' : 'Thu nhỏ'}
        >
          {isMinimized ? <Maximize2 size={13} /> : <Minimize2 size={13} />}
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 text-white/80 hover:text-white rounded"
            title="Đóng xem trước"
          >
            <X size={13} />
          </button>
        )}
      </div>

      {/* Live Badge */}
      <div className="absolute bottom-2 left-2 flex items-center space-x-1.5 bg-black/70 backdrop-blur-xs px-2 py-0.5 rounded-full text-[10px] text-white/90">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        <span>Live Tab</span>
      </div>
    </div>
  );
}
