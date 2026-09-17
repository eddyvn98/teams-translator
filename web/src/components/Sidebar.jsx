import React from 'react';
import {
  Menu,
  Sparkles,
  History,
  Plus,
  Grid,
  FolderKanban,
  LayoutDashboard,
  FileText,
  Bell,
  Settings,
  Search,
  Key,
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  onNewSession,
  onOpenSettings,
  onOpenHistory,
  collapsed,
  setCollapsed,
}) {
  return (
    <aside
      className={`h-screen flex flex-col justify-between border-r border-[#e3e3e3] bg-[#fdfdfd] text-[#1f1f1f] select-none transition-all duration-200 z-20 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Top Section */}
      <div>
        {/* Brand & Toggle */}
        <div className="flex items-center justify-between px-4 h-14 border-b border-[#f1f3f4]">
          <div className="flex items-center space-x-3 overflow-hidden">
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#444746] transition-colors"
              title={collapsed ? 'Mở rộng thanh menu' : 'Thu gọn'}
            >
              <Menu size={20} />
            </button>
            {!collapsed && (
              <div className="flex items-center space-x-2 whitespace-nowrap">
                <span className="font-semibold text-[17px] tracking-tight text-[#1f1f1f]">
                  Google <span className="font-normal text-[#444746]">AI Studio</span>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Groups */}
        <div className="p-3 space-y-6">
          {/* Explore */}
          <div>
            {!collapsed && (
              <div className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-[#747775] uppercase">
                Explore
              </div>
            )}
            <nav className="space-y-0.5">
              <button
                onClick={() => setActiveTab('playground')}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium transition-colors ${
                  activeTab === 'playground'
                    ? 'bg-[#e8f0fe] text-[#1967d2]'
                    : 'text-[#444746] hover:bg-[#f1f3f4]'
                }`}
                title="Playground"
              >
                <Sparkles size={18} className={activeTab === 'playground' ? 'text-[#1967d2]' : 'text-[#444746]'} />
                {!collapsed && <span>Playground</span>}
              </button>

              <button
                onClick={() => {
                  setActiveTab('history');
                  if (onOpenHistory) onOpenHistory();
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium transition-colors ${
                  activeTab === 'history'
                    ? 'bg-[#e8f0fe] text-[#1967d2]'
                    : 'text-[#444746] hover:bg-[#f1f3f4]'
                }`}
                title="History"
              >
                <History size={18} />
                {!collapsed && <span>History</span>}
              </button>
            </nav>
          </div>

          {/* Build */}
          <div>
            {!collapsed && (
              <div className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-[#747775] uppercase">
                Build
              </div>
            )}
            <nav className="space-y-0.5">
              <button
                onClick={onNewSession}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium text-[#444746] hover:bg-[#f1f3f4] transition-colors"
                title="New session"
              >
                <Plus size={18} />
                {!collapsed && <span>New session</span>}
              </button>

              <button
                onClick={() => setActiveTab('myapps')}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium text-[#444746] hover:bg-[#f1f3f4] transition-colors"
                title="My apps"
              >
                <FolderKanban size={18} />
                {!collapsed && <span>My apps</span>}
              </button>

              <button
                onClick={() => setActiveTab('gallery')}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium text-[#444746] hover:bg-[#f1f3f4] transition-colors"
                title="Gallery"
              >
                <Grid size={18} />
                {!collapsed && <span>Gallery</span>}
              </button>
            </nav>
          </div>

          {/* Manage */}
          <div>
            {!collapsed && (
              <div className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-[#747775] uppercase">
                Manage
              </div>
            )}
            <nav className="space-y-0.5">
              <button
                onClick={() => setActiveTab('dashboard')}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium text-[#444746] hover:bg-[#f1f3f4] transition-colors"
                title="Dashboard"
              >
                <LayoutDashboard size={18} />
                {!collapsed && <span>Dashboard</span>}
              </button>

              <button
                onClick={() => setActiveTab('docs')}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-full text-[13px] font-medium text-[#444746] hover:bg-[#f1f3f4] transition-colors"
                title="Documentation"
              >
                <FileText size={18} />
                {!collapsed && <span>Documentation</span>}
              </button>
            </nav>
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="p-3 border-t border-[#f1f3f4] space-y-2">
        {/* Quick Tools */}
        <div className="flex items-center justify-around py-1 text-[#444746]">
          <button className="p-1.5 rounded-full hover:bg-[#f1f3f4]" title="Thông báo">
            <Bell size={16} />
          </button>
          <button onClick={onOpenSettings} className="p-1.5 rounded-full hover:bg-[#f1f3f4]" title="Cài đặt">
            <Settings size={16} />
          </button>
          <button className="p-1.5 rounded-full hover:bg-[#f1f3f4]" title="Tìm kiếm">
            <Search size={16} />
          </button>
          <button className="p-1.5 rounded-full hover:bg-[#f1f3f4]" title="API Keys">
            <Key size={16} />
          </button>
        </div>

        {/* User Badge */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-[#f8f9fa] border border-[#e8eaed]">
          <div className="flex items-center space-x-2.5 overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#1a73e8] to-[#4285f4] text-white flex items-center justify-center text-xs font-semibold shrink-0">
              TT
            </div>
            {!collapsed && (
              <div className="truncate text-left">
                <div className="text-[12px] font-medium text-[#1f1f1f] truncate">teams-user</div>
                <div className="text-[10px] text-[#5f6368] truncate">Live Connected</div>
              </div>
            )}
          </div>
          {!collapsed && (
            <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-[#e8f0fe] text-[#1967d2] rounded-md uppercase">
              Pro
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
