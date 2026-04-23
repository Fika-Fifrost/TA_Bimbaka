@echo off
echo Resetting SQLite database...

REM 1. Hapus file database SQLite
if exist db.sqlite3 del db.sqlite3

REM 2. Hapus semua file migrations (kecuali __init__.py)
if exist belajar\migrations\0*.py del belajar\migrations\0*.py

REM 3. Buat ulang __init__.py
echo. > belajar\migrations\__init__.py

REM 4. Buat migrations baru
echo Creating new migrations...
python manage.py makemigrations

REM 5. Apply migrations
echo Applying migrations...
python manage.py migrate

REM 6. Buat superuser baru
echo Creating superuser...
python manage.py createsuperuser

echo.
echo Database reset complete!
pause