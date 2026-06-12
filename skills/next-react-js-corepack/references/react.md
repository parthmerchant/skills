# React — fundamentals

## Components & state
- Components are pure functions of props + state. Same inputs → same output; no
  side effects during render.
- `useState` for local state; lift state to the closest common ancestor when
  siblings need it; derive values during render instead of storing them.
- Keep state minimal and normalized — don't duplicate what you can compute.

## Hooks rules
- Call hooks at the top level, unconditionally, in the same order every render.
- `useEffect` is for **synchronizing with external systems** (subscriptions,
  timers, non-React widgets) — not for transforming data for rendering.
- Always specify the dependency array; include every reactive value you read.
  Clean up in the returned function.

## Lists & keys
- Give list items a **stable, unique `key`** (an id, not the array index).

## Performance (measure first)
- `useMemo` / `useCallback` to stabilize expensive values and callbacks passed to
  memoized children; `React.memo` to skip re-renders on equal props.
- Don't optimize prematurely — most re-renders are cheap.

## Data & effects
- Prefer data libraries (TanStack Query, Apollo, SWR, RTK Query) over hand-rolled
  `useEffect` fetching: they handle caching, dedupe, loading/error, refetch.
- Controlled inputs: value + `onChange`. Avoid mixing controlled/uncontrolled.

## Composition
- Favor composition over inheritance; share logic via **custom hooks**
  (`useX` returning state/handlers), not deep prop drilling — or use Context for
  truly global, low-churn values (theme, auth).
