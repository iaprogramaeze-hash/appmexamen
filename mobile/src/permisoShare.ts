/**
 * Loads the bundled permit template and shares the generated PDF.
 * Template stays on-device (informe §8: never sent to the colleague).
 *
 * Uses the expo-file-system v54+ `File`/`Paths` API (legacy helpers throw).
 */
import { Asset } from 'expo-asset';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';

/** Downloads (once) and returns the template bytes. */
export async function cargarPlantillaPermiso(): Promise<Uint8Array> {
  const module = require('../../assets/permiso-plantilla.pdf') as number;
  const asset = Asset.fromModule(module);
  await asset.downloadAsync();
  const uri = asset.localUri ?? asset.uri;
  const file = new File(uri);
  const b64 = await file.base64();
  return base64ToBytes(b64);
}

/** Writes bytes under the cache dir and opens the OS share sheet. */
export async function compartirPdf(
  bytes: Uint8Array,
  nombreArchivo: string,
): Promise<void> {
  const file = new File(Paths.cache, nombreArchivo);
  await file.write(bytes);
  const disponible = await Sharing.isAvailableAsync();
  if (!disponible) {
    throw new Error('No se puede compartir archivos en este dispositivo.');
  }
  await Sharing.shareAsync(file.uri, {
    mimeType: 'application/pdf',
    dialogTitle: 'Permiso de examen',
    UTI: 'com.adobe.pdf',
  });
}

/** Standard base64 → bytes (no `atob` in the RN runtime). */
export function base64ToBytes(b64: string): Uint8Array {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  const clean = b64.replace(/=+$/, '');
  const out = new Uint8Array(Math.floor((clean.length * 3) / 4));
  let o = 0;
  let buffer = 0;
  let bits = 0;
  for (let i = 0; i < clean.length; i++) {
    const idx = chars.indexOf(clean[i]);
    if (idx < 0) continue;
    buffer = (buffer << 6) | idx;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      out[o++] = (buffer >> bits) & 0xff;
    }
  }
  return out.subarray(0, o);
}

/** Standard bytes → base64 (no `btoa` for binary in RN). */
export function bytesToBase64(bytes: Uint8Array): string {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let out = '';
  for (let i = 0; i < bytes.length; i += 3) {
    const b0 = bytes[i];
    const b1 = i + 1 < bytes.length ? bytes[i + 1] : 0;
    const b2 = i + 2 < bytes.length ? bytes[i + 2] : 0;
    const triplet = (b0 << 16) | (b1 << 8) | b2;
    out += chars[(triplet >> 18) & 63];
    out += chars[(triplet >> 12) & 63];
    out += i + 1 < bytes.length ? chars[(triplet >> 6) & 63] : '=';
    out += i + 2 < bytes.length ? chars[triplet & 63] : '=';
  }
  return out;
}
