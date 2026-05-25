import React from 'react';

/**
 * iCOAtlas Logo Component
 * Renders the new image logo.
 */
const IcoAtlasLogo = ({ 
  size = 40, 
  className = '', 
  hasBg = false // The new logo has its own background styling
}) => {
  const imgSize = hasBg ? '100%' : size;
  
  const img = (
    <img 
      src="/logo.png" 
      alt="iCOAtlas Logo"
      style={{ width: imgSize, height: imgSize, objectFit: 'contain' }}
      className={hasBg ? "w-full h-full" : className}
    />
  );

  if (hasBg) {
    return (
      <div 
        style={{ width: size, height: size }}
        className={`flex items-center justify-center ${className}`}
      >
        {img}
      </div>
    );
  }

  return img;
};

export default IcoAtlasLogo;
export { IcoAtlasLogo as IcoAtlasLogo }; // Backward compatibility

