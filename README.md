# Neuro-Notion Telegram Bot

Bot de Telegram para consultar apuntes en Notion, generar resumenes tecnicos con Gemini y guardarlos en una base de Resumenes.

## Requisitos

- Linux (probado para flujo con EndeavourOS/Arch).
- Python 3.10 o superior.
- Un bot de Telegram creado con BotFather.
- Integracion de Notion creada y compartida con ambas bases de datos.
- API key de Gemini.

## Estructura del proyecto

- `bot.py`: comandos de Telegram y orquestacion del flujo.
- `notion_handler.py`: consulta de apuntes y creacion de paginas en Notion.
- `ai_handler.py`: generacion de resumenes con Gemini.
- `.env.example`: plantilla de variables de entorno.
- `requirements.txt`: dependencias de Python.

## Configuracion de Notion

1. Crea (o reutiliza) dos bases de datos:
   - DB de apuntes (debe tener propiedad `Materia` de tipo `Select`).
   - DB de resumenes (debe tener una propiedad de tipo `Title` y `Materia` tipo `Select`).
2. Comparte ambas bases con tu integracion de Notion.
3. Copia los IDs de las bases desde la URL de Notion.

## Instalacion en Linux (venv + pip)

```bash
cd IA_Notion
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Variables de entorno

1. Copia el ejemplo:

```bash
cp .env.example .env
```

2. Llena los valores en `.env`:

- `TELEGRAM_TOKEN`
- `NOTION_TOKEN`
- `NOTION_DB_APUNTES_ID`
- `NOTION_DB_RESUMENES_ID`
- `GEMINI_API_KEY`
- `PATH_HORARIO` (por defecto `assets/horario.png`)

## Ejecucion

Para pruebas locales:

```bash
python bot.py
```

## Mantener el bot corriendo en Google Cloud (produccion)

El bot necesita estar activo 24/7. Aqui hay 3 opciones ordenadas de menor a mayor robustez.

### Opcion 1: nohup (simple)

Para correr en segundo plano sin que la sesion SSH lo interrumpa:

```bash
source venv/bin/activate
nohup python bot.py > bot.log 2>&1 &
```

Detalles:
- `nohup`: ignora hangup si se desconecta SSH.
- `> bot.log 2>&1`: guarda stdout y stderr en `bot.log`.
- `&`: ejecuta en background.

Ver logs:
```bash
tail -f bot.log
```

Detener:
```bash
pkill -f "python bot.py"
```

### Opcion 2: screen o tmux (intermedio)

Mas control que nohup. La sesion sigue corriendo aunque cierres SSH.

Con `screen`:

```bash
source venv/bin/activate
screen -S neurobot -dm python bot.py
```

Ver sesion:
```bash
screen -ls
```

Reconectar:
```bash
screen -r neurobot
```

Detener (dentro de screen):
```bash
# Presiona Ctrl+A, luego D para desconectar
# O desde fuera:
screen -S neurobot -X quit
```

### Opcion 3: systemd service (recomendado para produccion)

Mas robusto y profesional. El bot arranca automaticamente si la VM reinicia.

1. Crea el archivo de servicio:

```bash
sudo nano /etc/systemd/system/neurobot.service
```

2. Pega este contenido:

```ini
[Unit]
Description=Neuro-Notion Telegram Bot
After=network.target

[Service]
Type=simple
User=<tu-usuario>
WorkingDirectory=/home/<tu-usuario>/Dev/Github/Neurobot/IA_Notion
Environment="PATH=/home/<tu-usuario>/Dev/Github/Neurobot/IA_Notion/venv/bin"
ExecStart=/home/<tu-usuario>/Dev/Github/Neurobot/IA_Notion/venv/bin/python bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Importante:** reemplaza `<tu-usuario>` con tu nombre de usuario (ej: charly).

3. Descarga la configuracion y habilita:

```bash
sudo systemctl daemon-reload
sudo systemctl enable neurobot.service
sudo systemctl start neurobot.service
```

4. Verifica estado:

```bash
sudo systemctl status neurobot.service
```

5. Ver logs:

```bash
sudo journalctl -u neurobot.service -f
```

6. Controlar servicio:

```bash
sudo systemctl stop neurobot.service    # detener
sudo systemctl restart neurobot.service # reiniciar
```

### Configuracion de Google Cloud (recomendado)

En Google Cloud Compute Engine, para que la VM no se apague:

1. **Configura etiquetas de tiempo de inactividad:** En la consola de GCP, configurar politicas de apagado automatico (si deseas).
2. **O deshabilita el apagado automatico:** Deja la VM corriendo 24/7 (verificar costo).
3. **Monitorea desde GCP Console:** Ve a Logs > Cloud Logging para revisar logs del bot.

## Comandos del bot

- `/start`: mensaje inicial.
- `/horario`: envia la imagen del horario usando `PATH_HORARIO`.
- `/resumir [materia] [YYYY-MM-DD]`: obtiene apuntes por materia desde la fecha indicada hasta hoy, genera resumen y lo guarda en Notion.

## Nota de escalabilidad

El codigo separa la logica por servicios (`NotionHandler`, `AIHandler`) para poder agregar nuevas integraciones, por ejemplo Google Calendar, sin reescribir la base del bot.