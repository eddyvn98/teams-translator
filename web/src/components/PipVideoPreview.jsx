import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Minimize2, Maximize2, X, GripHorizontal } from 'lucide-react';

export default function PipVideoPreview({ mediaStream, isVisible = true, onClose }) {
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [position, setPosition] = useState(() => {
    if (typeof window === 'undefined') return null;
    const width = typeof window !== 'undefined' && window.innerWidth < 640 ? 240 : 288;
    const height = typeof window !== 'undefined' && window.innerWidth < 640 ? 140 : 176;
    return {
      x: Math.max(16, (typeof window !== 'undefined' ? window.innerWidth : 800) - width - 24),
      y: Math.max(70, (typeof window !== 'undefined' ? window.innerHeight : 600) - height - 96),
    };
  });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ mouseX: 0, mouseY: 0, elemX: 0, elemY: 0 });

  useEffect(() => {
    if (videoRef.current && mediaStream) {
      videoRef.current.srcObject = mediaStream;
    }
  }, [mediaStream]);

  const handlePointerDown = (e) => {
    if (e.button !== undefined && e.button !== 0) return;
    if (e.target.closest('button')) return;

    const clientX = e.clientX ?? e.touches?.[0]?.clientX;
    const clientY = e.clientY ?? e.touches?.[0]?.clientY;
    if (clientX === undefined || clientY === undefined) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    dragStartRef.current = {
      mouseX: clientX,
      mouseY: clientY,
      elemX: rect.left,
      elemY: rect.top,
    };
    setIsDragging(true);
  };

  const handlePointerMove = useCallback(
    (e) => {
      if (!isDragging) return;
      const clientX = e.clientX ?? e.touches?.[0]?.clientX;
      const clientY = e.clientY ?? e.touches?.[0]?.clientY;
      if (clientX === undefined || clientY === undefined) return;

      const deltaX = clientX - dragStartRef.current.mouseX;
      const deltaY = clientY - dragStartRef.current.mouseY;

      const rect = containerRef.current?.getBoundingClientRect();
      const width = rect?.width || 288;
      const height = rect?.height || 176;

      const newX = Math.max(8, Math.min(window.innerWidth - width - 8, dragStartRef.current.elemX + deltaX));
      const newY = Math.max(60, Math.min(window.innerHeight - height - 8, dragStartRef.current.elemY + deltaY));

      setPosition({ x: newX, y: newY });
    },
    [isDragging]
  );

  const handlePointerUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handlePointerMove);
      window.addEventListener('mouseup', handlePointerUp);
      window.addEventListener('touchmove', handlePointerMove, { passive: false });
      window.addEventListener('touchend', handlePointerUp);
      return () => {
        window.removeEventListener('mousemove', handlePointerMove);
        window.removeEventListener('mouseup', handlePointerUp);
        window.removeEventListener('touchmove', handlePointerMove);
        window.removeEventListener('touchend', handlePointerUp);
      };
    }
  }, [isDragging, handlePointerMove, handlePointerUp]);

  if (!mediaStream || !isVisible) return null;

  return (
    <div
      ref={containerRef}
      onMouseDown={handlePointerDown}
      onTouchStart={handlePointerDown}
      style={
        position
          ? { left: `${position.x}px`, top: `${position.y}px` }
          : { right: '24px', bottom: '96px' }
      }
      className={`fixed z-30 bg-black rounded-xl overflow-hidden shadow-2xl border border-white/20 select-none cursor-grab active:cursor-grabbing transition-shadow duration-150 ${
        isDragging ? 'shadow-[0_20px_50px_rgba(0,0,0,0.6)] ring-2 ring-[#1a73e8]' : ''
      } ${isMinimized ? 'w-48 h-28' : 'w-64 h-38 sm:w-72 sm:h-44 md:w-80 md:h-48'}`}
    >
      {/* Video Stream */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover pointer-events-none"
      />

      {/* Drag Header Bar / Toolbar */}
      <div className="absolute top-0 inset-x-0 h-8 flex items-center justify-between px-2 bg-gradient-to-b from-black/80 via-black/40 to-transparent">
        <div className="flex items-center space-x-1 text-white/80 text-[11px]">
          <GripHorizontal size={14} className="opacity-80" />
          <span className="font-medium text-[10px] tracking-wide">Drag to move</span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            type="button"
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 text-white/80 hover:text-white hover:bg-white/20 rounded transition-colors"
            title={isMinimized ? 'Expand' : 'Minimize'}
          >
            {isMinimized ? <Maximize2 size={13} /> : <Minimize2 size={13} />}
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 text-white/80 hover:text-white hover:bg-white/20 rounded transition-colors"
              title="Close preview"
            >
              <X size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Live Badge */}
      <div className="absolute bottom-2 left-2 flex items-center space-x-1.5 bg-black/70 backdrop-blur-xs px-2 py-0.5 rounded-full text-[10px] text-white/90 pointer-events-none">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        <span>Live Tab</span>
      </div>
    </div>
  );
}
