const db = {
  /** @param {string} _sql @returns {Promise<unknown[]>} */
  query: (_sql) => Promise.resolve([]),
};

/** @returns {Promise<unknown[]>} */
export function listUsers() {
  return db.query("select id from users");
}
