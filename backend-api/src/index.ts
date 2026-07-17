import express from "express"
import cors from "cors"
import bcrypt from "bcryptjs"
import jwt from "jsonwebtoken"
import db from "./db"

const app = express()
const PORT = 3001
const JWT_SECRET = "platlab-dev-secret-2026"

app.use(cors({ origin: "http://localhost:5173", credentials: true }))
app.use(express.json())

// ── Register ──
app.post("/api/register", (req, res) => {
  const { name, email, password } = req.body

  if (!name || !email || !password) {
    res.status(400).json({ error: "name, email and password are required" })
    return
  }

  const existing = db.prepare("SELECT id FROM users WHERE email = ?").get(email)
  if (existing) {
    res.status(409).json({ error: "Email already registered" })
    return
  }

  const hashed = bcrypt.hashSync(password, 10)
  const result = db
    .prepare("INSERT INTO users (name, email, password) VALUES (?, ?, ?)")
    .run(name, email, hashed)

  const token = jwt.sign({ id: result.lastInsertRowid, email }, JWT_SECRET, {
    expiresIn: "24h",
  })

  res.status(201).json({
    token,
    user: { id: result.lastInsertRowid, name, email },
  })
})

// ── Login ──
app.post("/api/login", (req, res) => {
  const { email, password } = req.body

  if (!email || !password) {
    res.status(400).json({ error: "email and password are required" })
    return
  }

  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email) as
    | { id: number; name: string; email: string; password: string }
    | undefined

  if (!user || !bcrypt.compareSync(password, user.password)) {
    res.status(401).json({ error: "Invalid email or password" })
    return
  }

  const token = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, {
    expiresIn: "24h",
  })

  res.json({
    token,
    user: { id: user.id, name: user.name, email: user.email },
  })
})

// ── Me (validate token) ──
app.get("/api/me", (req, res) => {
  const auth = req.headers.authorization
  if (!auth?.startsWith("Bearer ")) {
    res.status(401).json({ error: "No token" })
    return
  }

  try {
    const payload = jwt.verify(auth.slice(7), JWT_SECRET) as {
      id: number
      email: string
    }
    const user = db
      .prepare("SELECT id, name, email FROM users WHERE id = ?")
      .get(payload.id)
    if (!user) {
      res.status(404).json({ error: "User not found" })
      return
    }
    res.json({ user })
  } catch {
    res.status(401).json({ error: "Invalid token" })
  }
})

app.listen(PORT, () => {
  console.log(`🚀 Backend running at http://localhost:${PORT}`)
})
