@echo off
REM Example CLI usage with organized output directories

REM Set up directory structure for a project
set PROJECT_DIR=crop_monitoring_2024
if not exist %PROJECT_DIR% mkdir %PROJECT_DIR%

echo ===================================
echo Sentinel-2 Crop Monitoring Project
echo ===================================

REM 1. Search for available imagery
echo.
echo Step 1: Searching for imagery...
geodes-sentinel2 search ^
    examples\data\sample_area.geojson ^
    -s 2024-03-01 ^
    -e 2024-06-30 ^
    -c 20 ^
    -d %PROJECT_DIR% ^
    -o search_results_q1_q2.json

REM 2. Download the products
echo.
echo Step 2: Downloading products...
geodes-sentinel2 download ^
    %PROJECT_DIR%\search_results_q1_q2.json ^
    -z sample_field ^
    -m 5 ^
    -o %PROJECT_DIR%\downloads

REM 3. Crop to area of interest
echo.
echo Step 3: Cropping bands...
geodes-sentinel2 crop ^
    %PROJECT_DIR%\downloads ^
    examples\data\sample_area.geojson ^
    -z sample_field ^
    -b B02 B03 B04 B08 B11 B12 ^
    -o %PROJECT_DIR%\crops

REM 4. Calculate vegetation indices
echo.
echo Step 4: Calculating vegetation indices...
geodes-sentinel2 indices ^
    %PROJECT_DIR%\crops ^
    -i NDVI EVI NDWI SAVI ^
    -o %PROJECT_DIR%\indices

REM 5. Alternative: All-in-one processing
echo.
echo Alternative: Complete processing pipeline...
geodes-sentinel2 process ^
    examples\data\sample_area.geojson ^
    -s 2024-03-01 ^
    -e 2024-03-31 ^
    -c 20 ^
    -m 2 ^
    -i NDVI EVI ^
    --keep-zips ^
    -o %PROJECT_DIR%\march_analysis ^
    --csv %PROJECT_DIR%\march_results.csv

echo.
echo ===================================
echo Processing Complete!
echo ===================================
echo.
echo Output structure:
echo %PROJECT_DIR%\
echo   - search_results_q1_q2.json    : Search results
echo   - downloads\                   : Original ZIP files
echo   - crops\                       : Cropped bands
echo   - indices\                     : Vegetation indices
echo   - march_analysis\              : March complete analysis
echo       - downloads\               : Preserved ZIPs
echo       - crops\                   : Cropped bands
echo       - indices\                 : NDVI, EVI
echo   - march_results.csv            : Processing metadata