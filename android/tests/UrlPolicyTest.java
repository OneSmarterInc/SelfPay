package com.onesmarter.myselfpay;
public final class UrlPolicyTest {
    public static void main(String[] args) {
        String host = java.net.URI.create(UrlPolicy.HOME).getHost();
        check(UrlPolicy.isInternal(UrlPolicy.HOME));
        check(UrlPolicy.isInternal("https://" + host + ":443/path?q=a#b"));
        check(!UrlPolicy.isInternal("http://" + host + "/"));
        check(!UrlPolicy.isInternal("https://" + host + ".evil.example/"));
        check(!UrlPolicy.isInternal("https://" + host + "@evil.example/"));
        check(!UrlPolicy.isInternal("https://user@" + host + "/"));
        check(!UrlPolicy.isInternal("https://" + host + ":444/"));
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
