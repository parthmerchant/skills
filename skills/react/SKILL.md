---
name: react
description: Modern React 18/19 fundamentals — function components, hooks, state management, and rendering performance, framework-agnostic. Use when writing or reviewing React components/hooks, debugging re-renders, stale-closure effect bugs, useEffect/useMemo/useCallback usage, Context, useReducer, Suspense, the React Compiler, or the `use` hook.
---

# React

App-agnostic React 18/19 fundamentals (function components + hooks). Read the
reference that matches your task. Not tied to any framework.

## References
- `references/components.md` — components, props, children, composition, lists/keys, fragments, forms, refs/forwardRef, portals, error boundaries, Suspense
- `references/hooks.md` — all built-in hooks, rules of hooks, effect pitfalls, the `use` hook, custom hooks
- `references/state.md` — local vs lifted vs global, Context, useReducer, derived/immutable state, stores vs server state
- `references/performance.md` — render behavior, memo/useMemo/useCallback, React Compiler, virtualization, code splitting, profiling

## TL;DR
- Components must be **pure** during render — no side effects, no mutation of props/state/DOM. Same props+state → same JSX.
- Hooks run at the **top level**, unconditionally, in the same order every render. Name custom hooks `useX`.
- `useEffect` is for **synchronizing with external systems**, not for transforming data — most effects you write are unnecessary. Derive during render instead.
- List items need a **stable unique `key`** (an id, never the array index for dynamic lists).
- State updates are **immutable** — always create new objects/arrays; never mutate in place.
- `memo`/`useMemo`/`useCallback` are manual optimizations the **React Compiler** can do for you automatically — measure before adding them by hand.
- Prefer a data library (TanStack Query, SWR, RTK Query) over hand-rolled `useEffect` fetching for caching, dedupe, and refetch.
- The new `use` hook reads promises/context and can be called conditionally — pair it with `<Suspense>` and an error boundary.

## Docs
- React docs: https://react.dev
- Learn React: https://react.dev/learn
- Hooks reference: https://react.dev/reference/react/hooks
- React Compiler: https://react.dev/learn/react-compiler
