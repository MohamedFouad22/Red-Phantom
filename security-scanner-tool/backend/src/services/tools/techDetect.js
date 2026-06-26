const detectTech = async (target, sections) => {
  const tech = { probable: [] };
  try {
    const headers = sections.headers?.headers || {};
    const robots = sections.robots?.robots?.body || "";

    if (headers['x-powered-by'] && /Express|Node/i.test(headers['x-powered-by'])) tech.probable.push("Node.js / Express");
    if (headers['server'] && /nginx/i.test(headers['server'])) tech.probable.push("nginx");
    if (/wp-admin/.test(robots) || /wp-content/.test(robots)) tech.probable.push("WordPress");

    return tech;
  } catch (e) {
    return { error: "tech detect failed: " + e.message };
  }
};

export default detectTech;
