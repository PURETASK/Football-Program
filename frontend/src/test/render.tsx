import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactElement } from 'react';

import { SessionProvider } from '../auth/SessionContext';

export function renderApp(ui: ReactElement, { initialEntries = ['/'] }: { initialEntries?: string[] } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
      </SessionProvider>
    </QueryClientProvider>,
  );
}
