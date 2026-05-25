import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import IcoAtlasLogo from '../IcoAtlasLogo';

describe('IcoAtlasLogo', () => {
  it('renders logo component', () => {
    const { container } = render(<IcoAtlasLogo />);
    const img = container.querySelector('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('alt', 'iCOAtlas Logo');
  });

  it('renders img with correct style sizes', () => {
    const { container } = render(<IcoAtlasLogo size={50} />);
    const img = container.querySelector('img');
    expect(img.style.width).toBe('50px');
    expect(img.style.height).toBe('50px');
  });

  it('applies className prop correctly', () => {
    const { container } = render(<IcoAtlasLogo className="test-class" />);
    const img = container.querySelector('img');
    expect(img).toHaveClass('test-class');
  });

  it('renders with default style size when not specified', () => {
    const { container } = render(<IcoAtlasLogo />);
    const img = container.querySelector('img');
    expect(img.style.width).toBe('40px');
    expect(img.style.height).toBe('40px');
  });
});
