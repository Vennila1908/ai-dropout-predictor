# `docker/`

The actual `Dockerfile` for each service lives next to its source:

* Backend: [`../backend/Dockerfile`](../backend/Dockerfile)
* Frontend: [`../frontend/Dockerfile`](../frontend/Dockerfile)

This folder only contains shared assets that don't fit cleanly inside a
single service:

* `nginx.conf` — reference Nginx config for fronting both services in
  production. The frontend image already bundles its own minimal Nginx
  ([`../frontend/nginx.conf`](../frontend/nginx.conf)); use the file in this
  folder if you want a single edge proxy for both backend and frontend.

See [`../docker-compose.yml`](../docker-compose.yml) for the full
docker-compose definition and profile flags (`postgres`, `ollama`, `full`).
