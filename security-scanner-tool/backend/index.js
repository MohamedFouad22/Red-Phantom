import express from "express";
import dotenv from "dotenv";
import scanRouter from "./src/routes/scan.routes.js";
import connectDB from "./src/config/db.js";
import errorHandler from "./src/middleware/errorHandler.js";
import cors from "cors";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());
connectDB();
app.get("/", (req, res) => res.send("Security Scanner API Running..."));
app.use("/api/scan", scanRouter);
app.use(errorHandler);
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
