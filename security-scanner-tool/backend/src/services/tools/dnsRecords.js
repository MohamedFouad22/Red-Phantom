import dns from "dns/promises";

const getDnsRecords = async (target) => {
  try {
    const host = new URL(target).hostname;
    const [a, aaaa, mx, txt, ns] = await Promise.allSettled([
      dns.resolve4(host).catch(() => []),
      dns.resolve6(host).catch(() => []),
      dns.resolveMx(host).catch(() => []),
      dns.resolveTxt(host).catch(() => []),
      dns.resolveNs(host).catch(() => [])
    ]);

    return {
      A: a.status === "fulfilled" ? a.value : [],
      AAAA: aaaa.status === "fulfilled" ? aaaa.value : [],
      MX: mx.status === "fulfilled" ? mx.value : [],
      TXT: txt.status === "fulfilled" ? txt.value : [],
      NS: ns.status === "fulfilled" ? ns.value : []
    };
  } catch (e) {
    return { error: "dns lookup failed: " + e.message };
  }
};

export default getDnsRecords;
