"""Shared Shopify Admin API client for the isrc tools.

Stores are configured in tools/shopify/stores.json (no secrets):
  {"source": {"shop": "brand.myshopify.com", "role": "production"},
   "dev":    {"shop": "brand-dev.myshopify.com", "role": "dev"}}
Secrets live in tools/shopify/.env (gitignored), prefixed by the store alias in capitals:
  SOURCE_CLIENT_ID=...  SOURCE_CLIENT_SECRET=...  SOURCE_ACCESS_TOKEN=... (written by the tool)

Tokens: a saved token is used first. Otherwise the client-credentials grant is tried, which works
when the app and store are in the same organisation (24-hour token, refreshed automatically when it
expires mid-run). Otherwise a one-time browser approval runs through a listener on localhost:3456
and saves a permanent offline token.

Paths: the tools folder is the folder this file sits in (tools/shopify in a project repo), and the
repo root is two levels up from it. Scripts can run from any working directory.
Standard library only. Python 3.9+.
"""
import datetime, glob, hashlib, hmac, html, http.client, http.server, json, os, re, secrets, sys, time
import urllib.error, urllib.parse, urllib.request, webbrowser

API_VERSION_DEFAULT = "2026-07"
PORT = 3456
REDIRECT_URI = f"http://localhost:{PORT}/callback"

READ_SCOPES = [
    "read_products", "read_content", "read_online_store_pages", "read_online_store_navigation",
    "read_metaobjects", "read_metaobject_definitions", "read_files", "read_translations",
    "read_locales", "read_markets", "read_themes",
]
MIGRATE_SCOPES = [
    "write_products", "write_content", "write_online_store_pages", "write_online_store_navigation",
    "write_metaobjects", "write_metaobject_definitions", "write_files",
]
SEO_WRITE_SCOPES = ["write_products", "write_content", "write_online_store_pages", "write_files"]

BULK_RUN = """mutation BulkRun($q: String!) { bulkOperationRunQuery(query: $q) {
  bulkOperation { id status } userErrors { field message } } }"""
BULK_CURRENT = "query BulkCurrent { bulkOperations(first: 5, sortKey: CREATED_AT, reverse: true) { nodes { id status type } } }"
BULK_NODE = """query BulkNode($id: ID!) { node(id: $id) { ... on BulkOperation {
  id status errorCode objectCount url partialDataUrl } } }"""


class ShopifyError(Exception):
    pass


# --- paths ---------------------------------------------------------------------------------------

def tools_dir():
    env = os.environ.get("ISRC_TOOLS_DIR")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, "stores.json")):
        return here
    return os.path.abspath(os.path.join(os.getcwd(), "tools", "shopify"))


def repo_root():
    d = tools_dir()
    if os.path.basename(d) == "shopify" and os.path.basename(os.path.dirname(d)) == "tools":
        return os.path.dirname(os.path.dirname(d))
    return os.getcwd()


def docs_path(*parts):
    return os.path.join(repo_root(), "docs", *parts)


def run_is_usable(run):
    """An export run counts when its summary says it completed and wasn't a --only run."""
    p = os.path.join(run, "summary.json")
    if not os.path.exists(p):
        return False
    try:
        s = json.load(open(p, encoding="utf-8"))
    except ValueError:
        return False
    return bool(s.get("complete", True)) and not s.get("partial")


def latest_run(root=None):
    """Newest complete export under docs/data/raw. Partial (--only) and failed runs are skipped."""
    root = root or docs_path("data", "raw")
    runs = sorted(d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d))
    if not runs:
        raise ShopifyError(f"No exports in {root}. Run export.py first.")
    usable = [r for r in runs if run_is_usable(r)]
    if not usable:
        raise ShopifyError(f"No complete export in {root}: every run is partial (--only) or failed. Run a full export, or pass the run folder explicitly.")
    return usable[-1]


# --- standard metafield definitions -------------------------------------------------------------
# Custom keys that usually mean the same thing as one of Shopify's standard definitions (Settings >
# Custom data > Add definition > Standard) or a category metafield (turned on per product category).
# The list covers the ones we meet most; the admin's Standard list is the current set.
STANDARD_DEFINITIONS = {
    "PRODUCT": {
        ("care_guide", "care_instructions", "care"): "descriptors.care_guide (standard: Care guide)",
        ("subtitle", "sub_title"): "descriptors.subtitle (standard: Subtitle)",
        ("color", "colour", "color_pattern", "colour_pattern"): "shopify.color-pattern (category metafield: Color)",
        ("fabric",): "shopify.fabric (category metafield: Fabric)",
        ("material",): "shopify.material (category metafield: Material)",
        ("gender", "target_gender"): "shopify.target-gender (category metafield: Target gender)",
        ("age_group",): "shopify.age-group (category metafield: Age group)",
        ("rating",): "reviews.rating (standard: Product rating)",
        ("rating_count", "review_count", "reviews_count"): "reviews.rating_count (standard: Product rating count)",
        ("related_products",): "shopify--discovery--product_recommendation.related_products (standard: Related products)",
        ("complementary_products",): "shopify--discovery--product_recommendation.complementary_products (standard: Complementary products)",
        ("google_product_category", "mpn", "condition"): "mm-google-shopping.* (standard: Google Shopping fields)",
    },
    "PRODUCTVARIANT": {
        ("mpn", "condition"): "mm-google-shopping.* (standard: Google Shopping fields)",
    },
}


def standard_match(owner, key):
    """The standard definition a custom key probably duplicates, or None. key is 'namespace.key' or 'key'."""
    ns, _, k = key.rpartition(".")
    if ns and not ns.startswith("custom"):
        return None
    k = k.lower()
    for names, target in STANDARD_DEFINITIONS.get((owner or "").upper().replace("_", ""), {}).items():
        if k in names:
            return target
    return None


# --- approvals -----------------------------------------------------------------------------------

DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def approval(phrase, plan_path=None):
    """Look for an approval in the Approval log of docs/plan.md.

    Accepts a table row in that section whose first cell is the phrase (with or without the
    'Approved: ' prefix), with a date and an approver, or a line in that section that starts with
    the phrase and carries a date. Text elsewhere in the plan never counts.
    Returns (True, "approver, date") or (False, reason).
    """
    plan_path = plan_path or docs_path("plan.md")
    if not os.path.exists(plan_path):
        return False, f"{plan_path} doesn't exist"
    text = open(plan_path, encoding="utf-8").read()
    m = re.search(r"^#+\s*Approval log\s*$(.*?)(?=^#+\s|\Z)", text, re.S | re.M | re.I)
    if not m:
        return False, "docs/plan.md has no 'Approval log' section"
    want = re.sub(r"\s+", " ", phrase.strip().lower())
    bare = want[len("approved: "):] if want.startswith("approved: ") else want
    incomplete = None
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip().strip("`").strip() for c in line.strip("|").split("|")]
            if len(cells) < 3 or set(cells[0]) <= set("-: "):
                continue
            first = re.sub(r"\s+", " ", cells[0].lower())
            if first in (want, bare):
                date = next((c for c in cells[1:] if DATE.search(c)), "")
                who = next((c for c in cells[1:] if c and not DATE.search(c)), "")
                if date and who:
                    return True, f"{who}, {DATE.search(date).group(0)}"
                incomplete = f"'{cells[0]}' is in the approval log but needs a date and an approver"
        elif re.sub(r"\s+", " ", line.lstrip("-* ").lower()).startswith(want) and DATE.search(line):
            return True, DATE.search(line).group(0)
    return False, incomplete or f"'{phrase}' isn't in the Approval log of {os.path.relpath(plan_path, repo_root())}"


def require_approval(phrase):
    ok, detail = approval(phrase)
    if not ok:
        die(f"Refusing: {detail}. Add a row to the approval log: | {phrase} | YYYY-MM-DD | Jeet | |")
    print(f"Approval found: {phrase} ({detail})")


# --- .env ----------------------------------------------------------------------------------------

def read_env(path):
    values = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line.startswith("export "):
                line = line[7:].strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def write_env_value(path, key, value):
    """Rewrite one key. The file is written to a temp file created with mode 600, then swapped in."""
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    out, done = [], False
    for line in lines:
        probe = line[7:].strip() if line.strip().startswith("export ") else line
        if probe.split("=", 1)[0].strip() == key:
            if not done:
                out.append(f"{key}={value}")
                done = True
        else:
            out.append(line)
    if not done:
        out.append(f"{key}={value}")
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _hmac_message(params):
    def esc(s, key=False):
        s = s.replace("%", "%25").replace("&", "%26")
        return s.replace("=", "%3D") if key else s
    return "&".join(f"{esc(k, True)}={esc(v)}" for k, v in sorted(params.items()))


class Store:
    def __init__(self, alias, directory=None):
        self.alias = alias
        self.dir = directory or tools_dir()
        cfg_path = os.path.join(self.dir, "stores.json")
        if not os.path.exists(cfg_path):
            raise ShopifyError(f"Missing {cfg_path}. Run setup_tools.sh first.")
        cfg = json.load(open(cfg_path, encoding="utf-8"))
        if alias not in cfg:
            raise ShopifyError(f"No store '{alias}' in {cfg_path}. Known: {', '.join(cfg)}")
        entry = cfg[alias]
        self.shop = entry["shop"].replace("https://", "").strip("/")
        self.role = entry.get("role", "production")
        self.api_version = entry.get("api_version", API_VERSION_DEFAULT)
        self.env_path = os.path.join(self.dir, ".env")
        env = read_env(self.env_path)
        p = alias.upper().replace("-", "_")
        self.prefix = p
        self.client_id = env.get(f"{p}_CLIENT_ID") or os.environ.get(f"{p}_CLIENT_ID")
        self.client_secret = env.get(f"{p}_CLIENT_SECRET") or os.environ.get(f"{p}_CLIENT_SECRET")
        self.token = env.get(f"{p}_ACCESS_TOKEN") or os.environ.get(f"{p}_ACCESS_TOKEN")
        self.token_expires = float(env.get(f"{p}_TOKEN_EXPIRES", "0") or 0)
        base = os.environ.get("ISRC_API_BASE")
        if base:
            host = urllib.parse.urlparse(base).hostname or ""
            if host not in ("localhost", "127.0.0.1", "::1") and not os.environ.get("ISRC_API_BASE_UNSAFE"):
                raise ShopifyError("ISRC_API_BASE may only point at localhost (it receives the access token). Set ISRC_API_BASE_UNSAFE=1 to override on purpose.")
            print(f"Note: ISRC_API_BASE is set, talking to {base} instead of {self.shop}")
        self.base = base or f"https://{self.shop}"
        self.oauth_base = base or f"https://{self.shop}"
        self._scopes = None

    def require_role(self, allowed):
        if self.role not in allowed:
            raise ShopifyError(f"Refusing: store '{self.alias}' ({self.shop}) has role '{self.role}', allowed: {', '.join(allowed)}")

    # --- tokens ---
    def ensure_token(self, scopes, reauth=False):
        if reauth:
            self.token, self.token_expires = None, 0
        if self.token and (self.token_expires == 0 or self.token_expires > time.time() + 300):
            return self.token
        if not (self.client_id and self.client_secret):
            raise ShopifyError(f"Set {self.prefix}_CLIENT_ID and {self.prefix}_CLIENT_SECRET in {self.env_path}")
        token = self._client_credentials()
        if not token:
            token = self._browser_approval(scopes)
        return token

    def ensure_scopes(self, required, scopes_for_reauth=None):
        """Fail plainly when the app lacks scopes, and re-authorise when a saved token predates a scope change."""
        granted = self.granted_scopes()
        missing = [s for s in required if s not in granted]
        if not missing:
            return granted
        if self.token_expires != 0 and self.client_id and self.client_secret:
            print("Saved 24-hour token lacks scopes; fetching a fresh one in case the app's scopes changed...")
            self._client_credentials()
            granted = self.granted_scopes()
        elif self.client_id and self.client_secret:
            print(f"The saved token lacks {', '.join(missing)}. If the app's scopes were changed, a new approval is needed.")
            self._browser_approval(scopes_for_reauth or (READ_SCOPES + list(required)))
            granted = self.granted_scopes()
        missing = [s for s in required if s not in granted]
        if missing:
            raise ShopifyError(f"The app on {self.shop} is missing scopes: {', '.join(missing)}. Add them to the app, release the version, have the store approve it, then run again with --reauth.")
        return granted

    def _client_credentials(self):
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }).encode()
        req = urllib.request.Request(f"{self.oauth_base}/admin/oauth/access_token", data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403):
                print(f"Direct token refused (HTTP {e.code}). The app and store are in different organisations, so a one-time approval is needed.")
                return None
            raise ShopifyError(f"Token request failed: HTTP {e.code} {e.read()[:300]!r}")
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            raise ShopifyError(f"Could not reach {self.shop} for a token: {e}")
        self.token = body["access_token"]
        self.token_expires = time.time() + int(body.get("expires_in", 86399))
        self._scopes = None
        write_env_value(self.env_path, f"{self.prefix}_ACCESS_TOKEN", self.token)
        write_env_value(self.env_path, f"{self.prefix}_TOKEN_EXPIRES", str(int(self.token_expires)))
        print(f"Got a 24-hour token for {self.shop}.")
        return self.token

    def _verify_hmac(self, params):
        given = params.pop("hmac", "")
        digest = hmac.new(self.client_secret.encode(), _hmac_message(params).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, given)

    def _browser_approval(self, scopes):
        state = secrets.token_urlsafe(16)
        authorize = f"https://{self.shop}/admin/oauth/authorize?" + urllib.parse.urlencode({
            "client_id": self.client_id,
            "scope": ",".join(scopes),
            "redirect_uri": REDIRECT_URI,
            "state": state,
        })
        result = {}
        store = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, text, location=None):
                self.send_response(code)
                if location:
                    self.send_header("Location", location)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<!doctype html><p style='font-family:sans-serif'>{html.escape(text)}</p>".encode())

            def do_GET(self):
                try:
                    self._handle()
                except Exception as e:  # noqa: BLE001 - anything here must end the wait with a message
                    result["error"] = f"Approval failed: {e}"
                    self._send(500, result["error"])

            def _handle(self):
                parsed = urllib.parse.urlparse(self.path)
                params = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
                if parsed.path != "/callback" or "code" not in params:
                    return self._send(302, "Redirecting to Shopify", authorize)
                if params.get("state") != state:
                    return self._send(400, "State mismatch. Open http://localhost:3456/ again.")
                if params.get("shop") != store.shop:
                    return self._send(400, f"Wrong store: {params.get('shop')}")
                if not store._verify_hmac(dict(params)):
                    return self._send(400, "HMAC check failed.")
                body = json.dumps({"client_id": store.client_id, "client_secret": store.client_secret, "code": params["code"]}).encode()
                req = urllib.request.Request(f"{store.oauth_base}/admin/oauth/access_token", data=body,
                                             headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=30) as r:
                        result.update(json.loads(r.read()))
                except urllib.error.HTTPError as e:
                    result["error"] = f"Token exchange failed: HTTP {e.code} {e.read()[:300]!r}"
                    return self._send(500, result["error"])
                self._send(200, "Approved. You can close this tab.")

        try:
            server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
        except OSError:
            raise ShopifyError(f"Port {PORT} is busy. Close whatever is using it and run again.")
        print("\nOne-time approval needed.")
        print(f"1. The app's allowed redirection URLs must include {REDIRECT_URI} (release a new app version if not).")
        print(f"2. In a browser logged into the {self.shop} admin, open http://localhost:{PORT}/ and approve.")
        print("Waiting for approval (Ctrl+C to stop)...")
        try:
            webbrowser.open(f"http://localhost:{PORT}/")
        except Exception:
            pass
        while "access_token" not in result and "error" not in result:
            server.handle_request()
        server.server_close()
        if "error" in result:
            raise ShopifyError(result["error"])
        self.token = result["access_token"]
        self.token_expires = 0
        self._scopes = None
        write_env_value(self.env_path, f"{self.prefix}_ACCESS_TOKEN", self.token)
        write_env_value(self.env_path, f"{self.prefix}_TOKEN_EXPIRES", "0")
        print(f"Saved a permanent token for {self.shop} (scopes: {result.get('scope')}).")
        return self.token

    # --- requests ---
    def gql(self, query, variables=None, retries=6, idempotent=True):
        """One GraphQL call with throttling and retries.

        idempotent=False (creates that aren't safe to repeat): never retried after a timeout, a
        connection error or a 5xx, since the request may have been applied. Throttling is always retried.
        """
        url = f"{self.base}/admin/api/{self.api_version}/graphql.json"
        payload = json.dumps({"query": query, "variables": variables or {}}).encode()
        refreshed = False
        for attempt in range(retries):
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.token or "",
            })
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    body = json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    time.sleep(float(e.headers.get("Retry-After") or 2 ** attempt))
                    continue
                if e.code in (500, 502, 503, 504) and idempotent and attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                if e.code == 401:
                    if not refreshed and self.token_expires != 0 and self.client_id and self.client_secret:
                        refreshed = True
                        print("Token expired mid-run, fetching a new one...")
                        if self._client_credentials():
                            continue
                    raise ShopifyError("401 Unauthorized: the token is invalid, the app was uninstalled, or its scopes changed. Run again with --reauth.")
                if e.code >= 500 and not idempotent:
                    raise ShopifyError(f"HTTP {e.code} on a write that can't be repeated safely. Check the store before running again.")
                raise ShopifyError(f"HTTP {e.code}: {e.read()[:500]!r}")
            except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
                if idempotent and attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                if not idempotent:
                    raise ShopifyError(f"Connection problem on a write that can't be repeated safely ({e}). Check the store before running again.")
                raise ShopifyError(f"Connection problem: {e}")
            errors = body.get("errors")
            if errors:
                codes = {(err.get("extensions") or {}).get("code") for err in errors if isinstance(err, dict)}
                cost = (body.get("extensions") or {}).get("cost") or {}
                if "THROTTLED" in codes and attempt < retries - 1:
                    status = cost.get("throttleStatus") or {}
                    need = cost.get("requestedQueryCost", 100)
                    rate = status.get("restoreRate", 50) or 50
                    time.sleep(max(1, (need - status.get("currentlyAvailable", 0)) / rate))
                    continue
                if "MAX_COST_EXCEEDED" in codes:
                    raise ShopifyError(f"This query costs {cost.get('requestedQueryCost', '?')} points, over Shopify's limit of 1,000 per query. "
                                       "Use smaller page sizes or a bulk operation.")
                raise ShopifyError(json.dumps(errors)[:1000])
            status = ((body.get("extensions") or {}).get("cost") or {}).get("throttleStatus") or {}
            if status and status.get("currentlyAvailable", 1000) < 200:
                time.sleep(1)
            return body["data"]
        raise ShopifyError("Gave up after retries")

    def paginate(self, query, path, variables=None):
        variables = dict(variables or {})
        after = None
        while True:
            variables["after"] = after
            data = self.gql(query, variables)
            node = data
            for key in path:
                node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                raise ShopifyError(f"Nothing at {'.'.join(path)} in the response (missing scope, or the object doesn't exist)")
            for item in node.get("nodes", []):
                yield item
            info = node.get("pageInfo") or {}
            if not info.get("hasNextPage"):
                return
            after = info["endCursor"]

    def granted_scopes(self):
        if self._scopes is None:
            data = self.gql("query { currentAppInstallation { accessScopes { handle } } }")
            self._scopes = sorted(s["handle"] for s in data["currentAppInstallation"]["accessScopes"])
        return self._scopes

    # --- bulk operations ---
    def bulk_query(self, query, dest, timeout=3600, on_status=None):
        """Run a bulk query and download its JSONL to dest. Returns the object count.

        Waits for any bulk query already running for this app on the store, since Shopify allows one
        at a time. A failed operation raises with Shopify's error code. dest is empty when the query
        matched nothing.
        """
        waited = 0
        while True:
            running = [o for o in self.gql(BULK_CURRENT)["bulkOperations"]["nodes"]
                       if o.get("type") == "QUERY" and o["status"] in ("CREATED", "RUNNING", "CANCELING")]
            if running:
                if waited == 0:
                    print("    another bulk operation is running on the store, waiting for it...")
                waited += 1
                time.sleep(5)
                continue
            break
        data = self.gql(BULK_RUN, {"q": query})["bulkOperationRunQuery"]
        if data.get("userErrors"):
            raise ShopifyError("; ".join(e["message"] for e in data["userErrors"]))
        op_id = data["bulkOperation"]["id"]
        delay, start = 2.0, time.time()
        while True:
            op = self.gql(BULK_NODE, {"id": op_id})["node"] or {}
            status = op.get("status")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELED", "EXPIRED"):
                raise ShopifyError(f"bulk operation {status.lower()}: {op.get('errorCode') or 'no error code'}"
                                   + (" (partial data was available but is not used)" if op.get("partialDataUrl") else ""))
            if time.time() - start > timeout:
                raise ShopifyError(f"bulk operation {op_id} still {status} after {timeout // 60} minutes")
            if on_status:
                on_status(status, op.get("objectCount"))
            time.sleep(delay)
            delay = min(delay * 1.5, 15)
        if not op.get("url"):
            open(dest, "w", encoding="utf-8").close()
            return 0
        tmp = dest + ".part"
        with urllib.request.urlopen(op["url"], timeout=300) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        os.replace(tmp, dest)
        return int(op.get("objectCount") or 0)


def utc_stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def die(message):
    print(message, file=sys.stderr)
    sys.exit(1)
