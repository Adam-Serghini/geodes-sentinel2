@echo off
REM Batch Processing Example using CLI (Windows)
REM This example shows how to process multiple agricultural fields in batch mode

echo ========================================
echo Batch Processing with CLI
echo ========================================

REM 1. Create multiple GeoJSON files with different dates
echo Creating sample GeoJSON files...

REM Field 1: Summer wheat monitoring
(
echo {
echo   "type": "FeatureCollection",
echo   "features": [{
echo     "type": "Feature",
echo     "properties": {
echo       "Name": "WheatField_North",
echo       "begin": "2024-06-01T00:00:00Z",
echo       "end": "2024-08-31T00:00:00Z",
echo       "crop": "wheat"
echo     },
echo     "geometry": {
echo       "type": "Polygon",
echo       "coordinates": [[
echo         [22.7724, 5.9666],
echo         [22.7751, 5.9675],
echo         [22.7777, 5.9643],
echo         [22.7750, 5.9633],
echo         [22.7724, 5.9666]
echo       ]]
echo     }
echo   }]
echo }
) > field1_wheat.geojson

REM Field 2: Spring corn monitoring
(
echo {
echo   "type": "FeatureCollection",
echo   "features": [{
echo     "type": "Feature",
echo     "properties": {
echo       "Name": "CornField_South",
echo       "begin": "2024-03-01T00:00:00Z",
echo       "end": "2024-05-31T00:00:00Z",
echo       "crop": "corn"
echo     },
echo     "geometry": {
echo       "type": "Polygon",
echo       "coordinates": [[
echo         [23.7724, 4.9666],
echo         [23.7751, 4.9675],
echo         [23.7777, 4.9643],
echo         [23.7750, 4.9633],
echo         [23.7724, 4.9666]
echo       ]]
echo     }
echo   }]
echo }
) > field2_corn.geojson

REM Field 3: Vineyard annual monitoring
(
echo {
echo   "type": "FeatureCollection",
echo   "features": [{
echo     "type": "Feature",
echo     "properties": {
echo       "Name": "VineyardWest",
echo       "begin": "2024-01-01T00:00:00Z",
echo       "end": "2024-12-31T00:00:00Z",
echo       "crop": "vineyard"
echo     },
echo     "geometry": {
echo       "type": "Polygon",
echo       "coordinates": [[
echo         [24.7724, 3.9666],
echo         [24.7751, 3.9675],
echo         [24.7777, 3.9643],
echo         [24.7750, 3.9633],
echo         [24.7724, 3.9666]
echo       ]]
echo     }
echo   }]
echo }
) > field3_vineyard.geojson

echo Created 3 GeoJSON files with different date ranges

REM 2. Run batch processing
echo.
echo Running batch processing for all fields...
echo Each field will use its own dates from GeoJSON properties
echo.

geodes-sentinel2 batch ^
    field1_wheat.geojson ^
    field2_corn.geojson ^
    field3_vineyard.geojson ^
    .\batch_output ^
    --cloud 30 ^
    --indices NDVI EVI NDWI ^
    --csv batch_results.csv

echo.
echo ========================================
echo Batch processing complete!
echo ========================================
echo.
echo Output structure:
echo batch_output\
echo +-- downloads\        # ZIP files for all areas
echo +-- crops\           # Cropped bands for all areas  
echo +-- indices\         # NDVI, EVI, NDWI for all areas
echo +-- batch_results.csv # Combined results for all fields
echo.
echo Each field was processed with its own date range:
echo - WheatField_North: June-August 2024 (summer growing season)
echo - CornField_South: March-May 2024 (spring planting season)
echo - VineyardWest: Full year 2024 (annual monitoring)

pause