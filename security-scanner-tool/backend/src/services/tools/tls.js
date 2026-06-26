import tls from "tls";
import urlLib from "url";

const getTLSInfo = (target) => {
  return new Promise((resolve) => {
    let hostname;
    try {
      hostname = new URL(target).hostname;
    } catch (e) {
      return resolve({ error: "Invalid URL" });
    }

    const socket = tls.connect(443, hostname, { servername: hostname, rejectUnauthorized: false }, () => {
      const cert = socket.getPeerCertificate(true);
      const valid = cert && cert.valid_to ? (new Date(cert.valid_to) > new Date()) : false;
      resolve({
        subject: cert.subject || null,
        issuer: cert.issuer || null,
        valid_from: cert.valid_from || null,
        valid_to: cert.valid_to || null,
        valid
      });
      socket.end();
    });

    socket.on("error", (err) => {
      resolve({ error: "TLS socket error: " + err.message });
    });
  });
};

export default getTLSInfo;
