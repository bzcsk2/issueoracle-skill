import express from "express";

const app = express();

app.use("/admin", authMiddleware, adminRoutes);

app.get("/public/info", (req, res) => {
  res.json({ status: "ok" });
});
