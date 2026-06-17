# React — Performance

Render behavior, memoization, the React Compiler, splitting, profiling.

---

## How rendering works

- A component re-renders when: its **state changes**, its **parent re-renders**,
  or a **context** it consumes changes. Props changing is *not* itself a trigger —
  it happens because the parent re-rendered.
- Re-rendering ≠ DOM update. React renders (calls your function), diffs, then
  commits only what changed. Most renders are cheap — **don't optimize blindly**.
- A parent re-render re-renders **all** children by default, regardless of whether
  their props changed (unless they're `memo`-ized).

https://react.dev/learn/render-and-commit

---

## memo, useMemo, useCallback

```tsx
const Row = memo(function Row({ item, onPick }: RowProps) { /* ... */ });
```

`memo` skips a re-render when props are shallowly equal. For it to help, **object
and function props must be stable** — otherwise every render passes new references:

```tsx
const handlePick = useCallback((id) => dispatch({ type: "pick", id }), [dispatch]);
const columns = useMemo(() => buildColumns(config), [config]);
<Row item={item} onPick={handlePick} />   // now memo can actually skip
```

- `useMemo` — cache an expensive computed value.
- `useCallback` — cache a function identity (for memo'd children / effect deps).
- These have a cost; only apply where there's a measured problem.

https://react.dev/reference/react/memo

---

## The React Compiler (often makes the above unnecessary)

The **React Compiler** automatically memoizes components and values at build time,
so most manual `memo`/`useMemo`/`useCallback` becomes redundant.

- It relies on code following the **Rules of React** (purity, no mutation).
- When enabled, write straightforward code and let the compiler optimize; remove
  hand-rolled memoization that exists purely for performance.

https://react.dev/learn/react-compiler

---

## Avoiding unnecessary re-renders

- **Don't lift state higher than needed** — local state re-renders less of the tree.
- **Push state down** into a child so the expensive siblings don't re-render.
- **Pass JSX as `children`** — children passed from above don't re-render when the
  wrapper's own state changes.
- **Split contexts** (state vs dispatch) and keep provider `value` stable so
  consumers don't re-render needlessly.
- For high-frequency shared state, use a store with **selectors** (Zustand/Redux)
  so only components reading the changed slice re-render.

https://react.dev/learn/render-and-commit

---

## Key stability

- Stable `key`s let React reuse component instances; unstable keys (array index on
  a reordering list, `Math.random()`) force remounts that destroy state and DOM.
- Conversely, **change a `key` on purpose** to intentionally reset a component's
  state (e.g. reset a form when the selected record changes).

```tsx
<Form key={selectedId} ... />   // remounts (fresh state) when selection changes
```

---

## Code splitting with lazy + Suspense

Defer loading code until it's needed; show a fallback while it loads.

```tsx
import { lazy, Suspense } from "react";
const Settings = lazy(() => import("./Settings"));

<Suspense fallback={<Spinner />}>
  <Settings />
</Suspense>
```

- Split at route boundaries and behind heavy/rarely-used UI (modals, editors, charts).
- Combine with `useTransition` so navigating doesn't flash the fallback abruptly.

https://react.dev/reference/react/lazy

---

## List virtualization

Rendering thousands of rows is slow — render only the visible window.

- **TanStack Virtual** (`@tanstack/react-virtual`) — headless, framework-agnostic.
- **react-window** / **react-virtuoso** — component-based.

```tsx
import { useVirtualizer } from "@tanstack/react-virtual";
const v = useVirtualizer({ count: rows.length, getScrollElement: () => parentRef.current, estimateSize: () => 40 });
```

https://tanstack.com/virtual/latest

---

## useTransition / useDeferredValue for responsiveness

Keep input responsive during expensive renders by deprioritizing non-urgent work.

```tsx
const [isPending, startTransition] = useTransition();
const onChange = (e) => { setInput(e.target.value); startTransition(() => setQuery(e.target.value)); };
```

```tsx
const deferred = useDeferredValue(query);   // heavy list renders against the lagged value
```

https://react.dev/reference/react/useTransition · https://react.dev/reference/react/useDeferredValue

---

## Profiling

- **React DevTools Profiler**: record an interaction, see which components rendered,
  how long, and **why** (enable "Record why each component rendered").
- The **`<Profiler>`** component measures render cost programmatically.
- Build in production mode before measuring real perf (dev mode is much slower).
- Measure → fix the actual hotspot → re-measure. Don't memoize on a hunch.

```tsx
<Profiler id="List" onRender={(id, phase, actualDuration) => log(id, phase, actualDuration)}>
  <List />
</Profiler>
```

https://react.dev/reference/react/Profiler · https://react.dev/learn/react-developer-tools

---

## Docs
- Render and commit: https://react.dev/learn/render-and-commit
- memo: https://react.dev/reference/react/memo
- React Compiler: https://react.dev/learn/react-compiler
- lazy: https://react.dev/reference/react/lazy
- Profiler: https://react.dev/reference/react/Profiler
- React DevTools: https://react.dev/learn/react-developer-tools
