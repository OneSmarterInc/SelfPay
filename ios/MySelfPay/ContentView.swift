import SwiftUI
import WebKit

final class BrowserModel: NSObject, ObservableObject, WKNavigationDelegate, WKUIDelegate {
    let webView: WKWebView
    @Published var loading = true
    @Published var failed = false
    @Published var canGoBack = false

    override init() {
        let configuration = WKWebViewConfiguration()
        // Guest session data lasts only for this app process.
        configuration.websiteDataStore = .nonPersistent()
        webView = WKWebView(frame: .zero, configuration: configuration)
        super.init()
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true
        webView.load(URLRequest(url: URLPolicy.home))
    }

    func retry() {
        failed = false
        loading = true
        let url = webView.url.flatMap { URLPolicy.isInternal($0) ? $0 : nil } ?? URLPolicy.home
        webView.load(URLRequest(url: url))
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else { decisionHandler(.cancel); return }
        if URLPolicy.isInternal(url) {
            if action.targetFrame == nil {
                webView.load(action.request)
                decisionHandler(.cancel)
            } else { decisionHandler(.allow) }
            return
        }
        // Only user-activated external links leave the app.
        if action.navigationType == .linkActivated && URLPolicy.canOpenExternally(url) {
            UIApplication.shared.open(url)
        }
        decisionHandler(.cancel)
    }

    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        loading = true
        failed = false
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        loading = false
        canGoBack = webView.canGoBack
    }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        handle(error)
    }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        handle(error)
    }
    private func handle(_ error: Error) {
        if (error as NSError).code == NSURLErrorCancelled { return }
        loading = false
        failed = true
        canGoBack = webView.canGoBack
    }
    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        if response.isForMainFrame, let http = response.response as? HTTPURLResponse, http.statusCode >= 400 {
            failed = true
            loading = false
            decisionHandler(.cancel)
        } else { decisionHandler(.allow) }
    }
}

struct SiteView: UIViewRepresentable {
    let webView: WKWebView
    func makeUIView(context: Context) -> WKWebView { webView }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

struct ContentView: View {
    @StateObject private var browser = BrowserModel()
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Button { browser.webView.goBack() } label: {
                    Image(systemName: "chevron.left").frame(width: 44, height: 44)
                }.disabled(!browser.canGoBack).accessibilityLabel("Go back")
                Spacer()
                Text("MySelfPay").font(.headline)
                Spacer()
                Button { browser.retry() } label: {
                    Image(systemName: "arrow.clockwise").frame(width: 44, height: 44)
                }.accessibilityLabel("Reload")
            }.padding(.horizontal, 8)
            Divider()
            ZStack {
                SiteView(webView: browser.webView)
                if browser.loading { ProgressView("Loading MySelfPay").padding().background(.regularMaterial).cornerRadius(12) }
                if browser.failed {
                    Color(uiColor: .systemBackground)
                    VStack(spacing: 18) {
                        Image(systemName: "wifi.exclamationmark").font(.largeTitle)
                        Text("Unable to load MySelfPay").font(.title2)
                        Text("Check your internet connection and try again.").multilineTextAlignment(.center)
                        Button("Try again") { browser.retry() }.buttonStyle(.borderedProminent)
                    }.padding(28)
                }
            }
        }.tint(Color(red: 16/255, green: 86/255, blue: 101/255))
    }
}
