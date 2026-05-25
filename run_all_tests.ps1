[CmdletBinding()]
param(
    [switch]$SkipNetwork,
    [switch]$SkipLighthouse,
    [switch]$RunWebTools,
    [switch]$FullRegression,
    [switch]$RunIntegration,
    [string]$IntegrationDeviceId = "",
    [int]$LatencySamples = 3,
    [int]$Concurrency = 20
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

$Root = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $Root "backend\manage.py"))) {
    $Root = (Get-Location).Path
}

$BackendDir = Join-Path $Root "backend"
$MobileDir = Join-Path $Root "mobile\commusafe_app"
$LoginUrl = "https://commusafe.onrender.com/login/"
$HealthUrl = "https://commusafe.onrender.com/health/"
$Results = New-Object System.Collections.Generic.List[object]

if (-not $env:SECRET_KEY) {
    $env:SECRET_KEY = "commusafe-local-test-secret-key-for-qa-script-2026"
}
if (-not $env:JWT_SIGNING_KEY) {
    $env:JWT_SIGNING_KEY = "commusafe-local-test-jwt-signing-key-for-qa-script-2026"
}
if (-not $env:DEBUG) {
    $env:DEBUG = "True"
}

$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "No se encontro Python ni backend\.venv\Scripts\python.exe."
    }
    $Python = $pythonCommand.Source
}

$FlutterCommand = Get-Command flutter -ErrorAction SilentlyContinue
$CurlCommand = Get-Command curl.exe -ErrorAction SilentlyContinue
$TracertCommand = Get-Command tracert.exe -ErrorAction SilentlyContinue
$NpxCommand = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $NpxCommand) {
    $NpxCommand = Get-Command npx -ErrorAction SilentlyContinue
}

function Write-CaseHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 88)
    Write-Host $Title
    Write-Host ("=" * 88)
}

function Invoke-ProcessCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $Root
    )

    $previousLocation = Get-Location
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $output = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) {
            $exitCode = 0
        }
        return [pscustomobject]@{
            ExitCode = [int]$exitCode
            Output = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
        }
    }
    finally {
        Set-Location -LiteralPath $previousLocation
    }
}

function Get-RegexInt {
    param([string]$Text, [string]$Pattern)
    if ($Text -match $Pattern) {
        return [int]$Matches[1]
    }
    return 0
}

function Get-PytestStats {
    param([string]$Text)
    return @{
        Passed = Get-RegexInt $Text "(\d+) passed"
        Failed = Get-RegexInt $Text "(\d+) failed"
        Skipped = Get-RegexInt $Text "(\d+) skipped"
        Errors = Get-RegexInt $Text "(\d+) error"
        Subtests = Get-RegexInt $Text "(\d+) subtests passed"
    }
}

function Get-FlutterTestStats {
    param([string]$Text)
    $passed = 0
    if ($Text -match "\+(\d+): All tests passed") {
        $passed = [int]$Matches[1]
    }
    return @{ Passed = $passed; Failed = 0; Skipped = 0 }
}

function Invoke-PytestCase {
    param([string[]]$PytestArgs)
    Write-Host ("Ejecutando: {0} -m pytest {1}" -f $Python, ($PytestArgs -join " "))
    $cmd = Invoke-ProcessCapture -FilePath $Python -Arguments (@("-m", "pytest") + $PytestArgs) -WorkingDirectory $BackendDir
    $stats = Get-PytestStats $cmd.Output
    $status = if ($cmd.ExitCode -eq 0) { "PASS" } else { "FAIL" }
    $details = "exit=$($cmd.ExitCode); passed=$($stats.Passed); failed=$($stats.Failed); subtests=$($stats.Subtests)"
    return @{
        Status = $status
        Output = $cmd.Output
        Passed = $stats.Passed
        Failed = $stats.Failed + $stats.Errors
        Skipped = $stats.Skipped
        Details = $details
        Interpretation = if ($status -eq "PASS") { "La validacion automatizada del caso paso correctamente." } else { "El caso requiere correccion antes de cerrar el plan." }
    }
}

function Invoke-FlutterCase {
    param([string[]]$FlutterArgs, [string]$SuccessMessage)
    if (-not $FlutterCommand) {
        return @{
            Status = "FAIL"
            Output = ""
            Passed = 0
            Failed = 1
            Skipped = 0
            Details = "flutter no disponible"
            Interpretation = "Instala Flutter o agrega flutter al PATH para ejecutar esta prueba."
        }
    }

    Write-Host ("Ejecutando: flutter {0}" -f ($FlutterArgs -join " "))
    $cmd = Invoke-ProcessCapture -FilePath $FlutterCommand.Source -Arguments $FlutterArgs -WorkingDirectory $MobileDir
    $status = if ($cmd.ExitCode -eq 0) { "PASS" } else { "FAIL" }
    $stats = Get-FlutterTestStats $cmd.Output
    return @{
        Status = $status
        Output = $cmd.Output
        Passed = $stats.Passed
        Failed = if ($status -eq "PASS") { 0 } else { 1 }
        Skipped = 0
        Details = "exit=$($cmd.ExitCode)"
        Interpretation = if ($status -eq "PASS") { $SuccessMessage } else { "La validacion movil fallo y debe revisarse." }
    }
}

function Invoke-TestCase {
    param(
        [string]$Id,
        [string]$Name,
        [scriptblock]$Action
    )

    Write-CaseHeader "$Id - $Name"
    if ($script:CaseGuide -and $script:CaseGuide.ContainsKey($Id)) {
        $guide = $script:CaseGuide[$Id]
        Write-Host "Que valida: $($guide.Valida)"
        Write-Host "Como lo valida: $($guide.Como)"
        Write-Host "Resultado esperado: $($guide.Esperado)"
        Write-Host "Lectura rapida: $($guide.Lectura)"
        Write-Host ""
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $caseResult = & $Action
    }
    catch {
        $caseResult = @{
            Status = "FAIL"
            Output = $_.Exception.ToString()
            Passed = 0
            Failed = 1
            Skipped = 0
            Details = $_.Exception.Message
            Interpretation = "La prueba no pudo ejecutarse."
        }
    }
    $sw.Stop()

    if ($caseResult.Output) {
        Write-Host $caseResult.Output
    }

    $status = if ($caseResult.ContainsKey("Status")) { $caseResult.Status } else { "PASS" }
    $passed = if ($caseResult.ContainsKey("Passed")) { [int]$caseResult.Passed } else { 0 }
    $failed = if ($caseResult.ContainsKey("Failed")) { [int]$caseResult.Failed } else { 0 }
    $skipped = if ($caseResult.ContainsKey("Skipped")) { [int]$caseResult.Skipped } else { 0 }
    $details = if ($caseResult.ContainsKey("Details")) { $caseResult.Details } else { "" }
    $interpretation = if ($caseResult.ContainsKey("Interpretation")) { $caseResult.Interpretation } else { "" }

    $record = [pscustomobject]@{
        Id = $Id
        Nombre = $Name
        Estado = $status
        DuracionSeg = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        Aprobadas = $passed
        Fallidas = $failed
        Omitidas = $skipped
        Detalle = $details
        Interpretacion = $interpretation
    }
    $Results.Add($record) | Out-Null

    Write-Host ""
    Write-Host "Estado: $status"
    if ($details) { Write-Host "Detalle: $details" }
    if ($interpretation) { Write-Host "Interpretacion: $interpretation" }
}

function New-ProjectEvidenceResult {
    param(
        [string]$Issue,
        [string]$Tool,
        [string]$LiveAction
    )

    return @{
        Status = "PROJECT"
        Output = ""
        Passed = 0
        Failed = 0
        Skipped = 1
        Details = "$Issue; herramienta=$Tool"
        Interpretation = "Evidencia centralizada en GitHub Projects. Se puede demostrar en vivo con: $LiveAction"
    }
}

function Convert-ToInvariantDouble {
    param([string]$Value)
    return [double]::Parse($Value, [System.Globalization.CultureInfo]::InvariantCulture)
}

$script:CaseGuide = @{
    "CP-001" = @{
        Valida = "Que un usuario valido pueda iniciar sesion y recibir tokens JWT."
        Como = "Ejecuta una prueba backend sobre el endpoint de login con credenciales correctas."
        Esperado = "Respuesta HTTP 200 con access, refresh y datos del usuario."
        Lectura = "Si pasa, la autenticacion principal funciona para usuarios activos."
    }
    "CP-002" = @{
        Valida = "Que credenciales incorrectas no permitan acceso al sistema."
        Como = "Ejecuta login con contrasena invalida desde pytest."
        Esperado = "Respuesta HTTP 401 y ausencia de tokens JWT."
        Lectura = "Si pasa, el backend rechaza accesos no autorizados por credenciales invalidas."
    }
    "CP-003" = @{
        Valida = "Que un endpoint protegido no responda datos sin token."
        Como = "Solicita el perfil sin encabezado Authorization mediante prueba automatizada."
        Esperado = "Respuesta HTTP 401."
        Lectura = "Si pasa, las rutas privadas exigen autenticacion."
    }
    "CP-004" = @{
        Valida = "Que los roles limiten acciones administrativas."
        Como = "Autentica un residente e intenta acceder a una ruta administrativa."
        Esperado = "Respuesta HTTP 403."
        Lectura = "Si pasa, el control de acceso por rol evita privilegios indebidos."
    }
    "CP-005" = @{
        Valida = "Que se pueda crear un incidente con los datos requeridos."
        Como = "Ejecuta pruebas backend de creacion de incidente y evidencias asociadas."
        Esperado = "Incidente creado con respuesta exitosa y reglas de negocio aplicadas."
        Lectura = "Si pasa, el flujo central de reporte de incidentes esta operativo."
    }
    "CP-006" = @{
        Valida = "Que la visibilidad de incidentes cambie segun el rol."
        Como = "Compara consultas como residente y vigilante."
        Esperado = "Residente ve solo sus casos; vigilante ve los incidentes correspondientes."
        Lectura = "Si pasa, la informacion de incidentes no se expone a usuarios no autorizados."
    }
    "CP-007" = @{
        Valida = "Que un cambio de estado genere trazabilidad."
        Como = "Cambia el estado de un incidente y revisa historial/notificacion."
        Esperado = "Estado actualizado y registro de historial creado."
        Lectura = "Si pasa, el seguimiento del incidente queda documentado."
    }
    "CP-008" = @{
        Valida = "Que el limite de evidencias por incidente se respete."
        Como = "Intenta superar el maximo permitido de evidencias en pruebas backend."
        Esperado = "El sistema rechaza la evidencia adicional y conserva el limite."
        Lectura = "Si pasa, la regla de negocio evita cargas excesivas o inconsistentes."
    }
    "CP-009" = @{
        Valida = "Que las notificaciones se generen segun prioridad y destinatarios."
        Como = "Crea escenarios de incidentes y revisa registros de notificacion."
        Esperado = "Notificaciones correctas, sin duplicar al reportante."
        Lectura = "Si pasa, las alertas comunitarias siguen la regla funcional definida."
    }
    "CP-010" = @{
        Valida = "Que el asistente responda dentro del dominio de CommuSafe."
        Como = "Ejecuta una consulta controlada al asistente desde pruebas backend."
        Esperado = "Respuesta no vacia, relacionada con la comunidad o el sistema."
        Lectura = "Si pasa, el asistente ofrece soporte sin salirse del contexto funcional."
    }
    "CP-011" = @{
        Valida = "Que el panel web tenga marcado HTML aceptable para W3C."
        Como = "Por defecto se marca como evidencia del Project; con -RunWebTools consulta Nu Html Checker."
        Esperado = "Sin errores criticos de HTML."
        Lectura = "Si aparece PROJECT, la evidencia esta en GitHub Projects o se muestra en vivo."
    }
    "CP-012" = @{
        Valida = "Accesibilidad basica del panel web."
        Como = "Por defecto usa evidencia del Project; con -RunWebTools ejecuta Lighthouse si esta disponible."
        Esperado = "Puntajes y observaciones sin fallos bloqueantes."
        Lectura = "Si aparece PROJECT, se valida durante la presentacion o con evidencia anexada."
    }
    "CP-013" = @{
        Valida = "Disponibilidad del backend desplegado en Render."
        Como = "Consulta el endpoint /health/ con curl."
        Esperado = "JSON con status ok."
        Lectura = "Si pasa, el servicio publicado esta respondiendo."
    }
    "CP-014" = @{
        Valida = "Tiempo de respuesta del servicio publicado."
        Como = "Ejecuta varias mediciones con curl y calcula promedio, minimo y maximo."
        Esperado = "Respuestas HTTP 200 con tiempos razonables para el entorno."
        Lectura = "Si pasa, el servicio esta disponible y responde de forma estable."
    }
    "CP-015" = @{
        Valida = "Conectividad de red hacia el dominio productivo."
        Como = "Ejecuta tracert contra commusafe.onrender.com."
        Esperado = "Resolucion DNS y ruta hasta el host/CDN."
        Lectura = "Si pasa, existe ruta de red desde el equipo hasta el servicio."
    }
    "CP-016" = @{
        Valida = "Comportamiento del health check bajo concurrencia basica."
        Como = "Lanza varias solicitudes paralelas al endpoint /health/."
        Esperado = "Todas o la totalidad esperada responden HTTP 200."
        Lectura = "Si pasa, el endpoint soporta carga ligera concurrente."
    }
    "CP-017" = @{
        Valida = "Compatibilidad entre navegadores y disponibilidad de entorno movil."
        Como = "Lista dispositivos Flutter y registra evidencia visual en GitHub Projects."
        Esperado = "Chrome/Edge/Android disponibles o evidencia manual documentada."
        Lectura = "Si aparece PROJECT, la compatibilidad se sustenta con evidencia visual o demo en vivo."
    }
    "CP-018" = @{
        Valida = "Que los enlaces publicos no presenten errores criticos."
        Como = "Se evidencia con W3C Link Checker en GitHub Projects o presentacion."
        Esperado = "Sin enlaces rotos criticos o con observaciones justificadas."
        Lectura = "PROJECT significa que esta prueba se revisa mejor desde navegador."
    }
    "CP-019" = @{
        Valida = "Internacionalizacion basica: idioma, codificacion y direccion del texto."
        Como = "Se evidencia con W3C Internationalization Checker."
        Esperado = "UTF-8, lang correcto y sin problemas criticos."
        Lectura = "PROJECT significa que la evidencia esta anexada o se muestra en vivo."
    }
    "CP-020" = @{
        Valida = "Validez basica de CSS del panel web."
        Como = "Se evidencia con W3C CSS Validator."
        Esperado = "Sin errores CSS criticos."
        Lectura = "PROJECT significa que no se ejecuta por terminal salvo demostracion web."
    }
    "CP-021" = @{
        Valida = "Contraste de color segun criterios WCAG."
        Como = "Se revisa con Lighthouse, WAVE, DevTools o herramienta WCAG equivalente."
        Esperado = "Textos y controles legibles."
        Lectura = "PROJECT significa que el resultado esta en evidencia visual o demo."
    }
    "CP-022" = @{
        Valida = "Rendimiento web en perfil movil."
        Como = "Se evalua con PageSpeed Insights movil."
        Esperado = "Metricas aceptables para la demostracion academica."
        Lectura = "PROJECT significa que se muestra mejor en PageSpeed durante la presentacion."
    }
    "CP-023" = @{
        Valida = "Rendimiento web en perfil escritorio."
        Como = "Se evalua con PageSpeed Insights escritorio."
        Esperado = "Metricas aceptables para la demostracion academica."
        Lectura = "PROJECT significa que se muestra mejor en PageSpeed durante la presentacion."
    }
    "REG-001" = @{
        Valida = "Regresion completa automatizada de backend y app movil."
        Como = "Ejecuta manage.py check, pytest completo, flutter analyze y flutter test."
        Esperado = "Todas las validaciones terminan sin errores."
        Lectura = "Si pasa, el estado tecnico general del repositorio es consistente."
    }
}

Write-Host "CommuSafe QA Runner"
Write-Host "Root: $Root"
Write-Host "Python: $Python"
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Modo: casos CP-001 a CP-023 del GitHub Project."
Write-Host "Nota: W3C, Lighthouse, WCAG, CSS y PageSpeed se reportan como PROJECT porque su evidencia esta en GitHub Projects o se muestra en vivo."
Write-Host "Para ejecutar tambien la bateria terminal completa usa: .\run_all_tests.ps1 -FullRegression"

Invoke-TestCase "CP-001" "Login correcto con JWT" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "-k", "login_correcto", "-q")
}

Invoke-TestCase "CP-002" "Login incorrecto" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "-k", "login_incorrecto", "-q")
}

Invoke-TestCase "CP-003" "Acceso protegido sin token" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "-k", "sin_token", "-q")
}

Invoke-TestCase "CP-004" "Control de acceso por rol" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "-k", "administracion", "-q")
}

Invoke-TestCase "CP-005" "Creacion de incidente" {
    Invoke-PytestCase @("incidentes/tests.py", "-k", "crear_incidente", "-q")
}

Invoke-TestCase "CP-006" "Visibilidad de incidentes por rol" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "incidentes/tests.py", "-k", "ve_sus_propios_incidentes or ve_todos_los_incidentes", "-q")
}

Invoke-TestCase "CP-007" "Cambio de estado e historial" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "incidentes/tests.py", "-k", "cambiar_estado", "-q")
}

Invoke-TestCase "CP-008" "Limite de evidencias" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "incidentes/tests.py", "-k", "mas_de_tres_evidencias or evidencia_limite", "-q")
}

Invoke-TestCase "CP-009" "Notificaciones por prioridad" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "notificaciones/tests.py", "-k", "notifica", "-q")
}

Invoke-TestCase "CP-010" "Asistente virtual dentro del dominio" {
    Invoke-PytestCase @("tests/test_sistema_completo.py", "-k", "chat_asistente", "-q")
}

Invoke-TestCase "CP-011" "Validacion W3C del panel web" {
    if (-not $RunWebTools) {
        return New-ProjectEvidenceResult "#54" "Nu Html Checker" "abrir https://validator.w3.org/nu/ y validar $LoginUrl"
    }
    if ($SkipNetwork) {
        return @{ Status = "PROJECT"; Passed = 0; Failed = 0; Skipped = 1; Details = "#54; red omitida"; Interpretation = "Validacion W3C queda para evidencia en GitHub Projects o presentacion en vivo." }
    }
    if (-not $CurlCommand) {
        return @{ Status = "FAIL"; Passed = 0; Failed = 1; Skipped = 0; Details = "curl.exe no disponible"; Interpretation = "No se pudo consultar el validador W3C." }
    }

    $encodedDoc = [System.Uri]::EscapeDataString($LoginUrl)
    $validatorUrl = "https://validator.w3.org/nu/?out=json&doc=$encodedDoc"
    $cmd = Invoke-ProcessCapture -FilePath $CurlCommand.Source -Arguments @("-s", "--max-time", "60", $validatorUrl) -WorkingDirectory $Root
    if ($cmd.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($cmd.Output)) {
        return @{ Status = "MANUAL"; Output = $cmd.Output; Passed = 0; Failed = 0; Skipped = 1; Details = "validador no disponible"; Interpretation = "La disponibilidad del panel debe revisarse manualmente en validator.w3.org/nu/." }
    }

    $json = $cmd.Output | ConvertFrom-Json
    $messages = @($json.messages)
    $errors = @($messages | Where-Object { $_.type -eq "error" })
    $status = if ($errors.Count -eq 0) { "PASS" } else { "FAIL" }
    return @{
        Status = $status
        Output = "Nu Html Checker messages=$($messages.Count); errors=$($errors.Count)"
        Passed = if ($status -eq "PASS") { 1 } else { 0 }
        Failed = $errors.Count
        Skipped = 0
        Details = "messages=$($messages.Count); errors=$($errors.Count)"
        Interpretation = if ($status -eq "PASS") { "El HTML publico no presenta errores criticos reportados por Nu Html Checker." } else { "Hay errores HTML que deben corregirse o justificarse." }
    }
}

Invoke-TestCase "CP-012" "Accesibilidad basica con Lighthouse" {
    if (-not $RunWebTools -or $SkipLighthouse) {
        return New-ProjectEvidenceResult "#55" "Lighthouse / WCAG" "abrir DevTools > Lighthouse o la herramienta WCAG usada en la presentacion"
    }
    if (-not $NpxCommand) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "npx no disponible"; Interpretation = "Instala Node/npx o ejecuta Lighthouse desde DevTools." }
    }

    $lighthouseDir = Join-Path ([System.IO.Path]::GetTempPath()) "commusafe-lighthouse"
    New-Item -ItemType Directory -Path $lighthouseDir -Force | Out-Null
    $out = Join-Path $lighthouseDir ("login-{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    $cmd = Invoke-ProcessCapture -FilePath $NpxCommand.Source -Arguments @(
        "--yes",
        "lighthouse",
        $LoginUrl,
        "--output=json",
        "--output-path=$out",
        "--chrome-flags=--headless --disable-gpu",
        "--quiet"
    ) -WorkingDirectory $Root

    if (-not (Test-Path -LiteralPath $out)) {
        return @{ Status = "MANUAL"; Output = $cmd.Output; Passed = 0; Failed = 0; Skipped = 1; Details = "sin reporte json"; Interpretation = "Lighthouse no genero reporte; ejecutar desde DevTools." }
    }

    $json = Get-Content -Raw -LiteralPath $out | ConvertFrom-Json
    $scores = @{}
    foreach ($category in $json.categories.PSObject.Properties) {
        $scores[$category.Name] = [int][math]::Round($category.Value.score * 100)
    }
    $mainScores = @($scores["performance"], $scores["accessibility"], $scores["best-practices"], $scores["seo"])
    $status = if (($mainScores | Where-Object { $_ -lt 90 }).Count -eq 0) { "PASS" } else { "FAIL" }
    $summary = "performance=$($scores["performance"]); accessibility=$($scores["accessibility"]); best-practices=$($scores["best-practices"]); seo=$($scores["seo"])"
    if ($cmd.ExitCode -ne 0) {
        $summary = "$summary; lighthouse_exit=$($cmd.ExitCode) con reporte parseado"
    }
    return @{
        Status = $status
        Output = $summary
        Passed = if ($status -eq "PASS") { 1 } else { 0 }
        Failed = if ($status -eq "PASS") { 0 } else { 1 }
        Skipped = 0
        Details = $summary
        Interpretation = if ($status -eq "PASS") { "Los puntajes principales de Lighthouse estan en rango aprobado." } else { "Uno o mas puntajes Lighthouse quedaron por debajo de 90." }
    }
}

Invoke-TestCase "CP-013" "Disponibilidad del servicio en Render" {
    if ($SkipNetwork) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "red omitida"; Interpretation = "Ejecuta sin -SkipNetwork para validar produccion." }
    }
    $cmd = Invoke-ProcessCapture -FilePath $CurlCommand.Source -Arguments @("-s", "--max-time", "60", $HealthUrl) -WorkingDirectory $Root
    $status = "FAIL"
    $details = $cmd.Output
    try {
        $json = $cmd.Output | ConvertFrom-Json
        if ($json.status -eq "ok") { $status = "PASS" }
    }
    catch {
        $status = "FAIL"
    }
    return @{
        Status = $status
        Output = $cmd.Output
        Passed = if ($status -eq "PASS") { 1 } else { 0 }
        Failed = if ($status -eq "PASS") { 0 } else { 1 }
        Skipped = 0
        Details = $details
        Interpretation = if ($status -eq "PASS") { "El endpoint /health/ confirma disponibilidad del servicio." } else { "El servicio publicado no respondio como se esperaba." }
    }
}

Invoke-TestCase "CP-014" "Latencia y tiempo de respuesta en Render" {
    if ($SkipNetwork) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "red omitida"; Interpretation = "Ejecuta sin -SkipNetwork para medir latencia." }
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $times = New-Object System.Collections.Generic.List[double]
    $ok = 0
    for ($i = 1; $i -le $LatencySamples; $i++) {
        $cmd = Invoke-ProcessCapture -FilePath $CurlCommand.Source -Arguments @("-s", "-o", "NUL", "--max-time", "60", "-w", "%{http_code} %{time_total}", $HealthUrl) -WorkingDirectory $Root
        $line = $cmd.Output.Trim()
        $lines.Add("run=$i $line") | Out-Null
        $parts = $line -split "\s+"
        if ($parts.Count -ge 2 -and $parts[0] -eq "200") {
            $ok++
            $times.Add((Convert-ToInvariantDouble $parts[1])) | Out-Null
        }
    }

    $avg = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Average).Average, 3) } else { 0 }
    $min = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Minimum).Minimum, 3) } else { 0 }
    $max = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Maximum).Maximum, 3) } else { 0 }
    $status = if ($ok -eq $LatencySamples) { "PASS" } else { "FAIL" }
    $interpretation = if ($status -eq "PASS" -and $avg -lt 0.75) {
        "Latencia promedio baja para una validacion externa de disponibilidad."
    }
    elseif ($status -eq "PASS") {
        "Servicio disponible; revisar si la latencia promedio supera el umbral esperado del proyecto."
    }
    else {
        "No todas las mediciones respondieron HTTP 200."
    }
    return @{
        Status = $status
        Output = ($lines -join [Environment]::NewLine)
        Passed = $ok
        Failed = $LatencySamples - $ok
        Skipped = 0
        Details = "samples=$LatencySamples; ok=$ok; avg=${avg}s; min=${min}s; max=${max}s"
        Interpretation = $interpretation
    }
}

Invoke-TestCase "CP-015" "Conectividad con tracert" {
    if ($SkipNetwork) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "red omitida"; Interpretation = "Ejecuta sin -SkipNetwork para validar conectividad." }
    }
    if (-not $TracertCommand) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "tracert no disponible"; Interpretation = "Usa una herramienta equivalente de traceroute." }
    }
    $cmd = Invoke-ProcessCapture -FilePath $TracertCommand.Source -Arguments @("-d", "-h", "12", "commusafe.onrender.com") -WorkingDirectory $Root
    $status = if ($cmd.ExitCode -eq 0) { "PASS" } else { "FAIL" }
    return @{
        Status = $status
        Output = $cmd.Output
        Passed = if ($status -eq "PASS") { 1 } else { 0 }
        Failed = if ($status -eq "PASS") { 0 } else { 1 }
        Skipped = 0
        Details = "exit=$($cmd.ExitCode)"
        Interpretation = if ($status -eq "PASS") { "Existe resolucion DNS y ruta de red hacia el servicio publicado." } else { "La conectividad debe revisarse desde la red actual." }
    }
}

Invoke-TestCase "CP-016" "Rendimiento y concurrencia basica" {
    if ($SkipNetwork) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "red omitida"; Interpretation = "Ejecuta sin -SkipNetwork para probar concurrencia." }
    }

    $jobs = 1..$Concurrency | ForEach-Object {
        Start-Job -ScriptBlock {
            param($Url)
            curl.exe -s -o NUL --max-time 60 -w "%{http_code} %{time_total}" $Url
        } -ArgumentList $HealthUrl
    }
    $jobOutput = $jobs | Wait-Job | Receive-Job
    $jobs | Remove-Job
    $lines = @($jobOutput | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ })
    $times = New-Object System.Collections.Generic.List[double]
    $ok = 0
    foreach ($line in $lines) {
        $parts = $line -split "\s+"
        if ($parts.Count -ge 2 -and $parts[0] -eq "200") {
            $ok++
            $times.Add((Convert-ToInvariantDouble $parts[1])) | Out-Null
        }
    }
    $avg = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Average).Average, 3) } else { 0 }
    $min = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Minimum).Minimum, 3) } else { 0 }
    $max = if ($times.Count -gt 0) { [math]::Round(($times | Measure-Object -Maximum).Maximum, 3) } else { 0 }
    $status = if ($ok -eq $Concurrency) { "PASS" } else { "FAIL" }
    return @{
        Status = $status
        Output = ($lines -join [Environment]::NewLine)
        Passed = $ok
        Failed = $Concurrency - $ok
        Skipped = 0
        Details = "requests=$Concurrency; ok=$ok; avg=${avg}s; min=${min}s; max=${max}s"
        Interpretation = if ($status -eq "PASS") { "Todas las solicitudes concurrentes respondieron correctamente." } else { "Hubo respuestas fallidas o incompletas bajo concurrencia." }
    }
}

Invoke-TestCase "CP-017" "Compatibilidad entre navegadores y dispositivos" {
    if (-not $FlutterCommand) {
        return @{ Status = "MANUAL"; Passed = 0; Failed = 0; Skipped = 1; Details = "flutter no disponible"; Interpretation = "Validacion de compatibilidad requiere Flutter y dispositivos/navegadores." }
    }

    $devices = Invoke-ProcessCapture -FilePath $FlutterCommand.Source -Arguments @("devices") -WorkingDirectory $MobileDir
    $hasAndroid = $devices.Output -match "android"
    $hasChrome = $devices.Output -match "chrome"
    $hasEdge = $devices.Output -match "edge"

    if ($RunIntegration) {
        if (-not $IntegrationDeviceId) {
            return @{
                Status = "MANUAL"
                Output = $devices.Output
                Passed = 0
                Failed = 0
                Skipped = 1
                Details = "#61; falta -IntegrationDeviceId"
                Interpretation = "Para integracion, ejecuta con -RunIntegration -IntegrationDeviceId <id> usando un emulador o dispositivo Android preparado."
            }
        }
        $integration = Invoke-ProcessCapture -FilePath $FlutterCommand.Source -Arguments @(
            "test",
            "integration_test",
            "-d",
            $IntegrationDeviceId,
            "--dart-define=COMMUSAFE_API_BASE_URL=https://commusafe.onrender.com"
        ) -WorkingDirectory $MobileDir
        $status = if ($integration.ExitCode -eq 0) { "PASS" } else { "FAIL" }
        return @{
            Status = $status
            Output = $integration.Output
            Passed = if ($status -eq "PASS") { 1 } else { 0 }
            Failed = if ($status -eq "PASS") { 0 } else { 1 }
            Skipped = 0
            Details = "device=$IntegrationDeviceId; exit=$($integration.ExitCode)"
            Interpretation = if ($status -eq "PASS") { "Flujos de integracion movil aprobados en el dispositivo seleccionado." } else { "La compatibilidad/integracion movil requiere correccion o entorno preparado." }
        }
    }

    $details = "#61; chrome=$hasChrome; edge=$hasEdge; android=$hasAndroid"
    return @{
        Status = "PROJECT"
        Output = $devices.Output
        Passed = 0
        Failed = 0
        Skipped = 1
        Details = $details
        Interpretation = "Compatibilidad queda centralizada en GitHub Projects y puede demostrarse en vivo; usa -RunIntegration con Android si quieres ejecutar flujos moviles instrumentados."
    }
}

Invoke-TestCase "CP-018" "Validacion de enlaces con W3C Link Checker" {
    New-ProjectEvidenceResult "#64" "W3C Link Checker" "abrir el validador de enlaces y revisar $LoginUrl o el dominio publicado"
}

Invoke-TestCase "CP-019" "Validacion de internacionalizacion W3C" {
    New-ProjectEvidenceResult "#66" "W3C Internationalization Checker" "abrir el Internationalization Checker y validar idioma, codificacion UTF-8 y direccion del texto"
}

Invoke-TestCase "CP-020" "Validacion CSS con W3C CSS Validator" {
    New-ProjectEvidenceResult "#69" "W3C CSS Validator" "abrir https://jigsaw.w3.org/css-validator/ y validar la hoja de estilos del panel"
}

Invoke-TestCase "CP-021" "Validacion de contraste de color WCAG" {
    New-ProjectEvidenceResult "#70" "WCAG contrast checker" "mostrar el contraste desde Lighthouse, DevTools, WAVE o la herramienta WCAG usada"
}

Invoke-TestCase "CP-022" "Evaluacion de rendimiento movil con PageSpeed" {
    New-ProjectEvidenceResult "#72" "PageSpeed Insights movil" "abrir PageSpeed Insights y seleccionar resultados moviles para $LoginUrl"
}

Invoke-TestCase "CP-023" "Evaluacion de rendimiento escritorio con PageSpeed" {
    New-ProjectEvidenceResult "#73" "PageSpeed Insights escritorio" "abrir PageSpeed Insights y seleccionar resultados de escritorio para $LoginUrl"
}

if ($FullRegression) {
    Invoke-TestCase "REG-001" "Regresion automatizada completa backend y movil" {
        $outputs = New-Object System.Collections.Generic.List[string]
        $passed = 0
        $failed = 0

        $django = Invoke-ProcessCapture -FilePath $Python -Arguments @("manage.py", "check") -WorkingDirectory $BackendDir
        $outputs.Add("manage.py check:`n$($django.Output)") | Out-Null
        if ($django.ExitCode -eq 0) { $passed++ } else { $failed++ }

        $pytest = Invoke-ProcessCapture -FilePath $Python -Arguments @("-m", "pytest", "-q") -WorkingDirectory $BackendDir
        $pytestStats = Get-PytestStats $pytest.Output
        $outputs.Add("pytest -q:`n$($pytest.Output)") | Out-Null
        if ($pytest.ExitCode -eq 0) { $passed += $pytestStats.Passed } else { $failed += [math]::Max(1, $pytestStats.Failed + $pytestStats.Errors) }

        $analyze = Invoke-FlutterCase @("analyze") "Analisis estatico movil sin issues."
        $outputs.Add("flutter analyze:`n$($analyze.Output)") | Out-Null
        if ($analyze.Status -eq "PASS") { $passed++ } else { $failed++ }

        $flutterTest = Invoke-FlutterCase @("test") "Pruebas widget moviles aprobadas."
        $outputs.Add("flutter test:`n$($flutterTest.Output)") | Out-Null
        if ($flutterTest.Status -eq "PASS") { $passed += [math]::Max(1, $flutterTest.Passed) } else { $failed++ }

        $status = if ($failed -eq 0) { "PASS" } else { "FAIL" }
        return @{
            Status = $status
            Output = ($outputs -join ([Environment]::NewLine + [Environment]::NewLine))
            Passed = $passed
            Failed = $failed
            Skipped = 0
            Details = "backend_pytest_passed=$($pytestStats.Passed); backend_subtests=$($pytestStats.Subtests); mobile_widget_passed=$($flutterTest.Passed)"
            Interpretation = if ($status -eq "PASS") { "La regresion completa confirma estabilidad backend y movil automatizada." } else { "No se debe cerrar el plan hasta corregir fallas de regresion." }
        }
    }
}

Write-CaseHeader "Resumen general"
$Results | Format-Table Id, Estado, DuracionSeg, Aprobadas, Fallidas, Omitidas, Detalle -AutoSize

$total = $Results.Count
$passedCases = @($Results | Where-Object { $_.Estado -eq "PASS" }).Count
$failedCases = @($Results | Where-Object { $_.Estado -eq "FAIL" }).Count
$manualCases = @($Results | Where-Object { $_.Estado -eq "MANUAL" }).Count
$projectCases = @($Results | Where-Object { $_.Estado -eq "PROJECT" }).Count
$duration = [math]::Round(($Results | Measure-Object -Property DuracionSeg -Sum).Sum, 2)
$assertionsPassed = ($Results | Measure-Object -Property Aprobadas -Sum).Sum
$assertionsFailed = ($Results | Measure-Object -Property Fallidas -Sum).Sum
$assertionsSkipped = ($Results | Measure-Object -Property Omitidas -Sum).Sum

Write-Host "Casos totales: $total"
Write-Host "Casos PASS: $passedCases"
Write-Host "Casos FAIL: $failedCases"
Write-Host "Casos MANUAL/condicional: $manualCases"
Write-Host "Casos con evidencia en Project/presentacion: $projectCases"
Write-Host "Validaciones aprobadas registradas: $assertionsPassed"
Write-Host "Validaciones fallidas registradas: $assertionsFailed"
Write-Host "Validaciones omitidas/manuales: $assertionsSkipped"
Write-Host "Duracion acumulada: ${duration}s"

Write-Host ""
if ($failedCases -gt 0 -or $assertionsFailed -gt 0) {
    Write-Host "Interpretacion final: existen fallas. No cerrar el plan hasta corregir y repetir la ejecucion."
    exit 1
}
if (($manualCases + $projectCases) -gt 0) {
    Write-Host "Interpretacion final: las pruebas automatizadas pasaron. Los casos PROJECT/MANUAL se cierran con evidencia en GitHub Projects o demostracion en vivo."
    exit 0
}

Write-Host "Interpretacion final: todas las pruebas automatizadas y de entorno disponibles pasaron correctamente."
exit 0
