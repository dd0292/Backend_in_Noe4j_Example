// ────────────────────────────────────────────────────────────────
// MANUAL VALIDATIONS
// ────────────────────────────────────────────────────────────────

// Users without posts
MATCH (u:Usuario) WHERE NOT (u)-[:CREA]->(:Publicación) RETURN u;

// Posts without tags
MATCH (p:Publicación) WHERE NOT (p)-[:TIENE_ETIQUETA]->(:Etiqueta) RETURN p;

// Non bidirectional friends (inconsistencies)
MATCH (a:Usuario)-[:AMIGO_DE]->(b)
WHERE NOT (b)-[:AMIGO_DE]->(a)
RETURN a,b;
