import dns from "dns/promises";
const common = ["www","api","dev","staging","test","mail","admin"];

const enumSubs = async (target) => {
  try {
    const host = new URL(target).hostname;
    const found = [];
    for (const s of common) {
      const candidate = `${s}.${host}`;
      try {
        const res = await dns.resolve4(candidate);
        if (res && res.length) found.push({ subdomain: candidate, addresses: res });
      } catch (e) {
      }
    }
    return found;
  } catch (e) {
    return { error: "subdomain enumeration failed: " + e.message };
  }
};

export default enumSubs;
