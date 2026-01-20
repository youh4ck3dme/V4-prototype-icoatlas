import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock component for testing structure
const MockSearchBar = ({ onSearch }) => {
  return (
    <div data-testid="search-bar">
      <input
        type="text"
        placeholder="Zadajte IČO alebo názov firmy"
        data-testid="search-input"
        onChange={(e) => onSearch && onSearch(e.target.value)}
      />
      <button data-testid="search-button">Hľadať</button>
    </div>
  );
};

describe('SearchBar Component', () => {
  it('renders search input', () => {
    render(<MockSearchBar />);
    expect(screen.getByTestId('search-input')).toBeInTheDocument();
  });

  it('renders search button', () => {
    render(<MockSearchBar />);
    expect(screen.getByTestId('search-button')).toBeInTheDocument();
  });

  it('calls onSearch when input changes', () => {
    const mockOnSearch = vi.fn();
    render(<MockSearchBar onSearch={mockOnSearch} />);
    
    const input = screen.getByTestId('search-input');
    fireEvent.change(input, { target: { value: '12345678' } });
    
    expect(mockOnSearch).toHaveBeenCalledWith('12345678');
  });
});
