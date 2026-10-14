# Shared application address

Edit `website_url` in root `app-config.json`. It must be an HTTPS root URL.
iOS and Android build generators read this setting; rebuild native apps after a change.
The PWA manifest reads it at request time as its start URL.
Deploy the website at that same origin before installing the PWA: browsers require
the start URL and manifest to share an origin. An existing installed PWA cannot be
moved across domains automatically; reinstall it from the new site.

Production publishing remains a separate owner decision. No deployment was requested.
