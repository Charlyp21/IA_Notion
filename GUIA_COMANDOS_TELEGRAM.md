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
- Explicacion breve de `/horario` y `/resumir`.

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
