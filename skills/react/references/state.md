# React — State Management

Where state lives, how to update it, and when to reach for a library.

---

## Local vs lifted vs global

- **Local**: `useState`/`useReducer` inside the component that owns it. Default choice.
- **Lifted**: when two siblings need the same state, move it to their closest
  common ancestor and pass it down as props + callbacks ("lifting state up").
- **Global**: shared across distant parts of the tree (theme, auth, locale) →
  Context, or a store library for high-churn data.

```tsx
// Lifting state up
function Parent() {
  const [value, setValue] = useState("");
  return (
    <>
      <Input value={value} onChange={setValue} />
      <Preview value={value} />
    </>
  );
}
```

https://react.dev/learn/sharing-state-between-components

---

## Keep state minimal

- Don't store what you can **derive** during render. No `fullName` state if you
  have `first` + `last`. No `isValid` state if it's a function of the inputs.
- Don't duplicate props into state (it goes stale). Use the prop, or `key` to reset.
- Avoid redundant/contradictory state — model one source of truth.

```tsx
// ❌ derived state stored & kept in sync by hand
const [items, setItems] = useState(data);
const [count, setCount] = useState(data.length);
// ✅ derive
const count = items.length;
```

https://react.dev/learn/choosing-the-state-structure

---

## Immutable updates

React detects change by **reference** (Object.is). Always produce new
objects/arrays — never mutate in place.

```tsx
setUser({ ...user, name: "Ada" });                 // object
setList([...list, item]);                          // append
setList(list.filter((x) => x.id !== id));          // remove
setList(list.map((x) => (x.id === id ? { ...x, done: true } : x)));  // update one
setMatrix(m.map((row, r) => r === ri ? row.map((c, ci) => ci === ix ? v : c) : row)); // nested
```

For deep/awkward updates use **Immer** (`produce`) or `useImmer`:

```tsx
import { produce } from "immer";
setState(produce((draft) => { draft.a.b.c = 1; }));   // write "mutations", get immutable result
```

https://react.dev/learn/updating-objects-in-state · https://react.dev/learn/updating-arrays-in-state

---

## Context for state

Context shares a value without prop drilling. Pair it with `useReducer` for a
lightweight app store.

```tsx
const StoreContext = createContext<State | null>(null);
const DispatchContext = createContext<React.Dispatch<Action> | null>(null);

function StoreProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initial);
  return (
    <StoreContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>{children}</DispatchContext.Provider>
    </StoreContext.Provider>
  );
}
```

- **All consumers re-render** when the provider value changes. Split state and
  dispatch into separate contexts (dispatch is stable → its consumers don't re-render).
- Memoize the `value` object (`useMemo`) if it's an inline object.
- Context is not a performance optimization tool — for high-frequency updates with
  many consumers, use a store with selectors.

https://react.dev/learn/scaling-up-with-reducer-and-context

---

## useReducer patterns

- Use it over `useState` when next state depends on several fields, when updates
  are interrelated, or when the same logic fires from many handlers.
- Keep reducers **pure**: no fetches, no mutation, no side effects — return new state.
- Actions describe *what happened* (`{ type: "addedTodo", text }`), not *how to set state*.

https://react.dev/learn/extracting-state-logic-into-a-reducer

---

## Avoiding prop drilling

In order of preference:
1. **Composition** — pass JSX as `children`/props so intermediate components don't need the data.
2. **Custom hooks** — encapsulate the logic and read context inside.
3. **Context** — for truly global, low-churn values (theme, auth, locale).
4. **A store** — when many components read/write frequently-changing shared state.

---

## Client state vs server state

These are different problems — don't manage server data with raw `useState`/`useEffect`.

| Need | Use |
|------|-----|
| Local UI state | `useState` / `useReducer` |
| Shared global UI state | Context, **Zustand**, **Redux Toolkit**, **Jotai** |
| Server/remote data (cache, fetch, sync) | **TanStack Query**, **SWR**, **RTK Query** |

**Server state** (data from an API) has caching, deduping, background refetch,
staleness, retries — a server-cache library handles all of it:

```tsx
import { useQuery } from "@tanstack/react-query";

const { data, isLoading, error } = useQuery({
  queryKey: ["user", id],
  queryFn: () => fetch(`/api/users/${id}`).then((r) => r.json()),
});
```

Reach for a **client store** (Redux Toolkit / Zustand) when:
- Many distant components read/write the same fast-changing state.
- You need middleware, devtools time-travel, or selector-based subscriptions.

Zustand is minimal and selector-based (no provider needed); Redux Toolkit is the
batteries-included standard for larger apps.

https://tanstack.com/query/latest · https://redux-toolkit.js.org · https://zustand.docs.pmnd.rs

---

## Docs
- Managing State: https://react.dev/learn/managing-state
- Choosing the state structure: https://react.dev/learn/choosing-the-state-structure
- Sharing state between components: https://react.dev/learn/sharing-state-between-components
- Reducer + Context: https://react.dev/learn/scaling-up-with-reducer-and-context
- Updating objects/arrays: https://react.dev/learn/updating-objects-in-state
- TanStack Query: https://tanstack.com/query/latest/docs/framework/react/overview
