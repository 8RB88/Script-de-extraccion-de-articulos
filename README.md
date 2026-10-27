# Extractor de artículos y metadatos de Scopus

Aplicación web en Python para buscar artículos de Scopus, consultar sus
metadatos y exportarlos en formatos reutilizables. También puede localizar y
descargar copias PDF que estén disponibles legalmente en acceso abierto.

La aplicación está pensada para investigadores, estudiantes y equipos que
necesiten construir una colección bibliográfica reproducible a partir de una
búsqueda configurada por tema y filtros.

## Funcionalidades

- Búsqueda en Scopus mediante la API oficial de Elsevier.
- Expresiones de búsqueda por título, resumen y palabras clave.
- Modo de búsqueda avanzada con la sintaxis nativa de Scopus.
- Configuración del número máximo de artículos.
- Filtro de artículos de acceso abierto mediante `OPENACCESS(1)`.
- Filtros opcionales por:
  - Año inicial y final.
  - Idioma.
  - Tipo de documento.
  - Área temática de Scopus.
  - Orden de resultados.
- Normalización de metadatos:
  - Título.
  - DOI.
  - EID de Scopus.
  - Autores.
  - Revista o publicación.
  - Fecha de publicación.
  - Resumen.
  - Número de citas.
  - Indicador de acceso abierto.
  - URL proporcionada por Scopus.
- Descarga de metadatos en JSON.
- Descarga de resultados en CSV compatible con Excel.
- Localización de copias PDF mediante Unpaywall.
- Descarga de los PDFs disponibles en un archivo ZIP.
- Validación de respuestas para evitar guardar contenido que no sea PDF.
- Informe separado de artículos sin copia PDF y errores de descarga.
- Pruebas automatizadas sin consumir la cuota de la API.

## Importante sobre Scopus, acceso abierto y PDFs

La API de Scopus está orientada principalmente a metadatos y enlaces. No
garantiza que entregue el archivo PDF del artículo.

Para localizar PDFs, la aplicación utiliza [Unpaywall](https://unpaywall.org/)
con el DOI de cada artículo. Unpaywall identifica ubicaciones de acceso abierto
en repositorios y sitios académicos. La aplicación solo descarga una copia
cuando Unpaywall proporciona una ubicación HTTP/HTTPS.

Esto significa que:

- No todos los artículos tienen un PDF descargable.
- Un artículo puede estar marcado como acceso abierto en Scopus y no tener una
  URL PDF disponible en Unpaywall.
- La aplicación no intenta evadir pagos, suscripciones, autenticación ni
  controles institucionales.
- Los PDFs se mantienen en memoria mientras se prepara el ZIP; no se guardan
  automáticamente en el repositorio.
- El usuario es responsable de respetar las licencias y condiciones de uso de
  cada publicación.

## Requisitos

- Windows, macOS o Linux.
- Python 3.10 o superior.
- Acceso a Internet.
- Una clave de API de Elsevier/Scopus.
- Un correo electrónico para identificar las solicitudes a Unpaywall si se
  quiere utilizar la descarga de PDFs.

## Obtener la clave de Scopus

1. Abre el [Elsevier Developer Portal](https://dev.elsevier.com/).
2. Crea una cuenta o inicia sesión.
3. Entra en la sección **API Keys** o **My API Keys**.
4. Crea una nueva clave.
5. Copia la clave y guárdala de forma privada.

El acceso, el límite de solicitudes y las API disponibles pueden depender de
los permisos de la cuenta o de una suscripción institucional. Si la clave
devuelve un error `401`, consulta los permisos de la cuenta o genera una nueva
clave.

La aplicación solicita la vista estándar de resultados de Scopus. No utiliza
`view=COMPLETE`, porque esa vista puede requerir permisos adicionales y producir
un `401` aunque la clave sí pueda realizar búsquedas normales.

## Clonar el proyecto

Desde PowerShell:

```powershell
git clone URL_DEL_REPOSITORIO
cd "Script de extraccion de articulos"
```

Reemplaza `URL_DEL_REPOSITORIO` por la URL real del repositorio. Si la carpeta
clonada tiene otro nombre, utiliza ese nombre en el comando `cd`.

## Instalación en Windows

Abre PowerShell en la carpeta raíz del proyecto y ejecuta:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell impide activar el entorno virtual, permite la activación solo
para la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

También se puede ejecutar todo sin activar el entorno, usando directamente el
Python de `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configurar las variables de entorno

Crea el archivo `.env` a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y coloca tus valores:

```env
SCOPUS_API_KEY="tu_clave_real_de_elsevier"
UNPAYWALL_EMAIL="tu_correo@ejemplo.com"
```

Las comillas dobles son opcionales para valores sencillos, pero se recomienda
mantenerlas para evitar problemas con espacios o caracteres especiales. No
dejes espacios alrededor del signo `=`.

Ejemplo válido:

```env
SCOPUS_API_KEY="abc123"
UNPAYWALL_EMAIL="investigador@universidad.edu"
```

Ejemplo que debe evitarse:

```env
SCOPUS_API_KEY = “abc123”
```

El archivo `.env` está incluido en `.gitignore`. No lo subas a GitHub ni
compartas su contenido. Si una clave se expone, revócala y genera otra.

La variable `UNPAYWALL_EMAIL` no es una clave secreta. Unpaywall la solicita
para identificar las peticiones realizadas a su servicio.

## Ejecutar la aplicación

Con el entorno virtual activado:

```powershell
python -m streamlit run app.py
```

Sin activar el entorno virtual:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Después abre en el navegador:

```text
http://localhost:8501
```

También se puede acceder desde otro equipo de la misma red usando la dirección
que Streamlit muestre en la terminal, siempre que la configuración de red lo
permita.

### No ejecutar `app.py` directamente

No uses:

```powershell
python app.py
```

Streamlit necesita iniciar el archivo mediante `streamlit run`. Si se ejecuta
como un script Python normal aparecerán mensajes como `missing
ScriptRunContext` y la interfaz no funcionará correctamente.

## Uso de la interfaz

### 1. Configuración de la API

La barra lateral permite introducir la clave API. Si existe `SCOPUS_API_KEY`
en `.env`, se carga automáticamente como valor inicial y se muestra oculta.

También se puede introducir manualmente la clave en la interfaz sin modificar
`.env`.

### 2. Configurar la búsqueda

La interfaz ofrece dos modos:

- **Guiada**: escribe un tema y utiliza los filtros de la barra lateral. La
  aplicación construye una consulta con `TITLE-ABS-KEY(...)`.
- **Avanzada**: escribe directamente la consulta de Scopus. En este modo la
  consulta se envía sin modificar; los filtros guiados de años, idioma, tipo de
  documento y área temática no se aplican. El número máximo de artículos y el
  orden de resultados siguen aplicándose a la petición de la API.

Ejemplo de consulta avanzada:

```text
TITLE-ABS-KEY("machine learning" OR "deep learning")
AND AUTHLASTNAME(Smith)
AND PUBYEAR > 2020
AND SUBJAREA(COMP)
AND OPENACCESS(1)
```

Algunos operadores habituales de Scopus son:

- `TITLE(...)`: busca en el título.
- `ABS(...)`: busca en el resumen.
- `KEY(...)`: busca en palabras clave.
- `TITLE-ABS-KEY(...)`: combina título, resumen y palabras clave.
- `AUTHLASTNAME(...)`: filtra por apellido del autor.
- `AUTH(...)`: busca por autor.
- `SRCTITLE(...)`: filtra por nombre de revista o fuente.
- `DOI(...)`: busca por DOI.
- `PUBYEAR`: filtra por año.
- `DOCTYPE(...)`: filtra por tipo de documento.
- `SUBJAREA(...)`: filtra por área temática.
- `OPENACCESS(1)`: limita a acceso abierto.
- `AND`, `OR`, `AND NOT`: combinan criterios.

Consulta siempre la documentación de sintaxis de Scopus para operadores
específicos. Si Scopus rechaza la consulta, la interfaz mostrará el error
devuelto por la API.

- **Tema o expresión de búsqueda**: escribe palabras o una expresión avanzada.
  Ejemplo:

  ```text
  ("machine learning" OR "deep learning") AND agriculture
  ```

- **Número de artículos**: cantidad máxima solicitada, entre 1 y 200.
- **Solo acceso abierto**: agrega `OPENACCESS(1)` a la consulta cuando está
  activado.
- **Rango de años**: limita el periodo de publicación.
- **Idioma**: permite seleccionar un idioma o todos.
- **Tipo de documento**:
  - `ar`: artículo.
  - `re`: revisión.
  - `cp`: artículo de conferencia.
  - `ch`: capítulo de libro.
- **Área temática**: utiliza códigos de Scopus, por ejemplo `COMP`, `MED` o
  `ENVI`.
- **Ordenar por**: fecha de publicación, número de citas o relevancia.

### 3. Ejecutar la búsqueda

Pulsa **Extraer artículos**. Los resultados se guardan en la sesión actual y
se muestran en una tabla.

Una nueva búsqueda reemplaza los resultados anteriores y limpia el ZIP de PDFs
preparado anteriormente.

### 4. Descargar metadatos

Después de una búsqueda aparecen dos botones:

- **Descargar metadatos JSON**: conserva todos los campos normalizados en una
  lista de objetos.
- **Descargar CSV**: genera un archivo tabular con codificación UTF-8 con BOM,
  adecuada para abrirlo en Excel.

### 5. Descargar PDFs de acceso abierto

Para habilitar esta opción, configura `UNPAYWALL_EMAIL` o escribe un correo en
la barra lateral.

1. Ejecuta una búsqueda.
2. Ve a la sección **PDFs de acceso abierto**.
3. Pulsa **Buscar y preparar PDFs OA**.
4. Espera a que se consulte Unpaywall y se descarguen las copias disponibles.
5. Pulsa **Descargar PDFs en ZIP**.

Los nombres de archivo se limpian para que sean compatibles con Windows. Si
dos artículos tienen el mismo título, se añaden sufijos como `_2` y `_3`.

El botón de descarga solo aparece si se preparó al menos un PDF. Si no se
encuentra una copia, la interfaz muestra cuántos artículos quedaron sin una
ubicación PDF en Unpaywall. Si una ubicación falla durante la descarga, se
muestra el número de errores y el expander **Ver detalles de los errores**
indica el artículo y el motivo.

Para comprobar que el mecanismo funciona, se puede probar con una consulta
marcada como acceso abierto que tenga DOI. Aun así, la disponibilidad final
depende del registro de Unpaywall y del repositorio del artículo; que Scopus
marque un registro como acceso abierto no garantiza que Unpaywall tenga un PDF.

## Estructura del proyecto

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── scopus_extractor/
│   ├── __init__.py
│   ├── client.py
│   ├── exporters.py
│   └── open_access.py
├── scripts/
│   └── check_publication.py
└── tests/
    ├── test_extractor.py
    └── test_open_access.py
```

### Responsabilidad de cada archivo

- `app.py`: interfaz Streamlit, formularios, mensajes y botones de descarga.
- `scopus_extractor/client.py`: consulta a la API de búsqueda de Scopus y
  normalización de resultados.
- `scopus_extractor/exporters.py`: conversión de artículos a JSON y CSV.
- `scopus_extractor/open_access.py`: consulta a Unpaywall, validación de PDFs y
  creación del ZIP.
- `tests/test_extractor.py`: pruebas de consultas, normalización y
  exportaciones.
- `tests/test_open_access.py`: prueba de localización y empaquetado simulado de
  PDFs.
- `requirements.txt`: dependencias de Python.
- `.env.example`: plantilla de variables de entorno.
- `.env`: configuración local; no debe publicarse.
- `scripts/check_publication.py`: verificador para bloquear secretos antes de
  preparar un commit.

## Dependencias

Las dependencias principales se encuentran en
[requirements.txt](requirements.txt):

- `requests`: solicitudes HTTP a Scopus y Unpaywall.
- `python-dotenv`: lectura del archivo `.env`.
- `streamlit`: interfaz web.
- `pandas`: visualización de los resultados.

## Ejecutar las pruebas

Con el entorno virtual activado:

```powershell
python -m pytest -q
```

Sin activarlo:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas utilizan sesiones HTTP simuladas. No necesitan una clave real,
Internet ni consumo de la cuota de Scopus.

Si `pytest` no está instalado, instala la dependencia únicamente para
desarrollo:

```powershell
python -m pip install pytest
```

Resultado esperado:

```text
5 passed
```

## Solución de problemas

### `streamlit` no se reconoce

Ejecuta Streamlit mediante el Python del entorno virtual:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Aparece `missing ScriptRunContext`

Se ejecutó `app.py` directamente. Utiliza:

```powershell
python -m streamlit run app.py
```

### Error `401` al consultar Scopus

La clave es incorrecta, está vencida o no tiene permisos para la API
solicitada. Revisa `.env`, elimina espacios extra y confirma los permisos en
Elsevier. La aplicación utiliza la vista estándar de resultados y no solicita
`view=COMPLETE`, porque esa vista puede requerir permisos adicionales.

### Error `429`

Scopus limitó temporalmente las solicitudes. Espera y vuelve a intentar más
tarde. Evita lanzar muchas búsquedas repetidas.

### No aparecen PDFs

Puede deberse a cualquiera de estas causas:

- El artículo no tiene DOI.
- Unpaywall no tiene una ubicación registrada.
- La ubicación no ofrece un PDF válido.
- El servidor del repositorio no responde.
- El artículo requiere suscripción.

El resultado de Scopus y la disponibilidad de un PDF son conceptos
independientes. Si todos los artículos aparecen como no disponibles, comprueba
que tengan DOI y que `UNPAYWALL_EMAIL` contenga un correo válido. Si hay errores,
abre **Ver detalles de los errores** en la interfaz.

### Error de activación de PowerShell

Ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Esto afecta solo a la ventana actual de PowerShell.

## Seguridad y buenas prácticas

- Nunca publiques `.env`.
- Nunca incluyas claves API en capturas de pantalla, commits o mensajes.
- Usa `.env.example` para documentar nombres de variables sin valores reales.
- Revoca las claves que se hayan expuesto.
- No subas PDFs descargados si sus licencias no lo permiten.
- Respeta los límites de la API y las condiciones de Elsevier y Unpaywall.
- No uses la aplicación para eludir controles de acceso o derechos de autor.

## Protocolo antes de publicar el proyecto o compartir resultados

Sigue este protocolo cada vez que vayas a subir cambios a GitHub o compartir
un ZIP/CSV/PDF:

1. Confirma que la clave real solo está en `.env` y que no está en
   `.env.example`, `README.md`, el código, capturas de pantalla ni notebooks.
2. No subas `.env`, PDFs, ZIPs, CSVs, JSONs de resultados ni carpetas
   `downloads/` o `exports/`. El `.gitignore` ya los excluye.
3. Revisa qué está preparado para el commit:

   ```powershell
   git status --short
   git diff --cached --name-only
   ```

4. Ejecuta el verificador antes de publicar:

   ```powershell
   .\.venv\Scripts\python.exe scripts\check_publication.py
   ```

   El comando analiza únicamente archivos preparados con `git add`. Si detecta
   `.env`, una clave API o un token, termina con error y debes retirar ese
   archivo del área preparada:

   ```powershell
   git restore --staged RUTA_DEL_ARCHIVO
   ```

5. Si el resultado es `OK`, revisa el contenido que se publicará:

   ```powershell
   git diff --cached --check
   git diff --cached
   ```

6. Solo después de esas comprobaciones ejecuta `git commit` y `git push`.

El verificador no reemplaza una revisión humana. Si una clave llegó a
prepararse, publicarse o compartirse, considérala comprometida: revócala de
inmediato en Elsevier y genera una nueva. Borrar el archivo en un commit
posterior no elimina la clave del historial de Git.

### Protección adicional al descargar PDFs

La aplicación no incorpora la clave API en los PDFs ni en el ZIP: la clave se
lee en memoria desde `SCOPUS_API_KEY` y no se escribe en los archivos
descargados. Aun así, los resultados y PDFs pueden contener material
restringido por licencia, por lo que `*.pdf`, `*.zip`, `*.csv` y `*.json` están
excluidos del repositorio. Antes de compartir un ZIP, verifica manualmente su
contenido y licencia.

## Limitaciones actuales

- La búsqueda depende de la disponibilidad y permisos de la API de Scopus.
- La cantidad de resultados está limitada a 200 por búsqueda en la interfaz.
- No se descargan artículos que no tengan una copia OA localizable.
- No se guardan resultados en una base de datos.
- No se reanudan descargas interrumpidas.
- Los PDFs se empaquetan en memoria; grandes cantidades pueden requerir
  bastante memoria RAM.
- El servicio de Unpaywall requiere un correo electrónico identificable.

## Licencia

Este repositorio no declara todavía una licencia de distribución. Antes de
publicarlo o reutilizarlo como paquete, añade una licencia adecuada al proyecto
y revisa las condiciones de uso de las APIs y de los contenidos descargados.
