# 🎄 Lions Club Adventskalender Checker

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)
![License](https://img.shields.io/badge/License-GPL--3.0-green?style=for-the-badge)

A web application to check if your Lions Club Schwenningen/Villingen advent calendar number has won a prize. Features a festive UI with falling snowflakes! ❄️

---

## ⚠️ Disclaimer

> **This is an unofficial hobby project!**
>
> I am **not affiliated, associated, authorized, endorsed by, or in any way officially connected** with the Lions Club Schwenningen, Lions Club Villingen, or any of their subsidiaries or affiliates.
>
> This project was created with help of AI for personal use and educational purposes only. For official information, please visit [adventskalender-vs.de](https://adventskalender-vs.de/) or the official Lions Club websites.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Check your number** | Instantly see if your calendar number has won |
| 🎁 **Prize details** | View what you've won, including prize value and sponsor |
| 📊 **Statistics** | See how many days have been drawn and total winners |
| 🗓️ **All winning numbers** | Browse all winning numbers organized by day |
| 📍 **Collection info** | Get details on where and when to pick up your prize |
| 📱 **Responsive design** | Works on desktop and mobile |
| ❄️ **Festive UI** | Christmas-themed interface with animated snowflakes |

---

## 🚀 Live Demo

👉 **Check out the live version:** [lionsclub-advent-checker.vercel.app](https://lionsclub-advent-checker.vercel.app/)

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | Backend runtime |
| ![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white) | Web framework |
| ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white) | Upstash Redis for caching |
| ![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup4-59666C?style=flat-square&logo=python&logoColor=white) | Web scraping |
| ![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white) | Hosting & serverless functions |
| ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white) | Frontend markup |
| ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white) | Styling |
| ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) | Frontend logic |

---

## ⚙️ Configuration

The application requires several environment variables to function correctly, especially for caching and administrative tasks.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `UPSTASH_REDIS_REST_URL` | Your Upstash Redis REST URL | Yes |
| `UPSTASH_REDIS_REST_TOKEN` | Your Upstash Redis REST Token | Yes |
| `ADMIN_SECRET_TOKEN` | A secret token used to protect administrative endpoints | Yes |

---

## 🔌 API Endpoints

### Public Endpoints

#### `GET /api/check?number=<YOUR_NUMBER>`
Checks if a specific calendar number has won a prize.
- **Parameters:** `number` (string/int)
- **Response:** JSON with winning status, days, and prize details.

### Protected Endpoints
*Requires authentication via `X-API-KEY` header or `token` query parameter.*

#### `GET /api/cache-status`
Returns the current status of the Redis cache, including the last update timestamp.

#### `GET /api/init-cache`
Manually triggers a fresh scrape of the winning numbers and updates the cache.

#### `GET /api/init-prize-cache`
Iterates through all winning days and pre-caches the detailed prize information (fetched via AJAX).

---

## 🚀 Deployment (Vercel)

1. **Push to GitHub**: Connect your repository to Vercel.
2. **Set Environment Variables**: Add the `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, and `ADMIN_SECRET_TOKEN` in the Vercel Project Settings.
3. **Deploy**: Vercel will automatically detect the `vercel.json` and deploy the Flask app as a serverless function.

---

