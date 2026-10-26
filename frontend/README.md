# Continuity Detective frontend

React + TypeScript + Vite workbench. See the repository README for the local FastAPI service and separate Python worker.

Run `npm install` and `npm run dev`; open http://127.0.0.1:5174. Vite proxies `/api` to 127.0.0.1:8000. Fonts are bundled locally. No API keys or cloud inference are required.

`npm run build` checks types and builds production assets. `npm run lint` checks source. `npm run test:e2e` exercises the live workflow with Playwright and the supplied local takes; start all three processes first.
