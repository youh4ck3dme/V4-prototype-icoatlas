# ICO Atlas Mailer

Custom secure SMTP mailer configuration for `support@icoatlas.sk` using Websupport SMTP.

## Purpose
Configures WordPress to use Websupport SMTP for all outgoing emails securely without storing secrets in the database or codebase.

## Installation
1. Upload the zip package via WordPress Admin -> Plugins -> Add New -> Upload Plugin.
2. Activate the plugin.

## Configuration
Define the `SMTP_PASSWORD` environment variable in your server `.env` file, which is loaded into the WordPress container. The plugin automatically retrieves this environment variable using `getenv('SMTP_PASSWORD')`.

## Security Notes
- No passwords or DB secrets are stored in the codebase or git.
- Fallback checks prevent email sending errors if the password is not set.
