import { useState, useEffect, useRef } from "react";
import { pairDevice, tarsApi, redeemLaunch } from "./services/tarsApi";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  const [paired, setPaired] = useState(false);
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const launchStarted = useRef(false);
  useEffect(() => {
    if (launchStarted.current) return;
    launchStarted.current = true;
    const ticket = new URLSearchParams(window.location.hash.slice(1)).get('launch');
    if (ticket) {
      window.history.replaceState(null, '', window.location.pathname);
      redeemLaunch(ticket).then(() => setPaired(true)).catch(e => setError(String(e)));
    } else tarsApi.getSettings().then(() => setPaired(true)).catch(() => {});
  }, []);
  if (!paired) return <main className="p-8 max-w-lg mx-auto space-y-4">
    <h1>Connect your TARS device</h1>
    <p>Enter the OWNER_TOKEN configured on your local TARS server.</p>
    <form onSubmit={async event => { event.preventDefault(); try { await pairDevice(token); setToken(''); setPaired(true); } catch (e) { setError(String(e)); } }}>
      <input aria-label="Owner pairing token" type="password" value={token} onChange={e => setToken(e.target.value)} className="bg-card border p-2 w-full" />
      <button className="p-2 border mt-2" type="submit">Pair device</button>
    </form><p role="alert">{error}</p>
  </main>;
  return (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);
};

export default App;
