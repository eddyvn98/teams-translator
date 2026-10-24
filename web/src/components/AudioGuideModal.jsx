import React, { useState } from 'react';
import {
  X,
  Check,
  Copy,
  Headphones,
  Mic,
  Volume2,
  Bluetooth,
  ShieldCheck,
  Radio,
} from 'lucide-react';

export default function AudioGuideModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('mac');
  const [copiedKey, setCopiedKey] = useState(null);

  if (!isOpen) return null;

  const handleCopy = (text, key) => {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => {
          setCopiedKey(key);
          setTimeout(() => setCopiedKey(null), 1800);
        })
        .catch(console.error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/45 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-[#dadce0] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#e3e3e3] bg-[#f8f9fa]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1a73e8] text-white flex items-center justify-center shadow-xs">
              <Headphones size={18} />
            </div>
            <div>
              <h2 className="text-[16px] font-semibold text-[#1f1f1f] leading-tight">
                Hướng dẫn cấu hình âm thanh 2 chiều
              </h2>
              <p className="text-[12px] text-[#5f6368]">
                Dành cho macOS, Windows, Microsoft Teams & Tai nghe Bluetooth
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#444746] hover:bg-[#e8eaed] transition-colors"
            title="Đóng"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-[#e3e3e3] bg-white px-5 pt-2 space-x-1 shrink-0 overflow-x-auto">
          <button
            onClick={() => setActiveTab('mac')}
            className={`flex items-center space-x-2 px-3.5 py-2.5 text-xs font-semibold rounded-t-lg transition-all border-b-2 -mb-[1px] whitespace-nowrap ${
              activeTab === 'mac'
                ? 'border-[#1a73e8] text-[#1a73e8] bg-[#f1f3f4]/50'
                : 'border-transparent text-[#5f6368] hover:text-[#202124] hover:bg-[#f8f9fa]'
            }`}
          >
            <span>🍎 macOS (MacBook)</span>
          </button>

          <button
            onClick={() => setActiveTab('teams')}
            className={`flex items-center space-x-2 px-3.5 py-2.5 text-xs font-semibold rounded-t-lg transition-all border-b-2 -mb-[1px] whitespace-nowrap ${
              activeTab === 'teams'
                ? 'border-[#1a73e8] text-[#1a73e8] bg-[#f1f3f4]/50'
                : 'border-transparent text-[#5f6368] hover:text-[#202124] hover:bg-[#f8f9fa]'
            }`}
          >
            <UsersIcon size={14} />
            <span>Microsoft Teams</span>
          </button>

          <button
            onClick={() => setActiveTab('bluetooth')}
            className={`flex items-center space-x-2 px-3.5 py-2.5 text-xs font-semibold rounded-t-lg transition-all border-b-2 -mb-[1px] whitespace-nowrap ${
              activeTab === 'bluetooth'
                ? 'border-[#1a73e8] text-[#1a73e8] bg-[#f1f3f4]/50'
                : 'border-transparent text-[#5f6368] hover:text-[#202124] hover:bg-[#f8f9fa]'
            }`}
          >
            <Bluetooth size={14} />
            <span>Tai nghe Bluetooth</span>
          </button>

          <button
            onClick={() => setActiveTab('windows')}
            className={`flex items-center space-x-2 px-3.5 py-2.5 text-xs font-semibold rounded-t-lg transition-all border-b-2 -mb-[1px] whitespace-nowrap ${
              activeTab === 'windows'
                ? 'border-[#1a73e8] text-[#1a73e8] bg-[#f1f3f4]/50'
                : 'border-transparent text-[#5f6368] hover:text-[#202124] hover:bg-[#f8f9fa]'
            }`}
          >
            <span>🪟 Windows</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs text-[#3c4043] leading-relaxed">
          {/* ZERO INTRUSIVE BANNER */}
          <div className="bg-[#f0f9eb] border border-[#b7eb8f] rounded-xl p-3 flex items-start space-x-2.5">
            <ShieldCheck size={18} className="text-[#52c41a] shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-[#274916]">Nguyên tắc Zero-Intrusive (Không can thiệp âm thanh hệ thống):</span>
              <p className="text-[#389e0d] mt-0.5">
                Mọi cấu hình KHÔNG làm thay đổi Loa hay Micro mặc định của máy tính. Khi bạn tắt ứng dụng hoặc kết thúc cuộc họp, âm thanh máy tính vẫn hoạt động nguyên trạng 100%, không bao giờ bị mất tiếng hay mất mic.
              </p>
            </div>
          </div>

          {/* TAB 1: macOS */}
          {activeTab === 'mac' && (
            <div className="space-y-4">
              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[13px] text-[#1f1f1f] flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[11px] font-bold">1</span>
                    <span>Cài đặt driver âm thanh ảo BlackHole 2ch</span>
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">Đã cài trên máy này</span>
                </div>
                <p className="text-[#5f6368]">
                  BlackHole 2ch hoạt động như một dây cáp âm thanh ảo trên macOS, giúp truyền tải âm thanh phát từ app vào Teams mà không làm nhiễu loa ngoài.
                </p>
                <div className="bg-[#f8f9fa] border border-[#e8eaed] rounded-lg p-2.5 font-mono text-[11px] flex items-center justify-between">
                  <code>brew install --cask blackhole-2ch</code>
                  <button
                    onClick={() => handleCopy('brew install --cask blackhole-2ch', 'brew')}
                    className="p-1 hover:bg-white rounded text-[#5f6368]"
                    title="Sao chép lệnh"
                  >
                    {copiedKey === 'brew' ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                  </button>
                </div>
              </div>

              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[13px] text-[#1f1f1f] flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[11px] font-bold">2</span>
                    <span>Thiết bị gộp: Teams Hybrid Mic (Aggregate Device)</span>
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">Đã kích hoạt</span>
                </div>
                <p className="text-[#5f6368]">
                  <strong>Teams Hybrid Mic</strong> gộp <strong>Mic MacBook Pro</strong> và <strong>BlackHole 2ch</strong> làm một. Nhờ đó, Teams có thể nghe thấy cả giọng bạn nói trực tiếp lẫn giọng dịch tiếng Anh từ điện thoại.
                </p>
                <div className="bg-[#e8f0fe]/60 border border-[#d2e3fc] rounded-lg p-2.5 space-y-1 text-[#1a73e8]">
                  <p className="font-semibold">💡 Tự động khởi tạo:</p>
                  <p>Ứng dụng đã có script tự động tạo thiết bị này nếu chưa có. Nếu cần tạo thủ công, bạn mở <strong>Audio MIDI Setup</strong> → bấm dấu <code>+</code> góc dưới → chọn <em>Create Aggregate Device</em> → đặt tên <code>Teams Hybrid Mic</code> → tick chọn <strong>Mic MacBook</strong> & <strong>BlackHole 2ch</strong>.</p>
                </div>
              </div>

              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-2">
                <span className="font-semibold text-[13px] text-[#1f1f1f] flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[11px] font-bold">3</span>
                  <span>Cơ chế phát đồng thời (Dual Output)</span>
                </span>
                <p className="text-[#5f6368]">
                  Khi bạn nói tiếng Việt ở điện thoại, câu dịch tiếng Anh sẽ được phát song song 2 luồng:
                </p>
                <ul className="list-disc list-inside space-y-1 pl-1 text-[#3c4043]">
                  <li><strong>Luồng 1 (vào Teams):</strong> Bắn vào BlackHole 2ch → Teams nghe thấy câu dịch tiếng Anh.</li>
                  <li><strong>Luồng 2 (Monitor cho bạn):</strong> Bắn ra Loa MacBook hoặc Tai nghe → Bạn tự nghe lại câu tiếng Anh để kiểm soát nội dung.</li>
                </ul>
              </div>
            </div>
          )}

          {/* TAB 2: MICROSOFT TEAMS */}
          {activeTab === 'teams' && (
            <div className="space-y-4">
              <div className="border border-[#1a73e8]/30 bg-[#e8f0fe]/20 rounded-xl p-4 space-y-3">
                <h3 className="font-semibold text-[14px] text-[#1a73e8] flex items-center space-x-2">
                  <UsersIcon size={16} />
                  <span>Cài đặt thiết bị trong Microsoft Teams (Chỉ 1 lần)</span>
                </h3>
                <p className="text-[#3c4043]">
                  Trong Microsoft Teams, bấm vào biểu tượng <strong>... (Cài đặt)</strong> → <strong>Devices (Thiết bị)</strong>:
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div className="bg-white border border-[#dadce0] rounded-xl p-3.5 shadow-2xs space-y-2">
                    <div className="flex items-center space-x-2 text-rose-600 font-semibold text-[13px]">
                      <Mic size={16} />
                      <span>Microphone (Mic)</span>
                    </div>
                    <div className="p-2 bg-[#f8f9fa] border border-[#e8eaed] rounded-lg font-bold text-[#1f1f1f] text-[12px]">
                      👉 Chọn: Teams Hybrid Mic
                    </div>
                    <p className="text-[11px] text-[#5f6368]">
                      (Trên Windows: Chọn <em>CABLE Output</em> hoặc <em>VoiceMeeter Output</em>). Teams sẽ thu được cả tiếng bạn nói và tiếng dịch từ điện thoại.
                    </p>
                  </div>

                  <div className="bg-white border border-[#dadce0] rounded-xl p-3.5 shadow-2xs space-y-2">
                    <div className="flex items-center space-x-2 text-[#1a73e8] font-semibold text-[13px]">
                      <Volume2 size={16} />
                      <span>Speaker (Loa)</span>
                    </div>
                    <div className="p-2 bg-[#f8f9fa] border border-[#e8eaed] rounded-lg font-bold text-[#1f1f1f] text-[12px]">
                      👉 Chọn: Loa MacBook Pro / Tai nghe
                    </div>
                    <p className="text-[11px] text-[#5f6368]">
                      Chọn thiết bị loa thật hoặc tai nghe bạn đang đeo. <strong>Tuyệt đối không chọn BlackHole hay CABLE</strong> ở mục này.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-[#fff8e6] border border-[#ffe58f] rounded-xl p-3.5 text-[#d46b08] space-y-1">
                <span className="font-semibold">⚠️ Mẹo tránh lọc âm thanh của Teams:</span>
                <p className="text-[11px]">
                  Trong mục <strong>Noise suppression (Khử tiếng ồn)</strong> của Teams, bạn nên chuyển từ <em>High/Tự động</em> sang <strong>Low (Thấp)</strong> hoặc <strong>Off</strong> để Teams không hiểu lầm giọng TTS là âm thanh lạ rồi lọc bớt.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: BLUETOOTH HEADSET */}
          {activeTab === 'bluetooth' && (
            <div className="space-y-4">
              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-3">
                <div className="flex items-center space-x-2 text-[#1a73e8] font-semibold text-[13px]">
                  <Headphones size={16} />
                  <span>Cách 1: Dùng tai nghe để NGHE (Khuyên dùng nhất ⭐)</span>
                </div>
                <p className="text-[#5f6368]">
                  Bạn đeo tai nghe để nghe người trong cuộc họp nói và nghe giọng tiếng Anh dịch về; còn khi nói trực tiếp, máy dùng Mic của MacBook.
                </p>
                <div className="bg-[#f8f9fa] border border-[#e8eaed] rounded-lg p-3 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[#5f6368]">Loa trong Teams:</span>
                    <span className="font-semibold text-[#1f1f1f]">Tai nghe Bluetooth của bạn</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#5f6368]">Mic trong Teams:</span>
                    <span className="font-semibold text-[#1f1f1f]">Teams Hybrid Mic</span>
                  </div>
                </div>
                <div className="text-[11px] text-[#274916] bg-[#f6ffed] border border-[#b7eb8f] rounded-lg p-2.5">
                  ✅ <strong>Ưu điểm:</strong> Giữ nguyên chất lượng âm thanh <strong>Hi-Fi Stereo / AAC</strong> trong trẻo nhất của tai nghe, hoàn toàn không bị chuyển sang chế độ đàm thoại mono băng thông thấp.
                </div>
              </div>

              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-3">
                <div className="flex items-center space-x-2 text-[#3c4043] font-semibold text-[13px]">
                  <Bluetooth size={16} />
                  <span>Cách 2: Muốn dùng cả MIC của tai nghe Bluetooth để đàm thoại từ xa</span>
                </div>
                <p className="text-[#5f6368]">
                  Thích hợp khi bạn đi lại trong phòng, ngồi xa máy tính mà vẫn muốn nói chuyện trực tiếp bằng mic tai nghe:
                </p>
                <ol className="list-decimal list-inside space-y-1.5 text-[#3c4043] pl-1">
                  <li>Kết nối tai nghe Bluetooth với máy Mac.</li>
                  <li>Mở <strong>Audio MIDI Setup</strong> (nhấn Cmd + Space gõ tìm).</li>
                  <li>Bấm vào <strong>Teams Hybrid Mic</strong> ở danh sách bên trái.</li>
                  <li>Tích chọn <strong>Use</strong> cạnh tên Tai nghe Bluetooth của bạn.</li>
                  <li>Tích chọn ô <strong>Drift Correction (Hiệu chỉnh trôi)</strong> ở dòng tai nghe đó.</li>
                </ol>
              </div>
            </div>
          )}

          {/* TAB 4: WINDOWS */}
          {activeTab === 'windows' && (
            <div className="space-y-4">
              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-3">
                <span className="font-semibold text-[13px] text-[#1f1f1f] flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[11px] font-bold">1</span>
                  <span>Cài đặt VB-Audio Virtual Cable (Miễn phí)</span>
                </span>
                <p className="text-[#5f6368]">
                  Tải driver cáp âm thanh ảo VB-CABLE cho Windows (giải nén và chạy file <code>VBCABLE_Setup_x64.exe</code> bằng quyền Administrator, sau đó restart máy).
                </p>
                <div className="bg-[#f8f9fa] border border-[#e8eaed] rounded-lg p-2.5 font-mono text-[11px]">
                  <span>https://vb-audio.com/Cable/</span>
                </div>
              </div>

              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-3">
                <span className="font-semibold text-[13px] text-[#1f1f1f] flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[11px] font-bold">2</span>
                  <span>Cấu hình Monitor (Nghe lại tiếng dịch)</span>
                </span>
                <p className="text-[#5f6368]">
                  Để bạn tự nghe được câu tiếng Anh phát qua CABLE:
                </p>
                <ol className="list-decimal list-inside space-y-1.5 pl-1">
                  <li>Nhấn <code>Win + R</code>, gõ lệnh <code>mmsys.cpl</code> và nhấn Enter.</li>
                  <li>Chuyển qua thẻ <strong>Recording</strong>.</li>
                  <li>Chuột phải vào <strong>CABLE Output</strong> → chọn <strong>Properties</strong>.</li>
                  <li>Mở thẻ <strong>Listen</strong> → tick chọn <strong>Listen to this device</strong>.</li>
                  <li>Mục <em>Playback through this device</em>: chọn <strong>Loa / Tai nghe thật</strong> của bạn.</li>
                </ol>
              </div>

              <div className="border border-[#e3e3e3] rounded-xl p-4 bg-white shadow-2xs space-y-2">
                <span className="font-semibold text-[13px] text-[#1f1f1f] flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[11px] font-bold">3</span>
                  <span>Gộp cả Mic thật và CABLE (Tùy chọn VoiceMeeter)</span>
                </span>
                <p className="text-[#5f6368]">
                  Nếu muốn vừa nói chuyện bằng mic thật vừa phát tiếng dịch tiếng Anh mà không cần đổi mic qua lại trong Teams: Cài đặt <strong>VoiceMeeter Banana</strong> để trộn <em>Hardware Input 1 (Mic thật)</em> và <em>Hardware Input 2 (CABLE Output)</em> vào một cổng <strong>VoiceMeeter Output</strong> cho Teams.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-[#e3e3e3] bg-[#f8f9fa] flex items-center justify-between">
          <span className="text-[11px] text-[#5f6368] flex items-center space-x-1.5">
            <Radio size={14} className="text-emerald-500 animate-pulse" />
            <span>Âm thanh 2 chiều song song đang hoạt động</span>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#1a73e8] text-white rounded-lg text-xs font-semibold hover:bg-[#1557b0] transition-colors shadow-2xs"
          >
            Đã hiểu & Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

function UsersIcon({ size = 14 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
