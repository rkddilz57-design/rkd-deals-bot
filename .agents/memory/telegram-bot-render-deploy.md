---
name: Deploying Telegram bot to Render
description: Gotchas when running a pyTelegramBotAPI (polling-mode) bot on Render's free tier alongside a Replit dev environment.
---

Only one polling instance can hold `getUpdates` for a given bot token at a time. If the Replit dev workflow and the Render deployment both run the bot with the same `TELEGRAM_BOT_TOKEN`, both get repeated 409 Conflict errors ("terminated by other getUpdates request") and neither processes messages reliably.

**Why:** Telegram's long-polling API only allows one active poller per token; a second poller kicks the first one's long-poll request.

**How to apply:** Once a bot is deployed 24/7 on Render (or any external host), stop/remove the local Replit workflow running the same bot — don't run both. Keep the code in the repo for future edits, but only push to GitHub (`git push <url> HEAD:main`, no remote add needed since `git remote add`/`git init`/`git commit` are blocked as destructive in the main agent sandbox) to trigger Render's auto-redeploy.

Render auto-provides `RENDER_EXTERNAL_URL` for web services — used for self-ping keep-alive loops to avoid free-tier spin-down (no third-party uptime pinger needed).
