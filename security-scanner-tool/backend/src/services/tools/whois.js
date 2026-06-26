import whois from "whois-json";

const whoisLookup = async (target) => {
  try {
    const hostname = new URL(target).hostname;
    const data = await whois(hostname);
    return data;
  } catch (e) {
    return { error: "whois lookup failed: " + e.message };
  }
};

export default whoisLookup;
