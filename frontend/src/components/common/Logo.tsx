import React from 'react';
import { Network } from 'lucide-react';

interface LogoProps {
  size?: 'md' | 'lg';
  showTagline?: boolean;
}

// Brand mark: gradient tile + "Kno(w)Hol(e)" wordmark with a blinking terminal cursor.
export const Logo: React.FC<LogoProps> = ({ size = 'md', showTagline = false }) => {
  const lg = size === 'lg';
  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20 ${
          lg ? 'h-12 w-12' : 'h-10 w-10'
        }`}
      >
        <Network className={lg ? 'h-6 w-6' : 'h-5 w-5'} />
      </div>
      <div>
        <span
          className={`flex items-center font-bold tracking-tight text-white ${lg ? 'text-2xl' : 'text-lg'}`}
          aria-label="Kno(w)Hol(e)"
        >
          Kno<span className="text-indigo-400">(w)</span>Hol<span className="text-indigo-400">(e)</span>
          <span
            aria-hidden="true"
            className={`ml-1 inline-block rounded-sm bg-indigo-400 animate-blink motion-reduce:animate-none ${
              lg ? 'h-6 w-2.5' : 'h-5 w-2'
            }`}
          />
        </span>
        {showTagline && <p className="text-xs text-slate-400">Discover What You Don't Know</p>}
      </div>
    </div>
  );
};

export default Logo;
