import { useEffect, useState } from 'react';

export function useWorkspaceRoute() {
  const readPath = () => {
    if (window.location.pathname === '/') return '/chat';
    return `${window.location.pathname}${window.location.search}`;
  };
  const [path, setPath] = useState(readPath);

  useEffect(() => {
    const onPopState = () => setPath(readPath());
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
