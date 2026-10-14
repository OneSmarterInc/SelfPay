import Foundation
let host = URLPolicy.home.host!
let good = ["https://\(host)/", "https://\(host):443/a?q=1"]
let bad = ["http://\(host)/", "https://\(host).evil.example/", "https://user@\(host)/", "https://\(host):444/", "https://\(host)@evil.example/"]
for value in good { precondition(URLPolicy.isInternal(URL(string:value)!)) }
for value in bad { precondition(!URLPolicy.isInternal(URL(string:value)!)) }
for value in ["javascript:alert(1)", "file:///private/test", "data:text/html,test"] {
    precondition(!URLPolicy.canOpenExternally(URL(string:value)!))
}
precondition(URLPolicy.canOpenExternally(URL(string:"tel:123456789")!))
print("11 iOS URL policy checks passed")
