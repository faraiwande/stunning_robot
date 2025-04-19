# 🛍️ WhatsApp Marketplace Bot

A smart, multilingual WhatsApp-powered marketplace built for rural and local commerce — powered by microservices, LLMs, and Redis caching.

---

## 🚀 Features

- Register sellers via WhatsApp
- Create and confirm product listings
- Handle buyer product requests and follow-ups
- Smart matching of buyer needs with seller listings
- Use Redis to cache and search listings
- Ratings and reviews for sellers
- LLM-powered conversation flow (English, Shona, Ndebele)

---

## 🧩 Microservices Architecture

- **`marketplace_api`** – Flask + PostgreSQL
  - Manages sellers, listings, payments, reviews

- **`bot_service`** – Flask + Twilio + LLM
  - Handles WhatsApp messages
  - Confirms listings, triggers flows

- **`llm_service`** – Flask + Ollama
  - Parses free text into structured JSON
  - Asks follow-up questions

- **`redis_cache`** – Optional for fast listing lookups
  - Index by product_name + location

---

## ⚙️ Technologies

| Layer        | Stack                          |
|--------------|-------------------------------|
| Backend      | Python, Flask, SQLAlchemy      |
| DB           | PostgreSQL                     |
| Messaging    | Twilio WhatsApp API            |
| AI/LLM       | Ollama (Mistral/OpenHermes)    |
| Cache        | Redis                          |
| Hosting      | Hetzner VM (Dockerized)        |

---

## 💬 WhatsApp Conversation Flow

1. `"I want to join"` → registers user
2. `"Selling 10 goats at $20 in Gokwe"` → triggers LLM parsing
3. Bot: *“Confirm? YES or NO”*
4. If YES → sends to `/listings`
5. Buyer: `"Looking for engine oil"` → triggers `/buy_requests`
6. If match in Redis → show seller(s)
7. If no match → ask: *“Want to alert sellers?”*

---

## 📂 Sample Folder Structure

```
marketplace_api/
│   ├── models.py
│   ├── routes.py
│   └── cache_service.py

bot_service/
│   ├── app.py
│   ├── message_handler.py
│   └── state.py

llm_service/
│   └── app.py

redis/ (optional)
```

---

## ✅ Todo

- [ ] Add image upload support for listings
- [ ] Allow seller profile updates
- [ ] Add `/search` endpoint for buyers
- [ ] Add admin dashboard for reviews & seller management
- [ ] Add Redis expiration and cache refresh

---

## ✨ 
Helping communities trade smarter, in their own language, using tools they already know.