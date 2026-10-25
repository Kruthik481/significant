import { defineConfig } from '@playwright/test';

const API = 'http://localhost:8300';
const WEB = 'http://localhost:3300';

export default defineConfig({
  testDir: 'e2e',
  timeout: 60_000,
  use: { baseURL: WEB },
  webServer: [
    {
      command: 'uv run uvicorn --factory app.main:app_from_env --port 8300',
      cwd: '../api',
      url: `${API}/readyz`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { DATABASE_URL: 'postgresql://ab:ab@localhost:5436/ab_test', WEB_ORIGIN: WEB },
    },
    {
      command: 'npm run dev',
      url: WEB,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { NEXT_PUBLIC_API_URL: API },
    },
  ],
});
