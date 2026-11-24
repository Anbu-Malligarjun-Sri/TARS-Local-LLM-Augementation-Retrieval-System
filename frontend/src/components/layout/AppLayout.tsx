import { ReactNode } from 'react';
import { MonolithSidebar } from '@/components/sidebar/MonolithSidebar';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="h-[100dvh] overflow-hidden w-full flex bg-background noise-overlay scanlines">
      {/* Sidebar - The Monolith */}
      <MonolithSidebar />
      
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
        {children}
      </main>
      
      {/* Ambient Effects */}
      <div className="fixed inset-0 pointer-events-none z-50">
        {/* Top vignette */}
        <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-black/40 to-transparent" />
        {/* Bottom vignette */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/40 to-transparent" />
        {/* Corner vignettes */}
        <div className="absolute inset-0 bg-radial-gradient from-transparent via-transparent to-black/30" 
             style={{ background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)' }} />
      </div>
    </div>
  );
}
