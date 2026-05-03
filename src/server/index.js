const http = require("node:http");
const { handleApi } = require("./routes/api");
const { getRequestParts, sendText } = require("./utils/http");
const { serveStatic } = require("./utils/static");

const port = process.env.PORT || 3000;

const server = http.createServer(async (req, res) => {
  const { pathname } = getRequestParts(req);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      Allow: "GET,POST,PATCH,OPTIONS"
    });
    res.end();
    return;
  }

  if (pathname.startsWith("/api/")) {
    const handled = await handleApi(req, res);
    if (!handled) {
      sendText(res, 404, "Not Found");
    }
    return;
  }

  if (!serveStatic(req, res, pathname)) {
    sendText(res, 404, "Not Found");
  }
});

server.listen(port, () => {
  console.log(`LZU Life Assistant running at http://localhost:${port}`);
});
