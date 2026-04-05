/**
 * MSW server shared across all component/integration tests.
 * Individual tests override handlers via server.use(...) for one-off scenarios.
 */
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

export const defaultHandlers = [
    http.get('*/session_info', () =>
        HttpResponse.json({ app_name: 'si_mapper', user_id: 'demo_user' })
    ),
    http.get('*/session_state', () =>
        HttpResponse.json({ status: 'idle', current_step: '', observed_steps: [] })
    ),
];

export const server = setupServer(...defaultHandlers);

