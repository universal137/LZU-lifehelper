const { parse } = require("node:url");

const sendJson = (res, statusCode, payload) => {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store"
  });
  res.end(body);
};

const sendText = (res, statusCode, text, contentType = "text/plain; charset=utf-8") => {
  res.writeHead(statusCode, {
    "Content-Type": contentType,
    "Content-Length": Buffer.byteLength(text)
  });
  res.end(text);
};

const readJsonBody = async (req) => {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  if (chunks.length === 0) {
    return {};
  }

  const bodyText = Buffer.concat(chunks).toString("utf8");
  try {
    return JSON.parse(bodyText);
  } catch {
    throw new Error("INVALID_JSON");
  }
};

const getRequestParts = (req) => {
  const { pathname, query } = parse(req.url, true);
  const segments = pathname.split("/").filter(Boolean);
  return { pathname, query, segments };
};

module.exports = {
  getRequestParts,
  readJsonBody,
  sendJson,
  sendText
};
