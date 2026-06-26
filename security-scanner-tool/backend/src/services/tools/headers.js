import axios from "axios";

const checkHeaders = async (target) => {
  try {
    const resp = await axios.get(target, { timeout: 10000, maxRedirects: 5, validateStatus: () => true });
    const h = resp.headers;

    const findings = {
      cspMissing: !h["content-security-policy"],
      xFrameNotSet: !h["x-frame-options"],
      hstsMissing: !h["strict-transport-security"],
      cookies: null
    };

    if (h["set-cookie"]) {
      findings.cookies = h["set-cookie"].map(c => {
        return {
          raw: c,
          httpOnly: /HttpOnly/i.test(c),
          secure: /Secure/i.test(c),
          sameSite: /SameSite/i.test(c)
        };
      });
    }

    return { status: resp.status, headers: h, findings };
  } catch (e) {
    throw new Error("headers check failed: " + e.message);
  }
};

export default checkHeaders;
