import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { CoverageShellEditor } from './CoverageShellEditor';

describe('CoverageShellEditor', () => {
  it('toggles spatial shell regions with an accessible button surface', () => {
    const onChange = vi.fn();
    const view = render(<CoverageShellEditor zones={['deep_middle']} onChange={onChange} />);
    const deepLeft = document.querySelector<SVGRectElement>('rect[aria-label="Deep left coverage zone"]');
    expect(deepLeft).not.toBeNull();
    expect(screen.getByText('1 declared')).toBeInTheDocument();
    expect(document.querySelector('rect[aria-label="Deep middle coverage zone · unowned"]')).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(deepLeft!);
    expect(onChange).toHaveBeenCalledWith(['deep_middle', 'deep_left']);
    view.rerender(<CoverageShellEditor zones={['deep_middle', 'deep_left']} onChange={onChange} />);
    const updatedDeepLeft = document.querySelector<SVGRectElement>('rect[aria-label="Deep left coverage zone · unowned"]');
    expect(updatedDeepLeft).not.toBeNull();
    fireEvent.keyDown(updatedDeepLeft!, { key: 'Enter' });
    expect(onChange).toHaveBeenLastCalledWith(['deep_middle']);
  });

  it('shows declared ownership and conflicts on the visual shell', () => {
    render(<CoverageShellEditor zones={['deep_middle', 'flat_left']} owners={new Map([
      ['deep_middle', ['FS']],
      ['flat_left', ['NB', 'MIKE']],
    ])} onChange={vi.fn()} />);
    expect(screen.getByText('2 declared')).toHaveTextContent('2 declared');
    expect(screen.getByText(/0 unowned · 1 conflict/)).toBeInTheDocument();
    expect(document.querySelector('rect[aria-label="Deep middle coverage zone · owner: FS"]')).toHaveAttribute('aria-pressed', 'true');
    expect(document.querySelector('rect[aria-label="Flat left coverage zone · owner: NB / MIKE · conflict"]')).toHaveAttribute('aria-pressed', 'true');
  });
});
