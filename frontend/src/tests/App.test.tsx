import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('Revenue Department Application Shell', () => {
  it('renders official header and Maharashtra identity', () => {
    render(<App />);
    const headings = screen.getAllByText(/Revenue & Forest Department/i);
    expect(headings.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Government of Maharashtra/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/GovMesh SIH26129 Demonstration Prototype/i)[0]).toBeInTheDocument();
  });

  it('renders login page by default', () => {
    render(<App />);
    expect(screen.getByText(/Departmental Officer Login/i)).toBeInTheDocument();
    expect(screen.getByText(/Key Revenue Services Catalog/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Department Portal/i })).toBeInTheDocument();
  });

  it('renders navigation tabs and services link', () => {
    render(<App />);
    expect(screen.getByText('Revenue Services')).toBeInTheDocument();
  });
});
