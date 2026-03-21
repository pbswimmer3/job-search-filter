const express = require("express");
const Database = require("better-sqlite3");
const path = require("path");

const app = express();
const PORT = 8082;
const DB_PATH = path.join(__dirname, "..", "jobs.db");

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

function getDb() {
  return new Database(DB_PATH, { readonly: false });
}

// GET /api/qualified
app.get("/api/qualified", (req, res) => {
  const db = getDb();
  try {
    let query = "SELECT * FROM qualified_roles WHERE 1=1";
    const params = [];

    if (req.query.status) {
      const statuses = req.query.status.split(",");
      query += ` AND status IN (${statuses.map(() => "?").join(",")})`;
      params.push(...statuses);
    }
    if (req.query.source) {
      const sources = req.query.source.split(",");
      query += ` AND source IN (${sources.map(() => "?").join(",")})`;
      params.push(...sources);
    }
    if (req.query.remote === "true") {
      query += " AND remote = 1";
    }
    if (req.query.location) {
      query += " AND location LIKE ?";
      params.push(`%${req.query.location}%`);
    }
    if (req.query.min_score) {
      query += " AND score >= ?";
      params.push(parseInt(req.query.min_score));
    }
    if (req.query.max_score) {
      query += " AND score <= ?";
      params.push(parseInt(req.query.max_score));
    }

    query += " ORDER BY score DESC, created_at DESC";
    const rows = db.prepare(query).all(...params);
    res.json(rows);
  } finally {
    db.close();
  }
});

// GET /api/unqualified
app.get("/api/unqualified", (req, res) => {
  const db = getDb();
  try {
    const rows = db
      .prepare("SELECT * FROM unqualified_roles ORDER BY score DESC, created_at DESC")
      .all();
    res.json(rows);
  } finally {
    db.close();
  }
});

// PATCH /api/qualified/:id
app.patch("/api/qualified/:id", (req, res) => {
  const db = getDb();
  try {
    const { status, notes } = req.body;
    const updates = [];
    const params = [];

    if (status !== undefined) {
      const valid = ["new", "applied", "interviewing", "offer", "rejected", "archived"];
      if (!valid.includes(status)) {
        return res.status(400).json({ error: `Invalid status. Must be one of: ${valid.join(", ")}` });
      }
      updates.push("status = ?");
      params.push(status);
    }
    if (notes !== undefined) {
      updates.push("notes = ?");
      params.push(notes);
    }

    if (updates.length === 0) {
      return res.status(400).json({ error: "No fields to update" });
    }

    params.push(req.params.id);
    const result = db
      .prepare(`UPDATE qualified_roles SET ${updates.join(", ")} WHERE id = ?`)
      .run(...params);

    if (result.changes === 0) {
      return res.status(404).json({ error: "Role not found" });
    }
    res.json({ ok: true });
  } finally {
    db.close();
  }
});

// POST /api/unqualified/:id/promote
app.post("/api/unqualified/:id/promote", (req, res) => {
  const db = getDb();
  try {
    const row = db
      .prepare("SELECT * FROM unqualified_roles WHERE id = ?")
      .get(req.params.id);
    if (!row) {
      return res.status(404).json({ error: "Role not found" });
    }

    const score = req.body.score !== undefined ? parseInt(req.body.score) : row.score;

    db.prepare(
      `INSERT OR IGNORE INTO qualified_roles
       (title, company, source, url, date_found, job_description, location, remote, score, score_rationale, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')`
    ).run(
      row.title, row.company, row.source, row.url, row.date_found,
      row.job_description, row.location, row.remote, score,
      row.score_rationale
    );

    db.prepare("DELETE FROM unqualified_roles WHERE id = ?").run(req.params.id);
    res.json({ ok: true });
  } finally {
    db.close();
  }
});

// GET /api/stats
app.get("/api/stats", (req, res) => {
  const db = getDb();
  try {
    const total_active = db
      .prepare("SELECT COUNT(*) as c FROM qualified_roles WHERE status NOT IN ('rejected', 'archived')")
      .get().c;
    const applied = db
      .prepare("SELECT COUNT(*) as c FROM qualified_roles WHERE status = 'applied'")
      .get().c;
    const interviewing = db
      .prepare("SELECT COUNT(*) as c FROM qualified_roles WHERE status = 'interviewing'")
      .get().c;
    const avg_score = db
      .prepare("SELECT COALESCE(AVG(score), 0) as a FROM qualified_roles WHERE status NOT IN ('rejected', 'archived')")
      .get().a;

    res.json({
      total_active,
      applied,
      interviewing,
      avg_score: Math.round(avg_score),
    });
  } finally {
    db.close();
  }
});

app.listen(PORT, () => {
  console.log(`Job Search Dashboard running at http://localhost:${PORT}`);
});
