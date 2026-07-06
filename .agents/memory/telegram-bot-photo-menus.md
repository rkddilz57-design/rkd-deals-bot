---
name: Telegram bot photo-branded menus
description: How to keep a logo/photo attached across all navigable menu screens in a pyTelegramBotAPI (telebot) bot
---

Once any screen in a navigation chain is sent via `bot.send_photo` (to show a logo/branding image), every subsequent "edit in place" call on that same message must use `bot.edit_message_caption`, not `bot.edit_message_text`. Telegram's API rejects `edit_message_text` on a message that has no text (it's a photo with a caption), causing silent failures or exceptions.

**Why:** The user wanted a logo attached to "all messages" a user navigates through (main menu, sub-menus, admin panel, etc.). The bot originally used a mix of `send_message`/`edit_message_text` in ~13+ near-identical screen-render call sites plus several one-off sites (language switch, admin prompts, cancel confirmations).

**How to apply:** Introduce one shared helper (e.g. `show_screen(chat_id, text, markup, message_id=None)`) that:
- sends a new photo with the branding image + caption when `message_id` is None (first render)
- edits the caption of the existing message when `message_id` is given
Route every menu/screen render through this helper instead of ad hoc `send_message`/`edit_message_text` calls. Leave true one-off notifications (e.g. buyer/seller deal alerts sent to a *different* chat/message than the navigable menu) as plain text — they aren't part of the persistent menu chain.
