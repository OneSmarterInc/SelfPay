package com.onesmarter.myselfpay;
import java.net.URI;
import java.util.Locale;

final class UrlPolicy {
    static final String HOME = "https://myselfpay-review.vercel.app/";
    static boolean isInternal(String value) {
        try {
            URI uri = new URI(value);
            return "https".equalsIgnoreCase(uri.getScheme())
                && "myselfpay-review.vercel.app".equalsIgnoreCase(uri.getHost())
                && uri.getRawUserInfo() == null
                && (uri.getPort() == -1 || uri.getPort() == 443);
        } catch (Exception ignored) { return false; }
    }
    static boolean isExternalAllowed(String value) {
        try {
            String scheme = new URI(value).getScheme();
            return scheme != null && java.util.Set.of("https", "http", "tel", "mailto", "geo").contains(scheme.toLowerCase(Locale.ROOT));
        } catch (Exception ignored) { return false; }
    }
}
