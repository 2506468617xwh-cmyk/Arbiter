from longbridge.openapi import Config, OAuthBuilder, QuoteContext


CLIENT_ID = "95eb6eeb-ebeb-4153-b9d9-9f5d2807e69c"


def main() -> None:
    oauth = OAuthBuilder(CLIENT_ID).build(
        lambda url: print("\n请复制下面这个 URL 到浏览器打开并授权：\n\n" + url + "\n")
    )

    config = Config.from_oauth(oauth)

    ctx = QuoteContext(config)
    resp = ctx.quote(["AAPL.US", "TSLA.US", "700.HK"])

    print("\nLongbridge OAuth 授权成功，行情测试结果：")
    print(resp)


if __name__ == "__main__":
    main()