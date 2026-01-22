'use client';

import { useEffect } from 'react';

export function ForceLightMode({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Force light mode on landing page
    const html = document.documentElement;
    const originalClass = html.className;
    
    // Remove dark class and add light
    html.classList.remove('dark');
    html.classList.add('light');
    html.style.colorScheme = 'light';
    
    // Cleanup on unmount - restore original
    return () => {
      html.className = originalClass;
      html.style.colorScheme = '';
    };
  }, []);

  return (
    <div className="light" style={{ colorScheme: 'light' }}>
      {children}
    </div>
  );
}
