package com.onesmarter.myselfpay;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.widget.ImageView;
import android.widget.ScrollView;
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

public class MainActivity extends Activity {
    private WebView web;
    private ScrollView home;
    private FrameLayout content;
    private TextView title;
    private Button homeTab, searchTab, moreTab;
    private boolean openSearch;
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
        content = root;
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setBackgroundColor(Color.WHITE);
        shell.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        root.setOnApplyWindowInsetsListener(null);
        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(8), dp(4), dp(8), dp(4));
        Button back = action("‹", "Go back");
        back.setOnClickListener(v -> onBackPressed());
        toolbar.addView(back, new LinearLayout.LayoutParams(dp(48), dp(48)));
        title = text("MySelfPay", 20, true);
        toolbar.addView(title, new LinearLayout.LayoutParams(0, dp(48), 1));
        title.setGravity(Gravity.CENTER_VERTICAL);
        Button refresh = action("↻", "Refresh live information");
        refresh.setOnClickListener(v -> { if(home.getVisibility()!=View.VISIBLE) web.reload(); });
        toolbar.addView(refresh, new LinearLayout.LayoutParams(dp(48), dp(48)));
        shell.addView(toolbar);
        home = createHome();
        root.addView(home, new FrameLayout.LayoutParams(-1,-1));
        shell.addView(root, new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout tabs = new LinearLayout(this);
        tabs.setPadding(dp(12),dp(4),dp(12),dp(4));
        homeTab = action("Home", "Home");
        searchTab = action("Search", "Search imaging");
        Button more = action("More", "About, privacy and support");
        moreTab = more;
        tabs.setElevation(dp(8));
        tabs.addView(homeTab,new LinearLayout.LayoutParams(0,dp(56),1));
        tabs.addView(searchTab,new LinearLayout.LayoutParams(0,dp(56),1));
        tabs.addView(more,new LinearLayout.LayoutParams(0,dp(56),1));
        homeTab.setOnClickListener(v -> showHome());
        searchTab.setOnClickListener(v -> showSearch());
        more.setOnClickListener(v -> new AlertDialog.Builder(this).setTitle("MySelfPay")
            .setItems(new String[]{"About","Contact","Terms & Privacy","For imaging centers","Sign out"},(dialog,index)->{
                if(index==4){
                    new AlertDialog.Builder(this).setMessage("Sign out?")
                        .setPositiveButton("Sign out",(d,w)->{
                            web.evaluateJavascript("(function(){var p=document.getElementById('profile');if(p&&p.textContent==='Sign out')p.click();})()",null);
                            showHome();
                        }).setNegativeButton("Cancel",null).show();
                }else{
                    String[] paths={"about","contact","privacy-terms","for-imaging-centers"};
                    home.setVisibility(View.GONE);web.setVisibility(View.VISIBLE);
                    title.setText(new String[]{"About","Contact","Terms & Privacy","For imaging centers"}[index]);
                    selectTab(moreTab);openSearch=false;web.loadUrl(UrlPolicy.HOME+paths[index]);
                }
            }).show());
        shell.addView(tabs);
        setContentView(shell);
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
                progress.setVisibility(View.GONE);
                if (!failed) errorPanel.setVisibility(View.GONE);
                if (UrlPolicy.isInternal(url)) applyAppLayout();
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
        showHome();
    }
    private int dp(int value){ return Math.round(value*getResources().getDisplayMetrics().density); }
    private TextView text(String value,int size,boolean bold){
        TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.rgb(30,34,38));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return t;
    }
    private Button action(String label,String description){
        Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(16);
        b.setContentDescription(description);b.setMinWidth(0);b.setMinimumWidth(0);
        b.setPadding(dp(8),0,dp(8),0);b.setStateListAnimator(null);
        styleButton(b,Color.TRANSPARENT,Color.rgb(30,34,38));return b;
    }
    private void styleButton(Button button,int background,int foreground){
        GradientDrawable shape=new GradientDrawable();shape.setColor(background);shape.setCornerRadius(dp(16));
        button.setBackground(new android.graphics.drawable.RippleDrawable(
            android.content.res.ColorStateList.valueOf(0x22000000),shape,null));
        button.setTextColor(foreground);
    }
    private void selectTab(Button selected){
        for(Button tab:new Button[]{homeTab,searchTab,moreTab}){
            boolean active=tab==selected;
            styleButton(tab,active?Color.rgb(253,234,235):Color.TRANSPARENT,
                active?Color.rgb(176,27,35):Color.rgb(80,85,90));
            tab.setTypeface(Typeface.DEFAULT,active?Typeface.BOLD:Typeface.NORMAL);
            tab.setSelected(active);
        }
    }
    private ScrollView createHome(){
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(Color.rgb(246,246,245));
        LinearLayout column=new LinearLayout(this);column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(24),dp(28),dp(24),dp(28));scroll.addView(column);
        ImageView logo=new ImageView(this);logo.setImageResource(com.onesmarter.myselfpay.R.drawable.ic_launcher);
        logo.setContentDescription("MySelfPay logo");column.addView(logo,new LinearLayout.LayoutParams(dp(76),dp(76)));
        TextView heading=text("Find self-pay MRI and CT near you.",32,true);
        heading.setPadding(0,dp(24),0,dp(12));column.addView(heading);
        TextView intro=text("Compare published prices, see what’s included, and call the facility in one tap.",18,false);column.addView(intro);
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(20),dp(20),dp(20),dp(20));
        GradientDrawable bg=new GradientDrawable();bg.setColor(Color.WHITE);bg.setCornerRadius(dp(20));card.setBackground(bg);card.setElevation(dp(3));
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.topMargin=dp(28);column.addView(card,cp);
        card.addView(text("Find imaging options",23,true));
        TextView detail=text("Choose your exam and location. Compare published prices and contact the facility.",16,false);
        detail.setPadding(0,dp(12),0,dp(20));card.addView(detail);
        Button start=action("Sign in as guest","Sign in as guest");
        styleButton(start,Color.rgb(176,27,35),Color.WHITE);start.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        start.setOnClickListener(v->showSearch());card.addView(start,new LinearLayout.LayoutParams(-1,dp(56)));
        TextView note=text("Live directory • No account needed",14,true);note.setPadding(0,dp(24),0,dp(12));column.addView(note);
        column.addView(text("Prices and availability are confirmed directly with the facility. Internet connection required.",14,false));
        return scroll;
    }
    private void showHome(){
        home.setVisibility(View.VISIBLE);web.setVisibility(View.INVISIBLE);
        title.setText("MySelfPay");selectTab(homeTab);
    }
    private void showSearch(){
        home.setVisibility(View.GONE);web.setVisibility(View.VISIBLE);title.setText("Find imaging options");
        selectTab(searchTab);
        openSearch=true;
        if(web.getUrl()==null || !web.getUrl().equals(UrlPolicy.HOME))web.loadUrl(UrlPolicy.HOME);
        else applyAppLayout();
    }
    private void applyAppLayout(){
        String css="body>header,body>.site-footer{display:none!important} .shell{margin:12px auto!important;padding:0 12px!important} .info-page>.panel{border:0!important} .back-to-search{display:none!important} .welcome-intro,.welcome-steps,.welcome-paths{display:none!important} .grid{grid-template-columns:minmax(0,1fr)!important} .panel,.card{border-radius:18px!important} button,input,select{min-height:48px} .sticky{bottom:8px!important}";
        web.evaluateJavascript("(function(){var s=document.getElementById('android-app-layout');if(!s){s=document.createElement('style');s.id='android-app-layout';document.head.appendChild(s);}s.textContent="+org.json.JSONObject.quote(css)+";})()",null);
        if(openSearch){
            openSearch=false;
            web.evaluateJavascript("(function(){var tries=0;function enter(){var b=document.getElementById('welcomeBegin');if(b){b.click();return;}if(document.getElementById('searchForm'))return;if(++tries<40)setTimeout(enter,150);}enter();})()",null);
        }
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
    @Override public void onBackPressed() {
        if(home.getVisibility()==View.VISIBLE){super.onBackPressed();return;}
        if(web.canGoBack())web.goBack();else showHome();
    }
    @Override protected void onDestroy() {
        web.stopLoading();
        web.destroy();
        super.onDestroy();
    }
}
