import axios from "axios";
import dns from "dns/promises";
import net from "net";
import { getTLSInfo } from "../utils/httpClient.js";

const COMMON_PORTS = [80, 443, 21, 22, 25, 3306, 8080, 8443];
const COMMON_SUBDOMAINS = ["www", "api", "admin", "dev", "staging", "mail", "vpn", "app"];
const COMMON_ADMIN_PATHS = [
  "/admin", "/administrator", "/admin/login", "/admin.php", "/wp-admin", "/user/login", "/manage"
];

const client = axios.create({
  timeout: 7000,
  maxRedirects: 5,
  validateStatus: () => true,
  headers: {
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    Accept: "*/*",
  },
});

const scanPort = (host, port) => {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(1500);

    socket.on("connect", () => {
      socket.destroy();
      resolve({ port, open: true });
    });

    socket.on("timeout", () => {
      socket.destroy();
      resolve({ port, open: false });
    });

    socket.on("error", () => {
      resolve({ port, open: false });
    });

    socket.connect(port, host);
  });
};

const detectWAF = (headers) => {
  const wafIndicators = ["cf-ray", "x-sucuri-id", "x-distil-cs", "x-firewall", "x-waf", "server"];
  for (let key of wafIndicators) {
    if (headers[key]) return `Possible WAF Detected: ${headers[key]}`;
  }
  return "No WAF Detected";
};

const checkCookieFlags = (setCookieArray) => {
  const cookieIssues = [];
  if (!setCookieArray) return cookieIssues;
  const arr = Array.isArray(setCookieArray) ? setCookieArray : [setCookieArray];
  arr.forEach((c) => {
    if (!/;\s*HttpOnly/i.test(c)) cookieIssues.push(`Cookie missing HttpOnly: ${c.split("=")[0]}`);
    if (!/;\s*Secure/i.test(c)) cookieIssues.push(`Cookie missing Secure flag: ${c.split("=")[0]}`);
    if (!/;\s*SameSite/i.test(c)) cookieIssues.push(`Cookie missing SameSite attribute: ${c.split("=")[0]}`);
  });
  return cookieIssues;
};

export const runScan = async (url, options = { doSubdomains: true, checkAdminPaths: true, doReflectionTest: true }) => {
  const result = {
    url,
    headers: {},
    securityHeaders: {},
    cors: {},
    cookies: [],
    dns: {},
    httpMethods: [],
    waf: "",
    serverLeak: "",
    robots: "",
    securityTxt: "",
    sitemap: "",
    tls: {},
    portScan: [],
    subdomains: [],
    adminPaths: [],
    reflection: { tested: false, reflected: false },
    issues: [],
    steps: [],
  };

  if (!url.startsWith("http://") && !url.startsWith("https://")) url = "https://" + url;
  const hostname = new URL(url).hostname;

  try {
    const res = await client.get(url);
    const h = res.headers || {};
    result.headers = h;

    result.securityHeaders = {
      "X-Frame-Options": h["x-frame-options"] || "Missing",
      "Content-Security-Policy": h["content-security-policy"] || "Missing",
      "Strict-Transport-Security": h["strict-transport-security"] || "Missing",
      "X-XSS-Protection": h["x-xss-protection"] || "Missing",
      "X-Content-Type-Options": h["x-content-type-options"] || "Missing",
    };

    if (h["server"]) {
      result.serverLeak = `Server header exposed: ${h["server"]}`;
      result.issues.push(`Server version exposed: ${h["server"]}`);
      result.steps.push("Remove or mask Server header in responses.");
    } else result.serverLeak = "No server leak";

    const cookieIssues = checkCookieFlags(h["set-cookie"]);
    cookieIssues.forEach((ci) => {
      result.issues.push(ci);
      result.steps.push("Ensure cookies set Secure, HttpOnly and SameSite as appropriate.");
    });
    result.cookies = h["set-cookie"] || [];

    for (const key in result.securityHeaders) {
      if (result.securityHeaders[key] === "Missing") {
        result.issues.push(`${key} header is missing`);
        result.steps.push(`Add ${key} header (configure server or CDN).`);
      }
    }

    result.waf = detectWAF(h);
    if (result.waf === "No WAF Detected") {
      result.issues.push("Website not protected by WAF");
      result.steps.push("Consider enabling a Web Application Firewall (WAF).");
    }

    const aca = h["access-control-allow-origin"];
    const acMethods = h["access-control-allow-methods"];
    result.cors = { origin: aca || "Not set", methods: acMethods || "Not set" };
    if (aca === "*" || (aca && aca.includes(hostname) === false && aca.includes("*"))) {
      result.issues.push(`CORS policy may be too permissive: ${aca}`);
      result.steps.push("Restrict Access-Control-Allow-Origin to trusted origins.");
    }
    if (acMethods && /DELETE|PUT|TRACE/i.test(acMethods)) {
      result.issues.push(`CORS allows risky methods: ${acMethods}`);
      result.steps.push("Limit allowed CORS methods to safe ones (GET, POST, HEAD).");
    }
  } catch (err) {
    result.headers = { error: "Cannot fetch headers or blocked by WAF/redirect" };
    result.issues.push("Failed to fetch headers (possible block/redirect).");
  }

  try {
    const robotsURL = new URL("/robots.txt", url).href;
    const r = await client.get(robotsURL);
    result.robots = r.data || "Empty";
  } catch {
    result.robots = "robots.txt not found";
    result.issues.push("robots.txt not found");
    result.steps.push("Create a robots.txt to control crawlers.");
  }

  try {
    const secURL = new URL("/.well-known/security.txt", url).href;
    const s = await client.get(secURL);
    result.securityTxt = s.data || "Empty";
  } catch {
    result.securityTxt = "security.txt not found";
  }

  try {
    const sitemapURL = new URL("/sitemap.xml", url).href;
    const sm = await client.get(sitemapURL);
    result.sitemap = sm.data || "Empty";
  } catch {
    result.sitemap = "sitemap.xml not found";
  }

  try {
    const methods = await client.options(url);
    const allow = methods.headers?.["allow"] || "";
    result.httpMethods = allow || "Unknown";
    ["PUT", "DELETE", "TRACE"].forEach((m) => {
      if (allow && allow.includes(m)) {
        result.issues.push(`Dangerous HTTP method allowed: ${m}`);
        result.steps.push(`Disable ${m} method on server unless explicitly required.`);
      }
    });
  } catch {
    result.httpMethods = "Cannot fetch allowed methods";
    result.issues.push("Failed to fetch allowed HTTP methods");
  }

  try {
    result.dns = {
      A: await dns.resolve4(hostname).catch(() => "None"),
      AAAA: await dns.resolve6(hostname).catch(() => "None"),
      MX: await dns.resolveMx(hostname).catch(() => "None"),
      TXT: await dns.resolveTxt(hostname).catch(() => "None"),
    };
  } catch {
    result.dns = "DNS lookup failed";
    result.issues.push("DNS lookup failed");
  }

  result.tls = await getTLSInfo(url);
  if (!result.tls.valid) {
    result.issues.push("TLS certificate invalid or expired");
    result.steps.push("Renew or fix TLS/SSL certificate.");
  }

  const portResults = await Promise.all(COMMON_PORTS.map((p) => scanPort(hostname, p)));
  portResults.forEach((pr) => {
    if (pr.open && [21, 22, 3306].includes(pr.port)) {
      result.issues.push(`Port ${pr.port} is open and potentially dangerous`);
      result.steps.push(`Close or firewall port ${pr.port} if not required.`);
    }
  });
  result.portScan = portResults;

  if (options.doSubdomains) {
    const found = [];
    for (const s of COMMON_SUBDOMAINS) {
      try {
        const host = `${s}.${hostname}`;
        const ips = await dns.resolve4(host).catch(() => null);
        if (ips && ips.length) {
          found.push({ subdomain: host, ips });
          result.steps.push(`Review exposure of subdomain ${host}`);
        }
      } catch {}
    }
    result.subdomains = found;
    if (found.length === 0) result.subdomains = "No common subdomains resolved";
  }

  if (options.checkAdminPaths) {
    const adminFound = [];
    for (const p of COMMON_ADMIN_PATHS) {
      try {
        const pathUrl = new URL(p, url).href;
        const r = await client.head(pathUrl);
        if (r.status === 200 || r.status === 401 || r.status === 403) {
          adminFound.push({ path: p, status: r.status });
          if (r.status === 200) {
            result.issues.push(`Accessible admin path: ${p} (status 200)`);
            result.steps.push(`Protect ${p} with authentication and restrict access by IP.`);
          } else if (r.status === 401 || r.status === 403) {
            result.steps.push(`${p} requires auth (status ${r.status}) — ensure proper hardening.`);
          }
        }
      } catch {}
    }
    result.adminPaths = adminFound.length ? adminFound : "No common admin paths found";
  }

  if (options.doReflectionTest) {
    try {
      result.reflection.tested = true;
      const token = `scan_token_${Date.now()}`;
      const testUrl = new URL(url);
      testUrl.searchParams.set("q", token);
      const r = await client.get(testUrl.href);
      if (typeof r.data === "string" && r.data.includes(token)) {
        result.reflection.reflected = true;
        result.issues.push("Possible reflected input (simple reflection detected) — potential XSS vector");
        result.steps.push("Validate and sanitize user-supplied input and use appropriate CSP.");
      } else {
        result.reflection.reflected = false;
      }
    } catch {
      result.reflection.tested = true;
      result.reflection.reflected = false;
    }
  }

  result.issues = Array.from(new Set(result.issues));
  result.steps = Array.from(new Set(result.steps));

  return result;
};
