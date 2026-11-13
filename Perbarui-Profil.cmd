@echo off
rem Perbarui kartu statistik dan ular kontribusi profil GitHub dari komputer ini, lalu push.
rem Dipakai selama GitHub Actions akun terkunci karena masalah tagihan. Token diambil dari git credential manager.
setlocal
cd /d "%~dp0"
python .github\scripts\stats.py || exit /b 1
node .github\scripts\snake.cjs || exit /b 1
git add assets\stats-*.svg assets\snake-*.svg
git diff --cached --quiet && (echo Tidak ada yang berubah.& exit /b 0)
git commit -q -m "Perbarui statistik profil."
git push -q origin main && echo Profil diperbarui: https://github.com/zoembut
