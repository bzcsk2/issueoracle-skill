import express from "express";

const app = express();

app.use("/admin", authMiddleware);
app.use("/admin", adminRoutes);

app.get("/admin/users", (req, res) => {
  res.json({ users: [] });
});
