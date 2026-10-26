import type { Project } from './types'

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('continuity-detective', 1)
    request.onupgradeneeded = () => { request.result.createObjectStore('project'); request.result.createObjectStore('images') }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}
async function put(store: string, key: string, value: unknown) {
  const db = await database()
  try { await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite'); tx.objectStore(store).put(value, key)
    tx.oncomplete = () => resolve(); tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error)
  }) } finally { db.close() }
}
async function get<T>(store: string, key: string): Promise<T | null> {
  const db = await database()
  try { return await new Promise<T | null>((resolve, reject) => {
    const tx = db.transaction(store, 'readonly'); const request = tx.objectStore(store).get(key)
    request.onsuccess = () => resolve(request.result ?? null); request.onerror = () => reject(request.error)
  }) } finally { db.close() }
}
let projectWrites: Promise<void> = Promise.resolve()
export function saveProject(p: Project) {
  projectWrites = projectWrites.catch(() => {}).then(() => put('project', 'last', p))
  return projectWrites
}
export const loadProject = () => get<Project>('project', 'last')
export const saveImage = (id: string, blob: Blob) => put('images', id, blob)
export const loadImage = (id: string) => get<Blob>('images', id)
