package com.onesmarter.myselfpay;

import androidx.activity.ComponentActivity;
import androidx.activity.OnBackPressedCallback;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.SslErrorHandler;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends ComponentActivity {
    private WebView web;
    private LinearLayout errorPanel;
    private ProgressBar progress;
    private boolean failed;
    private String retryUrl = UrlPolicy.HOME;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        web = new WebView(this);
        root.addView(web, new FrameLayout.LayoutParams(-1, -1));
        progress = new ProgressBar(this);
        FrameLayout.LayoutParams spinner = new FrameLayout.LayoutParams(96, 96, Gravity.CENTER);
        root.addView(progress, spinner);
        errorPanel = new LinearLayout(this);
        errorPanel.setOrientation(LinearLayout.VERTICAL);
        errorPanel.setGravity(Gravity.CENTER);
        errorPanel.setPadding(40, 40, 40, 40);
        errorPanel.setBackgroundColor(Color.WHITE);
        TextView message = new TextView(this);
        message.setText("Unable to load MySelfPay.\nCheck your internet connection and try again.");
        message.setGravity(Gravity.CENTER);
        message.setTextSize(18);
        errorPanel.addView(message);
        Button retry = new Button(this);
        retry.setText("Try again");
        retry.setOnClickListener(v -> web.loadUrl(retryUrl));
        errorPanel.addView(retry);
        root.addView(errorPanel, new FrameLayout.LayoutParams(-1, -1));
        errorPanel.setVisibility(View.GONE);
        setContentView(root);
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                if (web.canGoBack()) {
                    web.goBack();
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setGeolocationEnabled(false);
        settings.setSupportMultipleWindows(false);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        // No native JavaScript bridge or embedded credentials.
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return route(request.getUrl().toString(), request.isForMainFrame());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return route(url, true);
            }
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {
                failed = false;
                if (UrlPolicy.isInternal(url)) retryUrl = url;
                errorPanel.setVisibility(View.GONE);
                progress.setVisibility(View.VISIBLE);
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (UrlPolicy.isInternal(url)) injectOriginalMobileUi(view);
                progress.setVisibility(View.GONE);
                if (!failed) errorPanel.setVisibility(View.GONE);
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) showError();
            }
            @Override public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse response) {
                if (request.isForMainFrame() && response.getStatusCode() >= 400) showError();
            }
            @Override public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel();
                showError();
            }
        });
        web.loadUrl(UrlPolicy.HOME);
    }
    private boolean route(String url, boolean mainFrame) {
        if (UrlPolicy.isInternal(url)) return false;
        if (mainFrame && UrlPolicy.isExternalAllowed(url)) {
            try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); }
            catch (ActivityNotFoundException ignored) {
                Toast.makeText(this, "No app is available to open this link.", Toast.LENGTH_SHORT).show();
            }
        }
        return true;
    }
    private void showError() {
        failed = true;
        progress.setVisibility(View.GONE);
        errorPanel.setVisibility(View.VISIBLE);
    }

    // Mirror the original redesign APK: inject its exact CSS and JS into the trusted origin.
    private String readMobileAsset(String name) {
        try (java.io.InputStream in = getAssets().open(name);
             java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            return out.toString("UTF-8");
        } catch (java.io.IOException e) {
            android.util.Log.e("MySelfPay", "Mobile UI asset missing: " + name, e);
            return "";
        }
    }

    private void injectOriginalMobileUi(WebView view) {
        String css = readMobileAsset("mobile-flow.css");
        String js = readMobileAsset("mobile-flow.js");
        String shellCss = readMobileAsset("mobile-shell.css");
        String shellJs = readMobileAsset("mobile-shell.js");
        if (!css.isEmpty()) {
            view.evaluateJavascript("(function(){var el=document.getElementById('myselfpay-mobile-style');" +
                "if(!el){el=document.createElement('style');el.id='myselfpay-mobile-style';" +
                "(document.head||document.documentElement).appendChild(el);}" +
                "el.textContent=" + org.json.JSONObject.quote(css) + ";})();", null);
        }
        if (!js.isEmpty()) view.evaluateJavascript(js, null);
        if (!shellCss.isEmpty()) view.evaluateJavascript("(function(){var s=document.getElementById(\'myselfpay-shell-style\');if(!s){s=document.createElement(\'style\');s.id=\'myselfpay-shell-style\';document.head.appendChild(s);}s.textContent=" + org.json.JSONObject.quote(shellCss) + ";})();", null);
        if (!shellJs.isEmpty()) view.evaluateJavascript(shellJs, null);
    }

    @Override protected void onDestroy() {
        web.stopLoading();
        web.destroy();
        super.onDestroy();
    }
}
