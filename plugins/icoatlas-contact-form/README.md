# ICO Atlas Contact Form

Premium secure contact form with shortcode, glassmorphism design, rate-limiting, and admin messages tracker.

## Purpose
Renders a secure, beautiful, mobile-friendly contact form on the frontend and logs all valid submissions to a custom database table.

## Installation
1. Upload the zip package via WordPress Admin -> Plugins -> Add New -> Upload Plugin.
2. Activate the plugin.

## Usage
Add the following shortcode to any WordPress page:
```text
[icoatlas_contact_form]
```

## Admin Interface
All submitted messages can be viewed, marked as read/replied, or deleted under:
**ICO Atlas -> Contact Messages**

## Security and Spam Protection
- **Honeypot Field:** Silent spam-bot detection via a hidden form field.
- **Rate Limiting:** Maximum 5 submissions per 15 minutes per IP address (SHA-256 hashed and stored using WordPress transients).
- **Sanitization:** All inputs are fully sanitized before database insertion and email delivery.
