import crypto from "crypto";

function generateToken(): string {
  return crypto.randomBytes(16).toString("hex");
}
