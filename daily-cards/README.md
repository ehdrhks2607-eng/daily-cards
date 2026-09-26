# daily-cards

Daily Threads + Instagram carousel publisher (official Meta APIs, GitHub Actions).

- `posts/<date>/<account>/post.json` — text, caption, cards, publish time, approval flag, results
- `scripts/render_cards.py` — cards → 1080x1350 PNG (run on the content side)
- `scripts/publish.py` — posts due items (Actions, every 30 min)
- `scripts/refresh_tokens.py` — weekly long-lived token refresh
- Setup: see `SETUP.md`
