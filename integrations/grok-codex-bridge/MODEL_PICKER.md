# Optional native model-picker routing

This source path lets a compatible Codex desktop choose Grok using its existing model
button. The stdio router pairs model names with providers; the original Codex executable
still makes model requests, handles authentication/tools and persists history. Native
GPT uses OpenAI. This is experimental integration code, not a Codex binary patch.

The inspected local baseline was desktop 26.903.8094.0 with CLI 0.153.4 on Windows.
Use the existing [provider/catalog setup](SETUP.md) first. Its single selected Grok row
is enough to start. A menu entry alone does not choose the provider for a new task.

## 1. Verify the source first

From this integration directory with Python 3.11+:

```powershell
python -B -m unittest discover -s tests -v
```

On Windows, `test_model_router_bootstrap.py` also compiles the checked-in C# source in a
temporary directory and verifies arguments, raw stdio and error/exit handling. It uses
an argument-echo fixture, not your accounts or a model. On other systems that Windows
test is reported as skipped; Python routing controls still run.

## 2. Prepare local routing files

Keep the checkout in a stable location. In the example below, replace the four input
paths with your actual Python executable, original Codex executable, native model cache
and generated native-plus-Grok catalog from `configure.py`. Do not point the original
Codex path at this router itself. Keep all generated files outside the repository.

The native model list comes from the original native cache, not the proxy's GPT rows.
`grok_models` must be the explicit Grok selection already present in the generated catalog.
The router does not log prompts, credentials or tool output; its optional metadata log
is omitted in this example.

```powershell
$integrationRoot = (Get-Location).Path
$pythonBinary = 'C:/tools/python.exe'
$originalCodex = 'C:/tools/codex.exe'
$nativeCatalogPath = 'C:/tools/native-models-cache.json'
$generatedCatalogPath = 'C:/tools/native-plus-grok-catalog.json'
$routerOutput = Join-Path $env:LOCALAPPDATA 'GrokCodexModelRouter'
$grokModels = @('xai/grok-4.6')

# Read/validate inputs before creating any output files.
foreach ($inputPath in @($pythonBinary, $originalCodex, $nativeCatalogPath, $generatedCatalogPath)) {
    if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw "Missing input: $inputPath" }
}
$nativeCatalog = Get-Content -LiteralPath $nativeCatalogPath -Raw | ConvertFrom-Json
$generatedCatalog = Get-Content -LiteralPath $generatedCatalogPath -Raw | ConvertFrom-Json
$nativeModels = @($nativeCatalog.models | ForEach-Object { $_.slug })
if ($nativeModels.Count -eq 0 -or @($nativeModels | Where-Object { $_ -notlike 'gpt-*' }).Count -ne 0) {
    throw 'Choose the original native GPT model cache.'
}
foreach ($model in $grokModels) {
    if ($model -notin @($generatedCatalog.models | ForEach-Object { $_.slug })) {
        throw "Selected model is missing from the generated catalog: $model"
    }
}
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if (-not (Test-Path -LiteralPath $compiler -PathType Leaf)) { throw 'The .NET Framework C# compiler is required.' }
if (Test-Path -LiteralPath $routerOutput) { throw 'Existing output: preserve/reconcile that installation before updating.' }
New-Item -ItemType Directory -Path $routerOutput | Out-Null
$settingsPath = Join-Path $routerOutput 'router-settings.json'
$bootstrapPath = Join-Path $routerOutput 'bootstrap.json'
$routerExe = Join-Path $routerOutput 'codex-model-router.exe'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$settings = @{
    codex_binary = $originalCodex
    grok_models = $grokModels
    native_models = $nativeModels
    grok_provider = 'ocx-grok'
}
$bootstrap = @{
    python_executable = $pythonBinary
    router_entry = Join-Path $integrationRoot 'scripts/model_router.py'
    router_settings = $settingsPath
}
[IO.File]::WriteAllText($settingsPath, ($settings | ConvertTo-Json -Depth 6), $utf8)
[IO.File]::WriteAllText($bootstrapPath, ($bootstrap | ConvertTo-Json -Depth 6), $utf8)
& $compiler /nologo /target:exe ("/out:" + $routerExe) /reference:System.Web.Extensions.dll (Join-Path $integrationRoot 'scripts/model_router_bootstrap.cs')
if ($LASTEXITCODE -ne 0) { throw 'Bootstrap compilation failed; no desktop launch has occurred.' }
& $routerExe --version
if ($LASTEXITCODE -ne 0) { throw 'Original Codex passthrough failed; inspect the original executable path.' }
```

`configure.py` remains responsible for its provider and startup catalog. The files above
only describe the optional router. They neither change your global default model nor
install, log in to, or launch an upstream proxy.

Advanced callers can pass an explicit list to `catalog.extend_native_catalog` or
`catalog.refresh_catalog` when maintaining their owned generated catalog. All requested
rows must exist with valid metadata; duplicates and invalid/native substitutions fail.
Preserve the native source and align `grok_models` with the actual selected rows. Do not
infer that other advertised models have been tested from their presence in a catalog.

## 3. Launch only the selected desktop through the router

Normally quit the existing desktop first so a second launch does not simply reuse its
old backend. Keep your already configured proxy lifecycle as it is. Replace this app path:

```powershell
$desktopApp = 'C:/tools/Codex.exe'
if (-not (Test-Path -LiteralPath $desktopApp -PathType Leaf)) { throw 'Select the actual desktop executable.' }
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $desktopApp
$startInfo.UseShellExecute = $false
$startInfo.EnvironmentVariables['CODEX_CLI_PATH'] = $routerExe
[Diagnostics.Process]::Start($startInfo) | Out-Null
```

The override belongs only to that launched app. No global environment variable,
credential, installed Codex binary or database is edited. A host update can move the
original executable or change the launch/protocol contract; recheck those inputs.

Verify one new Grok task, then an idle GPT→Grok→GPT switch with a harmless remembered
marker. Check effective model/provider metadata as well as the UI. The stored creation
provider may remain historical after a runtime switch. Tool/approval messages must
still reach the app, and current cwd/permission settings must survive the switch.

The router rejects a cross-provider change during an active response: let it finish or
stop it through the normal UI before retrying. It does not interrupt work automatically.
A failed or policy-changing resume attempts restoration of the previous binding before
returning the error; a failure is never turned into a successful model reply.

## Recovery and scope

Launch the original desktop normally, without the child `CODEX_CLI_PATH` override, to
return to the earlier bridge-created-task route. Preserve the local routing files while
diagnosing; no history migration or deletion is necessary. If rolling back the provider
or catalog as well, follow [the separate configuration recovery](SETUP.md#4-recover-or-roll-back).

The [video](https://www.bilibili.com/video/BV1rRYk63ER5/) also shows local native Imagine.
That CLI wrapper and its machine-specific media-navigation patch are not in this package.
Native cross-provider Subagents, automatic permission inheritance, long-session quality
and account-level token savings are not established by this router's finite controls.
