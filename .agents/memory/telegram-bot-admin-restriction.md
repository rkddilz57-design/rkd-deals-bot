---
name: Telegram bot admin-restricted commands
description: How to safely restrict a pyTelegramBotAPI command to an admin chat/topic without it silently breaking.
---

Restrict sensitive commands (e.g. balance top-up) by checking `chat.id == ADMIN_CHAT_ID` AND `from_user.id == ADMIN_ID`. Do not add a hard equality check on `message.message_thread_id` against a hardcoded topic ID.

**Why:** Telegram forum topics can be deleted/recreated by admins in the UI, which changes their numeric ID. A hardcoded topic-ID check makes the command silently stop working (the handler just returns, no error surfaces) the next time the topic is recreated. This already happened once in production.

**How to apply:** For the reply, still use `message.message_thread_id` dynamically (whatever thread the incoming command was sent from) so replies land in the same thread — but never require it to equal a fixed constant for authorization purposes. Chat ID + admin user ID is enough to keep the command private/secure.
