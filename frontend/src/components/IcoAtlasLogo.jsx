import React from 'react';

/**
 * iCOAtlas Logo Component
 * Theme: Corporate / Government / Official
 * Colors: Slovak Blue (#0B4EA2), Slovak Red (#EE1C25)
 */
const IcoAtlasLogo = ({ 
  size = 40, 
  className = '', 
  strokeColor, 
  nodeColor = '#EE1C25',
  hasBg = true
}) => {
  const resolvedStrokeColor = strokeColor || (hasBg ? '#ffffff' : '#0B4EA2');

  const svg = (
    <svg 
      width={hasBg ? '100%' : size} 
      height={hasBg ? '100%' : size} 
      viewBox="0 0 100 100" 
      fill="none" 
      className={hasBg ? "w-full h-full" : className}
    >
      {/* Triangle Base */}
      <path d="M50 10 L90 85 L10 85 Z" stroke={resolvedStrokeColor} strokeWidth="3" fill="none" />
      {/* Nodes - Slovak Red */}
      <circle cx="50" cy="10" r="3" fill={nodeColor} />
      <circle cx="90" cy="85" r="3" fill={nodeColor} />
      <circle cx="10" cy="85" r="3" fill={nodeColor} />
      {/* Inner Eye / Core Globe */}
      <path d="M50 35 L50 65" stroke={resolvedStrokeColor} strokeWidth="1.5" strokeOpacity="0.3" />
      <path d="M35 50 L65 50" stroke={resolvedStrokeColor} strokeWidth="1.5" strokeOpacity="0.3" />
      <circle cx="50" cy="50" r="12" stroke={resolvedStrokeColor} strokeWidth="2" fill="none" />
      <circle cx="50" cy="50" r="4" fill={resolvedStrokeColor} />
    </svg>
  );

  if (hasBg) {
    return (
      <div 
        style={{ width: size, height: size }}
        className={`bg-[#0B4EA2] p-[20%] rounded-lg shadow-sm transition-all flex items-center justify-center ${className}`}
      >
        {svg}
      </div>
    );
  }

  return svg;
};

export default IcoAtlasLogo;
export { IcoAtlasLogo as IcoAtlasLogo }; // Backward compatibility during migration

