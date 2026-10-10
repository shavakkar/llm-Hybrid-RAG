import Sidebar from '@/components/Sidebar';
import ChatWorkspace from '@/components/ChatWorkspace';

export default function Home() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950">
      <Sidebar />
      <ChatWorkspace />
    </div>
  );
}