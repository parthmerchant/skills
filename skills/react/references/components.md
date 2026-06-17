# React — Components

Function components, composition, rendering, forms, refs, boundaries.

---

## Function components & props

Components are functions that take a single `props` object and return JSX. They
must be **pure**: no side effects, no mutation, same inputs → same output.

```tsx
type ButtonProps = {
  label: string;
  disabled?: boolean;
  onClick: () => void;
};

function Button({ label, disabled = false, onClick }: ButtonProps) {
  return (
    <button disabled={disabled} onClick={onClick}>
      {label}
    </button>
  );
}
```

- Component names must be **Capitalized** — lowercase is treated as a DOM tag.
- Props are read-only. To "change" a prop, the parent must pass a new value.
- Pass data **down** via props; communicate **up** via callback props.

https://react.dev/learn/passing-props-to-a-component

---

## children & composition

`children` is just a prop — favor composition over configuration props.

```tsx
function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

// Usage — generic "slot"
<Card title="Profile">
  <Avatar /> <Bio />
</Card>
```

Favor composition over inheritance. React has no class inheritance for UI —
build complex UIs by nesting and passing components as props/children.

https://react.dev/learn/passing-props-to-a-component#passing-jsx-as-children

---

## Conditional & list rendering

```tsx
{isLoggedIn ? <Dashboard /> : <Login />}
{error && <Banner>{error}</Banner>}      // beware: 0 && ... renders "0"
{count > 0 && <Badge n={count} />}        // guard with a boolean, not a number
```

```tsx
<ul>
  {items.map((item) => (
    <li key={item.id}>{item.name}</li>
  ))}
</ul>
```

- Render lists with `.map()`, returning an element per item.
- `&&` with a numeric left side leaks `0`/`NaN` into the DOM — coerce: `count > 0 && ...`.

https://react.dev/learn/conditional-rendering · https://react.dev/learn/rendering-lists

---

## Keys

Each sibling in a list needs a **stable, unique `key`**.

```tsx
{users.map((u) => <Row key={u.id} user={u} />)}   // ✅ stable id
{users.map((u, i) => <Row key={i} user={u} />)}   // ❌ index — breaks on reorder/insert
```

- Keys must be unique among siblings (not globally) and stable across renders.
- Index keys corrupt state and cause subtle bugs when items reorder, insert, or delete.
- Changing a component's `key` forces React to **remount** it (reset its state).

https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key

---

## Fragments

Return multiple elements without a wrapper DOM node.

```tsx
function Pair() {
  return (
    <>
      <dt>Term</dt>
      <dd>Definition</dd>
    </>
  );
}

// Keyed fragment needs the explicit form:
{rows.map((r) => (
  <React.Fragment key={r.id}>
    <dt>{r.term}</dt>
    <dd>{r.def}</dd>
  </React.Fragment>
))}
```

https://react.dev/reference/react/Fragment

---

## Forms — controlled vs uncontrolled

**Controlled**: React state is the source of truth (`value` + `onChange`).

```tsx
function NameField() {
  const [name, setName] = useState("");
  return (
    <input value={name} onChange={(e) => setName(e.target.value)} />
  );
}
```

**Uncontrolled**: the DOM holds the value; read it via a ref on submit.

```tsx
function Search() {
  const inputRef = useRef<HTMLInputElement>(null);
  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    console.log(inputRef.current?.value);
  }
  return (
    <form onSubmit={onSubmit}>
      <input ref={inputRef} defaultValue="" />
    </form>
  );
}
```

- Never flip between controlled and uncontrolled (don't pass `value={maybeUndefined}`).
- Use `defaultValue`/`defaultChecked` for uncontrolled initial values.
- React 19 supports form `action` props and `useActionState`/`useFormStatus` for progressive form handling.

https://react.dev/reference/react-dom/components/input · https://react.dev/reference/react/useActionState

---

## Refs & forwardRef

Refs hold a mutable value that persists across renders without triggering one —
typically a DOM node.

```tsx
function TextInput() {
  const ref = useRef<HTMLInputElement>(null);
  return <input ref={ref} onFocus={() => ref.current?.select()} />;
}
```

In **React 19**, `ref` is a regular prop — no `forwardRef` needed:

```tsx
function FancyInput({ ref, ...props }: React.ComponentProps<"input">) {
  return <input ref={ref} {...props} />;
}
```

Pre-19 (still common), forward refs explicitly:

```tsx
const FancyInput = React.forwardRef<HTMLInputElement, Props>((props, ref) => (
  <input ref={ref} {...props} />
));
```

- Don't read/write `ref.current` during render — only in effects or handlers.
- `useImperativeHandle` customizes the exposed ref API.

https://react.dev/reference/react/forwardRef · https://react.dev/reference/react/useRef

---

## Portals

Render children into a different DOM subtree (modals, tooltips, toasts) while
keeping them in the React tree (events still bubble through the parent).

```tsx
import { createPortal } from "react-dom";

function Modal({ children }: { children: React.ReactNode }) {
  return createPortal(children, document.body);
}
```

https://react.dev/reference/react-dom/createPortal

---

## Error boundaries

Catch render/lifecycle errors in the subtree and show a fallback. **Class-only**
API today (no hook equivalent); most teams use `react-error-boundary`.

```tsx
class ErrorBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    logError(error, info);
  }
  render() {
    return this.state.hasError ? this.props.fallback : this.props.children;
  }
}
```

- Boundaries do **not** catch errors in event handlers, async code, or SSR — handle those with try/catch.

https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary

---

## Suspense (basics)

`<Suspense>` shows a fallback while a child is "suspending" (waiting on lazy code
or data via a Suspense-enabled source).

```tsx
import { lazy, Suspense } from "react";

const Profile = lazy(() => import("./Profile"));

<Suspense fallback={<Spinner />}>
  <Profile />
</Suspense>
```

- Works with `lazy()` for code splitting and with `use(promise)` / Suspense-enabled data libraries.
- Wrap with an error boundary to handle rejected promises.

https://react.dev/reference/react/Suspense

---

## Docs
- Describing the UI: https://react.dev/learn/describing-the-ui
- Components & props: https://react.dev/learn/passing-props-to-a-component
- Rendering lists: https://react.dev/learn/rendering-lists
- Refs: https://react.dev/learn/referencing-values-with-refs
- Manipulating the DOM with refs: https://react.dev/learn/manipulating-the-dom-with-refs
- createPortal: https://react.dev/reference/react-dom/createPortal
- Error boundaries: https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
- Suspense: https://react.dev/reference/react/Suspense
