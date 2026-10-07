## Proceso de extracción

**Nivel 1 — Detección de secciones.** El currículum no tiene una estructura fija, así que primero hay que ubicar los límites de cada sección (resumen, skills, experiencia, educación) dentro del texto completo. Esto se hace buscando líneas que coincidan con uno de los encabezados conocidos (por ejemplo "Skills", "Technical Skills", "Experience", "Education", con sinónimos). Una vez localizado un encabezado, todo el texto entre ese encabezado y el siguiente (o el final del documento) se considera el contenido de esa sección. Este nivel no extrae datos todavía — solo recorta el texto en bloques más pequeños y manejables.

**Nivel 2 — Extracción de campos dentro de cada bloque.** Sobre cada bloque ya aislado (o sobre el texto completo, en el caso de datos de contacto que no están atados a ninguna sección) se aplican expresiones regulares específicas por tipo de dato: una para emails, otra para teléfonos, otra para separar skills por comas, otra para identificar el período de una experiencia laboral, etc. Cada una reconoce un patrón léxico puntual, no la estructura general del documento — esa ya quedó resuelta en el nivel 1.

La separación en dos niveles es la que permite que el extractor tolere currículums con secciones en distinto orden o con distintos títulos de sección, sin tener que escribir una regex gigante que intente capturar el documento entero de una sola vez.

---

## Definiciones de las expresiones regulares

### Nivel 1 — Encabezado de sección

```
^(TECHNICAL SKILLS|SKILLS|TECHNOLOGIES|TECH STACK|EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT|EDUCATION|ACADEMIC BACKGROUND|ACADEMIC QUALIFICATIONS):?$
```

(aplicada sin distinguir mayúsculas/minúsculas, y anclada al inicio y fin de línea)

**Qué reconoce:** una línea completa que sea exactamente uno de los nombres de sección conocidos, con dos puntos opcionales al final. El símbolo `|` indica una alternativa entre varias palabras o frases posibles — es decir, la línea debe coincidir con una (y solo una) de esas opciones completas, no con una parte de ella. El acento circunflejo al inicio y el signo de dólar al final obligan a que la coincidencia abarque toda la línea, para no confundir, por ejemplo, la palabra "Experience" si aparece mencionada dentro de un párrafo de texto libre.

---

### Nombre del candidato

```
^[A-Z][a-z]+( [A-Z][a-z]+){1,3}$
```

**Qué reconoce:** una línea formada por 2 a 4 palabras, cada una empezando con una letra mayúscula de A a Z seguida de una o más letras minúsculas de a a z, separadas por un espacio simple. Se aplica solo sobre las primeras líneas del documento, antes de cualquier encabezado de sección, porque el mismo patrón de "palabras con mayúscula inicial" también aparece más abajo en nombres de organizaciones.

---

### Email

```
[A-Za-z0-9.]+@[A-Za-z0-9]+\.[A-Za-z]{2,}
```

**Qué reconoce:** una secuencia de letras, dígitos o puntos antes del símbolo arroba; después del arroba, una secuencia de letras o dígitos; luego un punto literal; y finalmente al menos dos letras (la terminación del dominio, como "com" o "co"). El `{2,}` indica "dos o más repeticiones" de ese último grupo de letras.

---

### Teléfono

```
[0-9]{2,4}[- ]?[0-9]{3,4}[- ]?[0-9]{3,4}
```

**Qué reconoce:** grupos de 2 a 4 dígitos, luego 3 a 4 dígitos, luego 3 a 4 dígitos, cada grupo separado opcionalmente por un espacio o un guión. Esto cubre distintos formatos regionales de número telefónico sin exigir uno exacto, ya que el enunciado no fija un formato único.

---

### Ubicación (LinkedIn/GitHub se explican igual, solo cambia el dominio)

```
LINKEDIN.COM/IN/[A-Za-z0-9-]+
```

**Qué reconoce:** el texto literal "linkedin.com/in/" (sin importar mayúsculas o minúsculas) seguido de una o más letras, dígitos o guiones, que corresponde al nombre de usuario.

---

### Separador de skills (dentro de la sección de skills ya aislada en el Nivel 1)

```
[,;\n]+
```

**Qué reconoce:** uno o más caracteres consecutivos que sean coma, punto y coma, o salto de línea. No reconoce el contenido de cada skill en sí — solo marca dónde termina un ítem y empieza el siguiente. Esto es intencional: no le corresponde a esta etapa decidir si "JS" y "Javascript" son lo mismo, eso lo resuelve el transductor en la siguiente etapa.

---

### Período de experiencia

```
[0-9]{4}[- ]+([0-9]{4}|PRESENT|CURRENT)
```

**Qué reconoce:** un año de 4 dígitos, seguido de un guión o espacio, seguido de otro año de 4 dígitos o la palabra "PRESENT" o "CURRENT" (sin distinguir mayúsculas/minúsculas). Cubre formatos como "2021-2023" o "2021 Present".

---

### Línea de viñeta (bullets de experiencia)

```
^[-*] [A-Za-z].+$
```

**Qué reconoce:** una línea que empieza con un guión o un asterisco, seguido de un espacio y luego una letra, hasta el final de la línea. El contenido que sigue se captura tal cual, sin reescritura, según lo que acordamos.
