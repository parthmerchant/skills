## Frontend — nginx + Vite build

**`frontend/Dockerfile`** — multi-stage is essential; the final image is ~25 MB:
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**`frontend/nginx.conf`** — two critical rules: SPA fallback for client-side routing, `/api` proxy to backend hostname (Docker network DNS resolves `backend`):
```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;   # SPA fallback
    }

    location /api {
        proxy_pass http://backend:8000;     # no trailing slash — preserves full path
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }
}
```

**`tailwind.config.js`** — `important: '#root'` scopes utilities to `#root` giving them higher specificity than MUI's injected styles. `darkMode: 'class'` pairs with toggling `.dark` on `<html>`:
```js
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  important: '#root',
  darkMode: 'class',
  theme: { extend: {} },
  plugins: [],
}
```

**`postcss.config.js`:**
```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

**`package.json` dependencies:**
```json
{
  "dependencies": {
    "@emotion/react": "^11.11.3",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.15.0",
    "@mui/material": "^5.15.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "vite": "^4.4.0"
  }
}
```
