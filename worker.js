export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const authHeader = request.headers.get("X-Worker-Auth");

    // التحقق من صلاحية مفتاح التأمين الخاص بالـ Worker
    if (!authHeader || authHeader !== env.WORKER_SECRET_KEY) {
      return new Response(JSON.stringify({ error: "Unauthorized access" }), {
        status: 401,
        headers: { "Content-Type": "application/json" }
      });
    }

    // مسار البروكسي لتجاوز الحظر
    if (url.pathname === "/proxy") {
      const targetUrl = url.searchParams.get("url");
      if (!targetUrl) {
        return new Response("Missing target URL", { status: 400 });
      }

      try {
        const response = await fetch(targetUrl, {
          headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
          }
        });
        const body = await response.text();
        return new Response(body, {
          status: response.status,
          headers: { "Content-Type": response.headers.get("content-type") || "text/plain" }
        });
      } catch (err) {
        return new Response("Proxy Error: " + err.message, { status: 500 });
      }
    }

    // مسار استخراج الذكاء الاصطناعي المجاني (Worker AI Fallback)
    if (url.pathname === "/ai-extract") {
      try {
        const { prompt } = await request.json();
        const aiResponse = await env.AI.run("@cf/meta/llama-3-8b-instruct", {
          messages: [{ role: "user", content: prompt }]
        });

        return new Response(JSON.stringify({ response: aiResponse.response }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), { status: 500 });
      }
    }

    return new Response("Not Found", { status: 404 });
  }
};

