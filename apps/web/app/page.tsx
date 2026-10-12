import Sidebar from '@/components/Sidebar';
import ChatWorkspace from '@/components/ChatWorkspace';

export default function Home() {
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', fontFamily: 'sans-serif' }}>
      <Sidebar />
      <ChatWorkspace />
    </div>
  );
}