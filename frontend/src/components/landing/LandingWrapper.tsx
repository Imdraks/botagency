'use client';

import { useEffect } from 'react';

interface LandingWrapperProps {
  children: React.ReactNode;
}

export function LandingWrapper({ children }: LandingWrapperProps) {
  useEffect(() => {
    // Force light mode on landing page
    const html = document.documentElement;
    const originalTheme = html.classList.contains('dark') ? 'dark' : 'light';
    
    // Remove dark class and add light
    html.classList.remove('dark');
    html.classList.add('light');
    html.style.colorScheme = 'light';
    
    // Restore original theme when leaving landing page
    return () => {
      if (originalTheme === 'dark') {
        html.classList.remove('light');
        html.classList.add('dark');
        html.style.colorScheme = 'dark';
      }
    };
  }, []);

  return (
    <div className="light" style={{ colorScheme: 'light' }}>
      {children}
    </div>
  );
}
