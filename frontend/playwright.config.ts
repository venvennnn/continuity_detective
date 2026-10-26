import { defineConfig } from '@playwright/test'
export default defineConfig({ testDir: './tests', timeout: 120000,
  use: { baseURL: 'http://127.0.0.1:5174', viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  workers: 1, reporter: 'list' })
