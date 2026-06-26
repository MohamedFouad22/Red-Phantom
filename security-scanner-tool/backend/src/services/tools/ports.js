import portscanner from "portscanner";
import { URL } from "url";

const commonPorts = [21, 22, 25, 53, 80, 110, 143, 443, 3306, 6379, 8080];

const scanPorts = async (target) => {
  try {
    const host = new URL(target).hostname;
    const results = [];
    for (const p of commonPorts) {
      try {
        const status = await portscanner.checkPortStatus(p, host, 2000);
        if (status === "open") results.push(p);
      } catch (e) {
      }
    }
    return { open: results };
  } catch (e) {
    return { error: "ports scan failed: " + e.message };
  }
};

export default scanPorts;
