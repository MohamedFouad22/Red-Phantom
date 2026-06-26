import express from "express";
import { scanWebsite } from "../controllers/scan.controller.js";
const router = express.Router();
router.post("/", scanWebsite);
export default router;
