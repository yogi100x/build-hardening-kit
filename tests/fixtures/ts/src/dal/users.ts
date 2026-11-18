interface Db {
  query(sql: string): Promise<unknown[]>;
}

const db: Db = { query: () => Promise.resolve([]) };

export function listUsers(): Promise<unknown[]> {
  return db.query("select id from users");
}
