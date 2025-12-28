@echo off
setlocal enabledelayedexpansion

echo Detecting Python...

REM Try python
where python >nul 2>&1
if %errorlevel%==0 (
    set PY=python
) else (
    REM Try python3
    where python3 >nul 2>&1
    if %errorlevel%==0 (
        set PY=python3
    ) else (
        echo No Python installation detected!
        echo Please install Python before running this script.
        exit /b 1
    )
)

echo Using interpreter: %PY%
echo Upgrading pip...

%PY% -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip. Stopping...
    exit /b 1
)

echo Pip upgraded successfully.
echo ------------------------------------

echo Installing root requirements...
if exist requirements.txt (
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install root requirements
        exit /b 1
    )
    echo Root requirements installed
) else (
    echo No requirements.txt found in root
)

echo.
echo Scanning modules folder...

if not exist modules (
    echo Modules folder not found
    exit /b 0
)

for /d %%m in (modules\*) do (
    if exist "%%m\requirements.txt" (
        echo Installing requirements for %%m...
        %PY% -m pip install -r "%%m\requirements.txt"
        if errorlevel 1 (
            echo Failed to install requirements for %%m
        ) else (
            echo Completed %%m
        )
    )
)

echo.
echo All installations completed
