import express from "express";
import "express-async-errors";

const app = express();

app.get("/users", async (req, res) => {
  const users = await db.query("SELECT * FROM users");
  res.json(users);
});
