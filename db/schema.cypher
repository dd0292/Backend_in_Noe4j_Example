// ───────────────────────────────
// SCHEMA CONSTRAINTS
// ───────────────────────────────

// Ensure unique identifiers 
CREATE CONSTRAINT usuario_email_unique
IF NOT EXISTS FOR (u:Usuario)
REQUIRE u.email IS UNIQUE;

// Ensure unique etiqueta.name
CREATE CONSTRAINT etiqueta_name_unique
IF NOT EXISTS FOR (e:Etiqueta)
REQUIRE e.nombre IS UNIQUE;

// Ensure required properties
CREATE CONSTRAINT usuario_id_exists
IF NOT EXISTS FOR (u:Usuario)
REQUIRE (u.id) IS NOT NULL;

// Optionally, enforce other properties' existence
CREATE CONSTRAINT publicacion_id_unique
IF NOT EXISTS FOR (p:Publicación)
REQUIRE p.id IS UNIQUE;

// Ensures each post has an id (not null)
CREATE CONSTRAINT IF NOT EXISTS
FOR (p:Publicación)
REQUIRE (p.id) IS NOT NULL;

// [Optional] Index for names for fast searches (not required)
CREATE INDEX IF NOT EXISTS FOR (u:Usuario) ON (u.nombre);