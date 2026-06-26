import { runScan } from "../services/scanner.js";

export const scanWebsite = async (req, res, next) => {
  try {
    let { url } = req.body;
    if (!url) return res.status(400).json({ msg: "URL is required" });

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = "https://" + url;
    }

    const scanResult = await runScan(url);

    const result = {
      url,
      status: "scanned",
      issues: scanResult.issues || [],
      steps: scanResult.steps || []
    };

    res.json(result);

  } catch (err) {
    next(err);
  }
};
