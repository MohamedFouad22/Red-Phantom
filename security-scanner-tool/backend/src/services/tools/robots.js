import axios from "axios";

const fetchRobots = async (target) => {
  try {
    const url = new URL(target);
    const robotsUrl = `${url.protocol}//${url.hostname}/robots.txt`;
    const sitemapUrl = `${url.protocol}//${url.hostname}/sitemap.xml`;

    const [robotsResp, sitemapResp] = await Promise.allSettled([
      axios.get(robotsUrl, { timeout: 5000, validateStatus: () => true }),
      axios.get(sitemapUrl, { timeout: 5000, validateStatus: () => true })
    ]);

    return {
      robots: robotsResp.status === "fulfilled" ? { status: robotsResp.value.status, body: robotsResp.value.data } : null,
      sitemap: sitemapResp.status === "fulfilled" ? { status: sitemapResp.value.status, body: sitemapResp.value.data } : null
    };
  } catch (e) {
    throw new Error("robots check failed: " + e.message);
  }
};

export default fetchRobots;
