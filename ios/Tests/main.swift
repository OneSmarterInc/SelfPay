import Foundation
let good = ["https://myselfpay-review.vercel.app/", "https://myselfpay-review.vercel.app:443/a?q=1"]
let bad = ["http://myselfpay-review.vercel.app/", "https://myselfpay-review.vercel.app.evil.example/", "https://user@myselfpay-review.vercel.app/", "https://myselfpay-review.vercel.app:444/", "https://myselfpay-review.vercel.app@evil.example/"]
for value in good { precondition(URLPolicy.isInternal(URL(string:value)!)) }
for value in bad { precondition(!URLPolicy.isInternal(URL(string:value)!)) }
for value in ["javascript:alert(1)", "file:///private/test", "data:text/html,test"] {
    precondition(!URLPolicy.canOpenExternally(URL(string:value)!))
}
precondition(URLPolicy.canOpenExternally(URL(string:"tel:123456789")!))
print("11 iOS URL policy checks passed")
