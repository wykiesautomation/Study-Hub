
# Natasha's Study Hub (MVP)

A simple static website for selling South Africa CAPS-aligned study packs (Grade 8–12) from home. Includes a catalog, cart, WhatsApp checkout, and placeholders for PayFast and Google Apps Script lead capture.

## Features
- Brand-blue hero (\#2F76FF) with clear CTAs
- Product catalog loaded from JSON
- Cart + WhatsApp checkout (composes order message)
- PayFast button placeholder (requires server-side signature)
- Lead form ready to post to your Google Apps Script Web App

## Publish on GitHub Pages
1. Create a repository with this folder content.
2. Commit and push.
3. In repo Settings → Pages, select the `main` branch and `/ (root)`.
4. Your site will be live at `https://<your-username>.github.io/<repo-name>/`.
5. (Optional) Point your custom domain (e.g., `wykiesautomation.co.za`) to GitHub Pages via DNS.

## WhatsApp & Email
- WhatsApp: +27 71 681 6131
- Email: wykiesautomation@gmail.com

## PayFast Integration (Next Step)
- Implement a serverless endpoint (Google Apps Script / Cloudflare Workers) to:
  1. Create a signed payment request (merchant_id, merchant_key, amount, item_name, return_url, cancel_url, notify_url).
  2. Redirect customers to the hosted PayFast payment page.
  3. Handle ITN (Instant Transaction Notification) to verify payment and auto-email the download link + invoice PDF.

## Customize
- Update `assets/products.json` with your packs, prices, and Google Drive file links.
- Replace logo and text as preferred.
- Update the free download links.
