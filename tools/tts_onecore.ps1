# tts_onecore.ps1 — đọc văn bản UTF-8 ra .wav bằng giọng Windows OneCore.
#
# VÌ SAO PHẢI QUA WINRT. `KY_LUAT_THUC_THI.md` Chương II mục 2 đòi giọng
# `MSTTS_V110_viVN_An`. Đo 02/09/2026, đọc registry:
#
#   HKLM\SOFTWARE\Microsoft\Speech\Voices\Tokens           2 giọng, cả hai en-US
#   HKLM\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens   4 giọng, CÓ viVN_An
#
# `System.Speech` chỉ nhìn nhánh thứ nhất nên nó báo "không có giọng tiếng
# Việt" — sai. Giọng có thật, chỉ nằm ở nhánh OneCore, và
# `Windows.Media.SpeechSynthesis` (WinRT) mới với tới được.
#
# CHẠY BẰNG `powershell` (5.1), KHÔNG PHẢI `pwsh` (7+): PowerShell 7 đã bỏ hẳn
# lớp tương tác WinRT, gọi vào là lỗi kiểu.
#
# VĂN BẢN ĐI QUA TỆP, KHÔNG QUA DÒNG LỆNH. `CLAUDE.md` mục 4: PowerShell nuốt
# dấu — "Thủ đô" thành "Thu do". Đọc bằng `File.ReadAllText(..., UTF8)` thì
# dấu còn nguyên.
param(
    [Parameter(Mandatory = $true)][string]$InFile,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [string]$VoiceId = "MSTTS_V110_viVN_An"
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$text = [System.IO.File]::ReadAllText($InFile, [System.Text.Encoding]::UTF8)
if ([string]::IsNullOrWhiteSpace($text)) { Write-Output "LOI: van ban rong"; exit 2 }

$syn = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media, ContentType=WindowsRuntime]::new()
$voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media, ContentType=WindowsRuntime]::AllVoices |
         Where-Object { $_.Id -like ("*" + $VoiceId + "*") } | Select-Object -First 1
if (-not $voice) { Write-Output ("LOI: khong thay giong " + $VoiceId); exit 2 }
$syn.Voice = $voice

# WinRT trả IAsyncOperation; PowerShell 5.1 phải tự bắc cầu sang Task.
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

$op = $syn.SynthesizeTextToStreamAsync($text)
$task = $asTask.MakeGenericMethod([Windows.Media.SpeechSynthesis.SpeechSynthesisStream]).Invoke($null, @($op))
if (-not $task.Wait(180000)) { Write-Output "LOI: TTS qua 180s"; exit 2 }
$stream = $task.Result

$reader = [Windows.Storage.Streams.DataReader, Windows.Storage, ContentType=WindowsRuntime]::new($stream.GetInputStreamAt(0))
$loadOp = $reader.LoadAsync([uint32]$stream.Size)
$loadTask = $asTask.MakeGenericMethod([uint32]).Invoke($null, @($loadOp))
if (-not $loadTask.Wait(180000)) { Write-Output "LOI: doc stream qua 180s"; exit 2 }

$bytes = New-Object byte[] $stream.Size
$reader.ReadBytes($bytes)
[System.IO.File]::WriteAllBytes($OutFile, $bytes)
Write-Output ("OK " + $bytes.Length)
