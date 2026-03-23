# Guia de Comandos de Telegram

Este bot te ayuda a consultar apuntes en Notion y generar resumenes tecnicos con Gemini.

## /start

Inicia la conversacion con el bot y muestra una ayuda rapida de comandos.

Ejemplo:

```text
/start
```

Respuesta esperada:
- Mensaje de bienvenida.
- Explicacion breve de `/horario`, `/resumir` y `/definir`.

## /horario

Envia la imagen de tu horario desde la ruta configurada en `PATH_HORARIO` dentro de `.env`.

Ejemplo:

```text
/horario
```

Respuesta esperada:
- Si existe el archivo, el bot envia la imagen.
- Si no existe, el bot muestra una advertencia con la ruta que no encontro.

## /resumir [materia] [YYYY-MM-DD]

Genera un resumen para una materia usando todos los apuntes desde la fecha indicada hasta hoy.

Formato:

```text
/resumir [materia] [YYYY-MM-DD]
```

Ejemplos:

```text
/resumir Neuroanatomia 2026-03-01
/resumir Neurociencia Cognitiva 2026-02-15
/resumir Psicobiologia 2026-01-20
```

Que hace internamente:
1. Busca en Notion apuntes de la materia desde la fecha inicial hasta la fecha actual.
2. Extrae texto de bloques de parrafo y listas.
3. Envia el contenido a Gemini para crear el resumen.
4. Guarda el resultado en la base de datos de Resumenes en Notion.

Errores comunes:
- Si no hay apuntes en el rango de fechas: el bot lo informa.
- Si la fecha tiene formato invalido: Notion/Python puede lanzar error y el bot te lo reporta.
- Si faltan variables en `.env`: el bot no arranca hasta completar la configuracion.

## /definir [concepto]

Genera una definicion de un concepto desde el enfoque de Neurociencias.

Formato:

```text
/definir [concepto]
```

Ejemplos:

```text
/definir plasticidad sinaptica
/definir potencial de accion
/definir memoria de trabajo
```

Respuesta esperada:
- Definicion tecnica y clara.
- Relevancia dentro de Neurociencias.
- Ejemplo breve de aplicacion.
- Longitud maxima de 2000 caracteres.

Errores comunes:
- Si Gemini no responde a tiempo: el bot te pide reintentar.
- Si se excede rate limit/cuota: el bot te avisa que intentes despues.
- Si ocurre error inesperado: se registra detalle en logs para depuracion.
