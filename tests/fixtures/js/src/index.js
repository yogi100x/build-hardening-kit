import { listUsers } from "./dal/users.js";

/** @returns {Promise<number>} */
export async function countUsers() {
  const users = await listUsers();
  return users.length;
}
