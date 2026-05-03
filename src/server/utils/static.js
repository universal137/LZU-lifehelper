const fs = require("node:fs");
const path = require("node:path");
const { sendText } = require("./http");

const publicDir = path.resolve(__dirname, "..", "..", "..", "public");

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml"
};

const serveStatic = (req, res, pathname) => {
  const requested = pathname === "/" ? "/index.html" : pathname;
  const normalized = path.normalize(requested).replace(/^(\.\.[/\\])+/, "");
  const filePath = path.join(publicDir, normalized);

  if (!filePath.startsWith(publicDir)) {
    sendText(res, 403, "Forbidden");
    return true;
  }

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    return false;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || "application/octet-stream";
  const content = fs.readFileSync(filePath);
  res.writeHead(200, {
    "Content-Type": contentType,
    "Content-Length": content.length
  });
  res.end(content);
  return true;
};

module.exports = {
  serveStatic
};
