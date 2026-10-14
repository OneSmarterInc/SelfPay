import Foundation

enum URLPolicy {
    static let home = URL(string: "https://myselfpay-review.vercel.app/")!
    static func isInternal(_ url: URL) -> Bool {
        url.scheme?.lowercased() == "https" &&
        url.host?.lowercased() == home.host &&
        url.user == nil && url.password == nil &&
        (url.port == nil || url.port == 443)
    }
    static func canOpenExternally(_ url: URL) -> Bool {
        ["https", "http", "tel", "mailto", "geo"].contains(url.scheme?.lowercased() ?? "")
    }
}
