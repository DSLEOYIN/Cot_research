import { useEffect, useState } from 'react';

export function useWorkspaceRoute() {
  const [path, setPath] = useState(() => window.location.pathname === '/' ? '/chat' : window.location.pathname);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname === '/' ? '/chat' : window.location.pathname);
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  function navigate(nextPath: string) {
    if (nextPath === path) return;
    window.history.pushState({}, '', nextPath);
    setPath(nextPath);
  }

  return { path, navigate };
}
