const OpenAI = require("openai");

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

async function askGroq(text) {
  try {
    const response = await client.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: [{ role: "user", content: text }],
      temperature: 0.2,
    });

    return response.choices[0].message.content || "No response from AI.";
  } catch (e) {
    console.error("Groq API error:", e.message);
    return `Error Groq: ${e.message}`;
  }
}

module.exports = { askGroq };