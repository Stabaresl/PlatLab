// MD5 (RFC 1321) para `md5sum` en la consola simulada: los labs de hashing
// piden comparar hashes reales de palabras, así que tiene que dar el valor
// correcto, no uno inventado. Opera sobre los bytes UTF-8 del texto.

function rotl(x: number, c: number): number {
  return (x << c) | (x >>> (32 - c))
}

const _S = [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21]
const _K = Array.from({ length: 64 }, (_, i) => Math.floor(Math.abs(Math.sin(i + 1)) * 2 ** 32) >>> 0)

export function md5(texto: string): string {
  const bytes = new TextEncoder().encode(texto)
  const largoBits = bytes.length * 8
  const total = (((bytes.length + 8) >>> 6) + 1) * 64
  const buf = new Uint8Array(total)
  buf.set(bytes)
  buf[bytes.length] = 0x80
  const vista = new DataView(buf.buffer)
  vista.setUint32(total - 8, largoBits >>> 0, true)
  vista.setUint32(total - 4, Math.floor(largoBits / 2 ** 32), true)

  let a0 = 0x67452301
  let b0 = 0xefcdab89
  let c0 = 0x98badcfe
  let d0 = 0x10325476
  for (let off = 0; off < total; off += 64) {
    const m = Array.from({ length: 16 }, (_, i) => vista.getUint32(off + i * 4, true))
    let a = a0
    let b = b0
    let c = c0
    let d = d0
    for (let i = 0; i < 64; i++) {
      let f: number
      let g: number
      if (i < 16) {
        f = (b & c) | (~b & d)
        g = i
      } else if (i < 32) {
        f = (d & b) | (~d & c)
        g = (5 * i + 1) % 16
      } else if (i < 48) {
        f = b ^ c ^ d
        g = (3 * i + 5) % 16
      } else {
        f = c ^ (b | ~d)
        g = (7 * i) % 16
      }
      const tmp = d
      d = c
      c = b
      b = (b + rotl((a + f + _K[i] + m[g]) | 0, _S[i])) | 0
      a = tmp
    }
    a0 = (a0 + a) | 0
    b0 = (b0 + b) | 0
    c0 = (c0 + c) | 0
    d0 = (d0 + d) | 0
  }
  const out = new DataView(new ArrayBuffer(16))
  ;[a0, b0, c0, d0].forEach((v, i) => out.setUint32(i * 4, v >>> 0, true))
  return Array.from(new Uint8Array(out.buffer), (x) => x.toString(16).padStart(2, "0")).join("")
}
