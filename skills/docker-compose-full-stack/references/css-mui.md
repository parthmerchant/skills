## CSS architecture — all styles in `src/index.css`

Zero inline styles in JSX components. All visual styles — including dark-mode variants — live in `src/index.css` as `@layer components` classes. JSX uses only Tailwind layout utilities and these class names.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  *, *::before, *::after { box-sizing: border-box; }
  html, body, #root { height: 100%; margin: 0; padding: 0; }
  body { font-family: 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
}

@layer components {
  /* App background — toggled by class on the root div */
  .app-bg      { width: 100%; height: 100vh; background: #f9fafb; transition: background 0.3s; }
  .app-bg--dark { background: #000000; }

  /* Two-panel layout */
  .app-layout  { display: flex; gap: 1.25rem; padding: 1.25rem; height: 100vh; overflow: hidden; }

  /* Sidebar */
  .sidebar               { display: flex; flex-direction: column; width: 340px; flex-shrink: 0; height: 100%; border-radius: 18px; overflow: hidden; }
  .sidebar__header       { display: flex; align-items: center; gap: 0.75rem; padding: 1.1rem 1.25rem; border-bottom: 1px solid #e5e7eb; }
  .dark .sidebar__header { border-color: #1f2937; }
  /* ... repeat pattern for sidebar__search, sidebar__list, sidebar__footer */

  /* List items */
  .item-row             { border-radius: 12px; padding: 0.7rem 0.75rem; cursor: pointer; border: 1px solid transparent; transition: all 0.15s ease; }
  .item-row:hover:not(.item-row--active) { background: rgba(0,0,0,0.04); border-color: #e5e7eb; }
  .dark .item-row:hover:not(.item-row--active) { background: rgba(255,255,255,0.04); border-color: #1f2937; }
  .item-row--active      { background: #000; border-color: #000; color: #fff; }
  .dark .item-row--active { background: #fff; border-color: #fff; color: #000; }

  /* Form panel */
  .main-panel   { flex: 1; overflow-y: auto; }
  .form-wrapper { max-width: 680px; margin: 0 auto; padding: 0.25rem 0 1.5rem; }
  .form-card    { border-radius: 18px; padding: 2rem; }
  .form-grid    { display: grid; grid-template-columns: 1fr 1fr; gap: 1.1rem; margin-top: 1.5rem; }
  .form-col-full { grid-column: 1 / -1; }
  .form-actions { display: flex; gap: 0.75rem; padding-top: 0.75rem; }
}
```

---

## MUI theme — `src/theme.js`

Two themes exported: `lightTheme` and `darkTheme`. Override component defaults here, not in JSX. Key overrides to always include:

```js
import { createTheme } from '@mui/material/styles'

const shared = {
  shape: { borderRadius: 12 },
  typography: { fontFamily: "'Inter', system-ui, sans-serif" },
  components: {
    MuiPaper:       { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiButton:      { styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } } },
    MuiTextField:   { defaultProps: { variant: 'outlined', size: 'small' } },
    MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 10 } } },
  },
}

export const lightTheme = createTheme({
  ...shared,
  palette: { mode: 'light', primary: { main: '#000' }, background: { default: '#f9fafb', paper: '#fff' } },
})

export const darkTheme = createTheme({
  ...shared,
  palette: { mode: 'dark', primary: { main: '#fff', contrastText: '#000' }, background: { default: '#000', paper: '#111' } },
})
```

---

## Dark mode wiring — `src/App.jsx`

Toggle MUI theme AND the `.dark` class on `<html>` in one call. Always initialise both from `localStorage` on first load:

```js
function initDark() {
  const stored = localStorage.getItem('theme')
  const isDark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.classList.toggle('dark', isDark)  // for Tailwind dark: variants
  return isDark
}

function toggleDark() {
  setDark(prev => {
    const next = !prev
    localStorage.setItem('theme', next ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', next)
    return next
  })
}

// In JSX:
return (
  <ThemeProvider theme={dark ? darkTheme : lightTheme}>
    <CssBaseline />
    <div className={`app-bg${dark ? ' app-bg--dark' : ''}`}>
      {/* layout */}
    </div>
  </ThemeProvider>
)
```
