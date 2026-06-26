import axios from "axios";

const commonPaths = ["/admin","/login","/dashboard","/wp-admin","/config","/uploads","/backup","/phpmyadmin"];

const dirScan = async (target) => {
  try {
    const url = new URL(target);
    const results = [];
    await Promise.all(commonPaths.map(async (p) => {
      try {
        const r = await axios.get(`${url.origin}${p}`, { timeout: 5000, validateStatus: () => true });
        results.push({ path: p, status: r.status });
      } catch (e) {
        results.push({ path: p, status: "error" });
      }
    }));
    return results;
  } catch (e) {
    return { error: "dir scan failed: " + e.message };
  }
};

export default dirScan;
