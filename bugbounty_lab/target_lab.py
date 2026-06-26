from base64 import urlsafe_b64decode
from json import loads as json_loads
from urllib.parse import urlparse

from flask import Flask, jsonify, make_response, redirect, render_template_string, request

app = Flask(__name__)

FLAGS = {
    "recon-basics": "flag{local_recon_complete}",
    "web-auth-bypass": "flag{auth_logic_master}",
    "idor-training": "flag{idor_hunter}",
    "xss-context": "flag{xss_context_ace}",
    "ssrf-internal": "flag{ssrf_path_unlocked}",
    "subdomain-takeover-sim": "flag{dangling_record_found}",
    "open-redirect-chain": "flag{redirect_chain_complete}",
    "jwt-none-alg": "flag{jwt_validation_broken}",
    "rate-limit-bypass": "flag{rate_limit_bypassed}",
    "cors-misconfig": "flag{cors_policy_unsafe}",
    "ssti-jinja": "flag{jinja_context_escape}",
    "csrf-state-change": "flag{csrf_state_changed}",
    "blind-sqli-lab": "flag{blind_sqli_complete}",
    "xxe-parser-lab": "flag{xxe_file_read_success}",
    "path-traversal-static": "flag{path_escape_done}",
    "graph-ql-introspection": "flag{graphql_hidden_field}",
    "websocket-authz": "flag{ws_channel_broken_authz}",
    "race-condition-wallet": "flag{race_condition_won}",
    "host-header-poisoning": "flag{host_header_poisoned}",
    "oauth-misconfig-lab": "flag{oauth_redirect_exploited}",
    "request-smuggling-sim": "flag{parser_desync_success}",
    "cache-poisoning-lab": "flag{cache_poisoned_cleanly}",
    "prototype-pollution-sim": "flag{prototype_chain_polluted}",
    "ci-token-leak": "flag{ci_secret_recovered}",
}

CACHE_STATE = {"poisoned": False}
RATE_BUCKET = {}


def page(title: str, body: str):
    return render_template_string(
        """
<!doctype html>
<html lang="en">
<head><meta charset="UTF-8"><title>{{ title }}</title></head>
<body style="font-family:Segoe UI,Tahoma,sans-serif;max-width:900px;margin:20px auto;">
<h1>{{ title }}</h1>
<p><a href="/">Back to labs index</a></p>
<div>{{ body|safe }}</div>
</body>
</html>
""",
        title=title,
        body=body,
    )


@app.get("/")
def index():
    links = """
    <ul>
      <li><a href="/recon-lab">Recon Lab</a></li>
      <li><a href="/login-lab">Auth Bypass Lab</a></li>
      <li><a href="/api-lab">IDOR Lab</a></li>
      <li><a href="/xss-lab">XSS Lab</a></li>
      <li><a href="/ssrf-lab">SSRF Lab</a></li>
      <li><a href="/redirect-lab">Open Redirect Lab</a></li>
      <li><a href="/jwt-lab">JWT Lab</a></li>
      <li><a href="/rate-lab">Rate Limit Lab</a></li>
      <li><a href="/cors-lab">CORS Lab</a></li>
      <li><a href="/ssti-lab">SSTI Lab</a></li>
      <li><a href="/csrf-lab">CSRF Lab</a></li>
      <li><a href="/sqli-lab">SQLi Lab</a></li>
      <li><a href="/xxe-lab">XXE Lab</a></li>
      <li><a href="/files-lab">Path Traversal Lab</a></li>
      <li><a href="/graphql-lab">GraphQL Lab</a></li>
      <li><a href="/ws-lab">WebSocket AuthZ Sim</a></li>
      <li><a href="/race-lab">Race Condition Lab</a></li>
      <li><a href="/host-lab">Host Header Lab</a></li>
      <li><a href="/oauth-lab">OAuth Misconfig Lab</a></li>
      <li><a href="/smuggle-lab">Request Smuggling Sim</a></li>
      <li><a href="/cache-lab">Cache Poisoning Lab</a></li>
      <li><a href="/proto-lab">Prototype Pollution Lab</a></li>
      <li><a href="/ci-lab">CI Secret Leak Lab</a></li>
    </ul>
    <!-- recon-flag: flag{local_recon_complete} -->
    """
    return page("Local Target Lab", links)


@app.get("/recon-lab")
def recon_lab():
    record = request.args.get("record", "")
    body = "<p>Try enum records: ?record=staging-old</p>"
    if record == "staging-old":
        body += f"<p>Dangling record proof: <code>{FLAGS['subdomain-takeover-sim']}</code></p>"
    return page("Recon Lab", body)


@app.route("/login-lab", methods=["GET", "POST"])
def login_lab():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # Intentionally broken comparison for local training.
        if username == "admin" and (password == "admin" or "' OR '1'='1" in password):
            return page("Auth Dashboard", f"<p>Admin flag: <code>{FLAGS['web-auth-bypass']}</code></p>")
        return page("Login Failed", "<p>Try payload in password field.</p>")
    return page(
        "Auth Bypass Lab",
        """
<form method="post">
<input name="username" placeholder="username">
<input name="password" placeholder="password">
<button type="submit">Login</button>
</form>
<p>Hint: local SQL-style payload accepted in password.</p>
""",
    )


@app.get("/api-lab")
def api_lab():
    return page("IDOR Lab", "<p>Try: <code>/api-lab/doc/9001?user=guest</code></p>")


@app.get("/api-lab/doc/<int:doc_id>")
def api_doc(doc_id):
    if doc_id == 9001:
        return jsonify({"owner": "admin", "flag": FLAGS["idor-training"]})
    return jsonify({"owner": "guest", "message": "public doc"})


@app.route("/xss-lab", methods=["GET", "POST"])
def xss_lab():
    payload = request.values.get("payload", "")
    body = """
<p>Submit payload with parameter <code>payload</code>.</p>
<p>Admin simulator only reacts to: <code>&lt;script&gt;steal()&lt;/script&gt;</code></p>
"""
    if "<script>steal()</script>" in payload:
        body += f"<p>Admin simulator token: <code>{FLAGS['xss-context']}</code></p>"
    return page("XSS Lab", body)


@app.get("/ssrf-lab")
def ssrf_lab():
    target = request.args.get("url", "")
    if target == "http://127.0.0.1:5001/internal/metadata":
        return jsonify({"metadata": FLAGS["ssrf-internal"]})
    return jsonify({"message": "Try local metadata URL through url param."})


@app.get("/redirect-lab")
def redirect_lab():
    nxt = request.args.get("next")
    if nxt:
        return redirect(nxt)
    return page("Open Redirect Lab", "<p>Try <code>?next=/redirect-lab/final</code></p>")


@app.get("/redirect-lab/final")
def redirect_final():
    return page("Redirect Final", f"<p>Flag: <code>{FLAGS['open-redirect-chain']}</code></p>")


@app.get("/jwt-lab")
def jwt_lab():
    token = request.args.get("token", "")
    if token.count(".") == 2:
        try:
            payload_part = token.split(".")[1]
            pad = "=" * (-len(payload_part) % 4)
            payload = json_loads(urlsafe_b64decode(payload_part + pad).decode("utf-8"))
            if payload.get("role") == "admin":
                return jsonify({"flag": FLAGS["jwt-none-alg"]})
        except Exception:
            pass
    return jsonify({"hint": "Provide forged JWT payload with admin role."})


@app.get("/rate-lab")
def rate_lab():
    key = request.headers.get("X-Forwarded-For", request.remote_addr or "local")
    RATE_BUCKET[key] = RATE_BUCKET.get(key, 0) + 1
    if RATE_BUCKET[key] >= 6:
        return jsonify({"flag": FLAGS["rate-limit-bypass"], "requests": RATE_BUCKET[key]})
    return jsonify({"message": "Send at least 6 requests from same key.", "requests": RATE_BUCKET[key]})


@app.get("/cors-lab")
def cors_lab():
    origin = request.headers.get("Origin", "null")
    data = {"public": "demo", "private_flag": FLAGS["cors-misconfig"] if "evil.local" in origin else "hidden"}
    resp = make_response(jsonify(data))
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp


@app.get("/ssti-lab")
def ssti_lab():
    name = request.args.get("name", "guest")
    template = "Hello " + name
    rendered = render_template_string(template, flag=FLAGS["ssti-jinja"])
    return page("SSTI Lab", f"<p>Response: <code>{rendered}</code></p><p>Hint: use template variables.</p>")


@app.route("/csrf-lab", methods=["GET", "POST"])
def csrf_lab():
    action = request.values.get("action", "")
    if action == "change_email":
        return page("CSRF Result", f"<p>Email updated. Flag: <code>{FLAGS['csrf-state-change']}</code></p>")
    return page("CSRF Lab", "<p>Trigger state change with <code>action=change_email</code>.</p>")


@app.get("/sqli-lab")
def sqli_lab():
    q = request.args.get("q", "")
    if "' OR '1'='1" in q or "1=1" in q:
        return page("SQLi Lab", f"<p>Bypass successful: <code>{FLAGS['blind-sqli-lab']}</code></p>")
    return page("SQLi Lab", "<p>Search endpoint. Try boolean-based payload in q.</p>")


@app.route("/xxe-lab", methods=["GET", "POST"])
def xxe_lab():
    if request.method == "POST":
        xml = request.data.decode("utf-8", errors="ignore")
        if "<!ENTITY" in xml and "&xxe;" in xml:
            return jsonify({"flag": FLAGS["xxe-parser-lab"]})
        return jsonify({"message": "No external entity detected."})
    return page("XXE Lab", "<p>POST XML containing <!ENTITY ...> and use &xxe;.</p>")


@app.get("/files-lab")
def files_lab():
    file_name = request.args.get("file", "")
    if "../" in file_name:
        return page("Files Lab", f"<p>Read secret file: <code>{FLAGS['path-traversal-static']}</code></p>")
    return page("Files Lab", "<p>Try traversal in file parameter.</p>")


@app.post("/graphql-lab")
def graphql_lab():
    payload = request.get_json(silent=True) or {}
    query = payload.get("query", "")
    if "hiddenFlag" in query:
        return jsonify({"data": {"hiddenFlag": FLAGS["graph-ql-introspection"]}})
    return jsonify({"data": {"status": "ok"}, "hint": "Query hiddenFlag field."})


@app.get("/graphql-lab")
def graphql_lab_get():
    return page("GraphQL Lab", "<p>POST JSON: {'query':'{ hiddenFlag }'}</p>")


@app.get("/ws-lab")
def ws_lab():
    channel = request.args.get("channel", "")
    if channel == "admin":
        return jsonify({"event": "admin-feed", "flag": FLAGS["websocket-authz"]})
    return jsonify({"event": "public-feed"})


@app.get("/race-lab")
def race_lab():
    tries = int(request.args.get("tries", "1"))
    if tries >= 2:
        return jsonify({"flag": FLAGS["race-condition-wallet"]})
    return jsonify({"message": "Simulate concurrent requests with tries>=2"})


@app.get("/host-lab")
def host_lab():
    host = request.headers.get("Host", "")
    if "attacker.local" in host:
        return page("Host Header Lab", f"<p>Poisoned reset link flag: <code>{FLAGS['host-header-poisoning']}</code></p>")
    return page("Host Header Lab", "<p>Try changing Host header.</p>")


@app.get("/oauth-lab")
def oauth_lab():
    return page("OAuth Lab", "<p>Try callback: /oauth-lab/callback?redirect_uri=http://evil.local/cb&code=test</p>")


@app.get("/oauth-lab/callback")
def oauth_callback():
    redirect_uri = request.args.get("redirect_uri", "")
    code = request.args.get("code", "")
    if code and urlparse(redirect_uri).netloc == "evil.local":
        return page("OAuth Callback", f"<p>Code leaked. Flag: <code>{FLAGS['oauth-misconfig-lab']}</code></p>")
    return page("OAuth Callback", "<p>Invalid redirect.</p>")


@app.get("/smuggle-lab")
def smuggle_lab():
    te = request.headers.get("Transfer-Encoding") or request.headers.get("X-Transfer-Encoding")
    cl = request.headers.get("Content-Length") or request.headers.get("X-Content-Length")
    if te and cl:
        return jsonify({"flag": FLAGS["request-smuggling-sim"]})
    return jsonify({"message": "Send both TE and CL headers (or X-* simulation headers)."})


@app.get("/cache-lab")
def cache_lab():
    poison = request.args.get("poison")
    if poison == "1":
        CACHE_STATE["poisoned"] = True
        return page("Cache Lab", "<p>Cache poisoned. Now revisit without poison param.</p>")
    if CACHE_STATE["poisoned"]:
        return page("Cache Lab", f"<p>Poisoned cache hit: <code>{FLAGS['cache-poisoning-lab']}</code></p>")
    return page("Cache Lab", "<p>Try poisoning with <code>?poison=1</code>.</p>")


@app.route("/proto-lab", methods=["GET", "POST"])
def proto_lab():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        proto = payload.get("__proto__", {})
        if proto.get("isAdmin") is True:
            return jsonify({"flag": FLAGS["prototype-pollution-sim"]})
        return jsonify({"message": "No prototype pollution effect detected."})
    return page("Prototype Pollution Lab", "<p>POST JSON with __proto__.isAdmin=true</p>")


@app.get("/ci-lab")
def ci_lab():
    return page("CI Lab", "<p>Check build logs at <a href='/ci-lab/logs'>/ci-lab/logs</a>.</p>")


@app.get("/ci-lab/logs")
def ci_logs():
    log_text = f"""
[build] checkout branch
[build] tests passed
[build] warning: leaked_ci_token=abc123
[build] derived_flag={FLAGS["ci-token-leak"]}
"""
    return page("CI Logs", f"<pre>{log_text}</pre>")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
