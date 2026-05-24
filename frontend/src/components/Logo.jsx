import React from 'react';
import IcoAtlasLogo from './IcoAtlasLogo';

const Logo = ({ size = 'default', showText = true, className = '' }) => {
  const sizes = {
    small: { icon: 24, text: 'text-base', subtitle: 'text-[9px]' },
    default: { icon: 44, text: 'text-xl', subtitle: 'text-[11px]' },
    large: { icon: 60, text: 'text-3xl', subtitle: 'text-xs' },
    xl: { icon: 80, text: 'text-5xl', subtitle: 'text-sm' }
  };

  const config = sizes[size] || sizes.default;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Dynamic IcoAtlasLogo using Slovak Blue as default */}
      <IcoAtlasLogo size={config.icon} />
      
      {showText && (
        <div className="flex flex-col justify-center text-left">
          <span className={`${config.text} font-extrabold tracking-tight text-slate-900 leading-none`}>
            iCO<span className="text-[#0B4EA2]">Atlas</span>
          </span>
          {(size === 'large' || size === 'xl') && (
            <span className={`${config.subtitle} text-slate-500 mt-1 font-medium tracking-wider uppercase`}>
              V4 Identifier Intelligence
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default Logo;

