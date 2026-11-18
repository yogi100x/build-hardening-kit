import { listUsers } from "./dal/users.js";

export async function countUsers(): Promise<number> {
  const users = await listUsers();
  return users.length;
}
