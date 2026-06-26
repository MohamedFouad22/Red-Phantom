import tls from "tls";
import urlLib from "url";

export const getTLSInfo = (url) => {
  return new Promise((resolve) => {
    let hostname = url.replace("https://", "").replace("http://", "").split("/")[0];

    const socket = tls.connect(443, hostname, { servername: hostname }, () => {
      const cert = socket.getPeerCertificate();
      resolve({
        valid_from: cert.valid_from,
        valid_to: cert.valid_to,
        issuer: cert.issuer,
        valid: socket.authorized
      });
      socket.end();
    });

    socket.on("error", () => {
      resolve({ error: "TLS info not available" });
    });
  });
};
