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
    expect(document.querySelector('rect[aria-label="Deep middle coverage zone"]')).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(deepLeft!);
    expect(onChange).toHaveBeenCalledWith(['deep_middle', 'deep_left']);
    view.rerender(<CoverageShellEditor zones={['deep_middle', 'deep_left']} onChange={onChange} />);
    const updatedDeepLeft = document.querySelector<SVGRectElement>('rect[aria-label="Deep left coverage zone"]');
    expect(updatedDeepLeft).not.toBeNull();
    fireEvent.keyDown(updatedDeepLeft!, { key: 'Enter' });
    expect(onChange).toHaveBeenLastCalledWith(['deep_middle']);
  });
});
