# React — Hooks

Built-in hooks, rules, effect pitfalls, the `use` hook, custom hooks.

---

## Rules of Hooks

1. Call hooks **only at the top level** — never inside conditions, loops, nested
   functions, or after an early `return`. Order must be identical every render.
2. Call hooks **only from React functions** — components or other hooks.

The exception: the React 19 `use` hook *may* be called conditionally (see below).

https://react.dev/reference/rules/rules-of-hooks

---

## useState

```tsx
const [count, setCount] = useState(0);
setCount(count + 1);              // value
setCount((c) => c + 1);          // updater — use when next state depends on previous
const [v] = useState(() => expensiveInit());  // lazy initializer runs once
```

- State updates are **asynchronous and batched**; reading `count` right after `setCount` gives the old value.
- Setting state to the **same** value (Object.is) skips the re-render.
- Updates are **immutable** — replace objects/arrays, never mutate.

https://react.dev/reference/react/useState

---

## useEffect — and its pitfalls

Effects **synchronize with external systems** (subscriptions, timers, manual DOM,
non-React widgets, network when no data lib is used). They run *after* commit.

```tsx
useEffect(() => {
  const sub = source.subscribe(setData);
  return () => sub.unsubscribe();   // cleanup: runs before re-run and on unmount
}, [source]);                       // deps: re-run when source changes
```

Dependency array semantics:
- `[a, b]` — re-run when a or b change. Include **every reactive value** you read.
- `[]` — run once after mount (cleanup on unmount).
- *omitted* — run after **every** render (rarely what you want).

Pitfalls:
- **You probably don't need an effect.** Don't use one to transform data for
  rendering (derive during render) or to handle a user event (do it in the handler).
- **Stale closures**: an effect captures the values from its render. Missing deps
  read old values. Use the updater form of `setState` or add the dep.
- **Infinite loops**: setting state in an effect whose deps include that state, or
  depending on a new object/array/function created each render — memoize it or move it out.
- **Race conditions**: cancel stale async work with an `ignore` flag or `AbortController`.

```tsx
useEffect(() => {
  let ignore = false;
  fetch(`/api/${id}`).then((r) => r.json()).then((d) => { if (!ignore) setData(d); });
  return () => { ignore = true; };
}, [id]);
```

https://react.dev/reference/react/useEffect · https://react.dev/learn/you-might-not-need-an-effect

---

## useRef

A mutable container (`.current`) that **persists across renders without causing
one**. For DOM nodes and instance-like values (timers, previous values).

```tsx
const timer = useRef<number | null>(null);
timer.current = window.setTimeout(...);   // mutate freely, no re-render
```

- Don't read/write `.current` during render (it's not reactive — changing it won't update the UI).

https://react.dev/reference/react/useRef

---

## useMemo & useCallback

Cache an expensive computed value / a stable function identity between renders.

```tsx
const sorted = useMemo(() => bigList.slice().sort(cmp), [bigList]);
const onPick = useCallback((id: string) => dispatch({ type: "pick", id }), [dispatch]);
```

- `useCallback(fn, deps)` ≡ `useMemo(() => fn, deps)`.
- Only worth it for genuinely expensive work or for stabilizing props passed to
  `memo`-ized children / effect deps. **The React Compiler often makes these unnecessary.**

https://react.dev/reference/react/useMemo · https://react.dev/reference/react/useCallback

---

## useContext

Read a context value provided by an ancestor — avoids prop drilling.

```tsx
const ThemeContext = createContext<"light" | "dark">("light");

function Toolbar() {
  const theme = useContext(ThemeContext);
  return <div className={theme} />;
}

<ThemeContext.Provider value="dark"><Toolbar /></ThemeContext.Provider>
```

- Every consumer **re-renders** when the provider's `value` changes — keep values stable and split contexts.
- React 19 lets you render `<ThemeContext value="dark">` directly (no `.Provider`).

https://react.dev/reference/react/useContext

---

## useReducer

State logic as a pure `(state, action) => newState` reducer — best for complex or
interdependent state.

```tsx
type Action = { type: "inc" } | { type: "set"; n: number };
function reducer(state: { n: number }, action: Action) {
  switch (action.type) {
    case "inc": return { n: state.n + 1 };
    case "set": return { n: action.n };
  }
}
const [state, dispatch] = useReducer(reducer, { n: 0 });
dispatch({ type: "inc" });
```

https://react.dev/reference/react/useReducer

---

## useId

Generates a unique, SSR-stable id — for accessibility attributes, **not** list keys.

```tsx
const id = useId();
<label htmlFor={id}>Email</label>
<input id={id} />
```

https://react.dev/reference/react/useId

---

## useTransition & useDeferredValue

Mark state updates as non-urgent so the UI stays responsive (concurrent rendering).

```tsx
const [isPending, startTransition] = useTransition();
startTransition(() => setQuery(input));   // low-priority update, interruptible
```

```tsx
const deferredQuery = useDeferredValue(query);  // lags behind during heavy renders
const results = useMemo(() => search(deferredQuery), [deferredQuery]);
```

- `useTransition` wraps the **state update**; `useDeferredValue` wraps a **value** you already have.
- Use `isPending` to show a subtle loading indicator without blocking input.

https://react.dev/reference/react/useTransition · https://react.dev/reference/react/useDeferredValue

---

## useSyncExternalStore

Subscribe to an external (non-React) store safely under concurrent rendering —
the basis for store libraries.

```tsx
const width = useSyncExternalStore(
  (cb) => { window.addEventListener("resize", cb); return () => window.removeEventListener("resize", cb); },
  () => window.innerWidth,        // getSnapshot (client)
  () => 1024                      // getServerSnapshot (SSR)
);
```

https://react.dev/reference/react/useSyncExternalStore

---

## The `use` hook (React 19)

Reads the value of a **promise** (with Suspense) or **context**. Unlike other
hooks, `use` **can be called conditionally** and inside loops.

```tsx
import { use } from "react";

function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise);   // suspends until resolved
  return <ul>{comments.map((c) => <li key={c.id}>{c.text}</li>)}</ul>;
}
// Wrap the caller in <Suspense> + an error boundary.
```

```tsx
const theme = use(ThemeContext);   // like useContext, but conditional-safe
```

https://react.dev/reference/react/use

---

## Custom hooks

Extract reusable stateful logic into a `useX` function. They share *logic*, not
*state* — each call gets its own independent state.

```tsx
function useOnlineStatus() {
  return useSyncExternalStore(
    (cb) => {
      window.addEventListener("online", cb);
      window.addEventListener("offline", cb);
      return () => {
        window.removeEventListener("online", cb);
        window.removeEventListener("offline", cb);
      };
    },
    () => navigator.onLine,
    () => true
  );
}

function Status() {
  const online = useOnlineStatus();
  return <span>{online ? "🟢" : "🔴"}</span>;
}
```

- Must start with `use` so lint rules and React treat it as a hook.
- A custom hook may call other hooks; the Rules of Hooks apply to it too.

https://react.dev/learn/reusing-logic-with-custom-hooks

---

## Docs
- Hooks index: https://react.dev/reference/react/hooks
- Rules of Hooks: https://react.dev/reference/rules/rules-of-hooks
- You Might Not Need an Effect: https://react.dev/learn/you-might-not-need-an-effect
- Synchronizing with Effects: https://react.dev/learn/synchronizing-with-effects
- Custom hooks: https://react.dev/learn/reusing-logic-with-custom-hooks
