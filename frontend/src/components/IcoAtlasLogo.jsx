import React from 'react';

/**
 * iCOAtlas Logo Component
 * Theme: Corporate / Government / Official
 * Colors: Slovak Blue (#0B4EA2), Slovak Red (#EE1C25)
 */
const IcoAtlasLogo = ({ size = 40, className = '', strokeColor = '#0B4EA2', nodeColor = '#EE1C25' }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 100 100" 
    fill="none" 
    className={className}
  >
    {/* Triangle Base - Slovak Blue */}
    <path d="M50 10 L90 85 L10 85 Z" stroke={strokeColor} strokeWidth="3" fill="none" />
    {/* Nodes - Slovak Red */}
    <circle cx="50" cy="10" r="3" fill={nodeColor} />
    <circle cx="90" cy="85" r="3" fill={nodeColor} />
    <circle cx="10" cy="85" r="3" fill={nodeColor} />
    {/* Inner Eye / Core Globe */}
    <path d="M50 35 L50 65" stroke={strokeColor} strokeWidth="1.5" strokeOpacity="0.3" />
    <path d="M35 50 L65 50" stroke={strokeColor} strokeWidth="1.5" strokeOpacity="0.3" />
    <circle cx="50" cy="50" r="12" stroke={strokeColor} strokeWidth="2" fill="none" />
    <circle cx="50" cy="50" r="4" fill={strokeColor} />
  </svg>
);

export default IcoAtlasLogo;
export { IcoAtlasLogo as IcoAtlasLogo }; // Backward compatibility during migration
