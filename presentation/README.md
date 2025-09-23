# AI Technical Training — HTML Slides

A lightweight, GitHub Pages–ready slide app. It runs offline, supports keyboard navigation and fullscreen, and includes concise AI training content (LLMs, Transformers, Embeddings, RAG, etc.).

## Features

- Single HTML file app with CSS/JS
- Keyboard: Left/Right, Space, Home/End, F for fullscreen, ? for help
- Progress bar and slide counter
- Hash deep linking (share `#5` to jump to slide 5)
- Simple SVG diagrams embedded locally

## Run locally

Just open `index.html` in your browser. For local dev with a server (optional), use any static server.

## Customize

- Edit slide content in `index.html` (each `<section class="slide">` is one slide)
- Update styles in `css/styles.css`
- Add or remove slides by duplicating a `<section class="slide">` block
- Replace SVGs under `assets/svg/`

## Deploy to GitHub Pages

1. Commit and push this folder as a repository (e.g., `AI-LLM-RAG-MCP-demo`).
2. In GitHub: Settings → Pages → Build and deployment → Source: “Deploy from a branch”.
3. Select the `main` branch and root (`/`) folder. Save.
4. Pages will publish at `https://<your-username>.github.io/<repo>/`.

## Controls

- Next: Right Arrow, Space, PageDown, or click “Next”
- Previous: Left Arrow, PageUp
- First/Last: Home / End
- Fullscreen: F
- Help overlay: ? or top-right “?”

## License

MIT — free to use and modify. Diagrams are original simple SVGs.