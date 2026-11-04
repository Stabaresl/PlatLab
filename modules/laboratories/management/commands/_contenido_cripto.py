"""Contenido estilo AWS de los laboratorios de la pista «Criptografía Aplicada»."""

# Hashes MD5 reales (hashlib) — `md5sum` de la consola los recalcula igual.
_WORDLIST = {
    "123456": "e10adc3949ba59abbe56e057f20f883e",
    "password": "5f4dcc3b5aa765d61d8327deb882cf99",
    "qwerty": "d8578edf8458ce06fbc5bb76a58c5ca4",
    "admin": "21232f297a57a5a743894a0e4a801fc3",
    "letmein": "0d107d09f5bbe40cade3de5c71e9e9b7",
    "monkey": "d0763edaa9d9bd2a9516280e9044d885",
    "dragon": "8621ffdbc5698829397d97767ac13db3",
    "football": "37b4e2d82900d5e94b8da524fbeb33c0",
    "iloveyou": "f25a2fc72690b780b2a14e140ef6a9e0",
    "sunshine": "0571749e2ac330a7455809c6b0e7af90",
    "princess": "8afa847f50a716e64932d995c8e7435a",
    "shadow": "3bf1114a986ba87ed28fc1b5884fc2f8",
    "master": "eb0a191797624dd3a48fa681d3061212",
    "superman": "84d961568a65073a3bcf0eb216b2a576",
    "batman": "ec0e2603172c73a8b644bb9456c1ff6e",
    "trustno1": "5fcfd41e547a12215b173ff47fdd3739",
    "colombia": "25446782e2ccaf0afdb03e5d61d0fbb9",
    "manizales": "a1bb621444a3607ae67f5824ad8439e0",
    "hacker": "d6a6bc0db10694a2d90e3a69648f3a03",
    "welcome": "40be4e59b9a2a2b5dffb918c0e86b3d7",
}
_HASH_OBJETIVO = _WORDLIST["superman"]

CESAR = {
    "nombre": "Cifrado César y Frecuencia",
    # La flag no aparece escrita en la máquina: sale de descifrar el mensaje (es el ejercicio).
    "flag_derivada": True,
    "descripcion": (
        "Descifra un mensaje interceptado con el cifrado más antiguo de la historia: deduce el "
        "desplazamiento a partir de un texto conocido y aplícalo con tr."
    ),
    "resumen_cierre": (
        "<p>Rompiste un cifrado con solo 25 claves posibles usando un <strong>texto conocido</strong>: "
        "sabías que el mensaje empezaba por <code>FLAG</code> y eso bastó para deducir la clave.</p>"
        "<div class=\"importante\"><p>Ese mismo principio, el ataque con texto conocido, se usa contra "
        "cifrados modernos mal implementados. Un buen cifrado (AES) resiste aunque el atacante conozca "
        "buena parte del mensaje.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "El cifrado César",
            "duracion": 10,
            "objetivos": [
                "Cifrar y descifrar a mano con un desplazamiento.",
                "Explicar por qué César se rompe por fuerza bruta.",
                "Usar el análisis de frecuencia y el texto conocido como atajos.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Interceptaste un mensaje entre dos participantes de un reto "
                "de seguridad. Por la forma, parece cifrado con algo muy simple.</p></div>"
                "<h3>Desplazar el alfabeto</h3>"
                "<p>César reemplaza cada letra por la que está <em>n</em> posiciones más adelante. Con "
                "<em>n = 3</em>:</p>"
                "<table><thead><tr><th>Claro</th><th>A</th><th>B</th><th>C</th><th>…</th><th>X</th><th>Y</th><th>Z</th></tr></thead>"
                "<tbody><tr><td>Cifrado</td><td>D</td><td>E</td><td>F</td><td>…</td><td>A</td><td>B</td><td>C</td></tr></tbody></table>"
                "<p>Para descifrar se desplaza en sentido contrario. Números y símbolos no cambian.</p>"
                "<h3>Por qué es inseguro</h3>"
                "<ul><li><strong>Fuerza bruta</strong>: solo hay 25 desplazamientos posibles; se prueban todos en segundos.</li>"
                "<li><strong>Frecuencia</strong>: en español la letra más común es la E. La letra más repetida del mensaje cifrado probablemente es una E desplazada.</li>"
                "<li><strong>Texto conocido</strong>: si sabes una palabra del original, comparas letra con letra y obtienes la clave.</li></ul>"
                "<h3>César con tr</h3>"
                "<p><code>tr</code> traduce caracteres de un conjunto a otro. Desplazar −3 es decirle que la "
                "A se vuelve X, la B se vuelve Y… y lo mismo en minúsculas:</p>"
                "<pre>tr 'A-Za-z' 'X-ZA-Wx-za-w'</pre>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Descifrando el mensaje",
            "duracion": 15,
            "objetivos": [
                "Deducir la clave con un ataque de texto conocido.",
                "Aplicar el desplazamiento inverso con tr.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Descifra <code>mensaje_cifrado.txt</code>. Sabes que las flags de este reto siempre "
                "empiezan por <code>FLAG{</code>: úsalo.</p>"
            ),
            "pasos": [
                ("Lee el mensaje", "<p>Mira el texto cifrado. Observa que las llaves <code>{}</code> no cambiaron.</p>", "cat mensaje_cifrado.txt", "IODJ{fhvdu_hv_wulyldo}"),
                (
                    "Deduce la clave",
                    "<p>Si <code>IODJ</code> corresponde a <code>FLAG</code>: de F a I hay 3 letras (F→G→H→I). "
                    "Comprueba con la segunda: L + 3 = O. La clave es 3.</p>",
                    "cat pista.txt",
                    "Texto conocido: el original empieza por FLAG{",
                ),
                ("Prueba un desplazamiento equivocado", "<p>Con −1 obtienes basura: así se ve un intento fallido de fuerza bruta.</p>", "cat mensaje_cifrado.txt | tr 'A-Za-z' 'ZA-Yza-y'", "HNCI{eguct_gu_vtkxkcn}"),
                ("Descifra con −3", "<p>Aplica la clave correcta. Copia el resultado y entrégalo.</p>", "cat mensaje_cifrado.txt | tr 'A-Za-z' 'X-ZA-Wx-za-w'", "FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~/reto$",
                "banner": "Mensaje interceptado: mensaje_cifrado.txt",
                "escenario": {
                    "host": "kali",
                    "directorio": "~/reto",
                    "archivos": {
                        "reto/mensaje_cifrado.txt": "IODJ{fhvdu_hv_wulyldo}\n",
                        "reto/pista.txt": "Texto conocido: el original empieza por FLAG{\n",
                    },
                },
                "comandos": [],
            },
        },
    ],
    "flag": {
        "pista": "El desplazamiento correcto es 3, el clásico de Julio César: para descifrar, desplaza −3.",
        "paso_a_paso": "cat mensaje_cifrado.txt | tr 'A-Za-z' 'X-ZA-Wx-za-w'",
    },
    "examen": [
        {"enunciado": "¿Cuántas claves posibles tiene el cifrado César con el alfabeto inglés de 26 letras?", "tipo": "opcion_multiple", "opciones": ["25", "26!", "128", "1"], "respuesta": "25"},
        {"enunciado": "¿Qué letra es la más frecuente en textos en español?", "tipo": "opcion_multiple", "opciones": ["A", "E", "S", "O"], "respuesta": "E"},
        {"enunciado": "¿Cómo se llama el ataque que usaste al saber que el mensaje empezaba por FLAG?", "tipo": "opcion_multiple", "opciones": ["Ataque de texto conocido", "Ataque de diccionario", "Ataque de hombre en el medio", "Ataque de canal lateral"], "respuesta": "Ataque de texto conocido"},
        {"enunciado": "Escribe el resultado de cifrar la palabra HOLA con César de desplazamiento 3 (en mayúsculas).", "tipo": "abierta", "respuesta": "KROD"},
    ],
}

HASHES = {
    "nombre": "Hashes y Fuerza Bruta Básica",
    "descripcion": (
        "Recupera una contraseña a partir de su hash MD5 con un ataque de diccionario y entiende "
        "por qué MD5 sin sal ya no sirve para guardar contraseñas."
    ),
    "resumen_cierre": (
        "<p>Encontraste la contraseña sin «descifrar» nada: calculaste el hash de cada candidata y "
        "comparaste. Eso es un ataque de diccionario, y con MD5 una GPU prueba miles de millones por segundo.</p>"
        "<div class=\"importante\"><p>Para guardar contraseñas se usa una función lenta y con sal: "
        "<strong>bcrypt</strong>, <strong>scrypt</strong> o <strong>Argon2id</strong>. La sal hace que dos "
        "usuarios con la misma contraseña tengan hashes distintos y que no sirvan las tablas precalculadas.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Hashing y por qué MD5 ya no alcanza",
            "duracion": 12,
            "objetivos": [
                "Diferenciar un hash de un cifrado.",
                "Explicar cómo funciona un ataque de diccionario.",
                "Elegir una función adecuada para guardar contraseñas.",
            ],
            "html": (
                "<div class=\"escenario\"><p>En una auditoría encontraste la tabla de usuarios de un "
                "sistema viejo. Las contraseñas están guardadas como hashes MD5. Debes demostrar que eso "
                "equivale a tenerlas en claro.</p></div>"
                "<h3>Hash no es cifrado</h3>"
                "<table><thead><tr><th></th><th>Cifrado</th><th>Hash</th></tr></thead><tbody>"
                "<tr><td>¿Se puede revertir?</td><td>Sí, con la clave</td><td>No: es de un solo sentido</td></tr>"
                "<tr><td>Tamaño de la salida</td><td>Depende del mensaje</td><td>Fijo (MD5: 32 caracteres hex)</td></tr>"
                "<tr><td>Uso típico</td><td>Proteger datos que hay que leer</td><td>Verificar contraseñas, integridad</td></tr>"
                "</tbody></table>"
                "<h3>Cómo se «rompe» un hash</h3>"
                "<p>No se revierte: se <strong>adivina</strong>. Tomas una lista de contraseñas probables "
                "(wordlist), calculas el hash de cada una y comparas con el objetivo.</p>"
                "<pre>echo -n password | md5sum\n5f4dcc3b5aa765d61d8327deb882cf99  -</pre>"
                "<div class=\"aviso\"><p>El <code>-n</code> es clave: sin él, <code>echo</code> agrega un salto "
                "de línea y el hash cambia por completo.</p></div>"
                "<h3>Por qué MD5 es mala idea</h3>"
                "<ul><li>Es <strong>rápido</strong>: bueno para verificar archivos, pésimo para contraseñas.</li>"
                "<li>Sin <strong>sal</strong>, la misma contraseña siempre da el mismo hash y existen tablas precalculadas.</li></ul>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Crackeando el hash",
            "duracion": 20,
            "objetivos": [
                "Calcular hashes MD5 desde la consola.",
                "Encontrar la contraseña de un hash con una wordlist.",
                "Usar la contraseña recuperada para obtener la flag.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>El hash de la cuenta <code>admin</code> está en <code>hash_objetivo.txt</code>. Encuentra "
                "qué palabra de <code>wordlist.txt</code> lo produce y pruébala con el programa "
                "<code>./verificar</code>, que te entrega la flag si aciertas.</p>"
                "<div class=\"tip\"><p>Puedes probar palabra por palabra con <code>echo -n palabra | md5sum</code> "
                "o usar el bucle de la tarea 4, que recorre toda la lista.</p></div>"
            ),
            "pasos": [
                ("Mira el hash objetivo", "<p>32 caracteres hexadecimales: típico de MD5.</p>", "cat hash_objetivo.txt", f"admin:{_HASH_OBJETIVO}"),
                ("Calcula un hash de prueba", "<p>Comprueba que entiendes el formato con una palabra cualquiera.</p>", "echo -n password | md5sum", "5f4dcc3b5aa765d61d8327deb882cf99  -"),
                ("Revisa la wordlist", "<p>¿Cuántas candidatas hay?</p>", "wc -l wordlist.txt", "20 wordlist.txt"),
                (
                    "Calcula el hash de toda la lista",
                    "<p>El bucle imprime cada palabra con su hash. Busca la que coincide con el objetivo.</p>",
                    'for w in $(cat wordlist.txt); do echo "$w $(echo -n $w | md5sum)"; done',
                    "123456 e10adc3949ba59abbe56e057f20f883e  -\n...\nsuperman 84d961568a65073a3bcf0eb216b2a576  -\n...",
                ),
                ("Confirma la coincidencia", "<p>Calcula a mano el hash de la palabra que encontraste y compáralo.</p>", "echo -n superman | md5sum", f"{_HASH_OBJETIVO}  -"),
                ("Verifica la contraseña", "<p>Si es correcta, el programa te da la flag.</p>", "./verificar superman", "Contraseña correcta para admin. FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~/auditoria$",
                "banner": "Archivos de la auditoría: hash_objetivo.txt, wordlist.txt, verificar",
                "escenario": {
                    "host": "kali",
                    "directorio": "~/auditoria",
                    "archivos": {
                        "auditoria/hash_objetivo.txt": f"admin:{_HASH_OBJETIVO}\n",
                        "auditoria/wordlist.txt": "".join(f"{w}\n" for w in _WORDLIST),
                        "auditoria/verificar": {"contenido": "#!/bin/sh\n# verifica una contraseña contra el hash de admin\n", "permisos": "-rwxr-xr-x"},
                    },
                },
                "comandos": [
                    {
                        "comando": 'for w in $(cat wordlist.txt); do echo "$w $(echo -n $w | md5sum)"; done',
                        "patron": r"for\s+\w+\s+in\s+\$\(cat\s+wordlist\.txt\);.*md5sum.*done",
                        "salida": "\n".join(f"{w} {h}  -" for w, h in _WORDLIST.items()),
                    },
                    {"comando": "./verificar superman", "patron": r"(\./)?verificar\s+superman", "salida": "Contraseña correcta para admin. FLAG{md5_wordlist_crack}"},
                    {"comando": "./verificar <palabra>", "patron": r"(\./)?verificar\s+\S+", "salida": "Contraseña incorrecta."},
                    {"comando": "./verificar", "patron": r"(\./)?verificar", "salida": "uso: ./verificar <contraseña>"},
                ],
            },
        },
    ],
    "flag": {
        "pista": "Calcula el MD5 de cada palabra de wordlist.txt (echo -n palabra | md5sum) y compáralo con el hash de admin.",
        "paso_a_paso": "La palabra es superman: echo -n superman | md5sum coincide con el hash. Luego ./verificar superman entrega la flag.",
    },
    "examen": [
        {"enunciado": "¿Cuál es la diferencia principal entre un hash y un cifrado?", "tipo": "opcion_multiple", "opciones": ["El hash es de un solo sentido; el cifrado se revierte con la clave", "El hash es más largo", "El cifrado no usa claves", "No hay diferencia"], "respuesta": "El hash es de un solo sentido; el cifrado se revierte con la clave"},
        {"enunciado": "¿Para qué sirve la sal en el almacenamiento de contraseñas?", "tipo": "opcion_multiple", "opciones": ["Para que el hash sea reversible", "Para que contraseñas iguales den hashes distintos e inutilizar tablas precalculadas", "Para acelerar el login", "Para cifrar la base de datos"], "respuesta": "Para que contraseñas iguales den hashes distintos e inutilizar tablas precalculadas"},
        {"enunciado": "¿Qué función es adecuada para guardar contraseñas hoy?", "tipo": "opcion_multiple", "opciones": ["MD5", "SHA-1", "Argon2id", "Base64"], "respuesta": "Argon2id"},
        {"enunciado": "¿Por qué hay que usar echo -n al calcular el hash de una palabra?", "tipo": "opcion_multiple", "opciones": ["Para que no agregue un salto de línea que cambia el hash", "Para que sea más rápido", "Para ocultar la palabra", "Porque md5sum lo exige"], "respuesta": "Para que no agregue un salto de línea que cambia el hash"},
    ],
}

_PEM_PUBLICA = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tRgeLezV6ffAt0gunVTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u
+qKhbwKfBstIs+bMY2Zkp18gnTxKLxoS2tFczGkPLPgizskuemMghRniWaoLcyeh
kd3qqGElvW/VDL5AaWTg0nLVkjRo9z+40RQzuVaE8AkAFmxZzow3x+VJYKdjykkJ
0iT9wCS0DRTXu269V264Vf/3jvredZiKRkgwlL9xNAwxXFg0x/XFw005UWVRIkdg
cKWTjpBP2dPwVZ4WWC+9aGVd+Gyn1o0CLelf4rEjGoXbAAEgAqeGUxrcIlbjXfbc
mwIDAQAB
-----END PUBLIC KEY-----
"""
_PEM_PRIVADA = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu
NMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ
(material de práctica: no es una clave real)
-----END PRIVATE KEY-----
"""

RSA = {
    "nombre": "Introducción a Cifrado Asimétrico",
    "descripcion": (
        "Usa un par de claves RSA para entender qué clave cifra y cuál descifra, y recupera un "
        "mensaje cifrado con openssl."
    ),
    "resumen_cierre": (
        "<p>Comprobaste la regla central del cifrado asimétrico: lo que se cifra con la clave "
        "<strong>pública</strong> solo se descifra con la <strong>privada</strong>. Por eso la pública "
        "se puede repartir y la privada jamás sale de su dueño.</p>"
        "<div class=\"tip\"><p>Al revés también sirve: lo que se firma con la privada se verifica con "
        "la pública. Eso es una firma digital, la base de los certificados HTTPS y de las "
        "actualizaciones de software firmadas.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Cifrado asimétrico y RSA",
            "duracion": 12,
            "objetivos": [
                "Distinguir cifrado simétrico de asimétrico.",
                "Decidir qué clave usar para cifrar, descifrar, firmar y verificar.",
                "Ubicar RSA en protocolos que usas a diario.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Un compañero te envió un mensaje cifrado con tu clave "
                "pública. Tienes tu par de claves en la carpeta <code>claves/</code>.</p></div>"
                "<h3>Una clave o dos</h3>"
                "<table><thead><tr><th></th><th>Simétrico (AES)</th><th>Asimétrico (RSA)</th></tr></thead><tbody>"
                "<tr><td>Claves</td><td>Una compartida</td><td>Un par: pública y privada</td></tr>"
                "<tr><td>Problema</td><td>¿Cómo comparto la clave sin que la intercepten?</td><td>Es lento para muchos datos</td></tr>"
                "<tr><td>Uso típico</td><td>Cifrar los datos</td><td>Intercambiar claves y firmar</td></tr>"
                "</tbody></table>"
                "<h3>Qué clave para qué</h3>"
                "<table><thead><tr><th>Quiero…</th><th>Uso la clave</th></tr></thead><tbody>"
                "<tr><td>Enviarte un secreto</td><td>Tu <strong>pública</strong> (para cifrar)</td></tr>"
                "<tr><td>Leer un secreto que me enviaron</td><td>Mi <strong>privada</strong> (para descifrar)</td></tr>"
                "<tr><td>Firmar un documento</td><td>Mi <strong>privada</strong></td></tr>"
                "<tr><td>Verificar tu firma</td><td>Tu <strong>pública</strong></td></tr>"
                "</tbody></table>"
                "<div class=\"nota\"><p>HTTPS combina ambos: RSA (o curvas elípticas) para acordar una clave, "
                "y AES con esa clave para el resto de la conexión.</p></div>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Descifrando con la clave privada",
            "duracion": 15,
            "objetivos": [
                "Inspeccionar un par de claves RSA.",
                "Comprobar que la pública no descifra.",
                "Descifrar el mensaje con la privada.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Descifra <code>mensaje.enc</code>. Primero prueba con la clave equivocada para ver el error: "
                "entender por qué falla es parte del ejercicio.</p>"
            ),
            "pasos": [
                ("Mira tus claves", "<p>Dos archivos PEM: la pública y la privada.</p>", "ls claves", "clave_privada.pem  clave_publica.pem"),
                ("Lee la clave pública", "<p>Esto es lo que compartes con el mundo.</p>", "cat claves/clave_publica.pem", "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo\n..."),
                ("Intenta descifrar con la pública", "<p>Debe fallar: la pública solo sirve para cifrar.</p>", "openssl pkeyutl -decrypt -inkey claves/clave_publica.pem -in mensaje.enc", "Could not read private key from claves/clave_publica.pem\npkeyutl: Error initializing context"),
                ("Descifra con la privada", "<p>Ahora sí. Copia la flag.</p>", "openssl pkeyutl -decrypt -inkey claves/clave_privada.pem -in mensaje.enc", "FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@kali:~$",
                "banner": "Tu par de claves está en ~/claves. El mensaje recibido: mensaje.enc",
                "escenario": {
                    "host": "kali",
                    "archivos": {
                        "claves/clave_publica.pem": _PEM_PUBLICA,
                        "claves/clave_privada.pem": {"contenido": _PEM_PRIVADA, "permisos": "-rw-------"},
                        "mensaje.enc": "8a3fe1c09b47d2ffc8a1904e6b3d5c77e0a9b21f4c8d6e3a1b7f9c2d5e8a0b3c (256 bytes cifrados con RSA-2048)\n",
                    },
                },
                "comandos": [
                    {"comando": "openssl pkeyutl -decrypt -inkey claves/clave_privada.pem -in mensaje.enc", "patron": r"openssl\s+(pkeyutl|rsautl)\s+.*-decrypt.*-inkey\s+(\./)?(claves/)?clave_privada\.pem.*", "salida": "FLAG{rsa_asimetrico_intro}"},
                    {"comando": "openssl pkeyutl -decrypt -inkey claves/clave_publica.pem -in mensaje.enc", "patron": r"openssl\s+(pkeyutl|rsautl)\s+.*-decrypt.*clave_publica\.pem.*", "salida": "Could not read private key from claves/clave_publica.pem\npkeyutl: Error initializing context"},
                    {"comando": "openssl rsa -in claves/clave_privada.pem -text -noout", "patron": r"openssl\s+rsa\s+.*", "salida": "Private-Key: (2048 bit, 2 primes)\nmodulus:\n    00:bb:54:94:d4:b7:d5:2c:f1:c2:a3:33:31:1f:63:...\npublicExponent: 65537 (0x10001)\n(se omiten los factores primos)"},
                ],
            },
        },
    ],
    "flag": {
        "pista": "openssl pkeyutl -decrypt necesita la clave privada, nunca la pública.",
        "paso_a_paso": "openssl pkeyutl -decrypt -inkey claves/clave_privada.pem -in mensaje.enc",
    },
    "examen": [
        {"enunciado": "Quieres enviarle un secreto a Ana. ¿Con qué clave lo cifras?", "tipo": "opcion_multiple", "opciones": ["Con la clave pública de Ana", "Con la clave privada de Ana", "Con tu clave pública", "Con una clave compartida por correo"], "respuesta": "Con la clave pública de Ana"},
        {"enunciado": "¿Qué clave usa una firma digital para firmar?", "tipo": "opcion_multiple", "opciones": ["La pública del firmante", "La privada del firmante", "La pública del receptor", "Ninguna"], "respuesta": "La privada del firmante"},
        {"enunciado": "¿Qué tamaño mínimo de clave RSA se recomienda hoy?", "tipo": "opcion_multiple", "opciones": ["512 bits", "1024 bits", "2048 bits", "128 bits"], "respuesta": "2048 bits"},
        {"enunciado": "En HTTPS, ¿para qué se usa principalmente la criptografía asimétrica?", "tipo": "opcion_multiple", "opciones": ["Para cifrar todos los datos de la página", "Para autenticar al servidor y acordar una clave simétrica", "Para comprimir el tráfico", "Para guardar las cookies"], "respuesta": "Para autenticar al servidor y acordar una clave simétrica"},
    ],
}

# "Bytes" de la imagen simulada (sin \x00: PostgreSQL no admite el carácter nulo en JSON).
_FOTO = (
    "\xff\xd8\xff\xe0JFIF\x01\x01\x01Exif\x02\x02MM\x01*"
    "Canon EOS 2000D\x01 2026:10:30 08:41:12\x01"
    "\x13\x8a\x91\xf0\x02\x7f\x3c\x99\xaa\x10"
    "steghide 0.5.1\x01"
    "\x88\x12\xc4\x7e\x01\x55\x6d\xe3\x0f"
    "\xff\xd9"
)

ESTEGO = {
    "nombre": "Esteganografía: Mensajes Ocultos en Imágenes",
    "descripcion": (
        "Revisa una imagen sospechosa: lee sus metadatos, busca cadenas de texto y extrae el "
        "archivo que alguien escondió dentro con steghide."
    ),
    "resumen_cierre": (
        "<p>La imagen se veía normal, pero tenía un rastro: la cadena <code>steghide</code> dentro del "
        "archivo y una pista en los metadatos. Con eso extrajiste el mensaje oculto.</p>"
        "<div class=\"importante\"><p>Esteganografía no es cifrado: esconde que hay un mensaje, no su "
        "contenido. En análisis forense se revisan siempre metadatos, cadenas y tamaño del archivo; "
        "una foto que pesa más de lo normal es sospechosa.</p></div>"
    ),
    "secciones": [
        {
            "titulo": "Esconder datos a la vista",
            "duracion": 10,
            "objetivos": [
                "Diferenciar esteganografía de cifrado.",
                "Explicar la técnica LSB en imágenes.",
                "Nombrar las herramientas básicas de análisis.",
            ],
            "html": (
                "<div class=\"escenario\"><p>Durante una investigación interna, el equipo forense "
                "encontró una foto que un empleado compartía en un foro público. Sospechan que lleva "
                "información escondida.</p></div>"
                "<h3>Ocultar en lugar de cifrar</h3>"
                "<p>El cifrado hace ilegible un mensaje, pero se nota que existe. La "
                "<strong>esteganografía</strong> lo esconde dentro de algo inocente (una imagen, un audio) "
                "para que nadie sepa que está ahí.</p>"
                "<h3>La técnica LSB</h3>"
                "<p>Cada píxel guarda sus colores en bytes. Cambiar el <strong>bit menos significativo</strong> "
                "(LSB) de cada byte altera el color en una unidad sobre 255: imperceptible a la vista, pero "
                "suficiente para guardar un bit del mensaje por byte.</p>"
                "<table><thead><tr><th>Herramienta</th><th>Para qué</th></tr></thead><tbody>"
                "<tr><td><code>file</code></td><td>Confirmar el tipo real del archivo</td></tr>"
                "<tr><td><code>exiftool</code></td><td>Leer metadatos (cámara, fecha, comentarios)</td></tr>"
                "<tr><td><code>strings</code></td><td>Sacar el texto legible de un binario</td></tr>"
                "<tr><td><code>steghide</code></td><td>Ocultar y extraer datos protegidos con contraseña</td></tr>"
                "</tbody></table>"
            ),
            "pasos": [],
            "entorno": None,
        },
        {
            "titulo": "Extrayendo el mensaje oculto",
            "duracion": 18,
            "objetivos": [
                "Analizar una imagen con file, exiftool y strings.",
                "Deducir la contraseña de extracción a partir de los metadatos.",
                "Extraer y leer el archivo oculto.",
            ],
            "html": (
                "<h3>Tu misión</h3>"
                "<p>Analiza <code>evidencia/foto.jpg</code> y extrae lo que tiene escondido. La contraseña "
                "de steghide está insinuada en los metadatos de la imagen.</p>"
            ),
            "pasos": [
                ("Confirma el tipo de archivo", "<p>Que la extensión diga .jpg no garantiza nada.</p>", "file evidencia/foto.jpg", "evidencia/foto.jpg: JPEG image data, JFIF standard 1.01"),
                ("Lee los metadatos", "<p>Fíjate en el comentario del autor.</p>", "exiftool evidencia/foto.jpg", "Camera Model Name : Canon EOS 2000D\nComment           : la clave es el grupo de investigación que dicta este curso, en minúsculas\n..."),
                ("Busca cadenas reveladoras", "<p>¿Qué herramienta dejó su huella dentro de la imagen?</p>", "strings evidencia/foto.jpg", "JFIF\nExif\nCanon EOS 2000D\n2026:10:30 08:41:12\nsteghide 0.5.1"),
                ("Extrae con la contraseña", "<p>El grupo de investigación de PlatLAB es GAIA. Usa la contraseña en minúsculas.</p>", "steghide extract -sf evidencia/foto.jpg -p gaia", 'wrote extracted data to "secreto.txt".'),
                ("Lee el archivo extraído", "<p>Aparece un archivo nuevo en tu directorio.</p>", "cat secreto.txt", "FLAG{...}"),
            ],
            "entorno": {
                "prompt": "estudiante@forense:~$",
                "banner": "Estación forense. Evidencia en ~/evidencia (solo lectura).",
                "escenario": {
                    "host": "forense",
                    "archivos": {
                        "evidencia/foto.jpg": _FOTO,
                        "evidencia/cadena_custodia.txt": "Evidencia E-17: foto.jpg, publicada en foro externo el 30/10.\nHash registrado al recibirla.\n",
                    },
                    "efectos": [
                        {
                            "patron": r"steghide\s+extract\s+.*-sf\s+(\./)?(evidencia/)?foto\.jpg\s+.*-p\s+gaia.*",
                            "archivos": {"secreto.txt": "Mensaje recuperado de la imagen:\nFLAG{esteganografia_lsb_oculta}\n"},
                        }
                    ],
                },
                "comandos": [
                    {
                        "comando": "exiftool evidencia/foto.jpg",
                        "patron": r"exiftool\s+(\./)?(evidencia/)?foto\.jpg",
                        "salida": (
                            "ExifTool Version Number         : 12.76\nFile Name                       : foto.jpg\n"
                            "File Size                       : 412 kB\nFile Type                       : JPEG\n"
                            "Camera Model Name               : Canon EOS 2000D\nCreate Date                     : 2026:10:30 08:41:12\n"
                            "Comment                         : la clave es el grupo de investigación que dicta este curso, en minúsculas\n"
                            "Image Size                      : 1920x1080"
                        ),
                    },
                    {"comando": "steghide extract -sf evidencia/foto.jpg -p gaia", "patron": r"steghide\s+extract\s+.*-sf\s+(\./)?(evidencia/)?foto\.jpg\s+.*-p\s+gaia.*", "salida": 'wrote extracted data to "secreto.txt".'},
                    {"comando": "steghide extract -sf evidencia/foto.jpg -p <otra>", "patron": r"steghide\s+extract\s+.*", "salida": "steghide: could not extract any data with that passphrase!"},
                    {"comando": "steghide info evidencia/foto.jpg", "patron": r"steghide\s+info\s+.*", "salida": '"foto.jpg":\n  format: jpeg\n  capacity: 23.1 KB\nTry to get information about embedded data ? (y/n) [necesitas la contraseña]'},
                ],
            },
        },
    ],
    "flag": {
        "pista": "Los metadatos (exiftool) dicen que la clave es el grupo de investigación que dicta el curso, en minúsculas.",
        "paso_a_paso": "steghide extract -sf evidencia/foto.jpg -p gaia y luego cat secreto.txt",
    },
    "examen": [
        {"enunciado": "¿En qué se diferencia la esteganografía del cifrado?", "tipo": "opcion_multiple", "opciones": ["Esconde la existencia del mensaje en vez de volverlo ilegible", "Es más rápida", "Solo funciona con texto", "No usa contraseñas nunca"], "respuesta": "Esconde la existencia del mensaje en vez de volverlo ilegible"},
        {"enunciado": "¿Qué modifica la técnica LSB en una imagen?", "tipo": "opcion_multiple", "opciones": ["El bit menos significativo de cada byte de color", "El tamaño de la imagen", "Los metadatos EXIF", "La extensión del archivo"], "respuesta": "El bit menos significativo de cada byte de color"},
        {"enunciado": "¿Qué herramienta muestra los metadatos de una foto?", "tipo": "opcion_multiple", "opciones": ["exiftool", "nmap", "md5sum", "tr"], "respuesta": "exiftool"},
        {"enunciado": "¿Qué comando extrae el texto legible de un archivo binario?", "tipo": "abierta", "respuesta": "strings"},
    ],
}

LABS = [CESAR, HASHES, RSA, ESTEGO]
