## Creating a new React app

If you don't have a site yet, scaffold one with Vite:

```bash
npm create vite@latest my-site -- --template react
cd my-site
npm install
```

Replace `src/App.jsx` and `src/App.css` with the following to get a black-and-white "Coming Soon" page:

```jsx
// src/App.jsx
import './App.css'

export default function App() {
  return (
    <div className="page">
      <div className="card">
        <span className="icon">🚧</span>
        <h1>Coming Soon</h1>
        <p>Something great is on its way.</p>
      </div>
    </div>
  )
}
```

```css
/* src/App.css */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #000;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100dvh;
  display: grid;
  place-items: center;
}

.page { width: 100%; display: grid; place-items: center; padding: 2rem; }

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 3rem 4rem;
  text-align: center;
}

.icon { font-size: 3rem; }

h1 { font-size: clamp(2rem, 6vw, 3.5rem); font-weight: 700; letter-spacing: -0.02em; }

p { font-size: 1.1rem; color: #888; }
```

### Production build for a React SPA

Vite (and Create React App) emit a `dist/` (or `build/`) folder ready to be served as a static site:

```bash
npm run build          # outputs to dist/ (Vite) or build/ (CRA)
npm run preview        # optional local preview of the production bundle
```

Key things the build does:
- Bundles and tree-shakes JS/CSS, adds content-hash filenames (`assets/index-Bx9v1234.js`)
- Inlines small assets, copies public/ files verbatim
- Emits a single `index.html` — all routes must resolve to it (CloudFront's 404 → `/index.html` rule handles this)

When you run the deploy skill, set **Build output folder** to `dist` (Vite default) or `build` (CRA default).
