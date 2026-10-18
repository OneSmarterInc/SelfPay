# Frontend review follow-up

Affordable Imaging checked 2026-10-18: official https://affordablemedimaging.com/pricing/ lists MRI $495 plus $150 contrast; official https://affordablemedimaging.com/wp-content/uploads/2024/06/AIS-Self-pay-prices-UPDATE-6.6.24.pdf lists $495 without contrast and $645 with contrast. The review's $395 recommendation is not supported by these current official sources. No database change performed.

Added public About, Contact, Privacy, Terms and For imaging centers pages, header/footer links, and opt-in OpenStreetMap embeds on facility details. No API key or paid map service. Labels retain reference precision; multiple locations receive separate map buttons. No visitor search coordinates sent to map provider. Header/footer preserve current One Smarter branding.

Corporate contact care@onesmarter.com and address sourced from https://www.onesmarter.com/contact. Pilot fee has not been supplied; page directs facilities to confirm costs with the team rather than claiming a free pilot. Confirm pilot fees and approve public policy wording before launch.

Validation: JavaScript syntax, current client workflow tests (stub transport), two public-page/CSP tests, map helper checks for lazy loading, missing/invalid coordinates. Browser visual QA not performed. No production deployment, SQL, billing changes or outbound messages.
