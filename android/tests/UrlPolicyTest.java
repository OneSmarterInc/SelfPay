package com.onesmarter.myselfpay;
public final class UrlPolicyTest {
    public static void main(String[] args) {
        check(UrlPolicy.isInternal(UrlPolicy.HOME));
        check(UrlPolicy.isInternal("https://myselfpay-review.vercel.app:443/path?q=a#b"));
        check(!UrlPolicy.isInternal("http://myselfpay-review.vercel.app/"));
        check(!UrlPolicy.isInternal("https://myselfpay-review.vercel.app.evil.example/"));
        check(!UrlPolicy.isInternal("https://myselfpay-review.vercel.app@evil.example/"));
        check(!UrlPolicy.isInternal("https://user@myselfpay-review.vercel.app/"));
        check(!UrlPolicy.isInternal("https://myselfpay-review.vercel.app:444/"));
        check(UrlPolicy.isExternalAllowed("tel:123456789"));
        check(UrlPolicy.isExternalAllowed("https://provider.example/"));
        check(!UrlPolicy.isExternalAllowed("javascript:alert(1)"));
        check(!UrlPolicy.isExternalAllowed("file:///etc/passwd"));
        check(!UrlPolicy.isExternalAllowed("intent://example"));
        System.out.println("12 URL policy checks passed");
    }
    private static void check(boolean result) {
        if (!result) throw new AssertionError("URL policy check failed");
    }
}
