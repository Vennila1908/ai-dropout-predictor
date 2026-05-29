<#
.SYNOPSIS
  Shared helpers for the AI Dropout Predictor setup / launcher scripts.

.DESCRIPTION
  Dot-source from another script:    . "$PSScriptRoot\_lib.ps1"

  Currently exposes Find-Python311Plus, which works around the common
  Windows footgun where `python` on PATH resolves to a stale Python 2.7
  or to the Microsoft Store alias stub, while a perfectly good Python
  3.11+ is reachable via the `py` launcher.
#>

function Find-Python311Plus {
<#
.SYNOPSIS
  Locate a Python 3.11+ interpreter, preferring the Windows `py` launcher.

.OUTPUTS
  PSCustomObject with the following properties:
    Found    [bool]    - $true on success, $false otherwise.
    Exe      [string]  - Executable to invoke (e.g. 'py', 'python3').
    Args     [string[]]- Leading args (e.g. @('-3.12') for `py -3.12`).
    Invoke   [string]  - Human-readable form (e.g. 'py -3.12').
    Version  [string]  - Parsed version like '3.12.4'.
    Attempts [string[]]- One line per probed candidate (for error reporting).

  Callers run Python as:
    & $info.Exe @($info.Args + '-m','venv',$venvDir)
#>
  $candidates = @(
    [pscustomobject]@{ Exe = 'py';      Args = @('-3.12'); Invoke = 'py -3.12' },
    [pscustomobject]@{ Exe = 'py';      Args = @('-3.11'); Invoke = 'py -3.11' },
    [pscustomobject]@{ Exe = 'py';      Args = @('-3');    Invoke = 'py -3' },
    [pscustomobject]@{ Exe = 'python3'; Args = @();        Invoke = 'python3' },
    [pscustomobject]@{ Exe = 'python';  Args = @();        Invoke = 'python' }
  )

  $attempts = New-Object System.Collections.Generic.List[string]

  foreach ($c in $candidates) {
    $cmd = Get-Command $c.Exe -ErrorAction SilentlyContinue
    if (-not $cmd) {
      $attempts.Add(("{0,-10} : not found on PATH" -f $c.Invoke))
      continue
    }

    # The Microsoft Store alias stub for `python` / `python3` lives under
    # %LOCALAPPDATA%\Microsoft\WindowsApps and, when run without args, just
    # prints a redirect message and exits. Note it but still probe, since
    # the probe will simply fail to match the version regex below.
    $isStoreStub = $false
    if ($cmd.Source) {
      $isStoreStub = ($cmd.Source -like '*\Microsoft\WindowsApps\*')
    }

    $verOut = ''
    try {
      # Suspend Stop semantics for the probe: native stderr should not
      # become a terminating error during discovery.
      $oldEAP = $ErrorActionPreference
      $ErrorActionPreference = 'Continue'
      try {
        $verOut = (& $c.Exe @($c.Args + '--version') 2>&1 | ForEach-Object {
          if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message } else { $_ }
        } | Out-String).Trim()
      } finally {
        $ErrorActionPreference = $oldEAP
      }
    } catch {
      $attempts.Add(("{0,-10} : invocation failed ({1})" -f $c.Invoke, $_.Exception.Message))
      continue
    }

    # Check for known error patterns BEFORE the version regex so that messages
    # like "Python 3.12 not found!" are not mistakenly matched as a valid version.
    if ($isStoreStub) {
      $attempts.Add(("{0,-10} : Windows Store alias stub (no real Python installed at {1})" -f $c.Invoke, $cmd.Source))
      continue
    }
    if ($verOut -match 'No suitable Python runtime|Requested Python version|Can.t find a suitable Python|No Python at|not found') {
      $attempts.Add(("{0,-10} : py launcher reports no matching Python installed" -f $c.Invoke))
      continue
    }

    $m = [regex]::Match($verOut, 'Python\s+(\d+)\.(\d+)(?:\.(\d+))?')
    if (-not $m.Success) {
      $oneLine = (($verOut -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1))
      if ([string]::IsNullOrWhiteSpace($oneLine)) { $oneLine = '(no output)' }
      $attempts.Add(("{0,-10} : unexpected --version output: {1}" -f $c.Invoke, $oneLine.Trim()))
      continue
    }

    $major = [int]$m.Groups[1].Value
    $minor = [int]$m.Groups[2].Value
    $patch = if ($m.Groups[3].Success) { '.' + $m.Groups[3].Value } else { '' }
    $verStr = '{0}.{1}{2}' -f $major, $minor, $patch

    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
      $attempts.Add(("{0,-10} : Python {1} (too old; need >= 3.11)" -f $c.Invoke, $verStr))
      continue
    }

    return [pscustomobject]@{
      Found    = $true
      Exe      = $c.Exe
      Args     = $c.Args
      Invoke   = $c.Invoke
      Version  = $verStr
      Attempts = $attempts.ToArray()
    }
  }

  return [pscustomobject]@{
    Found    = $false
    Exe      = $null
    Args     = @()
    Invoke   = $null
    Version  = $null
    Attempts = $attempts.ToArray()
  }
}
