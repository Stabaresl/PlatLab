"""
Hash de secretos de laboratorio (flags y respuestas de examen) — NO de
contraseñas de usuario (esas siguen con `make_password`/PBKDF2).

Por qué HMAC-SHA256 con clave del servidor y no PBKDF2:

- Rendimiento (RNF-02.3, validar flag <1 s): PBKDF2 de Django 6 hace
  ~1.2M iteraciones (~200 ms de CPU por verificación). En las pruebas de
  carga eso convertía cada intento de flag en segundos de cola con 100
  usuarios, y un examen de N preguntas en N × 200 ms.
- Seguridad: PBKDF2 protege contraseñas elegidas por humanos ante una fuga
  de la base. Una respuesta de examen ("'" o el texto de una opción
  visible) no tiene entropía que proteger: con PBKDF2 se crackea igual en
  segundos. Con HMAC + clave que no vive en la base (`FLAG_HASH_KEY`, por
  defecto derivada de `SECRET_KEY`), una fuga de la base sola no permite
  probar candidatos offline — es estrictamente más fuerte para este caso.
- La comparación es en tiempo constante (`hmac.compare_digest`).

Compatibilidad: los hashes PBKDF2 ya guardados (formato `pbkdf2_sha256$...`)
se siguen verificando con `check_password`, así que no hace falta migrar
datos existentes.
"""

import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.hashers import check_password

_PREFIJO = "hmac_sha256$"


def _clave() -> bytes:
    base = getattr(settings, "FLAG_HASH_KEY", None) or settings.SECRET_KEY
    # Derivada (no la SECRET_KEY cruda) para que una misma clave no se use
    # tal cual en dos contextos criptográficos distintos (JWT y flags).
    return hashlib.sha256(b"platlab:secretos-laboratorio:" + base.encode()).digest()


def hashear_secreto(valor: str) -> str:
    digest = hmac.new(_clave(), valor.encode(), hashlib.sha256).hexdigest()
    return f"{_PREFIJO}{digest}"


def verificar_secreto(valor: str, hash_guardado: str) -> bool:
    if hash_guardado.startswith(_PREFIJO):
        return hmac.compare_digest(hashear_secreto(valor), hash_guardado)
    # Formato legado (PBKDF2 de Django) — datos creados antes de este cambio.
    return check_password(valor, hash_guardado)
